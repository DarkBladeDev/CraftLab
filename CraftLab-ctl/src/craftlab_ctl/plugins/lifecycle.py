import os
import sys
import time
import httpx
from pathlib import Path
from typing import Optional
from craftlab_ctl.core.models import DangerLevel, OperationResult
from craftlab_ctl.sdk import Plugin, command, Context
from craftlab_ctl.supervisor import ProcessSupervisor


class LifecyclePlugin(Plugin):
    name = "lifecycle"
    sdk_version = 1

    def _get_supervisor(self, ctx: Context) -> ProcessSupervisor:
        return ProcessSupervisor(paths=ctx.paths, service_name="backend")

    def _find_backend_python(self, ctx: Context) -> str:
        candidates = []
        if ctx.paths.active_release_dir:
            rel = ctx.paths.active_release_dir
            candidates.extend([
                rel / ".venv" / "Scripts" / "python.exe",
                rel / ".venv" / "bin" / "python",
                rel / "backend" / ".venv" / "Scripts" / "python.exe",
                rel / "backend" / ".venv" / "bin" / "python",
            ])
        home = ctx.paths.home
        candidates.extend([
            home / "backend" / ".venv" / "Scripts" / "python.exe",
            home / "backend" / ".venv" / "bin" / "python",
            home / ".venv" / "Scripts" / "python.exe",
            home / ".venv" / "bin" / "python",
        ])
        for c in candidates:
            if c.exists():
                return str(c)
        return sys.executable

    @command(mutates=True, danger=DangerLevel.DISRUPTIVE)
    async def start(
        self,
        ctx: Context,
        host: str = "127.0.0.1",
        port: int = 8000,
        timeout: int = 15,
    ) -> OperationResult:
        """Start the CraftLab backend service and await readiness."""
        supervisor = self._get_supervisor(ctx)
        await ctx.step("check_existing")
        if supervisor.is_running():
            pid = supervisor.get_pid()
            return OperationResult.ok(message=f"Backend is already running (PID {pid})", pid=pid)

        await ctx.step("prepare_command")
        py_exec = self._find_backend_python(ctx)
        backend_dir = ctx.paths.app_backend_dir

        cmd = [
            py_exec,
            "-m",
            "uvicorn",
            "main:app",
            "--host",
            host,
            "--port",
            str(port),
        ]
        log_out = ctx.paths.logs_dir / "backend.log"
        log_err = ctx.paths.logs_dir / "backend_err.log"

        env = {
            "CRAFTLAB_HOME": str(ctx.paths.home),
            "CRAFTLAB_HOST": host,
            "CRAFTLAB_PORT": str(port),
        }

        await ctx.step("spawn_process")
        pid = supervisor.start_process(
            cmd=cmd,
            cwd=backend_dir,
            env=env,
            stdout_file=log_out,
            stderr_file=log_err,
        )

        await ctx.step("await_readiness")
        ready_url = f"http://{host}:{port}/ready"
        start_time = time.time()
        is_ready = False
        last_error = ""

        async with httpx.AsyncClient(timeout=1.0) as client:
            while time.time() - start_time < timeout:
                if not supervisor.is_running():
                    last_error = "Process terminated unexpectedly during startup"
                    break
                try:
                    resp = await client.get(ready_url)
                    if resp.status_code == 200:
                        is_ready = True
                        break
                except Exception as e:
                    last_error = str(e)
                time.sleep(0.5)

        if not is_ready:
            supervisor.stop_process(timeout=3.0)
            return OperationResult.fail(
                error=f"Backend failed to become ready within {timeout}s: {last_error}",
                pid=pid,
            )

        return OperationResult.ok(
            message=f"Backend started successfully (PID {pid})",
            pid=pid,
            url=f"http://{host}:{port}",
        )

    @command(mutates=True, danger=DangerLevel.DISRUPTIVE)
    async def stop(self, ctx: Context, timeout: int = 10) -> OperationResult:
        """Stop the CraftLab backend service gracefully."""
        supervisor = self._get_supervisor(ctx)
        await ctx.step("stopping_process")
        if not supervisor.is_running():
            return OperationResult.ok(message="Backend is not running")

        pid = supervisor.get_pid()
        stopped = supervisor.stop_process(timeout=float(timeout))
        if stopped:
            return OperationResult.ok(message=f"Backend stopped (was PID {pid})")
        return OperationResult.fail(error=f"Failed to stop backend process (PID {pid})")

    @command(mutates=True, danger=DangerLevel.DISRUPTIVE)
    async def restart(
        self,
        ctx: Context,
        host: str = "127.0.0.1",
        port: int = 8000,
        timeout: int = 15,
    ) -> OperationResult:
        """Restart the CraftLab backend service."""
        await self.stop(ctx, timeout=10)
        return await self.start(ctx, host=host, port=port, timeout=timeout)

    @command(mutates=False, danger=DangerLevel.SAFE)
    async def status(
        self,
        ctx: Context,
        host: str = "127.0.0.1",
        port: int = 8000,
    ) -> OperationResult:
        """Check the status and health of the CraftLab backend service."""
        supervisor = self._get_supervisor(ctx)
        proc_status = supervisor.get_status()
        if proc_status.get("status") != "running":
            return OperationResult.ok(service="backend", status="stopped", pid=None)

        probe_status = "unreachable"
        probe_data = {}
        try:
            async with httpx.AsyncClient(timeout=1.0) as client:
                resp = await client.get(f"http://{host}:{port}/health")
                if resp.status_code == 200:
                    probe_status = "healthy"
                    probe_data = resp.json()
        except Exception:
            pass

        return OperationResult.ok(
            service="backend",
            status="running",
            pid=proc_status.get("pid"),
            uptime_seconds=proc_status.get("uptime_seconds"),
            memory_mb=proc_status.get("memory_mb"),
            health=probe_status,
            health_details=probe_data,
        )
