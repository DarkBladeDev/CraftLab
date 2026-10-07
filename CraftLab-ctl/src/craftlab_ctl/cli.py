import sys
import os
import json
import asyncio
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional
import click

from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.core.models import CheckStatus, OperationResult
from craftlab_ctl.transport import LocalControlClient, RemoteControlClient, TransportError
from craftlab_ctl.plugins.lifecycle import LifecyclePlugin
from craftlab_ctl.plugins.core import CorePlugin
from craftlab_ctl.plugins.update import UpdatePlugin
from craftlab_ctl.sdk import Context, PluginRegistry


def get_client() -> LocalControlClient:
    paths = get_paths()
    return LocalControlClient(paths=paths)


def format_command_output(command_name: str, data: Dict[str, Any]) -> None:
    if not isinstance(data, dict):
        return
    if command_name == "status":
        click.echo(json.dumps(data, indent=2))
    elif command_name in ("releases", "update.releases"):
        installed = data.get("installed_releases", [])
        active = data.get("active_release")
        maint = data.get("maintenance", {})
        click.secho("\nInstalled Releases:", fg="cyan", bold=True)
        if not installed:
            click.echo("  (no packaged releases installed; running in repository/dev mode)")
        else:
            for r in installed:
                is_active = (r == active) or (f"v{r}" == active) or (r == f"v{active}")
                badge = click.style(" (active)", fg="green", bold=True) if is_active else ""
                click.echo(f"  - {r}{badge}")
        click.secho(f"\nActive release: {active or 'dev (workspace)'}", fg="green" if active else "yellow")
        m_enabled = maint.get("enabled", False) if isinstance(maint, dict) else False
        m_msg = maint.get("message", "") if isinstance(maint, dict) else ""
        m_color = "red" if m_enabled else "green"
        msg_extra = f" ({m_msg})" if m_msg else ""
        click.secho(f"Maintenance mode: {'ENABLED' if m_enabled else 'DISABLED'}{msg_extra}\n", fg=m_color)
    elif command_name in ("check", "update.check"):
        curr = data.get("current_version", "unknown")
        latest = data.get("latest_version")
        avail = data.get("update_available", False)
        click.echo(f"Current version: {curr}")
        click.echo(f"Latest release:  {latest or 'None'}")
        if avail:
            click.secho(f"\n[!] A new version ({latest}) is available!", fg="yellow", bold=True)
            if data.get("release_notes"):
                click.echo(f"\nRelease notes:\n{data.get('release_notes')}\n")
        else:
            click.secho("\nCraftLab is up to date.\n", fg="green")
    elif command_name in ("maintenance", "update.maintenance"):
        if "enabled" in data:
            st = "ENABLED" if data["enabled"] else "DISABLED"
            color = "red" if data["enabled"] else "green"
            click.secho(f"Maintenance status: {st}", fg=color, bold=True)
            if data.get("message"):
                click.echo(f"Message: {data['message']}")
            if data.get("enabled_at"):
                click.echo(f"Enabled at: {data['enabled_at']}")


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
                format_command_output("status", res)
                return 0
            elif command_name in ("check", "update.check"):
                res = await remote.check_updates(parameters.get("github_repo"))
                click.secho(f"[ok] {res.get('message', 'Update check complete')}", fg="green")
                format_command_output("check", res)
                return 0
            elif command_name in ("releases", "update.releases"):
                res = await remote.get_releases()
                click.secho("[ok] Releases fetched", fg="green")
                format_command_output("releases", res)
                return 0
            elif command_name in ("prepare", "update.prepare"):
                res = await remote.prepare_update(**parameters)
                click.secho(f"[ok] {res.get('message', 'Release prepared')}", fg="green")
                return 0 if res.get("success") else 1
            elif command_name in ("apply", "update.apply"):
                res = await remote.apply_update(**parameters)
                click.secho(f"[ok] {res.get('message', 'Release applied')}", fg="green")
                return 0 if res.get("success") else 1
            elif command_name in ("rollback", "update.rollback"):
                res = await remote.rollback(**parameters)
                click.secho(f"[ok] {res.get('message', 'Rollback complete')}", fg="green")
                return 0 if res.get("success") else 1
            elif command_name in ("maintenance", "update.maintenance"):
                if parameters.get("enable") is not None:
                    res = await remote.set_maintenance(enable=parameters.get("enable"), message=parameters.get("message", ""))
                else:
                    res = await remote.get_maintenance()
                click.secho(f"[ok] {res.get('message', 'Maintenance updated')}", fg="green")
                format_command_output("maintenance", res.get("data", res))
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
        registry = PluginRegistry()
        registry.register_plugin(LifecyclePlugin())
        registry.register_plugin(CorePlugin())
        registry.register_plugin(UpdatePlugin())

        cmd_def = registry.get_command(command_name)
        if not cmd_def:
            click.secho(f"Error: Command '{command_name}' not available locally without daemon.", fg="red")
            return 1

        async def step_cb(step_evt):
            click.secho(f"  -> [{step_evt.status}] {step_evt.step}", fg="cyan")

        ctx._step_callback = step_cb
        res = await cmd_def.func(ctx, **parameters)
        if not isinstance(res, OperationResult):
            res = OperationResult.ok(data=res)

        if res.success:
            msg = res.message or (res.data.get("message", "Success") if isinstance(res.data, dict) else "Success")
            click.secho(f"[ok] {msg}", fg="green")
            format_command_output(command_name, res.data if isinstance(res.data, dict) else {})
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
                    inner_data = res_data.get("data", {})
                    msg = res_data.get("message") or (inner_data.get("message", "Operation completed successfully.") if isinstance(inner_data, dict) else "Operation completed successfully.")
                    click.secho(f"[ok] {msg}", fg="green")
                    format_command_output(command_name, inner_data if isinstance(inner_data, dict) else {})
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


