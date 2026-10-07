import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from craftlab_ctl.core.paths import CtlPaths
from craftlab_ctl.daemon import DaemonService
from craftlab_ctl.auth import Role, create_user
from craftlab_ctl.server.app import create_control_app
from craftlab_ctl.supervisor.logs import LogRingBuffer


@pytest.fixture
def temp_ctl_paths(tmp_path: Path) -> CtlPaths:
    paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "data" / "packs",
    )
    paths.ensure_directories()
    return paths


@pytest.fixture
def test_setup(temp_ctl_paths: CtlPaths):
    daemon = DaemonService(paths=temp_ctl_paths)
    daemon.setup()

    # Pre-create test users
    admin_user = create_user(
        temp_ctl_paths.auth_db_path,
        username="admin_user",
        password="AdminPassword123!",
        roles=[Role.ADMIN.value],
    )
    creator_user = create_user(
        temp_ctl_paths.auth_db_path,
        username="creator_user",
        password="CreatorPassword123!",
        roles=[Role.CREATOR.value],
    )

    ring_buf = LogRingBuffer(max_lines=100)
    app = create_control_app(
        daemon_service=daemon,
        paths=temp_ctl_paths,
        log_buffer=ring_buf,
    )
    client = TestClient(app)
    return {
        "daemon": daemon,
        "paths": temp_ctl_paths,
        "app": app,
        "client": client,
        "ring_buf": ring_buf,
        "admin": admin_user,
        "creator": creator_user,
    }


def test_unauthenticated_requests_rejected(test_setup):
    client = test_setup["client"]

    # Endpoints require authentication
    resp = client.get("/api/v1/status")
    assert resp.status_code == 401

    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 401

    resp = client.get("/api/v1/doctor")
    assert resp.status_code == 401


def test_auth_login_flow(test_setup):
    client = test_setup["client"]

    # Bad credentials
    bad_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "WrongPassword"},
    )
    assert bad_resp.status_code == 401

    # Good credentials
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword123!"},
    )
    assert login_resp.status_code == 200
    data = login_resp.json()
    assert data["username"] == "admin_user"
    assert "admin" in data["roles"]
    assert "craftlab_session" in client.cookies

    # Access /api/v1/auth/me with session cookie
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin_user"

    # Status check with session cookie
    status_resp = client.get("/api/v1/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["service"] == "backend"

    # Logout
    logout_resp = client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200
    assert "craftlab_session" not in client.cookies

    # After logout
    assert client.get("/api/v1/status").status_code == 401


def test_metrics_endpoint(test_setup):
    client = test_setup["client"]
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword123!"},
    )
    assert login_resp.status_code == 200

    resp = client.get("/api/v1/metrics")
    assert resp.status_code == 200
    data = resp.json()

    assert "host" in data
    assert "cpu_percent" in data["host"]
    assert "memory" in data["host"]
    assert "disk" in data["host"]
    assert "process" in data
    assert data["process"]["status"] in ["running", "stopped"]


def test_doctor_endpoint(test_setup):
    client = test_setup["client"]
    login_resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword123!"},
    )
    assert login_resp.status_code == 200

    resp = client.get("/api/v1/doctor")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall" in data
    assert "checks" in data
    assert isinstance(data["checks"], list)


def test_role_based_access_control(test_setup):
    client = test_setup["client"]

    # Login as creator (forbidden on lifecycle)
    client.post(
        "/api/v1/auth/login",
        json={"username": "creator_user", "password": "CreatorPassword123!"},
    )

    # Creator role cannot execute lifecycle
    resp = client.post("/api/v1/lifecycle/start")
    assert resp.status_code == 403

    # Login as admin (allowed on lifecycle)
    client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword123!"},
    )
    resp_admin = client.post("/api/v1/lifecycle/status")
    assert resp_admin.status_code == 200
    assert resp_admin.json()["success"] is True


def test_websocket_log_streaming(test_setup):
    client = test_setup["client"]
    ring_buf = test_setup["ring_buf"]
    ring_buf.append("Log line 1: Initialized")
    ring_buf.append("Log line 2: Ready")

    # Login as admin
    resp = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_user", "password": "AdminPassword123!"},
    )
    cookie_val = client.cookies.get("craftlab_session")

    with client.websocket_connect("/api/v1/ws/logs", headers={"cookie": f"craftlab_session={cookie_val}"}) as websocket:
        line1 = websocket.receive_text()
        assert line1 == "Log line 1: Initialized"
        line2 = websocket.receive_text()
        assert line2 == "Log line 2: Ready"


def test_static_spa_serving(temp_ctl_paths: CtlPaths):
    daemon = DaemonService(paths=temp_ctl_paths)
    daemon.setup()

    dist_dir = temp_ctl_paths.home / "web_dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = dist_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    (dist_dir / "index.html").write_text("<!DOCTYPE html><html><body>Root SPA</body></html>", encoding="utf-8")
    (assets_dir / "app.js").write_text("console.log('test');", encoding="utf-8")

    app = create_control_app(
        daemon_service=daemon,
        paths=temp_ctl_paths,
        static_dir=dist_dir,
    )
    client = TestClient(app)

    # Root serves index.html
    root_resp = client.get("/")
    assert root_resp.status_code == 200
    assert "Root SPA" in root_resp.text

    # Assets are served
    asset_resp = client.get("/assets/app.js")
    assert asset_resp.status_code == 200
    assert "console.log" in asset_resp.text

    # Client-side router path falls back to index.html
    fallback_resp = client.get("/dashboard/lifecycle")
    assert fallback_resp.status_code == 200
    assert "Root SPA" in fallback_resp.text
