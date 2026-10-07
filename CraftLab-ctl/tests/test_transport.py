import tempfile
from pathlib import Path
from typing import Dict, Any, AsyncIterator
import pytest
from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.transport import LocalControlServer, LocalControlClient, TransportError


async def sample_handler(action: str, payload: Dict[str, Any]) -> AsyncIterator[Dict[str, Any]]:
    yield {"event": "step", "step": "step_1", "status": "running"}
    yield {"event": "step", "step": "step_1", "status": "ok"}
    if action == "ping":
        yield {"event": "result", "data": {"response": "pong", "payload": payload}}
    elif action == "fail":
        yield {"event": "error", "error": "simulated failure"}
    else:
        yield {"event": "result", "data": {"echo": action}}


@pytest.mark.asyncio
async def test_transport_roundtrip_tcp():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        server = LocalControlServer(paths=paths, handler=sample_handler, force_tcp=True)
        await server.start()

        client = LocalControlClient(paths=paths)
        assert client.is_daemon_running()

        events = []
        async for event in client.execute("ping", {"message": "hello"}):
            events.append(event)

        assert len(events) == 3
        assert events[0]["event"] == "step"
        assert events[1]["event"] == "step"
        assert events[2]["event"] == "result"
        assert events[2]["data"]["response"] == "pong"
        assert events[2]["data"]["payload"] == {"message": "hello"}

        await server.stop()
        assert not client.is_daemon_running()


@pytest.mark.asyncio
async def test_transport_error_event():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        server = LocalControlServer(paths=paths, handler=sample_handler, force_tcp=True)
        await server.start()

        client = LocalControlClient(paths=paths)
        events = []
        async for event in client.execute("fail", {}):
            events.append(event)

        assert any(e.get("event") == "error" for e in events)

        await server.stop()


@pytest.mark.asyncio
async def test_transport_daemon_not_running():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        client = LocalControlClient(paths=paths)
        assert not client.is_daemon_running()

        with pytest.raises(TransportError):
            async for _ in client.execute("ping", {}):
                pass
