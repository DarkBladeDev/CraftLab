import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db, AsyncSessionLocal, engine, Base
from app.models.entities import TargetModel
from app.gateway.manager import gateway_manager
from app.protocol.envelope import MessageEnvelope


async def reset_db():
    await init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


@pytest.mark.asyncio
async def test_full_plan_and_approval_workflow():
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Create a target
        target_resp = await client.post("/api/targets", json={"id": "server-1", "name": "Survival 1"})
        assert target_resp.status_code == 200

        # 2. Create an item
        item_resp = await client.post("/api/items", json={
            "id": "emerald_dagger",
            "material": "DIAMOND_SWORD",
            "display_name": "<green>Emerald Dagger</green>",
            "lore": ["Quick and silent"],
            "custom_model_data": 5001,
            "item_flags": ["HIDE_ATTRIBUTES"]
        })
        assert item_resp.status_code == 200

        # 3. Create a revision
        rev_resp = await client.post("/api/revisions")
        assert rev_resp.status_code == 200
        rev_data = rev_resp.json()
        rev_id = rev_data["id"]

        # 4. Generate deployment plan (Task 2.5)
        plan_resp = await client.post("/api/deployments/plans", json={
            "revision_id": rev_id,
            "target_id": "server-1"
        })
        assert plan_resp.status_code == 200
        plan_data = plan_resp.json()
        assert plan_data["status"] == "draft"
        assert len(plan_data["operations"]) == 1
        assert plan_data["operations"][0]["action"] == "create_or_update_item"
        assert plan_data["operations"][0]["resourceId"] == "emerald_dagger"
        plan_id = plan_data["id"]

        # 5. Approve deployment plan (Task 2.5)
        approve_resp = await client.post(f"/api/deployments/plans/{plan_id}/approve")
        assert approve_resp.status_code == 200
        assert approve_resp.json()["status"] == "approved"

        # 6. Verify cannot execute if target is offline
        exec_offline_resp = await client.post(f"/api/deployments/plans/{plan_id}/execute")
        assert exec_offline_resp.status_code == 503


@pytest.mark.asyncio
async def test_deployment_execution_with_agent_result():
    # Test Task 2.6: execution dispatcher and correlation tracking
    await reset_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Register target and item
        await client.post("/api/targets", json={"id": "server-2", "name": "Survival 2"})
        await client.post("/api/items", json={
            "id": "solar_bow",
            "material": "BOW",
            "display_name": "<gold>Solar Bow</gold>"
        })
        rev_resp = await client.post("/api/revisions")
        rev_id = rev_resp.json()["id"]

        plan_resp = await client.post("/api/deployments/plans", json={
            "revision_id": rev_id,
            "target_id": "server-2"
        })
        plan_id = plan_resp.json()["id"]
        await client.post(f"/api/deployments/plans/{plan_id}/approve")

        # Mock connected agent WebSocket
        class MockWebSocket:
            def __init__(self):
                self.sent_messages = []

            async def send_text(self, text):
                self.sent_messages.append(text)

        mock_ws = MockWebSocket()
        await gateway_manager.register_session("server-2", mock_ws)

        # Background task that responds to the correlated request
        async def mock_agent_responder():
            for _ in range(50):
                await asyncio.sleep(0.05)
                if mock_ws.sent_messages:
                    last_msg = MessageEnvelope.model_validate_json(mock_ws.sent_messages[-1])
                    op_id = last_msg.payload.get("operationId")
                    # Send response back to gateway
                    resp_env = MessageEnvelope(
                        messageType="response",
                        correlationId=op_id,
                        targetId="server-2",
                        payload={"status": "applied", "itemHash": "hash123", "success": True}
                    )
                    await gateway_manager.handle_message(mock_ws, resp_env.model_dump_json(), AsyncSessionLocal)
                    break

        responder_task = asyncio.create_task(mock_agent_responder())

        # Execute deployment plan
        exec_resp = await client.post(f"/api/deployments/plans/{plan_id}/execute")
        await responder_task
        assert exec_resp.status_code == 200
        exec_data = exec_resp.json()
        assert exec_data["status"] == "applied"
        assert len(exec_data["log"]) == 1
        assert exec_data["log"][0]["status"] == "success"
        assert exec_data["log"][0]["result"]["success"] is True

        # Clean up
        await gateway_manager.unregister_session("server-2", AsyncSessionLocal)
