import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db, AsyncSessionLocal, engine, Base
from app.models.entities import TargetModel
from app.domain.catalogs import upsert_discovered_items
from app.gateway.manager import gateway_manager
from app.protocol.envelope import MessageEnvelope


async def reset_db():
    await init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_vanilla_catalog_api():
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Get all vanilla
        resp = await client.get("/api/catalogs/vanilla")
        assert resp.status_code == 200
        data = resp.json()
        assert "categories" in data
        assert "combat" in data["categories"]
        assert data["count"] > 0

        # Filter by category
        combat_resp = await client.get("/api/catalogs/vanilla?category=combat")
        assert combat_resp.status_code == 200
        combat_data = combat_resp.json()
        assert all(it["category"] == "combat" for it in combat_data["items"])

        # Search query
        search_resp = await client.get("/api/catalogs/vanilla?search=mace")
        assert search_resp.status_code == 200
        search_data = search_resp.json()
        assert any(it["id"] == "MACE" for it in search_data["items"])


@pytest.mark.asyncio
async def test_target_discovered_items_api():
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a target
        await client.post("/api/targets", json={"id": "api-target-1", "name": "API Target"})

        # Preload discovered items
        async with AsyncSessionLocal() as db:
            await upsert_discovered_items(db, "api-target-1", "oraxen", [
                {
                    "id": "molten_sword",
                    "material": "NETHERITE_SWORD",
                    "display_name": "<red>Molten Sword</red>",
                    "custom_model_data": 12001
                }
            ])

        # Query discovered items via API
        resp = await client.get("/api/catalogs/targets/api-target-1/items")
        assert resp.status_code == 200
        items = resp.json()
        assert len(items) == 1
        assert items[0]["item_id"] == "molten_sword"
        assert items[0]["material"] == "NETHERITE_SWORD"
        assert items[0]["custom_model_data"] == 12001


@pytest.mark.asyncio
async def test_sync_target_catalog_api():
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/api/targets", json={"id": "api-target-2", "name": "API Target 2"})

        # When offline, should return 503
        offline_resp = await client.post("/api/catalogs/targets/api-target-2/sync")
        assert offline_resp.status_code == 503

        # Mock online session
        class MockWebSocket:
            def __init__(self):
                self.sent_messages = []

            async def send_text(self, text):
                self.sent_messages.append(text)

        mock_ws = MockWebSocket()
        await gateway_manager.register_session("api-target-2", mock_ws)

        # Responder task
        async def mock_agent_catalog_responder():
            for _ in range(50):
                await asyncio.sleep(0.05)
                if mock_ws.sent_messages:
                    last_msg = MessageEnvelope.model_validate_json(mock_ws.sent_messages[-1])
                    if last_msg.payload.get("action") == "catalog:refresh":
                        resp_env = MessageEnvelope(
                            messageType="response",
                            correlationId=last_msg.messageId,
                            targetId="api-target-2",
                            payload={
                                "status": "success",
                                "source": "oraxen",
                                "items": [
                                    {
                                        "id": "synced_staff",
                                        "material": "BLAZE_ROD",
                                        "display_name": "<gold>Synced Staff</gold>",
                                        "custom_model_data": 13001
                                    }
                                ]
                            }
                        )
                        await gateway_manager.handle_message(mock_ws, resp_env.model_dump_json(), AsyncSessionLocal)
                        break

        responder = asyncio.create_task(mock_agent_catalog_responder())
        sync_resp = await client.post("/api/catalogs/targets/api-target-2/sync")
        await responder
        assert sync_resp.status_code == 200
        assert sync_resp.json()["status"] == "success"

        # Verify item was saved to db
        items_resp = await client.get("/api/catalogs/targets/api-target-2/items")
        assert items_resp.status_code == 200
        synced_items = items_resp.json()
        assert len(synced_items) == 1
        assert synced_items[0]["item_id"] == "synced_staff"

        await gateway_manager.unregister_session("api-target-2", AsyncSessionLocal)


@pytest.mark.asyncio
async def test_plugin_schemas_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # List schemas
        list_resp = await client.get("/api/catalogs/schemas")
        assert list_resp.status_code == 200
        schemas = list_resp.json()
        assert len(schemas) >= 1
        assert any(s["id"] == "oraxen-item-v1" for s in schemas)

        # Get specific schema
        schema_resp = await client.get("/api/catalogs/schemas/oraxen-item-v1")
        assert schema_resp.status_code == 200
        data = schema_resp.json()
        assert data["plugin"] == "oraxen"
        assert len(data["sections"]) == 2
        assert "default_yaml_template" in data

        # Non-existing schema
        notFound = await client.get("/api/catalogs/schemas/non_existent_schema_xyz")
        assert notFound.status_code == 404
