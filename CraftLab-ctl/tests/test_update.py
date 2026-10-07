import json
import tarfile
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import pytest

from craftlab_ctl.core import get_paths, OperationResult
from craftlab_ctl.core.github import GitHubReleasesClient, GitHubRelease, ReleaseAsset, compute_file_sha256
from craftlab_ctl.core.maintenance import (
    is_maintenance_enabled,
    set_maintenance,
    get_maintenance_status,
    prune_releases,
)
from craftlab_ctl.plugins.update import UpdatePlugin
from craftlab_ctl.sdk import Context


@pytest.fixture
def test_ctx(tmp_path: Path) -> Context:
    paths = get_paths(home=tmp_path)
    return Context(paths=paths, caller_id="test_admin")


def test_maintenance_mode_lifecycle(test_ctx: Context):
    paths = test_ctx.paths
    assert not is_maintenance_enabled(paths)
    status0 = get_maintenance_status(paths)
    assert not status0["enabled"]

    set_maintenance(paths, True, message="Upgrading database")
    assert is_maintenance_enabled(paths)
    status1 = get_maintenance_status(paths)
    assert status1["enabled"]
    assert status1["message"] == "Upgrading database"
    assert status1["enabled_at"] is not None

    set_maintenance(paths, False)
    assert not is_maintenance_enabled(paths)


def test_prune_releases(test_ctx: Context):
    paths = test_ctx.paths
    rel_names = ["v1.0.0", "v1.1.0", "v1.2.0", "v1.3.0", "v1.4.0"]
    for i, name in enumerate(rel_names):
        d = paths.releases_dir / name
        d.mkdir(parents=True)
        (d / "manifest.json").write_text(json.dumps({"version": name}), encoding="utf-8")
        # Ensure distinct timestamps
        import os
        os.utime(d, (1000 + i * 100, 1000 + i * 100))

    paths.set_active_release("1.4.0")
    pruned = prune_releases(paths, max_keep=3)
    assert len(pruned) == 2
    assert "v1.0.0" in pruned
    assert "v1.1.0" in pruned

    remaining = [d.name for d in paths.releases_dir.iterdir() if d.is_dir()]
    assert len(remaining) == 3
    assert "v1.4.0" in remaining
    assert "v1.3.0" in remaining
    assert "v1.2.0" in remaining


@pytest.mark.asyncio
async def test_update_plugin_checks(test_ctx: Context):
    plugin = UpdatePlugin()
    res_dir = plugin.check_releases_dir(test_ctx)
    assert res_dir.status.value in ("PASS", "WARN")

    res_wc = plugin.check_wheel_cache(test_ctx)
    assert res_wc.status.value in ("PASS", "WARN")

    res_ptr = plugin.check_active_pointer(test_ctx)
    assert res_ptr.status.value == "PASS"


@pytest.mark.asyncio
async def test_update_prepare_local_archive(test_ctx: Context, tmp_path: Path):
    # Prepare mock archive
    staging = tmp_path / "pkg_stage"
    staging.mkdir()
    (staging / "manifest.json").write_text(json.dumps({"version": "2.0.0"}), encoding="utf-8")
    backend_d = staging / "backend"
    backend_d.mkdir()
    (backend_d / "main.py").write_text("# main 2.0.0", encoding="utf-8")

    archive_path = tmp_path / "craftlab-v2.0.0.tar.gz"
    with tarfile.open(archive_path, "w:gz") as tar:
        for item in staging.iterdir():
            tar.add(item, arcname=item.name)

    sha = compute_file_sha256(archive_path)
    sha_file = tmp_path / "craftlab-v2.0.0.tar.gz.sha256"
    sha_file.write_text(f"{sha}  craftlab-v2.0.0.tar.gz\n", encoding="utf-8")

    plugin = UpdatePlugin()
    with patch("craftlab_ctl.plugins.update.provision_release_environment") as mock_prov:
        mock_prov.return_value = Path("/fake/python")
        res = await plugin.prepare(
            test_ctx,
            version="2.0.0",
            local_file=str(archive_path),
        )

    assert res.success
    assert res.data["version"] == "v2.0.0"
    target_dir = test_ctx.paths.releases_dir / "v2.0.0"
    assert target_dir.exists()
    assert (target_dir / "manifest.json").exists()
    assert (target_dir / "backend" / "main.py").exists()


