import os
import hmac
import base64
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError, InvalidHashError

_hasher = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
    hash_len=32,
    salt_len=16,
)


def hash_password(password: str) -> str:
    """Hashes a password with Argon2id and per-user salt."""
    return _hasher.hash(password)


def verify_password(hash_value: str, password: str) -> bool:
    """Verifies a password against an Argon2id hash using constant-time evaluation."""
    try:
        return _hasher.verify(hash_value, password)
    except (VerifyMismatchError, VerificationError, InvalidHashError):
        return False


def get_or_create_auth_secret(state_dir: Optional[Path] = None) -> bytes:
    """Gets the auth secret from env CRAFTLAB_AUTH_SECRET or persists a random secret to state/auth.key."""
    env_secret = os.getenv("CRAFTLAB_AUTH_SECRET")
    if env_secret:
        return env_secret.encode("utf-8")

    if state_dir:
        key_file = state_dir / "auth.key"
        if key_file.exists():
            return key_file.read_bytes()
        state_dir.mkdir(parents=True, exist_ok=True)
        new_secret = os.urandom(32)
        key_file.write_bytes(new_secret)
        return new_secret

    return b"craftlab_default_dev_secret_key_32b!"


def sign_session_token(session_id: str, secret: bytes) -> str:
    """Signs a session ID using HMAC-SHA256, returning session_id.signature."""
    sig = hmac.new(secret, session_id.encode("utf-8"), hashlib.sha256).digest()
    sig_b64 = base64.urlsafe_b64encode(sig).decode("ascii").rstrip("=")
    return f"{session_id}.{sig_b64}"


def unsign_session_token(token: str, secret: bytes) -> Optional[str]:
    """Validates the HMAC-SHA256 signature in constant time and returns session_id if valid."""
    if not token or "." not in token:
        return None
    session_id, sig_b64 = token.split(".", 1)
    # Re-pad base64
    missing_padding = len(sig_b64) % 4
    if missing_padding:
        sig_b64 += "=" * (4 - missing_padding)
    try:
        provided_sig = base64.urlsafe_b64decode(sig_b64.encode("ascii"))
    except Exception:
        return None

    expected_sig = hmac.new(secret, session_id.encode("utf-8"), hashlib.sha256).digest()
    if hmac.compare_digest(provided_sig, expected_sig):
        return session_id
    return None
