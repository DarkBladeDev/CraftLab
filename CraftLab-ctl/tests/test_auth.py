import pytest
from pathlib import Path
from craftlab_ctl.core.paths import CtlPaths
from craftlab_ctl.auth import (
    Role,
    init_auth_db,
    create_user,
    get_user_by_username,
    get_user_by_id,
    list_users,
    create_session,
    get_session,
    delete_session,
    create_api_token,
    get_user_by_api_token,
    hash_password,
    verify_password,
    sign_session_token,
    unsign_session_token,
    resolve_auth_context,
    verify_break_glass,
)


@pytest.fixture
def temp_ctl_paths(tmp_path: Path) -> CtlPaths:
    paths = CtlPaths(
        home=tmp_path,
        config_dir=tmp_path / "config",
        data_dir=tmp_path / "data",
        state_dir=tmp_path / "state",
        run_dir=tmp_path / "run",
        logs_dir=tmp_path / "logs",
        packs_dir=tmp_path / "data" / "packs",
    )
    paths.ensure_directories()
    return paths


def test_auth_db_initialization_and_crud(temp_ctl_paths: CtlPaths):
    db_path = temp_ctl_paths.auth_db_path
    init_auth_db(db_path)
    assert db_path.exists()

    # Create user
    user = create_user(
        db_path,
        username="admin",
        password="SuperSecretPassword123!",
        display_name="Administrator",
        roles=[Role.ADMIN.value],
    )
    assert user.id is not None
    assert user.username == "admin"
    assert user.roles == ["admin"]

    # Retrieve by username and by id
    fetched = get_user_by_username(db_path, "admin")
    assert fetched is not None
    assert fetched.id == user.id

    fetched_id = get_user_by_id(db_path, user.id)
    assert fetched_id is not None
    assert fetched_id.username == "admin"

    # List users
    all_users = list_users(db_path)
    assert len(all_users) == 1
    assert all_users[0].username == "admin"


def test_argon2id_hashing_and_verification():
    password = "MySecureTeamPassword#2026"
    pwd_hash = hash_password(password)

    assert pwd_hash.startswith("$argon2id$")
    assert verify_password(pwd_hash, password) is True
    assert verify_password(pwd_hash, "WrongPassword") is False
    assert verify_password("invalid_hash", password) is False


def test_session_cookie_signing_and_validation(temp_ctl_paths: CtlPaths):
    db_path = temp_ctl_paths.auth_db_path
    secret = b"test_secret_key_32_bytes_long_ok!"

    user = create_user(
        db_path,
        username="carlos",
        password="Password123!",
        roles=[Role.OPERATOR.value],
    )

    session = create_session(db_path, user.id, ttl_days=2)
    signed_cookie = sign_session_token(session.session_id, secret)

    # Valid unsign
    raw_session_id = unsign_session_token(signed_cookie, secret)
    assert raw_session_id == session.session_id

    # Tampered signature
    tampered_cookie = signed_cookie[:-4] + "xxxx"
    assert unsign_session_token(tampered_cookie, secret) is None

    # Retrieve active session
    loaded_session = get_session(db_path, raw_session_id)
    assert loaded_session is not None
    assert loaded_session.username == "carlos"
    assert Role.OPERATOR.value in loaded_session.roles

    # Delete session
    assert delete_session(db_path, session.session_id) is True
    assert get_session(db_path, session.session_id) is None


def test_api_token_creation_and_resolution(temp_ctl_paths: CtlPaths):
    db_path = temp_ctl_paths.auth_db_path
    user = create_user(
        db_path,
        username="bot_ci",
        password="BotPassword123!",
        roles=[Role.OPERATOR.value],
    )

    raw_token = create_api_token(db_path, user.id, name="github-actions")
    assert raw_token.startswith("ctl_")

    token_user = get_user_by_api_token(db_path, raw_token)
    assert token_user is not None
    assert token_user.username == "bot_ci"

    # Context resolution
    ctx = resolve_auth_context(temp_ctl_paths, bearer_token=raw_token)
    assert ctx is not None
    assert ctx.username == "bot_ci"
    assert ctx.has_role(Role.OPERATOR.value) is True
    assert ctx.has_role(Role.ADMIN.value) is False


def test_rbac_and_break_glass(temp_ctl_paths: CtlPaths, monkeypatch):
    # Test Break-Glass
    monkeypatch.setenv("CRAFTLAB_ROOT_KEY", "emergency-root-secret-key-999")
    bg_ctx = verify_break_glass("emergency-root-secret-key-999", temp_ctl_paths)
    assert bg_ctx is not None
    assert bg_ctx.is_break_glass is True
    assert bg_ctx.has_role(Role.ADMIN.value) is True
    assert bg_ctx.has_role(Role.OPERATOR.value) is True

    # Bad root key
    assert verify_break_glass("wrong-root-secret", temp_ctl_paths) is None

    # Context resolution with break glass via bearer token
    resolved_bg = resolve_auth_context(
        temp_ctl_paths, bearer_token="emergency-root-secret-key-999"
    )
    assert resolved_bg is not None
    assert resolved_bg.is_break_glass is True
