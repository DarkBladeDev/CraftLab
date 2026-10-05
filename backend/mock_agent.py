import asyncio
import json
import logging
from pathlib import Path
import websockets

logging.basicConfig(
    level=logging.INFO,
    format="\033[94m%(asctime)s\033[0m [\033[92mMockAgent\033[0m] %(message)s"
)
logger = logging.getLogger("MockAgent")

GATEWAY_URI = "ws://127.0.0.1:8000/ws/agent"
TARGET_ID = "local-paper-server"
STORAGE_DIR = Path("mock_server_storage")
STORAGE_FILE = STORAGE_DIR / "items.json"


def save_local_item(item_data: dict):
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    items = {}
    if STORAGE_FILE.exists():
        try:
            with open(STORAGE_FILE, "r", encoding="utf-8") as f:
                items = json.load(f)
        except Exception:
            items = {}
    items[item_data["id"]] = item_data
    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, indent=2)
    logger.info(f"Persisted item '{item_data['id']}' to {STORAGE_FILE}")


async def run_agent():
    logger.info(f"Connecting to MCP Gateway at {GATEWAY_URI} as target '{TARGET_ID}'...")
    while True:
        try:
            async with websockets.connect(GATEWAY_URI) as ws:
                logger.info("Connected to Gateway! Sending agent.hello handshake...")

                # 1. Hello Handshake
                hello_env = {
                    "protocolVersion": "1.0",
                    "messageType": "hello",
                    "messageId": "msg-hello-001",
                    "targetId": TARGET_ID,
                    "payload": {
                        "agentVersion": "1.0.0",
                        "minecraftVersion": "1.21.1",
                        "paperVersion": "Paper-1.21.1-R0.1-SNAPSHOT (MockRuntime)",
                        "adapters": ["paper-1.21"]
                    }
                }
                await ws.send(json.dumps(hello_env))

                # Background heartbeat task
                async def heartbeat():
                    while True:
                        await asyncio.sleep(15)
                        hb_env = {
                            "protocolVersion": "1.0",
                            "messageType": "event",
                            "messageId": f"msg-hb-{asyncio.get_event_loop().time()}",
                            "targetId": TARGET_ID,
                            "payload": {"type": "heartbeat"}
                        }
                        await ws.send(json.dumps(hb_env))
                        logger.info("Sent heartbeat to gateway.")

                hb_task = asyncio.create_task(heartbeat())

                try:
                    # Message listening loop
                    async for raw in ws:
                        msg = json.loads(raw)
                        msg_type = msg.get("messageType")
                        payload = msg.get("payload", {})

                        if msg_type == "response" and payload.get("status") == "accepted":
                            logger.info(f"\033[92mSession Accepted by Gateway!\033[0m Target '{TARGET_ID}' is now ONLINE.")

                        elif msg_type == "response" and payload.get("status") == "pong":
                            pass  # Heartbeat ack

                        elif msg_type == "request":
                            action = payload.get("action")
                            op_id = payload.get("operationId")
                            correlation_id = msg.get("correlationId") or msg.get("messageId")

                            logger.info(f"\033[93mReceived operation request:\033[0m action='{action}', op_id='{op_id}'")

                            if action == "create_or_update_item":
                                item_data = payload.get("item", {})
                                save_local_item(item_data)
                                logger.info(f"\033[92m[Paper 1.21 Adapter]\033[0m Compiled ItemStack: {item_data.get('material')} - '{item_data.get('display_name')}'")

                                # Send success response
                                resp_env = {
                                    "protocolVersion": "1.0",
                                    "messageType": "response",
                                    "messageId": f"msg-resp-{op_id}",
                                    "correlationId": correlation_id,
                                    "targetId": TARGET_ID,
                                    "payload": {
                                        "status": "applied",
                                        "success": True,
                                        "itemId": item_data.get("id"),
                                        "material": item_data.get("material")
                                    }
                                }
                                await ws.send(json.dumps(resp_env))
                                logger.info(f"\033[92mSent operation confirmation back to Gateway!\033[0m")
                finally:
                    hb_task.cancel()

        except (websockets.ConnectionClosed, ConnectionRefusedError, OSError) as e:
            logger.warning(f"Connection lost or gateway not ready ({e}). Retrying in 4s...")
            await asyncio.sleep(4)


if __name__ == "__main__":
    try:
        asyncio.run(run_agent())
    except KeyboardInterrupt:
        logger.info("Mock agent stopped.")
