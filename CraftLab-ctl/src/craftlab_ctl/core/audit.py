import json
from pathlib import Path
from typing import Optional, List
from craftlab_ctl.core.models import AuditEvent
from craftlab_security import (
    sanitize_dict,
    SecurityAuditSink,
    SecurityEvent,
    Component,
    EventType,
    Severity,
    Outcome,
    ActorContext,
    ActorType,
)


class AuditLogger:
    def __init__(self, state_dir: Path, db_path: Optional[Path] = None):
        self.state_dir = Path(state_dir)
        self.audit_file = self.state_dir / "audit.jsonl"
        self.db_path = Path(db_path) if db_path else self.state_dir.parent / "data" / "security-audit.sqlite3"
        self._sink: Optional[SecurityAuditSink] = None
        try:
            self._sink = SecurityAuditSink(db_path=self.db_path)
        except Exception:
            pass

    def log(self, event: AuditEvent) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        # Apply universal sanitizer before persistence
        event.parameters = sanitize_dict(event.parameters)
        if event.error and len(event.error) > 512:
            event.error = event.error[:512] + "...[TRUNCATED]"

        line = json.dumps(event.model_dump()) + "\n"
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(line)

        # Dual-write to SQLite sink
        if self._sink:
            try:
                outcome_val = (
                    Outcome.SUCCESS
                    if event.outcome == "success"
                    else (Outcome.DENIED if event.outcome == "vetoed" else Outcome.FAILED)
                )
                sec_event = SecurityEvent(
                    component=Component.DAEMON,
                    event_type=EventType.ADMIN_ACTION,
                    severity=Severity.HIGH if event.outcome != "success" else Severity.MEDIUM,
                    outcome=outcome_val,
                    actor=ActorContext(
                        type=ActorType.USER if str(event.caller_id).startswith("web:") else ActorType.CLI,
                        id=str(event.caller_id),
                    ),
                    reason_code=event.outcome if event.outcome != "success" else None,
                    attributes={
                        "command": event.command,
                        "parameters": event.parameters,
                        "error": event.error,
                    },
                )
                self._sink.emit_critical(sec_event)
            except Exception:
                pass

    def read_events(self, limit: Optional[int] = None) -> List[AuditEvent]:
        if not self.audit_file.exists():
            return []
        events = []
        with open(self.audit_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        events.append(AuditEvent(**json.loads(line)))
                    except Exception:
                        pass
        if limit:
            return events[-limit:]
        return events
