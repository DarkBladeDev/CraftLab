import os
import hmac
from pathlib import Path
from typing import Optional, List

from craftlab_ctl.core.paths import CtlPaths, get_paths
from craftlab_ctl.auth.models import AuthContext, Role
from craftlab_ctl.auth.crypto import unsign_session_token, get_or_create_auth_secret
from craftlab_ctl.auth.db import get_session, get_user_by_api_token


def get_break_glass_key(paths: Optional[CtlPaths] = None) -> Optional[str]:
    """Retrieves break glass emergency root key from env or config/craftctl.toml."""
    env_key = os.getenv("CRAFTLAB_ROOT_KEY")
    if env_key:
        return env_key.strip()

    # Check config/craftctl.toml or config/craftlab.toml if exists
    resolved_paths = paths or get_paths()
    config_file = resolved_paths.config_dir / "craftctl.toml"
    if config_file.exists():
        try:
            import tomllib
            data = tomllib.loads(config_file.read_text(encoding="utf-8"))
            return data.get("root_key")
        except Exception:
            pass

    return None


def verify_break_glass(token: str, paths: Optional[CtlPaths] = None) -> Optional[AuthContext]:
    """Checks if the given token matches the break glass emergency root key."""
    break_key = get_break_glass_key(paths)
    if not break_key:
        return None
    if hmac.compare_digest(token.strip(), break_key):
        return AuthContext(
            user_id="root",
            username="root",
            roles=[Role.ADMIN.value],
            is_break_glass=True,
        )
    return None


def resolve_auth_context(
    paths: CtlPaths,
    cookie_token: Optional[str] = None,
    bearer_token: Optional[str] = None,
) -> Optional[AuthContext]:
    """Resolves an AuthContext from session cookie, bearer token, or break glass key."""
    # 1. Break-glass check
    if bearer_token:
        bg_ctx = verify_break_glass(bearer_token, paths)
        if bg_ctx:
            return bg_ctx

    # 2. Bearer API token check
    if bearer_token:
        user = get_user_by_api_token(paths.auth_db_path, bearer_token)
        if user and user.is_active:
            return AuthContext(
                user_id=user.id,
                username=user.username,
                roles=user.roles,
                is_break_glass=False,
            )

    # 3. Session cookie check
    if cookie_token:
        secret = get_or_create_auth_secret(paths.state_dir)
        session_id = unsign_session_token(cookie_token, secret)
        if session_id:
            session = get_session(paths.auth_db_path, session_id)
            if session:
                return AuthContext(
                    user_id=session.user_id,
                    username=session.username,
                    roles=session.roles,
                    is_break_glass=False,
                )

    return None