@pytest.mark.asyncio
async def test_update_apply_success(test_ctx: Context, tmp_path: Path):
    # Create prepared release
    rel_dir = test_ctx.paths.releases_dir / "v1.2.0"
    rel_dir.mkdir(parents=True)
    (rel_dir / "manifest.json").write_text(json.dumps({"version": "1.2.0"}), encoding="utf-8")
    (rel_dir / "backend").mkdir()
    (rel_dir / "backend" / "main.py").write_text("# main", encoding="utf-8")

    plugin = UpdatePlugin()
    with patch("craftlab_ctl.plugins.lifecycle.LifecyclePlugin.start") as mock_start:
        mock_start.return_value = OperationResult.ok(message="Started")
        apply_res = await plugin.apply(test_ctx, version="1.2.0", timeout=5)

    assert apply_res.success
    assert test_ctx.paths.active_release_version == "v1.2.0"
    assert not is_maintenance_enabled(test_ctx.paths)


@pytest.mark.asyncio
async def test_update_apply_failure_with_auto_rollback(test_ctx: Context):
    # Set existing active release v1.0.0
    rel1 = test_ctx.paths.releases_dir / "v1.0.0"
    rel1.mkdir(parents=True)
    (rel1 / "backend").mkdir()
    (rel1 / "backend" / "main.py").write_text("# v1.0.0")
    test_ctx.paths.set_active_release("1.0.0")

    # Prepared target release v2.0.0
    rel2 = test_ctx.paths.releases_dir / "v2.0.0"
    rel2.mkdir(parents=True)
    (rel2 / "backend").mkdir()
    (rel2 / "backend" / "main.py").write_text("# v2.0.0")

    plugin = UpdatePlugin()
    with patch("craftlab_ctl.plugins.lifecycle.LifecyclePlugin.start") as mock_start:
        # First call fails (new release fails readiness), second call succeeds (rollback to v1.0.0 succeeds)
        mock_start.side_effect = [
            OperationResult.fail(error="Connection refused on /ready"),
            OperationResult.ok(message="Prior version restarted"),
        ]
        apply_res = await plugin.apply(test_ctx, version="2.0.0", timeout=5)

    assert not apply_res.success
    assert apply_res.data.get("rolled_back") is True
    # Verify pointer was restored to v1.0.0
    assert test_ctx.paths.active_release_version == "v1.0.0"
    assert not is_maintenance_enabled(test_ctx.paths)


@pytest.mark.asyncio
async def test_update_rollback_command(test_ctx: Context):
    rel1 = test_ctx.paths.releases_dir / "v1.0.0"
    rel1.mkdir(parents=True)
    (rel1 / "backend").mkdir()
    (rel1 / "backend" / "main.py").write_text("# v1.0.0")

    rel2 = test_ctx.paths.releases_dir / "v2.0.0"
    rel2.mkdir(parents=True)
    (rel2 / "backend").mkdir()
    (rel2 / "backend" / "main.py").write_text("# v2.0.0")

    test_ctx.paths.set_active_release("2.0.0")

    plugin = UpdatePlugin()
    with patch("craftlab_ctl.plugins.lifecycle.LifecyclePlugin.start") as mock_start:
        mock_start.return_value = OperationResult.ok(message="Rolled back")
        res = await plugin.rollback(test_ctx, target_version="v1.0.0")

    assert res.success
    assert test_ctx.paths.active_release_version == "v1.0.0"
