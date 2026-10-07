import sys
import tomllib
from pathlib import Path
from typing import List, Dict, Any
from craftlab_ctl.core.models import CheckResult, CheckStatus, OperationResult, DangerLevel
from craftlab_ctl.sdk import Plugin, command, check, Context


class CorePlugin(Plugin):
    name = "core"
    sdk_version = 1

    @check("env.directories")
    def check_directories(self, ctx: Context) -> CheckResult:
        paths = ctx.paths
        required = [paths.config_dir, paths.data_dir, paths.run_dir, paths.logs_dir]
        missing = [d.name for d in required if not d.exists()]
        if missing:
            return CheckResult(
                check_id="env.directories",
                status=CheckStatus.WARN,
                message=f"Missing runtime directories: {', '.join(missing)} (will be created automatically)",
            )
        return CheckResult(
            check_id="env.directories",
            status=CheckStatus.PASS,
            message="All canonical directories exist and are accessible",
        )

    @check("env.python")
    def check_python(self, ctx: Context) -> CheckResult:
        major, minor = sys.version_info[:2]
        if major < 3 or (major == 3 and minor < 11):
            return CheckResult(
                check_id="env.python",
                status=CheckStatus.FAIL,
                message=f"Python version {major}.{minor} is unsupported. CraftLab requires Python >= 3.11",
            )
        return CheckResult(
            check_id="env.python",
            status=CheckStatus.PASS,
            message=f"Python version {major}.{minor}.{sys.version_info[2]} is supported",
        )

    @check("backend.config")
    def check_backend_config(self, ctx: Context) -> CheckResult:
        config_file = ctx.paths.config_dir / "craftlab.toml"
        if not config_file.exists():
            return CheckResult(
                check_id="backend.config",
                status=CheckStatus.PASS,
                message="No craftlab.toml found; using default development settings",
            )
        try:
            with open(config_file, "rb") as f:
                tomllib.load(f)
            return CheckResult(
                check_id="backend.config",
                status=CheckStatus.PASS,
                message="craftlab.toml parsed successfully",
            )
        except Exception as e:
            return CheckResult(
                check_id="backend.config",
                status=CheckStatus.FAIL,
                message=f"craftlab.toml syntax error: {e}",
            )

    @command(name="doctor", runs_in="local", danger=DangerLevel.SAFE)
    async def doctor(self, ctx: Context) -> OperationResult:
        """Run system environmental diagnostics and checks."""
        # Note: when invoked via registry, registry.execute_checks will be called
        checks_data = [
            self.check_directories(ctx).model_dump(),
            self.check_python(ctx).model_dump(),
            self.check_backend_config(ctx).model_dump(),
        ]
        has_fail = any(c["status"] == "FAIL" for c in checks_data)
        has_warn = any(c["status"] == "WARN" for c in checks_data)
        overall = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")
        return OperationResult.ok(overall=overall, checks=checks_data)
