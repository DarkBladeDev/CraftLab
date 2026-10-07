import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from fastapi import FastAPI, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from craftlab_ctl.core.paths import CtlPaths, get_paths
from craftlab_ctl.core.models import OperationResult, CheckStatus, AuditEvent
from craftlab_ctl.auth.models import (
    Role,
    AuthContext,
    LoginRequest,
    LoginResponse,
    UserResponse,
)
from craftlab_ctl.auth.crypto import (
    verify_password,
    sign_session_token,
    get_or_create_auth_secret,
)
from craftlab_ctl.auth.db import (
    get_user_by_username,
    create_session,
    delete_session,
)
from craftlab_ctl.auth.rbac import resolve_auth_context
from craftlab_ctl.supervisor import ProcessSupervisor
from craftlab_ctl.supervisor.logs import LogRingBuffer, tail_file_to_buffer
from craftlab_ctl.server.metrics import collect_system_metrics
from craftlab_ctl.sdk import Context


def create_control_app(
    daemon_service: Any,
    paths: Optional[CtlPaths] = None,
    log_buffer: Optional[LogRingBuffer] = None,
    static_dir: Optional[Path] = None,
) -> FastAPI:
    ctl_paths = paths or daemon_service.paths
    ring_buf = log_buffer or LogRingBuffer(max_lines=1000)
    supervisor = ProcessSupervisor(paths=ctl_paths, service_name="backend")

    app = FastAPI(
        title="CraftLab Control Plane",
        version="1.0.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # State objects on app
    app.state.paths = ctl_paths
    app.state.daemon_service = daemon_service
    app.state.supervisor = supervisor
    app.state.log_buffer = ring_buf

    import contextlib

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI):
        stop_tail = asyncio.Event()
        log_file = ctl_paths.logs_dir / "backend.log"
        tail_task = asyncio.create_task(tail_file_to_buffer(log_file, ring_buf, stop_tail))
        try:
            yield
        finally:
            stop_tail.set()
            tail_task.cancel()

    app.router.lifespan_context = lifespan

    # --- Auth Helpers ---
    def extract_auth_context(request: Request) -> Optional[AuthContext]:
        bearer_token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header[7:].strip()

        cookie_token = request.cookies.get("craftlab_session")
        return resolve_auth_context(
            ctl_paths, cookie_token=cookie_token, bearer_token=bearer_token
        )

    def require_auth(request: Request) -> AuthContext:
        ctx = extract_auth_context(request)
        if not ctx:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
            )
        return ctx

    def require_roles(*allowed_roles: str) -> Callable[[AuthContext], AuthContext]:
        def role_checker(auth: AuthContext = Depends(require_auth)) -> AuthContext:
            if not auth.has_role(*allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Forbidden: requires role in {allowed_roles}",
                )
            return auth

        return role_checker

    # --- API Routes ---
    @app.post("/api/v1/auth/login", response_model=LoginResponse)
    async def login(req: LoginRequest, response: Response):
        user = get_user_by_username(ctl_paths.auth_db_path, req.username)
        if not user or not user.is_active or not verify_password(user.password_hash, req.password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid username or password",
            )

        # Create session
        session = create_session(ctl_paths.auth_db_path, user.id, ttl_days=7)
        secret = get_or_create_auth_secret(ctl_paths.state_dir)
        signed_cookie = sign_session_token(session.session_id, secret)

        response.set_cookie(
            key="craftlab_session",
            value=signed_cookie,
            httponly=True,
            samesite="lax",
            secure=False,  # Set to True when TLS is enforced
            max_age=7 * 86400,
            path="/",
        )

        return LoginResponse(
            status="ok",
            user_id=user.id,
            username=user.username,
            display_name=user.display_name,
            roles=user.roles,
        )

    @app.post("/api/v1/auth/logout")
    async def logout(request: Request, response: Response):
        cookie_token = request.cookies.get("craftlab_session")
        if cookie_token:
            secret = get_or_create_auth_secret(ctl_paths.state_dir)
            session_id = cookie_token.split(".")[0]
            try:
                delete_session(ctl_paths.auth_db_path, session_id)
            except Exception:
                pass
        response.delete_cookie("craftlab_session", path="/")
        return {"status": "ok", "message": "Logged out"}

    @app.get("/api/v1/auth/me")
    async def get_current_user(auth: AuthContext = Depends(require_auth)):
        return {
            "user_id": auth.user_id,
            "username": auth.username,
            "roles": auth.roles,
            "is_break_glass": auth.is_break_glass,
        }

    @app.get("/api/v1/status")
    async def get_status(auth: AuthContext = Depends(require_auth)):
        status_info = supervisor.get_status()
        return {
            "service": "backend",
            "supervisor": "craftctld",
            "is_running": supervisor.is_running(),
            **status_info,
        }

    @app.get("/api/v1/metrics")
    async def get_metrics(auth: AuthContext = Depends(require_auth)):
        return collect_system_metrics(ctl_paths, supervisor)

    @app.get("/api/v1/doctor")
    async def run_doctor(auth: AuthContext = Depends(require_auth)):
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}")
        checks = await daemon_service.registry.execute_checks(ctx)
        checks_data = [c.model_dump() for c in checks]
        has_fail = any(c["status"] == "FAIL" for c in checks_data)
        has_warn = any(c["status"] == "WARN" for c in checks_data)
        overall = "FAIL" if has_fail else ("WARN" if has_warn else "PASS")
        return {"overall": overall, "checks": checks_data}

    @app.post("/api/v1/lifecycle/{action}")
    async def execute_lifecycle(
        action: str,
        auth: AuthContext = Depends(require_roles(Role.ADMIN.value, Role.OPERATOR.value)),
    ):
        if action not in ["start", "stop", "restart", "status"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid lifecycle action: {action}",
            )

        cmd_def = daemon_service.registry.get_command(action)
        if not cmd_def:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Command '{action}' not registered",
            )

        steps = []
        async def step_cb(step_evt):
            steps.append(step_evt.model_dump())

        ctx = Context(
            paths=ctl_paths,
            caller_id=f"web:{auth.username}",
            step_callback=step_cb,
        )

        try:
            if cmd_def.mutates:
                await daemon_service.lock.acquire(action)
            try:
                result = await cmd_def.func(ctx)
                if not isinstance(result, OperationResult):
                    result = OperationResult.ok(data=result)
                # Audit log
                outcome = "success" if result.success else "failed"
                daemon_service.audit.log(
                    AuditEvent(
                        caller_id=ctx.caller_id,
                        command=action,
                        parameters={},
                        outcome=outcome,
                        error=result.error,
                    )
                )
                return {
                    "success": result.success,
                    "message": result.message,
                    "data": result.data,
                    "steps": steps,
                }
            finally:
                if cmd_def.mutates:
                    daemon_service.lock.release()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(e),
            )

    # --- WebSocket Routes ---
    @app.websocket("/api/v1/ws/logs")
    async def ws_logs(websocket: WebSocket):
        # Authenticate WS
        cookie_val = websocket.cookies.get("craftlab_session")
        token_val = websocket.query_params.get("token")
        auth = resolve_auth_context(
            ctl_paths, cookie_token=cookie_val, bearer_token=token_val
        )
        if not auth and token_val:
            auth = resolve_auth_context(ctl_paths, cookie_token=token_val)
        if not auth:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

        await websocket.accept()

        # Stream existing buffer
        recent = ring_buf.get_recent(50)
        for line in recent:
            await websocket.send_text(line)

        # Stream live lines
        try:
            async for line in ring_buf.subscribe():
                await websocket.send_text(line)
        except WebSocketDisconnect:
            pass

    # --- Static SPA Hosting ---
    resolved_static = static_dir or (ctl_paths.home / "CraftLab-ctl" / "web" / "dist")
    if resolved_static.exists() and (resolved_static / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=str(resolved_static / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            target = resolved_static / full_path
            if target.exists() and target.is_file():
                return FileResponse(target)
            return FileResponse(resolved_static / "index.html")

    return app
