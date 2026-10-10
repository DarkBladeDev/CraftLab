import os
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable
from pydantic import BaseModel
from fastapi import FastAPI, Depends, HTTPException, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles


class PrepareRequest(BaseModel):
    version: str
    github_repo: Optional[str] = "DarkBladeDev/CraftLab"
    local_file: Optional[str] = None


class ApplyRequest(BaseModel):
    version: str
    timeout: int = 15
    host: str = "127.0.0.1"
    port: int = 8000


class RollbackRequest(BaseModel):
    target_version: Optional[str] = None
    timeout: int = 15
    host: str = "127.0.0.1"
    port: int = 8000


class MaintenanceRequest(BaseModel):
    enable: Optional[bool] = None
    message: str = ""


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

    cors_env = os.getenv("CRAFTLAB_CTL_CORS_ORIGINS") or os.getenv("CRAFTLAB_CORS_ORIGINS")
    if cors_env:
        origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    else:
        origins = [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8443",
            "http://127.0.0.1:8443",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ]

    # Strictly disallow wildcard origins when credentials are enabled
    if "*" in origins:
        origins = [o for o in origins if o != "*"]
        if not origins:
            origins = ["http://127.0.0.1:8443"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
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
    async def login(req: LoginRequest, response: Response, request: Request):
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

        env_mode = (os.getenv("CRAFTLAB_ENV") or os.getenv("ENV") or "development").strip().lower()
        is_secure = (env_mode in ("production", "prod")) or (request.url.scheme == "https")

        response.set_cookie(
            key="craftlab_session",
            value=signed_cookie,
            httponly=True,
            samesite="lax",
            secure=is_secure,
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

    # --- Update & Release Routes ---
    @app.get("/api/v1/update/releases")
    async def get_releases(auth: AuthContext = Depends(require_auth)):
        cmd_def = daemon_service.registry.get_command("update.releases") or daemon_service.registry.get_command("releases")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Releases command not available")
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}")
        res = await cmd_def.func(ctx)
        return res.data if hasattr(res, "data") else res

    @app.get("/api/v1/update/check")
    async def check_updates(
        repo: Optional[str] = None,
        auth: AuthContext = Depends(require_auth),
    ):
        cmd_def = daemon_service.registry.get_command("update.check") or daemon_service.registry.get_command("check")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Update check command not available")
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}")
        params = {"github_repo": repo} if repo else {}
        res = await cmd_def.func(ctx, **params)
        return res.data if hasattr(res, "data") else res

    @app.post("/api/v1/update/prepare")
    async def prepare_update(
        req: PrepareRequest,
        auth: AuthContext = Depends(require_roles(Role.ADMIN.value, Role.OPERATOR.value)),
    ):
        cmd_def = daemon_service.registry.get_command("update.prepare") or daemon_service.registry.get_command("prepare")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Update prepare command not available")
        steps = []
        async def step_cb(step_evt):
            steps.append(step_evt.model_dump())
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}", step_callback=step_cb)
        await daemon_service.lock.acquire("update.prepare")
        try:
            params = {"version": req.version}
            if req.github_repo:
                params["github_repo"] = req.github_repo
            if req.local_file:
                params["local_file"] = req.local_file
            res = await cmd_def.func(ctx, **params)
            outcome = "success" if res.success else "failed"
            daemon_service.audit.log(
                AuditEvent(
                    caller_id=ctx.caller_id,
                    command="update.prepare",
                    parameters={"version": req.version},
                    outcome=outcome,
                    error=res.error,
                )
            )
            return {
                "success": res.success,
                "message": res.message,
                "error": res.error,
                "data": res.data,
                "steps": steps,
            }
        finally:
            daemon_service.lock.release()

    @app.post("/api/v1/update/apply")
    async def apply_update(
        req: ApplyRequest,
        auth: AuthContext = Depends(require_roles(Role.ADMIN.value, Role.OPERATOR.value)),
    ):
        cmd_def = daemon_service.registry.get_command("update.apply") or daemon_service.registry.get_command("apply")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Update apply command not available")
        steps = []
        async def step_cb(step_evt):
            steps.append(step_evt.model_dump())
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}", step_callback=step_cb)
        await daemon_service.lock.acquire("update.apply")
        try:
            params = {
                "version": req.version,
                "timeout": req.timeout,
                "host": req.host,
                "port": req.port,
            }
            res = await cmd_def.func(ctx, **params)
            outcome = "success" if res.success else "failed"
            daemon_service.audit.log(
                AuditEvent(
                    caller_id=ctx.caller_id,
                    command="update.apply",
                    parameters={"version": req.version},
                    outcome=outcome,
                    error=res.error,
                )
            )
            return {
                "success": res.success,
                "message": res.message,
                "error": res.error,
                "data": res.data,
                "steps": steps,
            }
        finally:
            daemon_service.lock.release()

    @app.post("/api/v1/update/rollback")
    async def rollback_update(
        req: RollbackRequest,
        auth: AuthContext = Depends(require_roles(Role.ADMIN.value, Role.OPERATOR.value)),
    ):
        cmd_def = daemon_service.registry.get_command("update.rollback") or daemon_service.registry.get_command("rollback")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Rollback command not available")
        steps = []
        async def step_cb(step_evt):
            steps.append(step_evt.model_dump())
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}", step_callback=step_cb)
        await daemon_service.lock.acquire("update.rollback")
        try:
            params = {
                "target_version": req.target_version,
                "timeout": req.timeout,
                "host": req.host,
                "port": req.port,
            }
            res = await cmd_def.func(ctx, **params)
            outcome = "success" if res.success else "failed"
            daemon_service.audit.log(
                AuditEvent(
                    caller_id=ctx.caller_id,
                    command="update.rollback",
                    parameters={"target_version": req.target_version},
                    outcome=outcome,
                    error=res.error,
                )
            )
            return {
                "success": res.success,
                "message": res.message,
                "error": res.error,
                "data": res.data,
                "steps": steps,
            }
        finally:
            daemon_service.lock.release()

    @app.get("/api/v1/update/maintenance")
    async def get_maintenance(auth: AuthContext = Depends(require_auth)):
        cmd_def = daemon_service.registry.get_command("update.maintenance") or daemon_service.registry.get_command("maintenance")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Maintenance command not available")
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}")
        res = await cmd_def.func(ctx)
        return res.data if hasattr(res, "data") else res

    @app.post("/api/v1/update/maintenance")
    async def set_maintenance_mode(
        req: MaintenanceRequest,
        auth: AuthContext = Depends(require_roles(Role.ADMIN.value, Role.OPERATOR.value)),
    ):
        cmd_def = daemon_service.registry.get_command("update.maintenance") or daemon_service.registry.get_command("maintenance")
        if not cmd_def:
            raise HTTPException(status_code=500, detail="Maintenance command not available")
        ctx = Context(paths=ctl_paths, caller_id=f"web:{auth.username}")
        await daemon_service.lock.acquire("update.maintenance")
        try:
            res = await cmd_def.func(ctx, enable=req.enable, message=req.message)
            outcome = "success" if res.success else "failed"
            daemon_service.audit.log(
                AuditEvent(
                    caller_id=ctx.caller_id,
                    command="update.maintenance",
                    parameters={"enable": req.enable, "message": req.message},
                    outcome=outcome,
                    error=res.error,
                )
            )
            return {
                "success": res.success,
                "message": res.message,
                "data": res.data,
            }
        finally:
            daemon_service.lock.release()

    # --- WebSocket Routes ---
    @app.websocket("/api/v1/ws/logs")
    async def ws_logs(websocket: WebSocket):
        # Authenticate WS strictly via session cookie or Authorization header (no query param token)
        cookie_val = websocket.cookies.get("craftlab_session")
        auth_header = websocket.headers.get("authorization")
        bearer_token = None
        if auth_header and auth_header.startswith("Bearer "):
            bearer_token = auth_header[7:].strip()

        auth = resolve_auth_context(
            ctl_paths, cookie_token=cookie_val, bearer_token=bearer_token
        )
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
    resolved_static = static_dir
    if not resolved_static and ctl_paths.active_release_dir:
        candidate_release_web = ctl_paths.active_release_dir / "ctl_web_dist"
        if candidate_release_web.exists() and (candidate_release_web / "index.html").exists():
            resolved_static = candidate_release_web
    if not resolved_static:
        resolved_static = ctl_paths.home / "CraftLab-ctl" / "web" / "dist"
    if resolved_static.exists() and (resolved_static / "index.html").exists():
        app.mount("/assets", StaticFiles(directory=str(resolved_static / "assets")), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            target = resolved_static / full_path
            if target.exists() and target.is_file():
                return FileResponse(target)
            return FileResponse(resolved_static / "index.html")

    return app
