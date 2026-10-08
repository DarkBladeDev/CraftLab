import tempfile
from pathlib import Path
import pytest
from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.sdk import Context
from craftlab_ctl.plugins.lifecycle import LifecyclePlugin
from craftlab_ctl.plugins.core import CorePlugin


@pytest.mark.asyncio
async def test_lifecycle_plugin_status_stopped():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        ctx = Context(paths=paths)
        plugin = LifecyclePlugin()

        res = await plugin.status(ctx)
        assert res.success is True
        assert res.data["status"] == "stopped"
        assert res.data["pid"] is None


@pytest.mark.asyncio
async def test_core_plugin_doctor():
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        ctx = Context(paths=paths)
        plugin = CorePlugin()

        res = await plugin.doctor(ctx)
        assert res.success is True
        assert res.data["overall"] in ("PASS", "WARN")
        checks = res.data["checks"]
        assert len(checks) >= 3
        check_ids = [c["check_id"] for c in checks]
        assert "env.directories" in check_ids
        assert "env.python" in check_ids
        assert "backend.config" in check_ids


@pytest.mark.asyncio
async def test_lifecycle_plugin_dynamic_port(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        ctx = Context(paths=paths)
        plugin = LifecyclePlugin()

        monkeypatch.setenv("CRAFTLAB_PORT", "9222")
        monkeypatch.setenv("CRAFTLAB_HOST", "0.0.0.0")

        captured = {}
        def mock_start(cmd, cwd=None, env=None, stdout_file=None, stderr_file=None):
            captured["cmd"] = cmd
            captured["env"] = env
            return 12345

        class MockSup:
            def is_running(self):
                return False
            def start_process(self, cmd, cwd=None, env=None, stdout_file=None, stderr_file=None):
                return mock_start(cmd, cwd=cwd, env=env, stdout_file=stdout_file, stderr_file=stderr_file)
            def stop_process(self, timeout=10.0):
                return True

        monkeypatch.setattr(plugin, "_get_supervisor", lambda c: MockSup())

        await plugin.start(ctx, timeout=0)
        assert captured["env"]["CRAFTLAB_PORT"] == "9222"
        assert captured["env"]["CRAFTLAB_HOST"] == "0.0.0.0"
        assert "--port" in captured["cmd"]
        port_idx = captured["cmd"].index("--port")
        assert captured["cmd"][port_idx + 1] == "9222"
        assert "--host" in captured["cmd"]
        host_idx = captured["cmd"].index("--host")
        assert captured["cmd"][host_idx + 1] == "0.0.0.0"


@pytest.mark.asyncio
async def test_lifecycle_plugin_explicit_port_override(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        paths = get_paths(home=Path(tmpdir))
        ctx = Context(paths=paths)
        plugin = LifecyclePlugin()

        monkeypatch.setenv("CRAFTLAB_PORT", "9222")
        captured = {}
        def mock_start(cmd, cwd=None, env=None, stdout_file=None, stderr_file=None):
            captured["cmd"] = cmd
            captured["env"] = env
            return 12345

        class MockSup:
            def is_running(self):
                return False
            def start_process(self, cmd, cwd=None, env=None, stdout_file=None, stderr_file=None):
                return mock_start(cmd, cwd=cwd, env=env, stdout_file=stdout_file, stderr_file=stderr_file)
            def stop_process(self, timeout=10.0):
                return True

        monkeypatch.setattr(plugin, "_get_supervisor", lambda c: MockSup())

        await plugin.start(ctx, port=7777, timeout=0)
        assert captured["env"]["CRAFTLAB_PORT"] == "7777"
        port_idx = captured["cmd"].index("--port")
        assert captured["cmd"][port_idx + 1] == "7777"

