import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, AsyncMock
from main import app
from app.core.database import init_db


@pytest.mark.asyncio
async def test_health_probe():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pass"
        assert data["service"] == "craftlab-backend"
        assert "uptime_seconds" in data
        assert "pid" in data


@pytest.mark.asyncio
async def test_ready_probe_success():
    await init_db()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"
        assert data["checks"]["database"] == "ok"
        assert data["checks"]["storage"] == "ok"


@pytest.mark.asyncio
async def test_ready_probe_database_failure():
    with patch("main.AsyncSessionLocal", side_effect=Exception("Database connection timeout")):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "degraded"
            assert "error:" in data["checks"]["database"]


@pytest.mark.asyncio
async def test_graceful_shutdown_lifespan():
    from app.gateway.manager import gateway_manager
    mock_ws = AsyncMock()
    await gateway_manager.register_session("test-target", mock_ws)
    assert gateway_manager.is_online("test-target")

    # Simulate lifespan shutdown
    from main import lifespan
    async with lifespan(app):
        pass

    assert not gateway_manager.is_online("test-target")
    mock_ws.close.assert_awaited()