class UpdateGroup(click.Group):
    def get_command(self, ctx, cmd_name):
        rv = click.Group.get_command(self, ctx, cmd_name)
        if rv is not None:
            return rv
        run_cmd = click.Group.get_command(self, ctx, "run")
        if run_cmd:
            ctx.args = [cmd_name] + ctx.args
            return run_cmd
        return None


@cli.group(cls=UpdateGroup)
def update():
    """Manage application updates and release lifecycle."""
    pass


@update.command(name="check")
@click.option("--repo", default="DarkBladeDev/CraftLab", help="GitHub repository (owner/repo)")
@click.pass_context
def update_check(ctx, repo: str):
    """Check for newer releases published on GitHub."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    sys.exit(asyncio.run(run_client_command("check", {"github_repo": repo}, server=server, token=token)))


@update.command(name="prepare")
@click.argument("version")
@click.option("--repo", default="DarkBladeDev/CraftLab", help="GitHub repository (owner/repo)")
@click.option("--file", "local_file", default=None, help="Local release tar.gz archive")
@click.pass_context
def update_prepare(ctx, version: str, repo: str, local_file: Optional[str]):
    """Download, verify, and stage release environment without downtime."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    sys.exit(asyncio.run(run_client_command("prepare", {"version": version, "github_repo": repo, "local_file": local_file}, server=server, token=token)))


@update.command(name="apply")
@click.argument("version")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.pass_context
def update_apply(ctx, version: str, yes: bool, timeout: int, host: str, port: int):
    """Atomically activate prepared release with automated rollback."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    if not yes:
        click.confirm(f"Applying release '{version}' will restart backend service. Proceed?", abort=True)
    sys.exit(asyncio.run(run_client_command("apply", {"version": version, "timeout": timeout, "host": host, "port": port}, server=server, token=token)))


@update.command(name="run")
@click.argument("version")
@click.option("--repo", default="DarkBladeDev/CraftLab", help="GitHub repository (owner/repo)")
@click.option("--file", "local_file", default=None, help="Local release archive")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.pass_context
def update_run(ctx, version: str, repo: str, local_file: Optional[str], yes: bool, timeout: int, host: str, port: int):
    """Update CraftLab to <version> (runs prepare and apply in sequence)."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    if not yes:
        click.confirm(f"Are you sure you want to update CraftLab to release '{version}'?", abort=True)
    click.secho(f"[*] Phase 1/2: Preparing release '{version}'...", fg="cyan", bold=True)
    prep_code = asyncio.run(run_client_command(
        "prepare",
        {"version": version, "github_repo": repo, "local_file": local_file},
        server=server,
        token=token,
    ))
    if prep_code != 0:
        click.secho("[error] Preparation failed. Aborting update.", fg="red")
        sys.exit(prep_code)
    click.secho(f"\n[*] Phase 2/2: Applying release '{version}'...", fg="cyan", bold=True)
    apply_code = asyncio.run(run_client_command(
        "apply",
        {"version": version, "timeout": timeout, "host": host, "port": port},
        server=server,
        token=token,
    ))
    sys.exit(apply_code)


@cli.command()
@click.argument("version", required=False, default=None)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
@click.option("--timeout", default=15, type=int, help="Readiness timeout in seconds")
@click.option("--host", default="127.0.0.1", help="Host interface to bind")
@click.option("--port", default=8000, type=int, help="Port to listen on")
@click.pass_context
def rollback(ctx, version: Optional[str], yes: bool, timeout: int, host: str, port: int):
    """Roll back to a previously installed release version."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    target_desc = f"release '{version}'" if version else "previous installed release"
    if not yes:
        click.confirm(f"Rollback to {target_desc} will restart backend service. Proceed?", abort=True)
    sys.exit(asyncio.run(run_client_command("rollback", {"target_version": version, "timeout": timeout, "host": host, "port": port}, server=server, token=token)))


@cli.command()
@click.pass_context
def releases(ctx):
    """List all locally installed releases and active release pointer."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    sys.exit(asyncio.run(run_client_command("releases", {}, server=server, token=token)))


@cli.group(invoke_without_command=True)
@click.option("--message", "-m", default="", help="Maintenance message description")
@click.pass_context
def maintenance(ctx, message: str):
    """Inspect or toggle application maintenance mode."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    if ctx.invoked_subcommand is None:
        sys.exit(asyncio.run(run_client_command("maintenance", {}, server=server, token=token)))


@maintenance.command(name="enable")
@click.option("--message", "-m", default="Manual maintenance enabled", help="Reason for maintenance")
@click.pass_context
def maintenance_enable(ctx, message: str):
    """Enable application maintenance mode."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    sys.exit(asyncio.run(run_client_command("maintenance", {"enable": True, "message": message}, server=server, token=token)))


@maintenance.command(name="disable")
@click.pass_context
def maintenance_disable(ctx):
    """Disable application maintenance mode."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    sys.exit(asyncio.run(run_client_command("maintenance", {"enable": False}, server=server, token=token)))


@maintenance.command(name="status")
@click.pass_context
def maintenance_status(ctx):
    """Show current maintenance mode status."""
    server = ctx.obj.get("server") if ctx.obj else None
    token = ctx.obj.get("token") if ctx.obj else None
    sys.exit(asyncio.run(run_client_command("maintenance", {}, server=server, token=token)))


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
