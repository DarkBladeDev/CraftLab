"""
CraftLab Security Package
Canonical security event contracts, universal sanitizer, and persistence sink.
"""

from craftlab_security.models import (
    Component,
    EventType,
    Severity,
    Outcome,
    ActorType,
    TransportType,
    TargetType,
    ReasonCode,
    ActorContext,
    SourceContext,
    RequestContext,
    TargetContext,
    SecurityEvent,
)
from craftlab_security.sanitizer import sanitize_event, sanitize_dict
from craftlab_security.sink import SecurityAuditSink
from craftlab_security.validation import validate_production_security_environment

__all__ = [
    "Component",
    "EventType",
    "Severity",
    "Outcome",
    "ActorType",
    "TransportType",
    "TargetType",
    "ReasonCode",
    "ActorContext",
    "SourceContext",
    "RequestContext",
    "TargetContext",
    "SecurityEvent",
    "sanitize_event",
    "sanitize_dict",
    "SecurityAuditSink",
    "validate_production_security_environment",
]
