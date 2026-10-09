import os
import time
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.core.database import init_db, AsyncSessionLocal, engine
from app.api.items import router as items_router, revisions_router
from app.api.blocks import router as blocks_router
from app.api.targets import router as targets_router
from app.api.deployments import router as deployments_router
from app.api.catalogs import router as catalogs_router
from app.api.packs import router as packs_router, public_router as public_packs_router
from app.api.auth import router as auth_router
from app.core.auth import require_roles
from app.gateway.manager import gateway_manager
from craftlab_ctl.auth import Role

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp")

start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing database...")
    await init_db()
    yield
    logger.info("Shutting down CraftLab backend...")
    # Clean up active gateway connections
    await gateway_manager.shutdown(AsyncSessionLocal)
    # Dispose database connection pool
    await engine.dispose()
    logger.info("Graceful shutdown complete.")


app = FastAPI(title="Minecraft Content Platform", version="0.5.2", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.server.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
async def health_check():
    """
    Unauthenticated liveness check returning 200 OK and basic runtime info.
    """
    return {
        "status": "pass",
        "service": "craftlab-backend",
        "uptime_seconds": round(time.time() - start_time, 2),
        "pid": os.getpid(),
    }


@app.get("/ready", tags=["system"])
async def readiness_check():
    """
    Unauthenticated readiness check verifying database and storage connectivity.
    """
    checks = {}
    is_ready = True

    # 1. Database connectivity
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"
        is_ready = False

    # 2. Storage directories accessibility
    try:
        packs_dir = settings.paths.packs_dir
        packs_dir.mkdir(parents=True, exist_ok=True)
        test_file = packs_dir / ".ready_check"
        test_file.touch()
        test_file.unlink()
        checks["storage"] = "ok"
    except Exception as e:
        checks["storage"] = f"error: {str(e)}"
        is_ready = False

    if is_ready:
        return {"status": "ready", "checks": checks}
    return JSONResponse(status_code=503, content={"status": "degraded", "checks": checks})


app.include_router(auth_router)

content_auth = [Depends(require_roles(Role.CREATOR.value, Role.ADMIN.value))]
app.include_router(items_router, dependencies=content_auth)
app.include_router(blocks_router, dependencies=content_auth)
app.include_router(revisions_router, dependencies=content_auth)
app.include_router(targets_router, dependencies=content_auth)
app.include_router(deployments_router, dependencies=content_auth)
app.include_router(catalogs_router, dependencies=content_auth)
app.include_router(packs_router, dependencies=content_auth)
app.include_router(public_packs_router)


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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.server.host, port=settings.server.port, reload=True)

