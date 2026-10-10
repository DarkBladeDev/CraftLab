import pytest
from craftlab_security.models import (
    SecurityEvent,
    Component,
    EventType,
    ActorContext,
    RequestContext,
)
from craftlab_security.sanitizer import sanitize_dict, sanitize_event


def test_sanitize_dict_redaction():
    payload = {
        "password": "supersecretpassword",
        "api_key": "abc-123",
        "nested": {
            "token": "bearer 999",
            "safe_key": "safe_value",
        },
        "craftlab_session": "sess-xyz",
        "safe_data": 42,
    }
    sanitized = sanitize_dict(payload)
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["api_key"] == "[REDACTED]"
    assert sanitized["craftlab_session"] == "[REDACTED]"
    assert sanitized["safe_data"] == 42
    assert sanitized["nested"]["token"] == "[REDACTED]"
    assert sanitized["nested"]["safe_key"] == "safe_value"


def test_sanitize_string_length_and_injection():
    long_str = "A" * 600
    payload = {"long_field": long_str, "injection": "line1\r\nline2"}
    sanitized = sanitize_dict(payload)
    assert sanitized["long_field"].endswith("...[TRUNCATED]")
    assert len(sanitized["long_field"]) == 512 + len("...[TRUNCATED]")
    assert "\\r\\n" in sanitized["injection"]


def test_sanitize_event_strips_query_string():
    evt = SecurityEvent(
        component=Component.BACKEND,
        event_type=EventType.AUTH_FAILURE,
        actor=ActorContext(id="admin"),
        request=RequestContext(route="/api/v1/auth/login?token=leakyme&secret=1234"),
        attributes={"password": "password123", "user": "admin"},
    )
    sanitized = sanitize_event(evt)
    assert sanitized.request.route == "/api/v1/auth/login"
    assert sanitized.attributes["password"] == "[REDACTED]"
    assert sanitized.attributes["user"] == "admin"
