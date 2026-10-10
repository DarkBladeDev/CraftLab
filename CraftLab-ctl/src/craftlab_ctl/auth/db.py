import json
import sqlite3
import uuid
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

from craftlab_ctl.auth.models import User, Session, Role
from craftlab_ctl.auth.crypto import hash_password


def get_db_connection(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=10.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def init_auth_db(db_path: Path) -> None:
    """Initializes the authentication database schema."""
    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                display_name TEXT NOT NULL,
                roles TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS api_tokens (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                token_hash TEXT NOT NULL,
                name TEXT NOT NULL,
                expires_at TEXT,
                created_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
        conn.commit()


def create_user(
    db_path: Path,
    username: str,
    password: str,
    display_name: Optional[str] = None,
    roles: Optional[List[str]] = None,
) -> User:
    init_auth_db(db_path)
    user_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc).isoformat()
    roles_list = roles or [Role.VIEWER.value]
    pwd_hash = hash_password(password)
    disp_name = display_name or username

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO users (id, username, password_hash, display_name, roles, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                display_name = excluded.display_name,
                roles = excluded.roles,
                updated_at = excluded.updated_at
            """,
            (user_id, username, pwd_hash, disp_name, json.dumps(roles_list), 1, now, now),
        )
        conn.commit()

    return User(
        id=user_id,
        username=username,
        password_hash=pwd_hash,
        display_name=disp_name,
        roles=roles_list,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


def get_user_by_username(db_path: Path, username: str) -> Optional[User]:
    init_auth_db(db_path)
    with get_db_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            roles=json.loads(row["roles"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def get_user_by_id(db_path: Path, user_id: str) -> Optional[User]:
    init_auth_db(db_path)
    with get_db_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            roles=json.loads(row["roles"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )


def list_users(db_path: Path) -> List[User]:
    init_auth_db(db_path)
    with get_db_connection(db_path) as conn:
        cur = conn.execute("SELECT * FROM users ORDER BY created_at ASC")
        users = []
        for row in cur.fetchall():
            users.append(
                User(
                    id=row["id"],
                    username=row["username"],
                    password_hash=row["password_hash"],
                    display_name=row["display_name"],
                    roles=json.loads(row["roles"]),
                    is_active=bool(row["is_active"]),
                    created_at=row["created_at"],
                    updated_at=row["updated_at"],
                )
            )
        return users


def create_session(db_path: Path, user_id: str, ttl_days: int = 7) -> Session:
    init_auth_db(db_path)
    user = get_user_by_id(db_path, user_id)
    if not user:
        raise ValueError(f"User {user_id} not found")

    session_id = uuid.uuid4().hex
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=ttl_days)
    now_iso = now.isoformat()
    expires_iso = expires.isoformat()

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO sessions (session_id, user_id, expires_at, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (session_id, user_id, expires_iso, now_iso),
        )
        conn.commit()

    return Session(
        session_id=session_id,
        user_id=user.id,
        username=user.username,
        roles=user.roles,
        created_at=now_iso,
        expires_at=expires_iso,
    )


def get_session(db_path: Path, session_id: str) -> Optional[Session]:
    init_auth_db(db_path)
    now_iso = datetime.now(timezone.utc).isoformat()
    with get_db_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT s.session_id, s.user_id, s.expires_at, s.created_at,
                   u.username, u.roles, u.is_active
            FROM sessions s
            JOIN users u ON s.user_id = u.id
            WHERE s.session_id = ? AND s.expires_at > ? AND u.is_active = 1
            """,
            (session_id, now_iso),
        )
        row = cur.fetchone()
        if not row:
            return None
        return Session(
            session_id=row["session_id"],
            user_id=row["user_id"],
            username=row["username"],
            roles=json.loads(row["roles"]),
            created_at=row["created_at"],
            expires_at=row["expires_at"],
        )


def delete_session(db_path: Path, session_id: str) -> bool:
    init_auth_db(db_path)
    with get_db_connection(db_path) as conn:
        cur = conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
        conn.commit()
        return cur.rowcount > 0


def revoke_user_sessions(db_path: Path, username_or_id: str) -> int:
    """Revokes all active sessions for a specific user by username or user ID."""
    init_auth_db(db_path)
    with get_db_connection(db_path) as conn:
        cur = conn.execute(
            """
            DELETE FROM sessions
            WHERE user_id = ? OR user_id IN (SELECT id FROM users WHERE username = ?)
            """,
            (username_or_id, username_or_id),
        )
        conn.commit()
        return cur.rowcount


def revoke_all_sessions_except(db_path: Path, except_session_id: Optional[str] = None) -> int:
    """Revokes all active sessions across the system, optionally preserving the caller's session."""
    init_auth_db(db_path)
    with get_db_connection(db_path) as conn:
        if except_session_id:
            cur = conn.execute("DELETE FROM sessions WHERE session_id != ?", (except_session_id,))
        else:
            cur = conn.execute("DELETE FROM sessions")
        conn.commit()
        return cur.rowcount


def create_api_token(
    db_path: Path, user_id: str, name: str, token_str: Optional[str] = None
) -> str:
    init_auth_db(db_path)
    token_val = token_str or f"ctl_{uuid.uuid4().hex}"
    token_hash = hashlib.sha256(token_val.encode("utf-8")).hexdigest()
    token_id = uuid.uuid4().hex
    now_iso = datetime.now(timezone.utc).isoformat()

    with get_db_connection(db_path) as conn:
        conn.execute(
            """
            INSERT INTO api_tokens (id, user_id, token_hash, name, expires_at, created_at)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (token_id, user_id, token_hash, name, now_iso),
        )
        conn.commit()

    return token_val


def get_user_by_api_token(db_path: Path, token_val: str) -> Optional[User]:
    init_auth_db(db_path)
    token_hash = hashlib.sha256(token_val.encode("utf-8")).hexdigest()
    with get_db_connection(db_path) as conn:
        cur = conn.execute(
            """
            SELECT u.*
            FROM api_tokens t
            JOIN users u ON t.user_id = u.id
            WHERE t.token_hash = ? AND u.is_active = 1
            """,
            (token_hash,),
        )
        row = cur.fetchone()
        if not row:
            return None
        return User(
            id=row["id"],
            username=row["username"],
            password_hash=row["password_hash"],
            display_name=row["display_name"],
            roles=json.loads(row["roles"]),
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
