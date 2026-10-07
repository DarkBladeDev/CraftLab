import json
from pathlib import Path
from typing import Optional, List
from craftlab_ctl.core.models import AuditEvent


class AuditLogger:
    def __init__(self, state_dir: Path):
        self.state_dir = state_dir
        self.audit_file = state_dir / "audit.jsonl"

    def log(self, event: AuditEvent) -> None:
        self.state_dir.mkdir(parents=True, exist_ok=True)
        line = json.dumps(event.model_dump()) + "\n"
        with open(self.audit_file, "a", encoding="utf-8") as f:
            f.write(line)

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
