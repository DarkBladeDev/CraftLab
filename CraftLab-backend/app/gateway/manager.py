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

    async def shutdown(self, db_session_maker):
        """
        Gracefully closes all active sessions and marks targets offline.
        """
        target_ids = list(self._active_sessions.keys())
        for tid in target_ids:
            ws = self._active_sessions.get(tid)
            if ws:
                try:
                    await ws.close(code=1001, reason="Server shutting down")
                except Exception:
                    pass
            await self.unregister_session(tid, db_session_maker)

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

    async def send_to_target(self, target_id: str, envelope: MessageEnvelope, timeout: float = 3.0) -> bool:
        """Sends an event or message to the target WebSocket if online."""
        websocket = self._active_sessions.get(target_id)
        if websocket:
            try:
                await asyncio.wait_for(websocket.send_text(envelope.model_dump_json()), timeout=timeout)
                return True
            except Exception as e:
                logger.warning(f"Failed to send envelope to target '{target_id}': {e}")
                return False
        return False

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
            detected_plugins = env.payload.get("detectedPlugins", [])
            initial_manifest = env.payload.get("catalogManifest")

            async with db_session_maker() as db:
                stmt = select(TargetModel).where(TargetModel.id == target_id)
                res = await db.execute(stmt)
                target = res.scalar_one_or_none()
                env_meta = {
                    "agentVersion": agent_version,
                    "minecraftVersion": minecraft_version,
                    "paperVersion": paper_version,
                    "adapters": adapters,
                    "detectedPlugins": detected_plugins
                }
                if not target:
                    # Auto-register target if not existing in dev mode
                    target = TargetModel(
                        id=target_id,
                        name=f"Server {target_id}",
                        secret="dev-secret",
                        status="online",
                        environment_metadata=env_meta,
                        last_seen_at=datetime.now(timezone.utc)
                    )
                    db.add(target)
                else:
                    target.status = "online"
                    target.environment_metadata = env_meta
                    target.last_seen_at = datetime.now(timezone.utc)
                await db.commit()

                # Process initial manifest if provided during handshake
                if initial_manifest:
                    from app.domain.catalogs import upsert_discovered_items
                    source = initial_manifest.get("source", "oraxen")
                    items = initial_manifest.get("items", [])
                    if items:
                        await upsert_discovered_items(db, target_id, source, items)

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

        # 2b. Catalog Manifest Event
        elif env.messageType == "event" and env.payload.get("type") == "catalog:manifest":
            from app.domain.catalogs import upsert_discovered_items
            source = env.payload.get("source", "oraxen")
            items = env.payload.get("items", [])
            async with db_session_maker() as db:
                await upsert_discovered_items(db, target_id, source, items)
            logger.info(f"Target '{target_id}' streamed catalog:manifest with {len(items)} {source} items.")
            return env

        # 2c. Resource Pack Source Sync Event
        elif env.messageType == "event" and env.payload.get("type") == "resource_pack:source_sync":
            import base64
            from pathlib import Path
            from app.domain.pack_sources import PackRepository
            plugin = env.payload.get("plugin", "oraxen")
            sha1 = env.payload.get("sha1")
            zip_b64 = env.payload.get("zipBase64")
            from app.core.config import settings
            source_id = f"src-agent-{target_id}-{plugin}"
            storage_path = str(settings.paths.packs_dir / "sources" / source_id / "contents")

            if zip_b64:
                try:
                    data = base64.b64decode(zip_b64)
                    dest_dir = Path(storage_path)
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    zip_path = dest_dir.parent / "agent_synced.zip"
                    zip_path.write_bytes(data)
                    import zipfile
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        zf.extractall(dest_dir)
                except Exception as e:
                    logger.error(f"Error extracting synced pack from target {target_id}: {e}")

            async with db_session_maker() as db:
                await PackRepository.create_or_update_source(
                    db=db,
                    source_id=source_id,
                    target_id=target_id,
                    name=f"Agent {plugin.capitalize()} Pack ({target_id})",
                    source_type="agent",
                    plugin=plugin,
                    layer_priority=20,
                    storage_path=storage_path,
                    sha1_hash=sha1,
                    meta_info={"synced_via": "ws", "plugin": plugin}
                )
            logger.info(f"Target '{target_id}' synced resource pack source for plugin '{plugin}'.")
            return env

        # 3. Response to correlated request
        elif env.messageType == "response":
            correlation_id = env.correlationId
            if correlation_id and correlation_id in self._pending_requests:
                future = self._pending_requests[correlation_id]
                if not future.done():
                    future.set_result(env.payload)
            return env

        return None

    async def refresh_catalog(self, target_id: str, db_session_maker, timeout: float = 10.0) -> Dict[str, Any]:
        """Sends a catalog refresh request to the target agent and stores received manifest items."""
        req_env = MessageEnvelope(
            messageType="request",
            targetId=target_id,
            payload={"action": "catalog:refresh"}
        )
        res_payload = await self.send_request(target_id, req_env, timeout=timeout)
        
        # If the agent responded with manifest items, upsert them
        source = res_payload.get("source", "oraxen")
        items = res_payload.get("items", [])
        if items:
            from app.domain.catalogs import upsert_discovered_items
            async with db_session_maker() as db:
                await upsert_discovered_items(db, target_id, source, items)

        return res_payload


gateway_manager = AgentSessionManager()
