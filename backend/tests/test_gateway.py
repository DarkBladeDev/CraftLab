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


from app.models.entities import DiscoveredCatalogItemModel


@pytest.mark.asyncio
async def test_gateway_hello_with_detected_plugins_and_manifest():
    await init_db()
    manager = AgentSessionManager()
    mock_ws = AsyncMock()

    hello_msg = json.dumps({
        "protocolVersion": "1.0",
        "messageType": "hello",
        "messageId": "msg-hello-plugins",
        "targetId": "paper-target-plugins",
        "payload": {
            "agentVersion": "1.1.0",
            "minecraftVersion": "1.21.1",
            "paperVersion": "1.21.1-R0.1-SNAPSHOT",
            "adapters": ["paper-1.21", "oraxen-adapter"],
            "detectedPlugins": [
                {"name": "Oraxen", "version": "1.18.0", "enabled": True}
            ],
            "catalogManifest": {
                "source": "oraxen",
                "items": [
                    {
                        "id": "crystal_blade",
                        "material": "DIAMOND_SWORD",
                        "display_name": "<cyan>Crystal Blade</cyan>",
                        "custom_model_data": 20001
                    }
                ]
            }
        }
    })

    resp = await manager.handle_message(mock_ws, hello_msg, AsyncSessionLocal)
    assert resp is not None
    assert resp.payload["status"] == "accepted"

    # Verify target has detected plugins in environment_metadata
    async with AsyncSessionLocal() as db:
        res = await db.execute(select(TargetModel).where(TargetModel.id == "paper-target-plugins"))
        target = res.scalar_one_or_none()
        assert target is not None
        assert target.environment_metadata["detectedPlugins"][0]["name"] == "Oraxen"

        # Verify catalog item was stored
        item_res = await db.execute(
            select(DiscoveredCatalogItemModel).where(DiscoveredCatalogItemModel.target_id == "paper-target-plugins")
        )
        items = list(item_res.scalars().all())
        assert len(items) == 1
        assert items[0].item_id == "crystal_blade"
        assert items[0].custom_model_data == 20001


@pytest.mark.asyncio
async def test_gateway_catalog_manifest_event():
    await init_db()
    manager = AgentSessionManager()
    mock_ws = AsyncMock()

    # Stream catalog manifest event
    event_msg = json.dumps({
        "protocolVersion": "1.0",
        "messageType": "event",
        "messageId": "msg-event-manifest",
        "targetId": "paper-target-plugins",
        "payload": {
            "type": "catalog:manifest",
            "source": "oraxen",
            "items": [
                {
                    "id": "shadow_bow",
                    "material": "BOW",
                    "display_name": "<dark_purple>Shadow Bow</dark_purple>",
                    "custom_model_data": 20002
                }
            ]
        }
    })

    resp = await manager.handle_message(mock_ws, event_msg, AsyncSessionLocal)
    assert resp is not None

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(DiscoveredCatalogItemModel).where(
                DiscoveredCatalogItemModel.id == "paper-target-plugins:oraxen:shadow_bow"
            )
        )
        item = res.scalar_one_or_none()
        assert item is not None
        assert item.material == "BOW"
        assert item.custom_model_data == 20002
