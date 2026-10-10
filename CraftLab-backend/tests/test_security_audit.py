import json
import pytest
from unittest.mock import AsyncMock
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal
from app.gateway.manager import AgentSessionManager
from app.models.entities import TargetModel
from craftlab_security.sink import SecurityAuditSink


@pytest.mark.asyncio
async def test_auth_login_emits_audit_events():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Failed login attempt
        resp = await client.post(
            "/api/v1/auth/login",
            json={"username": "nonexistent", "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    sink = SecurityAuditSink(settings.paths.data_dir / "security-audit.sqlite3")
    events = sink.query_events(component="backend", event_type="auth.failure")
    assert len(events) >= 1
    last_event = events[0]
    assert last_event["status_code"] == 401
    assert last_event["reason_code"] == "invalid_credentials"


@pytest.mark.asyncio
async def test_agent_handshake_secret_validation():
    await init_db()
    import uuid
    target_id = f"test-sec-{uuid.uuid4().hex[:8]}"
    target_secret = "correct-super-secret"
    async with AsyncSessionLocal() as db:
        target = TargetModel(
            id=target_id,
            name="Secure Agent",
            secret=target_secret,
            status="offline",
        )
        db.add(target)
        await db.commit()

    manager = AgentSessionManager()

    # 1. Reject handshake with wrong secret
    mock_ws_wrong = AsyncMock()
    wrong_hello = json.dumps({
        "protocolVersion": "1.0",
        "messageType": "hello",
        "messageId": "msg-1",
        "targetId": target_id,
        "sentAt": "2026-10-09T00:00:00Z",
        "payload": {
            "targetSecret": "wrong-secret",
            "agentVersion": "1.0.0"
        }
    })
    resp = await manager.handle_message(mock_ws_wrong, wrong_hello, AsyncSessionLocal)
    assert resp is None
    mock_ws_wrong.close.assert_awaited_once_with(code=1008, reason="Authentication failed: target secret mismatch")

    sink = SecurityAuditSink(settings.paths.data_dir / "security-audit.sqlite3")
    events = sink.query_events(component="websocket_gateway", event_type="websocket.auth.failure")
    assert any(e["actor_id"] == target_id for e in events)

    # 2. Accept handshake with correct secret
    mock_ws_ok = AsyncMock()
    correct_hello = json.dumps({
        "protocolVersion": "1.0",
        "messageType": "hello",
        "messageId": "msg-2",
        "targetId": target_id,
        "sentAt": "2026-10-09T00:00:00Z",
        "payload": {
            "targetSecret": target_secret,
            "agentVersion": "1.0.0"
        }
    })
    resp = await manager.handle_message(mock_ws_ok, correct_hello, AsyncSessionLocal)
    assert resp is not None
    assert resp.messageType == "response"
    assert resp.payload["status"] == "accepted"
