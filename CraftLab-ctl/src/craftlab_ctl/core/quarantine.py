import json
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QuarantineEntry(BaseModel):
    ip: str
    reason: str = "Suspicious activity detected"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    expires_at: str
    quarantined_by: str = "system"

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        current_time = now or datetime.now(timezone.utc)
        try:
            exp = datetime.fromisoformat(self.expires_at)
            return current_time >= exp
        except Exception:
            return False


class IpQuarantineManager:
    """
    Manages in-memory and disk-persisted IP quarantine lists with TTL expiration.
    Provides sub-millisecond lookup for request middleware.
    """

    def __init__(self, state_dir: Optional[Path] = None, storage_path: Optional[Path] = None):
        if storage_path:
            self.file_path = Path(storage_path)
        elif state_dir:
            self.file_path = Path(state_dir) / "quarantine.json"
        else:
            self.file_path = Path.home() / ".craftlab" / "state" / "quarantine.json"

        self._entries: Dict[str, QuarantineEntry] = {}
        self.load()

    def quarantine(
        self,
        ip: str,
        duration_minutes: int = 60,
        reason: str = "Suspicious activity detected",
        actor: str = "system",
    ) -> QuarantineEntry:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=duration_minutes)
        clean_ip = str(ip).strip()
        entry = QuarantineEntry(
            ip=clean_ip,
            reason=reason,
            created_at=now.isoformat(),
            expires_at=expires.isoformat(),
            quarantined_by=actor,
        )
        self._entries[clean_ip] = entry
        self.save()
        logger.warning(f"Quarantined IP {clean_ip} until {entry.expires_at} (Reason: {reason})")
        return entry

    def unquarantine(self, ip: str) -> bool:
        clean_ip = str(ip).strip()
        if clean_ip in self._entries:
            del self._entries[clean_ip]
            self.save()
            logger.info(f"Unquarantined IP {clean_ip}")
            return True
        return False

    def is_quarantined(self, ip: str) -> bool:
        clean_ip = str(ip).strip()
        entry = self._entries.get(clean_ip)
        if not entry:
            return False
        if entry.is_expired():
            del self._entries[clean_ip]
            self.save()
            return False
        return True

    def get_active_quarantines(self) -> List[QuarantineEntry]:
        now = datetime.now(timezone.utc)
        active: List[QuarantineEntry] = []
        expired: List[str] = []

        for ip, entry in self._entries.items():
            if entry.is_expired(now):
                expired.append(ip)
            else:
                active.append(entry)

        if expired:
            for ip in expired:
                self._entries.pop(ip, None)
            self.save()

        return sorted(active, key=lambda e: e.expires_at)

    def clear(self) -> None:
        self._entries.clear()
        self.save()

    def load(self) -> None:
        if not self.file_path.exists():
            return
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                now = datetime.now(timezone.utc)
                for item in data:
                    entry = QuarantineEntry(**item)
                    if not entry.is_expired(now):
                        self._entries[entry.ip] = entry
        except Exception as e:
            logger.error(f"Failed to load quarantine list from {self.file_path}: {e}")

    def save(self) -> None:
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump([e.model_dump() for e in self._entries.values()], f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save quarantine list to {self.file_path}: {e}")
