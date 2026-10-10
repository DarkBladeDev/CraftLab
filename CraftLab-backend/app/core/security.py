import os
from typing import Optional, Dict, Any
from app.core.config import settings
from craftlab_security import (
    SecurityAuditSink,
    SecurityEvent,
    Component,
    EventType,
    Severity,
    Outcome,
    ActorContext,
    ActorType,
    SourceContext,
    RequestContext,
    TransportType,
)

_sink: Optional[SecurityAuditSink] = None


def get_security_sink() -> SecurityAuditSink:
    global _sink
    if _sink is None:
        db_path = settings.paths.data_dir / "security-audit.sqlite3"
        _sink = SecurityAuditSink(db_path=db_path)
    return _sink


def emit_audit_event(
    event_type: EventType,
    severity: Severity = Severity.INFO,
    outcome: Outcome = Outcome.SUCCESS,
    actor_id: Optional[str] = None,
    actor_type: ActorType = ActorType.ANONYMOUS,
    source_ip: Optional[str] = None,
    route: Optional[str] = None,
    method: Optional[str] = None,
    status_code: Optional[int] = None,
    reason_code: Optional[str] = None,
    attributes: Optional[Dict[str, Any]] = None,
    critical: bool = False,
) -> None:
    try:
        sink = get_security_sink()
        evt = SecurityEvent(
            component=Component.BACKEND,
            event_type=event_type,
            severity=severity,
            outcome=outcome,
            actor=ActorContext(type=actor_type, id=actor_id),
            source=SourceContext(ip=source_ip, transport=TransportType.HTTP),
            request=RequestContext(method=method, route=route, status_code=status_code),
            reason_code=reason_code,
            attributes=attributes or {},
        )
        if critical:
            sink.emit_critical(evt)
        else:
            sink.emit_telemetry(evt)
    except Exception:
        pass
