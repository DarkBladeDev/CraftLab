import pytest
import sqlite3
from pathlib import Path
from craftlab_security.models import (
    SecurityEvent,
    Component,
    EventType,
    Severity,
    Outcome,
    ActorContext,
    SourceContext,
    RequestContext,
)
from craftlab_security.sink import SecurityAuditSink


@pytest.fixture
def sink(tmp_path: Path):
    db_file = tmp_path / "security-audit.sqlite3"
    return SecurityAuditSink(db_path=db_file)


def test_sink_emit_critical(sink: SecurityAuditSink):
    evt = SecurityEvent(
        component=Component.DAEMON,
        event_type=EventType.ADMIN_ACTION,
        severity=Severity.HIGH,
        outcome=Outcome.SUCCESS,
        actor=ActorContext(id="admin"),
        source=SourceContext(ip="127.0.0.1"),
        request=RequestContext(route="/api/v1/update/apply"),
        attributes={"version": "1.0.0", "secret_key": "hidden"},
    )
    sink.emit_critical(evt)

    events = sink.query_events(component="daemon")
    assert len(events) == 1
    row = events[0]
    assert row["event_id"] == evt.event_id
    assert row["actor_id"] == "admin"
    assert row["event_type"] == "admin.action"
    assert row["route"] == "/api/v1/update/apply"
    assert "[REDACTED]" in row["attributes_json"]


def test_sink_purge_retention(sink: SecurityAuditSink):
    evt = SecurityEvent(
        component=Component.BACKEND,
        event_type=EventType.HTTP_REQUEST,
        occurred_at="2020-01-01T00:00:00Z",
    )
    sink.emit_critical(evt)
    events = sink.query_events()
    assert len(events) == 1

    deleted = sink.purge_retention(retention_days=30)
    assert deleted == 1

    events_after = sink.query_events()
    assert len(events_after) == 0


@pytest.mark.asyncio
async def test_sink_telemetry_batching(sink: SecurityAuditSink):
    await sink.start_worker()
    for i in range(5):
        evt = SecurityEvent(
            component=Component.BACKEND,
            event_type=EventType.HTTP_REQUEST,
            attributes={"req_num": i},
        )
        sink.emit_telemetry(evt)

    await sink.stop_worker()
    events = sink.query_events()
    assert len(events) == 5
