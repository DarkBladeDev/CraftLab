from datetime import datetime, timezone
from typing import Optional, Dict, Any, Literal
import uuid
from pydantic import BaseModel, Field


def utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class MessageEnvelope(BaseModel):
    protocolVersion: str = Field(default="1.0")
    messageType: Literal["hello", "event", "request", "response", "error"]
    messageId: str = Field(default_factory=lambda: str(uuid.uuid4()))
    correlationId: Optional[str] = None
    targetId: str
    sentAt: str = Field(default_factory=utcnow_iso)
    expiresAt: Optional[str] = None
    payload: Dict[str, Any] = Field(default_factory=dict)
