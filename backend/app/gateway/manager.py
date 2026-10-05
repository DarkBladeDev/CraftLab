import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from fastapi import WebSocket
from sqlalchemy import select
from app.protocol.envelope import MessageEnvelope, utcnow_iso
from app.models.entities import TargetModel

logger = logging.getLogger("mcp.gateway")


class AgentSessionManager:
    def __init__(self):
        self._active_sessions: Dict[str, WebSocket] = {}
        self._pending_requests: Dict[str, asyncio.Future] = {}

    def is_online(self, target_id: str) -> bool:
        return target_id in self._active_sessions

    def get_online_targets(self) -> list[str]:
        return list(self._active_sessions.keys())

    async def register_session(self, target_id: str, websocket: WebSocket):
        self._active_sessions[target_id] = websocket
        logger.info(f"Target '{target_id}' connected via WebSocket.")

    async def unregister_session(self, target_id: str, db_session_maker):
        if target_id in self._active_sessions:
            del self._active_sessions[target_id]
            logger.info(f"Target '{target_id}' disconnected.")

        # Update target status to offline in database
        try:
            async with db_session_maker() as db:
                stmt = select(TargetModel).where(TargetModel.id == target_id)
                res = await db.execute(stmt)
                target = res.scalar_one_or_none()
                if target:
                    target.status = "offline"
                    await db.commit()
        except Exception as e:
            logger.error(f"Error marking target {target_id} offline in db: {e}")

    async def send_request(self, target_id: str, envelope: MessageEnvelope, timeout: float = 10.0) -> Dict[str, Any]:
        """
        Sends a request envelope to the target agent and awaits the correlated response.
        """
        websocket = self._active_sessions.get(target_id)
        if not websocket:
            raise ConnectionError(f"Target '{target_id}' is not connected.")

        correlation_id = envelope.correlationId or envelope.messageId
        future = asyncio.get_running_loop().create_future()
        self._pending_requests[correlation_id] = future

        try:
            await websocket.send_text(envelope.model_dump_json())
            response_payload = await asyncio.wait_for(future, timeout=timeout)
            return response_payload
        finally:
            self._pending_requests.pop(correlation_id, None)

    async def handle_message(self, websocket: WebSocket, raw_text: str, db_session_maker) -> Optional[MessageEnvelope]:
        """
        Processes an incoming envelope from an agent WebSocket.
        """
        data = json.loads(raw_text)
        env = MessageEnvelope(**data)
        target_id = env.targetId

        # 1. Hello handshake
        if env.messageType == "hello":
            agent_version = env.payload.get("agentVersion", "unknown")
            minecraft_version = env.payload.get("minecraftVersion", "unknown")
            paper_version = env.payload.get("paperVersion", "unknown")
            adapters = env.payload.get("adapters", [])

            async with db_session_maker() as db:
                stmt = select(TargetModel).where(TargetModel.id == target_id)
                res = await db.execute(stmt)
                target = res.scalar_one_or_none()
                if not target:
                    # Auto-register target if not existing in dev mode
                    target = TargetModel(
                        id=target_id,
                        name=f"Server {target_id}",
                        secret="dev-secret",
                        status="online",
                        environment_metadata={
                            "agentVersion": agent_version,
                            "minecraftVersion": minecraft_version,
                            "paperVersion": paper_version,
                            "adapters": adapters
                        },
                        last_seen_at=datetime.now(timezone.utc)
                    )
                    db.add(target)
                else:
                    target.status = "online"
                    target.environment_metadata = {
                        "agentVersion": agent_version,
                        "minecraftVersion": minecraft_version,
                        "paperVersion": paper_version,
                        "adapters": adapters
                    }
                    target.last_seen_at = datetime.now(timezone.utc)
                await db.commit()

            await self.register_session(target_id, websocket)

            accept_env = MessageEnvelope(
                messageType="response",
                correlationId=env.messageId,
                targetId=target_id,
                payload={
                    "status": "accepted",
                    "sessionId": f"sess-{target_id}",
                    "negotiatedProtocol": "1.0"
                }
            )
            await websocket.send_text(accept_env.model_dump_json())
            return accept_env

        # 2. Heartbeat
        elif env.messageType == "event" and env.payload.get("type") == "heartbeat":
            async with db_session_maker() as db:
                stmt = select(TargetModel).where(TargetModel.id == target_id)
                res = await db.execute(stmt)
                target = res.scalar_one_or_none()
                if target:
                    target.last_seen_at = datetime.now(timezone.utc)
                    target.status = "online"
                    await db.commit()

            ack_env = MessageEnvelope(
                messageType="response",
                correlationId=env.messageId,
                targetId=target_id,
                payload={"status": "pong", "timestamp": utcnow_iso()}
            )
            await websocket.send_text(ack_env.model_dump_json())
            return ack_env

        # 3. Response to correlated request
        elif env.messageType == "response":
            correlation_id = env.correlationId
            if correlation_id and correlation_id in self._pending_requests:
                future = self._pending_requests[correlation_id]
                if not future.done():
                    future.set_result(env.payload)
            return env

        return None


gateway_manager = AgentSessionManager()
