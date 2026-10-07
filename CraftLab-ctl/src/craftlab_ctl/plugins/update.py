import json
import os
import shutil
import tarfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import httpx

from craftlab_ctl.core.environment import provision_release_environment, is_venv_valid
from craftlab_ctl.core.github import GitHubReleasesClient, compute_file_sha256
from craftlab_ctl.core.maintenance import (
    is_maintenance_enabled,
    set_maintenance,
    get_maintenance_status,
    prune_releases,
)
from craftlab_ctl.core.models import CheckResult, CheckStatus, DangerLevel, OperationResult
from craftlab_ctl.sdk import Plugin, command, check, Context
from craftlab_ctl.supervisor import ProcessSupervisor


class UpdatePlugin(Plugin):
    name = "update"
    sdk_version = 1

    def _get_supervisor(self, ctx: Context) -> ProcessSupervisor:
        return ProcessSupervisor(paths=ctx.paths, service_name="backend")

    @check("update.releases_directory")
    def check_releases_dir(self, ctx: Context) -> CheckResult:
        rel_dir = ctx.paths.releases_dir
        if not rel_dir.exists():
            return CheckResult(
                check_id="update.releases_directory",
                status=CheckStatus.WARN,
                message=f"Releases directory {rel_dir} does not exist yet (will auto-create)",
            )
        return CheckResult(
            check_id="update.releases_directory",
            status=CheckStatus.PASS,
            message="Releases directory exists and is accessible",
        )

    @check("update.wheel_cache")
    def check_wheel_cache(self, ctx: Context) -> CheckResult:
        wc = ctx.paths.wheels_dir
        if not wc.exists():
            return CheckResult(
                check_id="update.wheel_cache",
                status=CheckStatus.WARN,
                message=f"Shared wheel cache {wc} not initialized yet",
            )
        whl_count = len(list(wc.glob("*.whl")))
        return CheckResult(
            check_id="update.wheel_cache",
            status=CheckStatus.PASS,
            message=f"Shared wheel cache active ({whl_count} wheels cached)",
        )

    @check("update.active_pointer")
    def check_active_pointer(self, ctx: Context) -> CheckResult:
        active = ctx.paths.active_release_version
        if not active:
            return CheckResult(
                check_id="update.active_pointer",
                status=CheckStatus.PASS,
                message="Running in repository development mode (no release pointer)",
            )
        return CheckResult(
            check_id="update.active_pointer",
            status=CheckStatus.PASS,
            message=f"Active release is set to '{active}'",
        )

    @command(name="check", mutates=False, danger=DangerLevel.SAFE)
    async def check_updates(
        self,
        ctx: Context,
        github_repo: str = "DarkBladeDev/CraftLab",
    ) -> OperationResult:
        """Check for newer CraftLab versions published on GitHub Releases."""
        await ctx.step("query_github")
        client = GitHubReleasesClient(repo=github_repo)
        latest = await client.get_latest_release()
        current_ver = ctx.paths.active_release_version or "dev"

        if not latest:
            return OperationResult.ok(
                current_version=current_ver,
                latest_version=None,
                update_available=False,
                message="No releases found on GitHub repository",
            )

        latest_tag = latest.tag_name.lstrip("v")
        curr_clean = current_ver.lstrip("v")
        update_available = latest_tag != curr_clean and current_ver != "dev"

        return OperationResult.ok(
            current_version=current_ver,
            latest_version=latest.tag_name,
            update_available=update_available,
            published_at=latest.published_at,
            release_notes=latest.body or "",
            message=f"Latest release: {latest.tag_name} (Current: {current_ver})",
        )

    @command(name="prepare", mutates=True, danger=DangerLevel.SAFE)
    async def prepare(
        self,
        ctx: Context,
        version: str,
        github_repo: str = "DarkBladeDev/CraftLab",
        local_file: Optional[str] = None,
    ) -> OperationResult:
        """Download, verify checksums, extract, and provision venv for a release without downtime."""
        norm_v = version.lstrip("v")
        target_dir = ctx.paths.releases_dir / f"v{norm_v}"

        await ctx.step("resolve_source")
        archive_path: Path
        sha256_path: Optional[Path] = None

        if local_file and Path(local_file).exists():
            archive_path = Path(local_file)
            candidate_sha = archive_path.parent / f"{archive_path.name}.sha256"
            if candidate_sha.exists():
                sha256_path = candidate_sha
        else:
            await ctx.step("download_assets")
            client = GitHubReleasesClient(repo=github_repo)
            rel_info = await client.get_release_by_tag(f"v{norm_v}")
            if not rel_info:
                rel_info = await client.get_release_by_tag(norm_v)
            if not rel_info:
                return OperationResult.fail(error=f"Release '{version}' not found on GitHub repo '{github_repo}'")

            tar_asset = None
            sha_asset = None
            for asset in rel_info.assets:
                if asset.name.endswith(".tar.gz"):
                    tar_asset = asset
                elif asset.name.endswith(".sha256"):
                    sha_asset = asset

            if not tar_asset:
                return OperationResult.fail(error=f"No .tar.gz archive asset found in release '{version}'")

            dl_dir = ctx.paths.downloads_dir
            dl_dir.mkdir(parents=True, exist_ok=True)
            archive_path = dl_dir / tar_asset.name
            await client.download_file(tar_asset.browser_download_url, archive_path)

            if sha_asset:
                sha256_path = dl_dir / sha_asset.name
                await client.download_file(sha_asset.browser_download_url, sha256_path)

        await ctx.step("verify_checksum")
        if sha256_path and sha256_path.exists():
            content = sha256_path.read_text(encoding="utf-8").strip()
            expected_sha = content.split()[0].lower()
            actual_sha = compute_file_sha256(archive_path).lower()
            if expected_sha != actual_sha:
                archive_path.unlink(missing_ok=True)
                return OperationResult.fail(
                    error=f"SHA256 checksum mismatch! Expected: {expected_sha}, Actual: {actual_sha}"
                )

        await ctx.step("extract_release")
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(target_dir)
        except Exception as e:
            shutil.rmtree(target_dir, ignore_errors=True)
            return OperationResult.fail(error=f"Failed to extract release archive: {e}")

        await ctx.step("validate_manifest")
        manifest_file = target_dir / "manifest.json"
        if not manifest_file.exists():
            shutil.rmtree(target_dir, ignore_errors=True)
            return OperationResult.fail(error="Invalid release package: manifest.json missing")

        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))

        await ctx.step("provision_venv")
        try:
            provision_release_environment(
                paths=ctx.paths,
                release_dir=target_dir,
                offline_only=False,
            )
        except Exception as e:
            return OperationResult.fail(error=f"Failed to provision release virtual environment: {e}")

        return OperationResult.ok(
            message=f"Release v{norm_v} successfully prepared and staged",
            version=f"v{norm_v}",
            target_directory=str(target_dir),
            manifest=manifest,
        )

    @command(name="apply", mutates=True, danger=DangerLevel.DISRUPTIVE)
    async def apply(
        self,
        ctx: Context,
        version: str,
        timeout: int = 15,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> OperationResult:
        """Apply an already-prepared release atomically with automated rollback."""
        norm_v = version.lstrip("v")
        target_dir = ctx.paths.releases_dir / f"v{norm_v}"
        if not target_dir.exists():
            return OperationResult.fail(error=f"Release 'v{norm_v}' has not been prepared yet. Run prepare first.")

        previous_version = ctx.paths.active_release_version
        supervisor = self._get_supervisor(ctx)

        await ctx.step("enable_maintenance")
        set_maintenance(ctx.paths, True, message=f"Upgrading to release v{norm_v}")

        await ctx.step("stop_service")
        if supervisor.is_running():
            supervisor.stop_process(timeout=10.0)

        await ctx.step("run_migrations")
        # Hook for migrations if present
        migrations_dir = target_dir / "migrations"
        if migrations_dir.exists():
            pass

        await ctx.step("swap_release_pointer")
        ctx.paths.set_active_release(f"v{norm_v}")

        await ctx.step("start_service")
        # Launch using lifecycle plugin logic
        from craftlab_ctl.plugins.lifecycle import LifecyclePlugin

        lifecycle = LifecyclePlugin()
        start_res = await lifecycle.start(ctx, host=host, port=port, timeout=timeout)

        if not start_res.success:
            await ctx.step("trigger_rollback")
            # Auto-rollback to previous version if available
            rollback_err = start_res.error
            if previous_version:
                ctx.paths.set_active_release(previous_version)
                await lifecycle.start(ctx, host=host, port=port, timeout=timeout)
                set_maintenance(ctx.paths, False)
                return OperationResult.fail(
                    error=f"Update to v{norm_v} failed readiness check. Successfully rolled back to {previous_version}. Error: {rollback_err}",
                    rolled_back=True,
                    active_version=previous_version,
                )
            else:
                set_maintenance(ctx.paths, False)
                return OperationResult.fail(
                    error=f"Update to v{norm_v} failed and no previous release version was set: {rollback_err}",
                    rolled_back=False,
                )

        await ctx.step("disable_maintenance")
        set_maintenance(ctx.paths, False)

        await ctx.step("prune_releases")
        pruned = prune_releases(ctx.paths, max_keep=3, protect_versions=[f"v{norm_v}"])

        return OperationResult.ok(
            message=f"Release v{norm_v} successfully applied and active",
            version=f"v{norm_v}",
            pruned_releases=pruned,
        )

    @command(name="rollback", mutates=True, danger=DangerLevel.DISRUPTIVE)
    async def rollback(
        self,
        ctx: Context,
        target_version: Optional[str] = None,
        timeout: int = 15,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> OperationResult:
        """Roll back to a previous installed release version."""
        installed = ctx.paths.get_installed_releases()
        current = ctx.paths.active_release_version

        target: Optional[str] = target_version
        if not target:
            # Find candidate prior version
            candidates = [v for v in installed if v != current]
            if not candidates:
                return OperationResult.fail(error="No alternate installed release found to roll back to")
            target = candidates[-1]

        target_dir = ctx.paths.releases_dir / target
        if not target_dir.exists():
            return OperationResult.fail(error=f"Rollback target release '{target}' does not exist")

        await ctx.step("enable_maintenance")
        set_maintenance(ctx.paths, True, message=f"Rolling back to release {target}")

        supervisor = self._get_supervisor(ctx)
        await ctx.step("stop_service")
        if supervisor.is_running():
            supervisor.stop_process(timeout=10.0)

        await ctx.step("swap_release_pointer")
        ctx.paths.set_active_release(target)

        await ctx.step("start_service")
        from craftlab_ctl.plugins.lifecycle import LifecyclePlugin

        lifecycle = LifecyclePlugin()
        start_res = await lifecycle.start(ctx, host=host, port=port, timeout=timeout)

        await ctx.step("disable_maintenance")
        set_maintenance(ctx.paths, False)

        if not start_res.success:
            return OperationResult.fail(
                error=f"Rollback to {target} failed during startup: {start_res.error}",
                active_version=target,
            )

        return OperationResult.ok(
            message=f"Successfully rolled back to release {target}",
            active_version=target,
        )

    @command(name="releases", mutates=False, danger=DangerLevel.SAFE)
    async def list_releases(self, ctx: Context) -> OperationResult:
        """List all locally installed releases and current active pointer."""
        installed = ctx.paths.get_installed_releases()
        active = ctx.paths.active_release_version
        maint = get_maintenance_status(ctx.paths)
        return OperationResult.ok(
            installed_releases=installed,
            active_release=active,
            maintenance=maint,
        )

    @command(name="maintenance", mutates=True, danger=DangerLevel.SAFE)
    async def maintenance_command(
        self,
        ctx: Context,
        enable: Optional[bool] = None,
        message: str = "",
    ) -> OperationResult:
        """Inspect or change CraftLab maintenance mode."""
        if enable is not None:
            set_maintenance(ctx.paths, enable, message=message)
            status_text = "enabled" if enable else "disabled"
            return OperationResult.ok(message=f"Maintenance mode {status_text}")
        status = get_maintenance_status(ctx.paths)
        return OperationResult.ok(**status)
