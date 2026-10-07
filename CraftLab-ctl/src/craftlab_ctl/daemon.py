import sys
import asyncio
import signal
from pathlib import Path
from typing import Dict, Any, AsyncIterator, Optional

from craftlab_ctl.core.paths import get_paths, CtlPaths
from craftlab_ctl.core.models import (
    OperationResult,
    CheckStatus,
    AuditEvent,
    StepEvent,
    DangerLevel,
)
from craftlab_ctl.core.audit import AuditLogger
from craftlab_ctl.core.lock import OperationLock, LockError
from craftlab_ctl.transport import LocalControlServer
from craftlab_ctl.sdk import PluginRegistry, Context, VetoException
from craftlab_ctl.plugins.lifecycle import LifecyclePlugin
from craftlab_ctl.plugins.core import CorePlugin


class DaemonService:
    def __init__(self, paths: Optional[CtlPaths] = None):
        self.paths = paths or get_paths()
        self.registry = PluginRegistry()
        self.lock = OperationLock()
        self.audit = AuditLogger(state_dir=self.paths.state_dir)
        self.server: Optional[LocalControlServer] = None
        self._running = False

    def setup(self) -> None:
        self.paths.ensure_directories()
        # Register built-ins
        self.registry.register_plugin(LifecyclePlugin())
        self.registry.register_plugin(CorePlugin())
        # Discover third-party plugins from entry points
        self.registry.discover_and_load()

    async def handle_action(
        self, action: str, payload: Dict[str, Any]
    ) -> AsyncIterator[Dict[str, Any]]:
        if action == "ping":
            yield {"event": "result", "data": {"status": "pong"}}
            return

        if action == "get_schemas":
            schemas = self.registry.list_command_schemas()
            yield {"event": "result", "data": {"schemas": schemas}}
            return

        if action == "doctor":
            ctx = Context(paths=self.paths, caller_id="daemon")
            checks = await self.registry.execute_checks(ctx)
            checks_data = [c.model_dump() for c in checks]
            has_fail = any(c["status"] == "FAIL" for c in checks_data)
            has_warn = any(c["status"] == "WARN" for c in checks_data)
            overall = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")
            yield {"event": "result", "data": {"overall": overall, "checks": checks_data}}
            return

        if action == "execute":
            cmd_name = payload.get("command")
            params = payload.get("parameters", {})
            caller_id = payload.get("caller_id", "cli")

            cmd_def = self.registry.get_command(cmd_name)
            if not cmd_def:
                yield {
                    "event": "error",
                    "error": f"Unknown command '{cmd_name}'",
                }
                return

            # Acquire lock if mutates
            acquired_lock = False
            if cmd_def.mutates:
                try:
                    await self.lock.acquire(cmd_name)
                    acquired_lock = True
                except LockError as e:
                    yield {"event": "error", "error": str(e)}
                    return

            queue: asyncio.Queue = asyncio.Queue()

            async def step_cb(step_evt: StepEvent):
                await queue.put({"event": "step", **step_evt.model_dump()})

            async def emit_cb(evt_name: str, evt_data: Dict[str, Any]):
                await queue.put({"event": "custom", "name": evt_name, "data": evt_data})

            ctx = Context(
                paths=self.paths,
                caller_id=caller_id,
                step_callback=step_cb,
                emit_callback=emit_cb,
            )

            async def run_task():
                try:
                    # Dispatch pre-execution hook
                    await self.registry.dispatch_hook(
                        f"before_{cmd_name}", ctx, parameters=params
                    )
                    # Run command
                    res = await cmd_def.func(ctx, **params)
                    if not isinstance(res, OperationResult):
                        res = OperationResult.ok(data=res)

                    outcome = "success" if res.success else "failed"
                    self.audit.log(
                        AuditEvent(
                            caller_id=caller_id,
                            command=cmd_name,
                            parameters=params,
                            outcome=outcome,
                            error=res.error,
                        )
                    )
                    await queue.put({"event": "result", "data": res.model_dump()})
                except VetoException as ve:
                    self.audit.log(
                        AuditEvent(
                            caller_id=caller_id,
                            command=cmd_name,
                            parameters=params,
                            outcome="vetoed",
                            error=ve.reason,
                        )
                    )
                    await queue.put(
                        {
                            "event": "error",
                            "error": f"Operation vetoed: {ve.reason}",
                        }
                    )
                except Exception as e:
                    self.audit.log(
                        AuditEvent(
                            caller_id=caller_id,
                            command=cmd_name,
                            parameters=params,
                            outcome="failed",
                            error=str(e),
                        )
                    )
                    await queue.put({"event": "error", "error": f"Execution error: {e}"})
                finally:
                    if acquired_lock:
                        self.lock.release()
                    await queue.put(None)  # Sentinel to end stream

            task = asyncio.create_task(run_task())

            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item

            await task
            return

        yield {"event": "error", "error": f"Unknown daemon action '{action}'"}

    async def start(self) -> None:
        self.setup()
        self.server = LocalControlServer(paths=self.paths, handler=self.handle_action)
        await self.server.start()
        self._running = True

    async def stop(self) -> None:
        if self.server:
            await self.server.stop()
            self._running = False


async def run_daemon():
    daemon = DaemonService()
    await daemon.start()
    print("craftctld daemon started.")

    stop_event = asyncio.Event()

    def signal_handler():
        stop_event.set()

    if sys.platform != "win32":
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, signal_handler)

    try:
        if sys.platform == "win32":
            while not stop_event.is_set():
                await asyncio.sleep(1)
        else:
            await stop_event.wait()
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        print("Shutting down craftctld daemon...")
        await daemon.stop()
        print("craftctld daemon stopped.")


def main():
    try:
        asyncio.run(run_daemon())
        return 0
    except Exception as e:
        print(f"Error starting craftctld: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
