import os
import sys
import time
import asyncio
from pathlib import Path
import pytest
from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.daemon import DaemonService
from craftlab_ctl.transport import LocalControlClient


@pytest.mark.asyncio
async def test_e2e_ctl_full_lifecycle():
    # Target port for isolated integration testing
    test_port = 8991
    paths = get_paths()

    # Ensure any stray backend PID from previous test runs is stopped
    from craftlab_ctl.supervisor import ProcessSupervisor
    supervisor = ProcessSupervisor(paths=paths, service_name="backend")
    if supervisor.is_running():
        supervisor.stop_process(timeout=5.0)

    # 1. Start daemon service
    daemon = DaemonService(paths=paths)
    await daemon.start()

    client = LocalControlClient(paths=paths)
    assert client.is_daemon_running()

    try:
        # 2. Check initial status (should be stopped)
        status_events = []
        async for evt in client.execute("execute", {"command": "status", "parameters": {"port": test_port}}):
            status_events.append(evt)
        result_evt = next((e for e in status_events if e.get("event") == "result"), None)
        assert result_evt is not None
        assert result_evt["data"]["data"]["status"] == "stopped"

        # 3. Start backend service via daemon
        start_events = []
        async for evt in client.execute(
            "execute",
            {"command": "start", "parameters": {"port": test_port, "timeout": 20}},
        ):
            start_events.append(evt)

        start_res = next((e for e in start_events if e.get("event") == "result"), None)
        assert start_res is not None
        assert start_res["data"]["success"] is True
        pid = start_res["data"]["data"]["pid"]
        assert pid is not None
        assert supervisor.is_running()

        # 4. Check status (should be running & healthy)
        status_events = []
        async for evt in client.execute("execute", {"command": "status", "parameters": {"port": test_port}}):
            status_events.append(evt)
        status_res = next((e for e in status_events if e.get("event") == "result"), None)
        assert status_res is not None
        assert status_res["data"]["data"]["status"] == "running"
        assert status_res["data"]["data"]["health"] == "healthy"

        # 5. Run doctor diagnostics via daemon
        doc_events = []
        async for evt in client.execute("doctor", {}):
            doc_events.append(evt)
        doc_res = next((e for e in doc_events if e.get("event") == "result"), None)
        assert doc_res is not None
        assert doc_res["data"]["overall"] in ("PASS", "WARN")

        # 6. Stop backend service via daemon
        stop_events = []
        async for evt in client.execute("execute", {"command": "stop", "parameters": {"timeout": 10}}):
            stop_events.append(evt)
        stop_res = next((e for e in stop_events if e.get("event") == "result"), None)
        assert stop_res is not None
        assert stop_res["data"]["success"] is True
        assert not supervisor.is_running()

    finally:
        # Stop daemon
        await daemon.stop()
        if supervisor.is_running():
            supervisor.stop_process(timeout=3.0)
