import os
import sys
import json
import uuid
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, AsyncIterator, Callable, Awaitable
from craftlab_ctl.core.paths import CtlPaths


class TransportError(Exception):
    pass


class TransportAuthError(TransportError):
    pass


class TransportMessage:
    def __init__(self, action: str, payload: Dict[str, Any], auth_token: Optional[str] = None):
        self.action = action
        self.payload = payload
        self.auth_token = auth_token

    def to_line(self) -> bytes:
        data = {
            "action": self.action,
            "payload": self.payload,
            "auth_token": self.auth_token,
        }
        return (json.dumps(data) + "\n").encode("utf-8")

    @classmethod
    def from_line(cls, line: bytes) -> "TransportMessage":
        data = json.loads(line.decode("utf-8").strip())
        return cls(
            action=data.get("action", ""),
            payload=data.get("payload", {}),
            auth_token=data.get("auth_token"),
        )


class LocalControlServer:
    def __init__(
        self,
        paths: CtlPaths,
        handler: Callable[[str, Dict[str, Any]], AsyncIterator[Dict[str, Any]]],
        force_tcp: bool = False,
    ):
        self.paths = paths
        self.handler = handler
        self.force_tcp = force_tcp
        self.is_windows = sys.platform == "win32" or force_tcp
        self._server: Optional[asyncio.Server] = None
        self._token: Optional[str] = None
        self._endpoint_file = self.paths.run_dir / "craftctld.endpoint"
        self._sock_file = self.paths.run_dir / "craftctld.sock"

    async def start(self) -> None:
        self.paths.ensure_directories()
        if self.is_windows:
            self._token = uuid.uuid4().hex
            self._server = await asyncio.start_server(
                self._handle_client,
                host="127.0.0.1",
                port=0,
            )
            sockets = self._server.sockets
            if not sockets:
                raise TransportError("Failed to bind TCP server")
            port = sockets[0].getsockname()[1]
            endpoint_data = {
                "transport": "tcp",
                "host": "127.0.0.1",
                "port": port,
                "token": self._token,
            }
            self._endpoint_file.write_text(json.dumps(endpoint_data), encoding="utf-8")
        else:
            if self._sock_file.exists():
                self._sock_file.unlink()
            self._server = await asyncio.start_unix_server(
                self._handle_client,
                path=str(self._sock_file),
            )
            # Set socket permissions to 0660 (user + group rw)
            try:
                os.chmod(self._sock_file, 0o660)
            except Exception:
                pass
            endpoint_data = {
                "transport": "unix",
                "path": str(self._sock_file),
            }
            self._endpoint_file.write_text(json.dumps(endpoint_data), encoding="utf-8")

    async def _handle_client(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        try:
            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                try:
                    msg = TransportMessage.from_line(line)
                    # Verify auth token if on Windows/TCP
                    if self.is_windows and msg.auth_token != self._token:
                        err_line = (
                            json.dumps({"event": "error", "error": "Invalid auth token"}) + "\n"
                        ).encode("utf-8")
                        writer.write(err_line)
                        await writer.drain()
                        break

                    async for event in self.handler(msg.action, msg.payload):
                        out_line = (json.dumps(event) + "\n").encode("utf-8")
                        writer.write(out_line)
                        await writer.drain()

                except Exception as e:
                    err_line = (
                        json.dumps({"event": "error", "error": str(e)}) + "\n"
                    ).encode("utf-8")
                    writer.write(err_line)
                    await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def stop(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            self._server = None
        if self._endpoint_file.exists():
            try:
                self._endpoint_file.unlink()
            except Exception:
                pass
        if self._sock_file.exists():
            try:
                self._sock_file.unlink()
            except Exception:
                pass


class LocalControlClient:
    def __init__(self, paths: CtlPaths):
        self.paths = paths
        self._endpoint_file = self.paths.run_dir / "craftctld.endpoint"

    def is_daemon_running(self) -> bool:
        return self._endpoint_file.exists()

    async def execute(
        self, action: str, payload: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        if not self._endpoint_file.exists():
            raise TransportError("craftctld daemon is not running (endpoint file not found)")

        try:
            endpoint_data = json.loads(self._endpoint_file.read_text(encoding="utf-8"))
        except Exception as e:
            raise TransportError(f"Failed to read endpoint file: {e}")

        transport_type = endpoint_data.get("transport")
        if transport_type == "tcp":
            host = endpoint_data.get("host", "127.0.0.1")
            port = endpoint_data.get("port")
            token = endpoint_data.get("token")
            try:
                reader, writer = await asyncio.open_connection(host=host, port=port)
            except Exception as e:
                raise TransportError(f"Failed to connect to daemon at {host}:{port}: {e}")
            msg = TransportMessage(action=action, payload=payload, auth_token=token)
        else:
            path = endpoint_data.get("path")
            try:
                reader, writer = await asyncio.open_unix_connection(path=path)
            except Exception as e:
                raise TransportError(f"Failed to connect to daemon socket at {path}: {e}")
            msg = TransportMessage(action=action, payload=payload)

        try:
            writer.write(msg.to_line())
            await writer.drain()

            while not reader.at_eof():
                line = await reader.readline()
                if not line:
                    break
                try:
                    event = json.loads(line.decode("utf-8").strip())
                    yield event
                    if event.get("event") in ("result", "error"):
                        break
                except Exception:
                    pass
        finally:
            writer.close()
            await writer.wait_closed()
