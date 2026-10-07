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
