import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from main import app
from app.core.database import init_db, AsyncSessionLocal, engine, Base
from app.gateway.manager import gateway_manager
from app.protocol.envelope import MessageEnvelope


@pytest.mark.asyncio
async def test_end_to_end_full_pipeline():
    # 0. Fresh database setup
    await init_db()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Author custom item in API
        item_payload = {
            "id": "ruby_sword",
            "material": "DIAMOND_SWORD",
            "display_name": "<red><bold>Ruby Sword</bold></red>",
            "lore": ["<gray>Forged in ancient magma chambers.</gray>", "<dark_red>Attack Damage: +12</dark_red>"],
            "custom_model_data": 10001,
            "item_flags": ["HIDE_ATTRIBUTES"],
            "amount": 1
        }
        item_res = await client.post("/api/items", json=item_payload)
        assert item_res.status_code == 200

        # 2. Snapshot an immutable revision
        rev_res = await client.post("/api/revisions")
        assert rev_res.status_code == 200
        rev_data = rev_res.json()
        assert rev_data["revision_number"] == 1
        assert len(rev_data["revision_hash"]) == 64
        revision_id = rev_data["id"]

        # 3. Simulate Paper Server Agent connection
        target_id = "paper-prod-server"
        mock_server_storage = {}

        class AgentWebSocketMock:
            def __init__(self):
                self.messages = []

            async def send_text(self, text):
                self.messages.append(text)

        agent_ws = AgentWebSocketMock()

        # Agent Handshake (agent.hello)
        hello_msg = json.dumps({
            "protocolVersion": "1.0",
            "messageType": "hello",
            "messageId": "msg-agent-hello",
            "targetId": target_id,
            "payload": {
                "agentVersion": "1.0.0",
                "minecraftVersion": "1.21.1",
                "paperVersion": "git-Paper-123 (MC: 1.21.1)",
                "adapters": ["paper-1.21"]
            }
        })
        hello_resp = await gateway_manager.handle_message(agent_ws, hello_msg, AsyncSessionLocal)
        assert hello_resp is not None
        assert hello_resp.payload["status"] == "accepted"
        assert gateway_manager.is_online(target_id)

        # Agent Heartbeat
        hb_msg = json.dumps({
            "protocolVersion": "1.0",
            "messageType": "event",
            "messageId": "msg-agent-hb",
            "targetId": target_id,
            "payload": {"type": "heartbeat"}
        })
        hb_resp = await gateway_manager.handle_message(agent_ws, hb_msg, AsyncSessionLocal)
        assert hb_resp is not None
        assert hb_resp.payload["status"] == "pong"

        # 4. Generate deployment plan
        plan_res = await client.post("/api/deployments/plans", json={
            "revision_id": revision_id,
            "target_id": target_id
        })
        assert plan_res.status_code == 200
        plan_data = plan_res.json()
        plan_id = plan_data["id"]
        assert plan_data["status"] == "draft"
        assert len(plan_data["operations"]) == 1
        assert plan_data["operations"][0]["resourceId"] == "ruby_sword"

        # 5. Review & approve deployment plan
        approve_res = await client.post(f"/api/deployments/plans/{plan_id}/approve")
        assert approve_res.status_code == 200
        assert approve_res.json()["status"] == "approved"

        # 6. Background simulated agent execution logic (simulating Paper 1.21 adapter & local storage)
        with tempfile.TemporaryDirectory() as tmp_dir:
            items_json_path = Path(tmp_dir) / "items.json"

            async def agent_execution_loop():
                for _ in range(50):
                    await asyncio.sleep(0.05)
                    if agent_ws.messages:
                        # Find the last unhandled request message
                        for msg_text in list(agent_ws.messages):
                            msg_env = json.loads(msg_text)
                            if msg_env.get("messageType") == "request":
                                action = msg_env["payload"]["action"]
                                op_id = msg_env["payload"]["operationId"]
                                if action == "create_or_update_item":
                                    item_data = msg_env["payload"]["item"]
                                    mock_server_storage[item_data["id"]] = item_data
                                    # Write to items.json file to verify persistence
                                    with open(items_json_path, "w", encoding="utf-8") as f:
                                        json.dump(mock_server_storage, f, indent=2)

                                    # Send back success response envelope
                                    resp_env = MessageEnvelope(
                                        messageType="response",
                                        correlationId=op_id,
                                        targetId=target_id,
                                        payload={
                                            "status": "applied",
                                            "success": True,
                                            "itemId": item_data["id"],
                                            "material": item_data["material"]
                                        }
                                    )
                                    await gateway_manager.handle_message(
                                        agent_ws, resp_env.model_dump_json(), AsyncSessionLocal
                                    )
                                    return

            agent_task = asyncio.create_task(agent_execution_loop())

            # 7. Trigger deployment execution
            exec_res = await client.post(f"/api/deployments/plans/{plan_id}/execute")
            await agent_task

            assert exec_res.status_code == 200
            exec_data = exec_res.json()
            assert exec_data["status"] == "applied"
            assert len(exec_data["log"]) == 1
            assert exec_data["log"][0]["status"] == "success"

            # 8. Verify the local server file storage holds the deployed item!
            assert items_json_path.exists()
            with open(items_json_path, "r", encoding="utf-8") as f:
                saved_items = json.load(f)
                assert "ruby_sword" in saved_items
                assert saved_items["ruby_sword"]["material"] == "DIAMOND_SWORD"
                assert saved_items["ruby_sword"]["custom_model_data"] == 10001
                assert saved_items["ruby_sword"]["item_flags"] == ["HIDE_ATTRIBUTES"]

        # Clean up session
        await gateway_manager.unregister_session(target_id, AsyncSessionLocal)
