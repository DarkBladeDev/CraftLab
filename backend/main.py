from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import logging
from app.core.database import init_db, AsyncSessionLocal
from app.api.items import router as items_router, revisions_router
from app.api.targets import router as targets_router
from app.api.deployments import router as deployments_router
from app.api.catalogs import router as catalogs_router
from app.gateway.manager import gateway_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    yield
    logger.info("Shutting down MCP...")


app = FastAPI(title="Minecraft Content Platform", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items_router)
app.include_router(revisions_router)
app.include_router(targets_router)
app.include_router(deployments_router)
app.include_router(catalogs_router)


@app.websocket("/ws/agent")
async def websocket_agent_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_target_id = None
    try:
        while True:
            text = await websocket.receive_text()
            response = await gateway_manager.handle_message(websocket, text, AsyncSessionLocal)
            if response and not connected_target_id:
                connected_target_id = response.targetId
    except WebSocketDisconnect:
        logger.info(f"Agent websocket disconnected: {connected_target_id}")
    except Exception as e:
        logger.error(f"Error in websocket loop: {e}")
    finally:
        if connected_target_id:
            await gateway_manager.unregister_session(connected_target_id, AsyncSessionLocal)
