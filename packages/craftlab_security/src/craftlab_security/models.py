from enum import Enum
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field


class Component(str, Enum):
    BACKEND = "backend"
    WEBSOCKET_GATEWAY = "websocket_gateway"
    DAEMON = "daemon"
    CLI = "cli"


class EventType(str, Enum):
    HTTP_REQUEST = "http.request"
    AUTH_SUCCESS = "auth.success"
    AUTH_FAILURE = "auth.failure"
    AUTHZ_DENIED = "authz.denied"
    API_ENUMERATION_DETECTED = "api.enumeration.detected"
    WEBSOCKET_AUTH_FAILURE = "websocket.auth.failure"
    WEBSOCKET_CONNECTED = "websocket.connected"
    WEBSOCKET_DISCONNECTED = "websocket.disconnected"
    WEBSOCKET_LIMIT_EXCEEDED = "websocket.limit.exceeded"
    ADMIN_ACTION = "admin.action"
    DAEMON_OPERATION_FAILED = "daemon.operation.failed"
    SECURITY_ALERT = "security.alert"


class Severity(str, Enum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Outcome(str, Enum):
    SUCCESS = "success"
    DENIED = "denied"
    FAILED = "failed"
    UNKNOWN = "unknown"


class ActorType(str, Enum):
    USER = "user"
    AGENT = "agent"
    BREAK_GLASS = "break_glass"
    ANONYMOUS = "anonymous"


class TransportType(str, Enum):
    HTTP = "http"
    WS = "ws"
    IPC = "ipc"
    CLI = "cli"


class TargetType(str, Enum):
    USER = "user"
    RESOURCE = "resource"
    AGENT = "agent"
    SYSTEM = "system"
    CONFIG = "config"


class ReasonCode(str, Enum):
    INVALID_CREDENTIALS = "invalid_credentials"
    PERMISSION_DENIED = "permission_denied"
    TOKEN_EXPIRED = "token_expired"
    INVALID_TOKEN = "invalid_token"
    TARGET_SECRET_MISMATCH = "target_secret_mismatch"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    UNAUTHORIZED = "unauthorized"
    OPERATION_FAILED = "operation_failed"
    VETOED = "vetoed"


class ActorContext(BaseModel):
    type: ActorType = ActorType.ANONYMOUS
    id: Optional[str] = None


class SourceContext(BaseModel):
    ip: Optional[str] = None
    transport: TransportType = TransportType.HTTP
    user_agent: Optional[str] = None


class RequestContext(BaseModel):
    request_id: Optional[str] = None
    method: Optional[str] = None
    route: Optional[str] = None
    status_code: Optional[int] = None


class TargetContext(BaseModel):
    type: Optional[str] = None
    id: Optional[str] = None


class SecurityEvent(BaseModel):
    schema_version: int = 1
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    occurred_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    component: Component
    event_type: EventType
    severity: Severity = Severity.INFO
    outcome: Outcome = Outcome.SUCCESS
    actor: ActorContext = Field(default_factory=ActorContext)
    source: SourceContext = Field(default_factory=SourceContext)
    request: Optional[RequestContext] = None
    target: Optional[TargetContext] = None
    reason_code: Optional[str] = None
    operation_id: Optional[str] = None
    duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = Field(default_factory=dict)
