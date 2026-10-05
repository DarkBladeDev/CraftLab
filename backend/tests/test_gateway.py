import pytest
import json
from unittest.mock import AsyncMock
from app.protocol.envelope import MessageEnvelope
from app.gateway.manager import AgentSessionManager
from app.core.database import init_db, AsyncSessionLocal
from app.models.entities import TargetModel
from sqlalchemy import select


@pytest.mark.asyncio
async def test_envelope_serialization():
    env = MessageEnvelope(
        messageType="request",
        targetId="paper-target-1",
        payload={"action": "test"}
    )
    dumped = env.model_dump_json()
    loaded = MessageEnvelope.model_validate_json(dumped)
    assert loaded.messageType == "request"
    assert loaded.targetId == "paper-target-1"
    assert loaded.protocolVersion == "1.0"


@pytest.mark.asyncio
async def test_gateway_hello_and_heartbeat():
    await init_db()
    manager = AgentSessionManager()
    mock_ws = AsyncMock()

    # 1. Hello handshake
    hello_msg = json.dumps({
        "protocolVersion": "1.0",
        "messageType": "hello",
        "messageId": "msg-001",
        "targetId": "paper-target-1",
        "payload": {
            "agentVersion": "1.0.0",
            "minecraftVersion": "1.21.1",
            "paperVersion": "1.21.1-R0.1-SNAPSHOT",
            "adapters": ["paper-1.21"]
        }
    })

    resp = await manager.handle_message(mock_ws, hello_msg, AsyncSessionLocal)
    assert resp is not None
    assert resp.messageType == "response"
    assert resp.payload["status"] == "accepted"
    assert manager.is_online("paper-target-1")

    # Verify target was persisted in DB
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TargetModel).where(TargetModel.id == "paper-target-1"))
        target = res.scalar_one_or_none()
        assert target is not None
        assert target.status == "online"
        assert target.environment_metadata["minecraftVersion"] == "1.21.1"

    # 2. Heartbeat
    heartbeat_msg = json.dumps({
        "protocolVersion": "1.0",
        "messageType": "event",
        "messageId": "msg-002",
        "targetId": "paper-target-1",
        "payload": {"type": "heartbeat"}
    })
    resp_hb = await manager.handle_message(mock_ws, heartbeat_msg, AsyncSessionLocal)
    assert resp_hb is not None
    assert resp_hb.payload["status"] == "pong"

    # 3. Disconnect
    await manager.unregister_session("paper-target-1", AsyncSessionLocal)
    assert not manager.is_online("paper-target-1")
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TargetModel).where(TargetModel.id == "paper-target-1"))
        target = res.scalar_one_or_none()
        assert target.status == "offline"
