import pytest
from craftlab_security.models import (
    SecurityEvent,
    Component,
    EventType,
    Severity,
    Outcome,
    ActorType,
    TransportType,
    ReasonCode,
    ActorContext,
    SourceContext,
    RequestContext,
)


def test_create_security_event():
    evt = SecurityEvent(
        component=Component.BACKEND,
        event_type=EventType.AUTH_FAILURE,
        severity=Severity.MEDIUM,
        outcome=Outcome.DENIED,
        actor=ActorContext(type=ActorType.ANONYMOUS),
        source=SourceContext(ip="127.0.0.1", transport=TransportType.HTTP),
        request=RequestContext(method="POST", route="/api/v1/auth/login", status_code=401),
        reason_code=ReasonCode.INVALID_CREDENTIALS.value,
    )
    assert evt.schema_version == 1
    assert evt.component == Component.BACKEND
    assert evt.event_type == EventType.AUTH_FAILURE
    assert evt.severity == Severity.MEDIUM
    assert evt.outcome == Outcome.DENIED
    assert evt.actor.type == ActorType.ANONYMOUS
    assert evt.source.ip == "127.0.0.1"
    assert evt.request.status_code == 401
    assert evt.reason_code == "invalid_credentials"

    d = evt.model_dump()
    assert d["schema_version"] == 1
    assert d["component"] == "backend"
    assert d["event_type"] == "auth.failure"
