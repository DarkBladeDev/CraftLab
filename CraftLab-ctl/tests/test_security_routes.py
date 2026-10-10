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

    admin_user = create_user(
        temp_ctl_paths.auth_db_path,
        username="sec_admin",
        password="AdminPassword123!",
        roles=[Role.ADMIN.value],
    )
    viewer_user = create_user(
        temp_ctl_paths.auth_db_path,
        username="sec_viewer",
        password="ViewerPassword123!",
        roles=[Role.VIEWER.value],
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
        "admin": admin_user,
        "viewer": viewer_user,
    }


def login_user(client: TestClient, username: str, password: str) -> None:
    res = client.post("/api/v1/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200


def test_security_telemetry_and_containment_flow(test_setup):
    client = test_setup["client"]

    # 1. Unauthenticated request to posture should fail 401
    res = client.get("/api/v1/security/posture")
    assert res.status_code == 401

    # 2. Login as admin
    login_user(client, "sec_admin", "AdminPassword123!")

    # 3. Query posture and anomalies
    res_posture = client.get("/api/v1/security/posture")
    assert res_posture.status_code == 200
    posture_data = res_posture.json()
    assert "threat_index" in posture_data
    assert posture_data["classification"] in ("NORMAL", "ELEVATED", "HIGH", "CRITICAL")

    res_anomalies = client.get("/api/v1/security/anomalies")
    assert res_anomalies.status_code == 200
    assert isinstance(res_anomalies.json(), list)

    res_quarantines = client.get("/api/v1/security/quarantines")
    assert res_quarantines.status_code == 200
    assert res_quarantines.json() == []

    # 4. Quarantine IP
    res_q = client.post(
        "/api/v1/security/quarantine",
        json={"ip": "192.168.1.99", "duration_minutes": 15, "reason": "Test attack probe"},
    )
    assert res_q.status_code == 200
    assert res_q.json()["success"] is True

    # Verify active quarantines list contains it
    res_q_list = client.get("/api/v1/security/quarantines")
    assert len(res_q_list.json()) == 1
    assert res_q_list.json()[0]["ip"] == "192.168.1.99"

    # 5. Unquarantine IP
    res_unq = client.post("/api/v1/security/unquarantine", json={"ip": "192.168.1.99"})
    assert res_unq.status_code == 200
    assert res_unq.json()["success"] is True

    # 6. Session revocation
    res_revoke = client.post(
        "/api/v1/security/revoke-sessions",
        json={"all_except_caller": True},
    )
    assert res_revoke.status_code == 200
    assert res_revoke.json()["success"] is True

    # 7. Lockdown toggle
    res_lock = client.post(
        "/api/v1/security/toggle-lockdown",
        json={"enabled": True, "reason": "Emergency security testing"},
    )
    assert res_lock.status_code == 200
    assert res_lock.json()["enabled"] is True

    # In lockdown mode, posture shows LOCKDOWN
    res_posture2 = client.get("/api/v1/security/posture")
    assert res_posture2.json()["classification"] == "LOCKDOWN"

    # In lockdown mode, non-admin login should be rejected with 403
    client2 = TestClient(test_setup["app"])
    res_viewer_login = client2.post(
        "/api/v1/auth/login",
        json={"username": "sec_viewer", "password": "ViewerPassword123!"},
    )
    assert res_viewer_login.status_code == 403
    assert "lockdown" in res_viewer_login.json()["detail"].lower()

    # Disable lockdown
    client.post("/api/v1/security/toggle-lockdown", json={"enabled": False})


def test_quarantine_middleware_enforcement(test_setup):
    client = test_setup["client"]
    app = test_setup["app"]

    # Directly quarantine an IP
    app.state.quarantine_manager.quarantine("203.0.113.5", duration_minutes=30)

    # Issue request with x-forwarded-for of the quarantined IP
    res = client.get("/api/v1/status", headers={"X-Forwarded-For": "203.0.113.5"})
    assert res.status_code == 403
    assert "quarantined" in res.json()["detail"]


def test_rbac_mitigation_endpoints_forbidden_for_viewer(test_setup):
    client = test_setup["client"]
    login_user(client, "sec_viewer", "ViewerPassword123!")

    # Viewer can read posture and anomalies
    assert client.get("/api/v1/security/posture").status_code == 200

    # Viewer is rejected from mutating actions
    assert client.post("/api/v1/security/quarantine", json={"ip": "1.2.3.4"}).status_code == 403
    assert client.post("/api/v1/security/unquarantine", json={"ip": "1.2.3.4"}).status_code == 403
    assert client.post("/api/v1/security/revoke-sessions", json={}).status_code == 403
    assert client.post("/api/v1/security/toggle-lockdown", json={"enabled": True}).status_code == 403
    assert client.post("/api/v1/security/purge", json={"retention_days": 30}).status_code == 403
