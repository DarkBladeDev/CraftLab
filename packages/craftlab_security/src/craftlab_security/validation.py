import os
from typing import Set

DEFAULT_PLACEHOLDER_ROOT_KEYS: Set[str] = {
    "change_me_to_a_secure_root_token",
    "root",
    "admin",
    "password",
    "secret",
    "changeme",
}


def validate_production_security_environment() -> None:
    """
    Validates security environment variables upon startup.
    In production environments (ENV or CRAFTLAB_ENV set to production/prod),
    this function raises RuntimeError if:
      1. Authentication is disabled (CRAFTLAB_AUTH_ENABLED is false/0/no/off)
      2. CRAFTLAB_ROOT_KEY is empty or matches known placeholder tokens.
    """
    env = (os.getenv("CRAFTLAB_ENV") or os.getenv("ENV") or "development").strip().lower()
    is_production = env in ("production", "prod")

    if not is_production:
        return

    auth_enabled_val = os.getenv("CRAFTLAB_AUTH_ENABLED", "").strip().lower()
    if auth_enabled_val in ("false", "0", "no", "off"):
        raise RuntimeError(
            "FATAL SECURITY CONFIGURATION: Production mode forbids CRAFTLAB_AUTH_ENABLED=false. "
            "Authentication must be enabled in production."
        )

    root_key = os.getenv("CRAFTLAB_ROOT_KEY", "").strip()
    if not root_key or root_key.lower() in DEFAULT_PLACEHOLDER_ROOT_KEYS:
        raise RuntimeError(
            "FATAL SECURITY CONFIGURATION: Production mode requires a secure, non-default CRAFTLAB_ROOT_KEY. "
            "Placeholder token detected or key is empty."
        )
