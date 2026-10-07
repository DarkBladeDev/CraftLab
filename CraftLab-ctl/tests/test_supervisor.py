import sys
import tempfile
from pathlib import Path
import pytest
from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.supervisor import ProcessSupervisor


def test_supervisor_process_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        supervisor = ProcessSupervisor(paths=paths, service_name="dummy")

        assert not supervisor.is_running()
        assert supervisor.get_pid() is None

        # Start dummy python process
        cmd = [sys.executable, "-c", "import time; time.sleep(30)"]
        pid = supervisor.start_process(cmd=cmd)

        assert pid > 0
        assert supervisor.is_running()
        assert supervisor.get_pid() == pid

        status = supervisor.get_status()
        assert status["status"] == "running"
        assert status["pid"] == pid
        assert status["service"] == "dummy"

        # Stop process
        stopped = supervisor.stop_process(timeout=5.0)
        assert stopped is True
        assert not supervisor.is_running()
        assert supervisor.get_pid() is None


def test_supervisor_already_running_error():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        supervisor = ProcessSupervisor(paths=paths, service_name="dummy")

        cmd = [sys.executable, "-c", "import time; time.sleep(30)"]
        supervisor.start_process(cmd=cmd)

        with pytest.raises(RuntimeError) as exc_info:
            supervisor.start_process(cmd=cmd)
        assert "already running" in str(exc_info.value)

        supervisor.stop_process(timeout=3.0)
