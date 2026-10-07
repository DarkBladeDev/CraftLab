import sys
import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import click

from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.core.models import CheckStatus
from craftlab_ctl.transport import LocalControlClient, TransportError
from craftlab_ctl.plugins.lifecycle import LifecyclePlugin
from craftlab_ctl.plugins.core import CorePlugin
from craftlab_ctl.sdk import Context


def get_client() -> LocalControlClient:
    paths = get_paths()
    return LocalControlClient(paths=paths)


async def run_client_command(command_name: str, parameters: Dict[str, Any]) -> int:
    client = get_client()
    paths = get_paths()

    if not client.is_daemon_running():
        # Fallback to direct execution for seamless dev experience
        click.secho("[info] craftctld daemon is not running; executing locally...", fg="yellow")
        ctx = Context(paths=paths)
        lifecycle = LifecyclePlugin()
        func = getattr(lifecycle, command_name, None)
        if not func:
            click.secho(f"Error: Command '{command_name}' not available locally without daemon.", fg="red")
            return 1

        async def step_cb(step_evt):
            click.secho(f"  -> [{step_evt.status}] {step_evt.step}", fg="cyan")

        ctx._step_callback = step_cb
        res = await func(ctx, **parameters)
        if res.success:
            click.secho(f"[ok] {res.data.get('message', 'Success')}", fg="green")
            if command_name == "status":
                click.echo(json.dumps(res.data, indent=2))
            return 0
        else:
            click.secho(f"[error] {res.error}", fg="red")
            return 1

    # Execute via daemon
    exit_code = 0
    try:
        async for event in client.execute(
            "execute", {"command": command_name, "parameters": parameters}
        ):
            evt_type = event.get("event")
            if evt_type == "step":
                status = event.get("status", "ok")
                name = event.get("step", "")
                click.secho(f"  -> [{status}] {name}", fg="cyan")
            elif evt_type == "result":
                res_data = event.get("data", {})
                if res_data.get("success"):
                    msg = res_data.get("data", {}).get("message", "Operation completed successfully.")
                    click.secho(f"[ok] {msg}", fg="green")
                    if command_name == "status":
                        click.echo(json.dumps(res_data.get("data", {}), indent=2))
                else:
                    err = res_data.get("error", "Operation failed.")
                    click.secho(f"[error] {err}", fg="red")
                    exit_code = 1
            elif evt_type == "error":
                click.secho(f"[error] {event.get('error')}", fg="red")
                exit_code = 1
    except Exception as e:
        click.secho(f"[error] Communication error with craftctld: {e}", fg="red")
        return 1

    return exit_code


@click.group()
def cli():
    """CraftLab Control CLI (craftctl)"""
    pass


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
def start(host: str, port: int, timeout: int):
    """Start the CraftLab backend service."""
    sys.exit(asyncio.run(run_client_command("start", {"host": host, "port": port, "timeout": timeout})))


@cli.command()
@click.option("--timeout", default=10, type=int, help="Graceful shutdown timeout in seconds")
def stop(timeout: int):
    """Stop the CraftLab backend service."""
    sys.exit(asyncio.run(run_client_command("stop", {"timeout": timeout})))


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
def restart(host: str, port: int, timeout: int):
    """Restart the CraftLab backend service."""
    sys.exit(asyncio.run(run_client_command("restart", {"host": host, "port": port, "timeout": timeout})))


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface to query")
@click.option("--port", default=8000, type=int, help="Port to query")
def status(host: str, port: int):
    """Inspect backend service status and health."""
    sys.exit(asyncio.run(run_client_command("status", {"host": host, "port": port})))


@cli.command()
def doctor():
    """Run environmental diagnostics and health checks."""
    client = get_client()
    paths = get_paths()

    async def _run():
        if client.is_daemon_running():
            async for event in client.execute("doctor", {}):
                if event.get("event") == "result":
                    return event.get("data", {})
        # Local fallback
        ctx = Context(paths=paths)
        core = CorePlugin()
        res = await core.doctor(ctx)
        return res.data

    data = asyncio.run(_run())
    overall = data.get("overall", "PASS")
    color = "green" if overall == "PASS" else ("yellow" if overall == "WARN" else "red")
    click.secho(f"\nCraftLab System Doctor: [{overall}]\n", fg=color, bold=True)

    for chk in data.get("checks", []):
        st = chk.get("status")
        st_str = st.value if hasattr(st, "value") else str(st).split(".")[-1]
        c_color = "green" if st_str == "PASS" else ("yellow" if st_str == "WARN" else "red")
        click.secho(f"  [{st_str:4}] {chk.get('check_id')}: {chk.get('message')}", fg=c_color)

    click.echo("")
    sys.exit(0 if overall in ("PASS", "WARN") else 1)


@cli.group()
def daemon():
    """Manage the craftctld supervisor daemon."""
    pass


@daemon.command(name="start")
@click.option("--foreground", is_flag=True, help="Run daemon in foreground")
def daemon_start(foreground: bool):
    """Start the craftctld supervisor daemon."""
    paths = get_paths()
    client = get_client()
    if client.is_daemon_running():
        click.secho("craftctld daemon is already running.", fg="yellow")
        return

    if foreground:
        from craftlab_ctl.daemon import run_daemon
        asyncio.run(run_daemon())
    else:
        # Spawn daemon in background
        py_exec = sys.executable
        cmd = [py_exec, "-m", "craftlab_ctl.daemon"]
        kwargs = {}
        if sys.platform == "win32":
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
        else:
            kwargs["preexec_fn"] = os.setsid

        log_file = paths.logs_dir / "craftctld.log"
        with open(log_file, "a", encoding="utf-8") as f:
            proc = subprocess.Popen(cmd, stdout=f, stderr=f, **kwargs)

        click.secho(f"craftctld started in background (PID {proc.pid}).", fg="green")


@daemon.command(name="stop")
def daemon_stop():
    """Stop the running craftctld supervisor daemon."""
    paths = get_paths()
    client = get_client()
    if not client.is_daemon_running():
        click.secho("craftctld daemon is not running.", fg="yellow")
        return

    endpoint_file = paths.run_dir / "craftctld.endpoint"
    if endpoint_file.exists():
        endpoint_file.unlink()
    click.secho("craftctld daemon stopped.", fg="green")


@daemon.command(name="status")
def daemon_status():
    """Check craftctld daemon running status."""
    client = get_client()
    if client.is_daemon_running():
        click.secho("craftctld daemon is running.", fg="green")
    else:
        click.secho("craftctld daemon is stopped.", fg="yellow")


def main():
    cli()


if __name__ == "__main__":
    main()
