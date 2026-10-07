from fastapi import APIRouter, HTTPException, Depends, Request, Response, status
from app.core.config import settings
from app.core.auth import get_ctl_paths, require_auth
from craftlab_ctl.auth.models import (
    LoginRequest,
    LoginResponse,
    AuthContext,
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

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
async def login(req: LoginRequest, response: Response):
    paths = get_ctl_paths()
    user = get_user_by_username(paths.auth_db_path, req.username)
    if not user or not user.is_active or not verify_password(user.password_hash, req.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    session = create_session(paths.auth_db_path, user.id, ttl_days=7)
    secret = get_or_create_auth_secret(paths.state_dir)
    signed_cookie = sign_session_token(session.session_id, secret)

    response.set_cookie(
        key="craftlab_session",
        value=signed_cookie,
        httponly=True,
        samesite="lax",
        secure=False,
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


@router.post("/logout")
async def logout(request: Request, response: Response):
    paths = get_ctl_paths()
    cookie_token = request.cookies.get("craftlab_session")
    if cookie_token:
        session_id = cookie_token.split(".")[0]
        try:
            delete_session(paths.auth_db_path, session_id)
        except Exception:
            pass
    response.delete_cookie("craftlab_session", path="/")
    return {"status": "ok", "message": "Logged out"}


@router.get("/me")
async def get_me(auth: AuthContext = Depends(require_auth)):
    return {
        "user_id": auth.user_id,
        "username": auth.username,
        "roles": auth.roles,
        "is_break_glass": auth.is_break_glass,
    }
