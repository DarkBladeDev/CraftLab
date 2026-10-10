from typing import Any, Dict, List, Set
from craftlab_security.models import SecurityEvent

REDACTED_PATTERNS: Set[str] = {
    "password",
    "secret",
    "token",
    "accesstoken",
    "refreshtoken",
    "craftlabsession",
    "authorization",
    "cookie",
    "apikey",
    "rootkey",
    "privatekey",
    "credentials",
    "authsecret",
    "targetsecret",
}

MAX_STRING_LENGTH: int = 512
MAX_DEPTH: int = 3
MAX_DICT_KEYS: int = 20


def _is_sensitive_key(key: str) -> bool:
    clean_key = key.lower().replace("-", "").replace("_", "")
    return any(pat in clean_key for pat in REDACTED_PATTERNS)


def sanitize_string(val: str) -> str:
    # Escape dangerous control characters to prevent log injection
    sanitized = val.replace("\r", "\\r").replace("\n", "\\n")
    if len(sanitized) > MAX_STRING_LENGTH:
        return sanitized[:MAX_STRING_LENGTH] + "...[TRUNCATED]"
    return sanitized


def sanitize_value(val: Any, depth: int = 0) -> Any:
    if depth > MAX_DEPTH:
        return "[PRUNED:DEPTH_EXCEEDED]"

    if isinstance(val, str):
        return sanitize_string(val)
    elif isinstance(val, dict):
        return sanitize_dict(val, depth=depth + 1)
    elif isinstance(val, (list, tuple)):
        return [sanitize_value(item, depth=depth + 1) for item in val[:50]]
    elif isinstance(val, (int, float, bool)) or val is None:
        return val
    else:
        return sanitize_string(str(val))


def sanitize_dict(data: Dict[str, Any], depth: int = 0) -> Dict[str, Any]:
    if not isinstance(data, dict):
        return {}

    result: Dict[str, Any] = {}
    items = list(data.items())[:MAX_DICT_KEYS]

    for k, v in items:
        key_str = sanitize_string(str(k))
        if _is_sensitive_key(key_str):
            result[key_str] = "[REDACTED]"
        else:
            result[key_str] = sanitize_value(v, depth=depth)

    return result


def sanitize_event(event: SecurityEvent) -> SecurityEvent:
    """
    Sanitizes attributes, route context, and parameters inside a SecurityEvent.
    Returns a sanitized copy of the event.
    """
    data = event.model_dump()
    if "attributes" in data and isinstance(data["attributes"], dict):
        data["attributes"] = sanitize_dict(data["attributes"])

    if "request" in data and data["request"]:
        req = data["request"]
        if req.get("route"):
            # Strip query strings if present
            route = req["route"].split("?")[0]
            req["route"] = sanitize_string(route)

    return SecurityEvent(**data)
