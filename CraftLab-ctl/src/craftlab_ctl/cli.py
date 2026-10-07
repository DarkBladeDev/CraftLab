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
from craftlab_ctl.transport import LocalControlClient, RemoteControlClient, TransportError
from craftlab_ctl.plugins.lifecycle import LifecyclePlugin
from craftlab_ctl.plugins.core import CorePlugin
from craftlab_ctl.sdk import Context


def get_client() -> LocalControlClient:
    paths = get_paths()
    return LocalControlClient(paths=paths)


async def run_client_command(
    command_name: str,
    parameters: Dict[str, Any],
    server: Optional[str] = None,
    token: Optional[str] = None,
) -> int:
    if server:
        remote = RemoteControlClient(server, token)
        try:
            if command_name in ("start", "stop", "restart"):
                res = await remote.execute_lifecycle(command_name)
                click.secho(f"[ok] {res.get('message', 'Success')}", fg="green")
                return 0 if res.get("success") else 1
            elif command_name == "status":
                res = await remote.get_status()
                click.secho(f"[ok] Service status: {res.get('status')}", fg="green")
                click.echo(json.dumps(res, indent=2))
                return 0
        except Exception as e:
            click.secho(f"[error] Remote execution error: {e}", fg="red")
            return 1

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
@click.option("--server", envvar="CRAFTLAB_SERVER", default=None, help="Remote craftctld daemon URL (e.g. https://vps:8443)")
@click.option("--token", envvar="CRAFTLAB_TOKEN", default=None, help="Authentication token for remote daemon")
@click.pass_context
def cli(ctx, server, token):
    """CraftLab Control CLI (craftctl)"""
    ctx.ensure_object(dict)
    ctx.obj["server"] = server
    ctx.obj["token"] = token


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
@click.pass_context
def start(ctx, host: str, port: int, timeout: int):
    """Start the CraftLab backend service."""
    server = ctx.obj.get("server")
    token = ctx.obj.get("token")
    sys.exit(asyncio.run(run_client_command("start", {"host": host, "port": port, "timeout": timeout}, server=server, token=token)))


@cli.command()
@click.option("--timeout", default=10, type=int, help="Graceful shutdown timeout in seconds")
@click.pass_context
def stop(ctx, timeout: int):
    """Stop the CraftLab backend service."""
    server = ctx.obj.get("server")
    token = ctx.obj.get("token")
    sys.exit(asyncio.run(run_client_command("stop", {"timeout": timeout}, server=server, token=token)))


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
@click.pass_context
def restart(ctx, host: str, port: int, timeout: int):
    """Restart the CraftLab backend service."""
    server = ctx.obj.get("server")
    token = ctx.obj.get("token")
    sys.exit(asyncio.run(run_client_command("restart", {"host": host, "port": port, "timeout": timeout}, server=server, token=token)))


@cli.command()
@click.option("--host", default="127.0.0.1", help="Host interface to query")
@click.option("--port", default=8000, type=int, help="Port to query")
@click.pass_context
def status(ctx, host: str, port: int):
    """Inspect backend service status and health."""
    server = ctx.obj.get("server")
    token = ctx.obj.get("token")
    sys.exit(asyncio.run(run_client_command("status", {"host": host, "port": port}, server=server, token=token)))


@cli.command()
@click.pass_context
def metrics(ctx):
    """View host and process metrics."""
    server = ctx.obj.get("server")
    token = ctx.obj.get("token")
    if server:
        remote = RemoteControlClient(server, token)
        try:
            data = asyncio.run(remote.get_metrics())
            click.echo(json.dumps(data, indent=2))
            sys.exit(0)
        except Exception as e:
            click.secho(f"[error] Remote metrics error: {e}", fg="red")
            sys.exit(1)
    else:
        from craftlab_ctl.server.metrics import collect_system_metrics
        from craftlab_ctl.supervisor import ProcessSupervisor
        paths = get_paths()
        sup = ProcessSupervisor(paths=paths)
        data = collect_system_metrics(paths, sup)
        click.echo(json.dumps(data, indent=2))
        sys.exit(0)


@cli.command()
@click.pass_context
def doctor(ctx):
    """Run environmental diagnostics and health checks."""
    server = ctx.obj.get("server")
    token = ctx.obj.get("token")
    if server:
        remote = RemoteControlClient(server, token)
        try:
            data = asyncio.run(remote.get_doctor())
        except Exception as e:
            click.secho(f"[error] Remote doctor error: {e}", fg="red")
            sys.exit(1)
    else:
        client = get_client()
        paths = get_paths()

        async def _run():
            if client.is_daemon_running():
                async for event in client.execute("doctor", {}):
                    if event.get("event") == "result":
                        return event.get("data", {})
            # Local fallback
            ctx_local = Context(paths=paths)
            core = CorePlugin()
            res = await core.doctor(ctx_local)
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


@cli.group()
def user():
    """Manage authentication users and roles in data/auth.db."""
    pass


@user.command(name="add")
@click.argument("username")
@click.option("--password", "-p", default=None, help="User password (prompts if omitted)")
@click.option("--role", "-r", "roles", multiple=True, default=["viewer"], help="Roles: admin, operator, creator, viewer")
@click.option("--display-name", "-d", default=None, help="User display name")
def user_add(username: str, password: Optional[str], roles: tuple, display_name: Optional[str]):
    """Create or update a user."""
    from craftlab_ctl.auth import create_user
    if not password:
        password = click.prompt("Password", hide_input=True, confirmation_prompt=True)
    paths = get_paths()
    u = create_user(
        paths.auth_db_path,
        username=username,
        password=password,
        display_name=display_name,
        roles=list(roles),
    )
    click.secho(f"[ok] User '{u.username}' saved with roles: {u.roles}", fg="green")


@user.command(name="list")
def user_list():
    """List all registered users in data/auth.db."""
    from craftlab_ctl.auth import list_users
    paths = get_paths()
    users = list_users(paths.auth_db_path)
    if not users:
        click.secho("No users found in database.", fg="yellow")
        return
    click.secho(f"\nRegistered Users ({len(users)}):\n", fg="cyan", bold=True)
    for u in users:
        status_str = "active" if u.is_active else "disabled"
        click.echo(f"  - {u.username:15} | roles: {', '.join(u.roles):20} | name: {u.display_name:15} | status: {status_str}")
    click.echo("")


def main():
    cli()


if __name__ == "__main__":
    main()
