import json
import sqlite3
import asyncio
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from craftlab_security.models import SecurityEvent
from craftlab_security.sanitizer import sanitize_event


DDL_SCHEMA = """
CREATE TABLE IF NOT EXISTS security_events (
    event_id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL,
    occurred_at TEXT NOT NULL,
    received_at TEXT NOT NULL,
    component TEXT NOT NULL,
    event_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    outcome TEXT NOT NULL,
    actor_type TEXT NOT NULL,
    actor_id TEXT,
    source_ip TEXT,
    source_transport TEXT NOT NULL,
    route TEXT,
    method TEXT,
    status_code INTEGER,
    reason_code TEXT,
    operation_id TEXT,
    request_id TEXT,
    duration_ms REAL,
    attributes_json TEXT NOT NULL DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_security_events_occurred_at 
    ON security_events(occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_events_type_time 
    ON security_events(event_type, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_events_source_time 
    ON security_events(source_ip, occurred_at DESC);

CREATE INDEX IF NOT EXISTS idx_security_events_actor_time 
    ON security_events(actor_id, occurred_at DESC);
"""


class SecurityAuditSink:
    """
    Dedicated SQLite sink for security audit events.
    Supports fail-closed synchronous persistence for administrative events
    and bounded async queue batching for network telemetry.
    """

    def __init__(self, db_path: Path, queue_maxsize: int = 5000):
        self.db_path = Path(db_path)
        self.queue_maxsize = queue_maxsize
        self._queue: Optional[asyncio.Queue] = None
        self._flusher_task: Optional[asyncio.Task] = None
        self._stop_event = asyncio.Event()
        self._init_db()

    from contextlib import contextmanager

    @contextmanager
    def _connection(self):
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self.db_path), timeout=5.0)
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._connection() as conn:
            conn.executescript(DDL_SCHEMA)
            conn.commit()

    def _prepare_params(self, event: SecurityEvent) -> tuple:
        sanitized = sanitize_event(event)
        received_at = datetime.now(timezone.utc).isoformat()
        req = sanitized.request
        src = sanitized.source
        return (
            sanitized.event_id,
            sanitized.schema_version,
            sanitized.occurred_at,
            received_at,
            sanitized.component.value if hasattr(sanitized.component, "value") else str(sanitized.component),
            sanitized.event_type.value if hasattr(sanitized.event_type, "value") else str(sanitized.event_type),
            sanitized.severity.value if hasattr(sanitized.severity, "value") else str(sanitized.severity),
            sanitized.outcome.value if hasattr(sanitized.outcome, "value") else str(sanitized.outcome),
            sanitized.actor.type.value if hasattr(sanitized.actor.type, "value") else str(sanitized.actor.type),
            sanitized.actor.id,
            src.ip if src else None,
            src.transport.value if src and hasattr(src.transport, "value") else "http",
            req.route if req else None,
            req.method if req else None,
            req.status_code if req else None,
            sanitized.reason_code,
            sanitized.operation_id,
            req.request_id if req else None,
            sanitized.duration_ms,
            json.dumps(sanitized.attributes, ensure_ascii=False),
        )

    def emit_critical(self, event: SecurityEvent) -> None:
        """
        Synchronously persists a critical security event using fail-closed semantics.
        Raises sqlite3.Error if persistence fails.
        """
        params = self._prepare_params(event)
        stmt = """
        INSERT INTO security_events (
            event_id, schema_version, occurred_at, received_at, component,
            event_type, severity, outcome, actor_type, actor_id,
            source_ip, source_transport, route, method, status_code,
            reason_code, operation_id, request_id, duration_ms, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        with self._connection() as conn:
            conn.execute(stmt, params)
            conn.commit()

    def emit_telemetry(self, event: SecurityEvent) -> None:
        """
        Enqueues a non-critical event for batched asynchronous persistence.
        If the async queue is not initialized or full, attempts best-effort write.
        """
        if self._queue is not None:
            try:
                self._queue.put_nowait(event)
                return
            except asyncio.QueueFull:
                pass  # Fall back to synchronous best-effort or drop

        # Direct write fallback
        try:
            self.emit_critical(event)
        except Exception:
            pass  # Suppress error on telemetric events

    async def start_worker(self) -> None:
        """Starts the background batch flusher."""
        if self._flusher_task and not self._flusher_task.done():
            return
        self._queue = asyncio.Queue(maxsize=self.queue_maxsize)
        self._stop_event.clear()
        self._flusher_task = asyncio.create_task(self._flusher_loop())

    async def stop_worker(self) -> None:
        """Stops the flusher worker and drains remaining items."""
        if not self._flusher_task:
            return
        self._stop_event.set()
        await self._flusher_task
        self._flusher_task = None
        # Drain remaining
        if self._queue:
            batch: List[SecurityEvent] = []
            while not self._queue.empty():
                batch.append(self._queue.get_nowait())
            if batch:
                self.flush_batch(batch)

    async def _flusher_loop(self) -> None:
        batch: List[SecurityEvent] = []
        while not self._stop_event.is_set():
            try:
                while len(batch) < 50:
                    try:
                        evt = await asyncio.wait_for(self._queue.get(), timeout=0.25)
                        batch.append(evt)
                    except asyncio.TimeoutError:
                        break
                if batch:
                    self.flush_batch(batch)
                    batch.clear()
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(0.5)

        if batch:
            self.flush_batch(batch)

    def flush_batch(self, events: List[SecurityEvent]) -> int:
        if not events:
            return 0
        stmt = """
        INSERT OR IGNORE INTO security_events (
            event_id, schema_version, occurred_at, received_at, component,
            event_type, severity, outcome, actor_type, actor_id,
            source_ip, source_transport, route, method, status_code,
            reason_code, operation_id, request_id, duration_ms, attributes_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        rows = [self._prepare_params(e) for e in events]
        with self._connection() as conn:
            cursor = conn.executemany(stmt, rows)
            conn.commit()
            return cursor.rowcount

    def purge_retention(self, retention_days: int = 30) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=retention_days)).isoformat()
        stmt = "DELETE FROM security_events WHERE occurred_at < ?"
        with self._connection() as conn:
            cursor = conn.execute(stmt, (cutoff,))
            conn.commit()
            return cursor.rowcount

    def query_events(
        self,
        component: Optional[str] = None,
        event_type: Optional[str] = None,
        actor_id: Optional[str] = None,
        source_ip: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params = []
        if component:
            clauses.append("component = ?")
            params.append(component)
        if event_type:
            clauses.append("event_type = ?")
            params.append(event_type)
        if actor_id:
            clauses.append("actor_id = ?")
            params.append(actor_id)
        if source_ip:
            clauses.append("source_ip = ?")
            params.append(source_ip)
        if severity:
            clauses.append("severity = ?")
            params.append(severity)

        where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM security_events {where_sql} ORDER BY occurred_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
