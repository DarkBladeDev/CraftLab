from enum import Enum
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class DangerLevel(str, Enum):
    SAFE = "SAFE"
    DISRUPTIVE = "DISRUPTIVE"
    DESTRUCTIVE = "DESTRUCTIVE"


class CheckStatus(str, Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


class CheckResult(BaseModel):
    check_id: str
    status: CheckStatus
    message: str
    details: Optional[Dict[str, Any]] = None


class StepEvent(BaseModel):
    step: str
    status: str = "ok"  # "running", "ok", "failed"
    message: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class OperationResult(BaseModel):
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    steps: List[StepEvent] = Field(default_factory=list)

    @classmethod
    def ok(cls, **kwargs) -> "OperationResult":
        return cls(success=True, data=kwargs)

    @classmethod
    def fail(cls, error: str, **kwargs) -> "OperationResult":
        return cls(success=False, error=error, data=kwargs)


class AuditEvent(BaseModel):
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    caller_id: str = "anonymous"
    command: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    outcome: str  # "success", "failed", "vetoed"
    error: Optional[str] = None
