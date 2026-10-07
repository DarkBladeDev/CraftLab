from typing import Optional, Callable
from fastapi import Request, HTTPException, Depends, status

from app.core.config import settings
from craftlab_ctl.core.paths import CtlPaths, get_paths
from craftlab_ctl.auth import Role, AuthContext, resolve_auth_context


def get_ctl_paths() -> CtlPaths:
    return get_paths(settings.paths.home)


def get_current_auth(request: Request) -> Optional[AuthContext]:
    if not settings.server.auth_enabled:
        return AuthContext(
            user_id="dev-bypass",
            username="dev",
            roles=[Role.ADMIN.value, Role.CREATOR.value],
            is_break_glass=False,
        )

    bearer_token = None
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:].strip()

    cookie_token = request.cookies.get("craftlab_session")
    paths = get_ctl_paths()
    return resolve_auth_context(
        paths, cookie_token=cookie_token, bearer_token=bearer_token
    )


def require_auth(request: Request) -> AuthContext:
    auth = get_current_auth(request)
    if not auth:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
        )
    return auth


def require_roles(*allowed_roles: str) -> Callable[[AuthContext], AuthContext]:
    def dependency(auth: AuthContext = Depends(require_auth)) -> AuthContext:
        if not auth.has_role(*allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: requires role in {allowed_roles}",
            )
        return auth

    return dependency
