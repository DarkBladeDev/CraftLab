import os
import pytest
from pathlib import Path
from fastapi.testclient import TestClient
from craftlab_ctl.core.paths import CtlPaths, get_paths
from craftlab_ctl.daemon import DaemonService
from craftlab_ctl.server.app import create_control_app
from craftlab_ctl.auth.db import init_auth_db, create_user
from craftlab_ctl.auth.crypto import hash_password, get_or_create_auth_secret, sign_session_token
from craftlab_ctl.auth.models import Role
from craftlab_security import validate_production_security_environment


def test_production_environment_validation(monkeypatch):
    monkeypatch.setenv("CRAFTLAB_ENV", "production")
    monkeypatch.setenv("CRAFTLAB_AUTH_ENABLED", "false")
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "custom_key")
    with pytest.raises(RuntimeError, match="Production mode forbids CRAFTLAB_AUTH_ENABLED=false"):
        validate_production_security_environment()

    monkeypatch.setenv("CRAFTLAB_AUTH_ENABLED", "true")
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "change_me_to_a_secure_root_token")
    with pytest.raises(RuntimeError, match="Production mode requires a secure"):
        validate_production_security_environment()


def test_cors_disallows_wildcard_with_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("CRAFTLAB_CTL_CORS_ORIGINS", "*")
    paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "packs",
    )
    paths.ensure_directories()
    daemon = DaemonService(paths=paths)
    app = create_control_app(paths=paths, daemon_service=daemon)
    client = TestClient(app)

    # Preflight request from an arbitrary origin
    resp = client.options(
        "/api/v1/status",
        headers={
            "Origin": "http://evil-attacker.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert resp.headers.get("access-control-allow-origin") != "*"
    assert resp.headers.get("access-control-allow-origin") != "http://evil-attacker.com"


def test_login_cookie_secure_flag_in_production(monkeypatch, tmp_path):
    monkeypatch.setenv("CRAFTLAB_ENV", "production")
    paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "packs",
    )
    paths.ensure_directories()
    init_auth_db(paths.auth_db_path)
    create_user(
        paths.auth_db_path,
        username="admin_user",
        password="AdminPass123!",
        display_name="Admin",
        roles=[Role.ADMIN.value],
    )
    daemon = DaemonService(paths=paths)
    app = create_control_app(paths=paths, daemon_service=daemon)
    client = TestClient(app)

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPass123!"},
    )
    assert resp.status_code == 200
    set_cookie = resp.headers.get("set-cookie", "")
    assert "Secure" in set_cookie
    assert "HttpOnly" in set_cookie
    assert "SameSite=lax" in set_cookie


def test_ws_logs_rejects_query_token(tmp_path):
    paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "packs",
    )
    paths.ensure_directories()
    init_auth_db(paths.auth_db_path)
    user = create_user(
        paths.auth_db_path,
        username="admin_user",
        password="AdminPass123!",
        display_name="Admin",
        roles=[Role.ADMIN.value],
    )
    secret = get_or_create_auth_secret(paths.state_dir)
    token = sign_session_token("valid-sess-id", secret)

    daemon = DaemonService(paths=paths)
    app = create_control_app(paths=paths, daemon_service=daemon)
    client = TestClient(app)

    # Trying to connect with token in query params must be rejected
    with pytest.raises(Exception):
        with client.websocket_connect(f"/api/v1/ws/logs?token={token}"):
            pass


@pytest.mark.asyncio
async def test_daemon_handle_action_ignores_spoofed_caller_id(tmp_path):
    paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "packs",
    )
    paths.ensure_directories()
    daemon = DaemonService(paths=paths)
    daemon.setup()

    events = []
    # Attacker tries to send caller_id: "root" in payload
    payload = {
        "command": "status",
        "parameters": {},
        "caller_id": "root_spoofed",
    }
    async for evt in daemon.handle_action("execute", payload):
        events.append(evt)

    res = next((e for e in events if e.get("event") == "result"), None)
    assert res is not None

    # Check audit logger: caller_id recorded must NOT be root_spoofed
    audit_events = daemon.audit.read_events()
    assert len(audit_events) >= 1
    last_audit = audit_events[-1]
    assert last_audit.caller_id != "root_spoofed"
    assert last_audit.caller_id.startswith("ipc:")
