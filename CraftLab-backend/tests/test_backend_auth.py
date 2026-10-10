import pytest
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.config import settings
from app.core.database import init_db
from craftlab_ctl.core.paths import CtlPaths
from craftlab_ctl.auth import Role, init_auth_db, create_user


@pytest.fixture(autouse=True)
def setup_auth_env(tmp_path, monkeypatch):
    # Enable auth for this test module
    monkeypatch.setattr(settings.server, "auth_enabled", True)
    monkeypatch.setattr(settings.paths, "home", tmp_path)

    tmp_ctl_paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "data" / "packs",
    )
    tmp_ctl_paths.ensure_directories()
    init_auth_db(tmp_ctl_paths.auth_db_path)

    # Monkeypatch get_ctl_paths in app.core.auth and app.api.auth
    monkeypatch.setattr("app.core.auth.get_ctl_paths", lambda: tmp_ctl_paths)
    monkeypatch.setattr("app.api.auth.get_ctl_paths", lambda: tmp_ctl_paths)

    # Create creator user and viewer user
    create_user(
        tmp_ctl_paths.auth_db_path,
        username="steve_builder",
        password="BlockBuilderPassword123!",
        roles=[Role.CREATOR.value],
    )
    create_user(
        tmp_ctl_paths.auth_db_path,
        username="just_viewer",
        password="ViewerPassword123!",
        roles=[Role.VIEWER.value],
    )


@pytest.mark.asyncio
async def test_backend_auth_protection_and_sso():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unauthenticated request rejected with 401
        res = await client.get("/api/v1/packs/sources")
        assert res.status_code == 401

        # 2. Login as creator
        login_res = await client.post(
            "/api/v1/auth/login",
            json={"username": "steve_builder", "password": "BlockBuilderPassword123!"},
        )
        assert login_res.status_code == 200
        assert "craftlab_session" in client.cookies

        # 3. Check /me
        me_res = await client.get("/api/v1/auth/me")
        assert me_res.status_code == 200
        assert me_res.json()["username"] == "steve_builder"

        # 4. Access protected packs endpoint as creator -> 200
        packs_res = await client.get("/api/v1/packs/sources")
        assert packs_res.status_code == 200

        # 5. Logout
        logout_res = await client.post("/api/v1/auth/logout")
        assert logout_res.status_code == 200
        assert "craftlab_session" not in client.cookies


@pytest.mark.asyncio
async def test_backend_viewer_role_forbidden():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as viewer
        await client.post(
            "/api/v1/auth/login",
            json={"username": "just_viewer", "password": "ViewerPassword123!"},
        )

        # Viewer role gets 403 on content endpoints (creator/admin required)
        res = await client.get("/api/v1/packs/sources")
        assert res.status_code == 403


@pytest.mark.asyncio
async def test_public_pack_endpoints_unauthenticated():
    """Verify that resource pack download and latest endpoints are publicly accessible without auth for Minecraft clients."""
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Protected endpoint returns 401 when unauthenticated
        res_prot = await client.get("/api/v1/packs/sources")
        assert res_prot.status_code == 401
        assert res_prot.json() == {"detail": "Authentication required"}

        # Public download endpoint must NOT return 401 (returns 200 with zip when pack exists or 404 when not yet compiled)
        res_dl = await client.get("/api/v1/packs/dev-server/download")
        assert res_dl.status_code in (200, 404)
        assert res_dl.status_code != 401
        if res_dl.status_code == 200:
            assert "application/zip" in res_dl.headers.get("content-type", "")

        # Public latest endpoint must NOT return 401 (returns 200 or 404 depending on records, never 401)
        res_latest = await client.get("/api/v1/packs/dev-server/latest")
        assert res_latest.status_code in (200, 404)
        if res_latest.status_code == 404:
            assert res_latest.json() != {"detail": "Authentication required"}

