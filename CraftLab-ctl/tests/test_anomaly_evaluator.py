from datetime import datetime, timezone
from craftlab_ctl.core.anomaly import SecurityAnomalyEvaluator
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
)


def test_anomaly_evaluator_empty(tmp_path):
    db_path = tmp_path / "security-audit.sqlite3"
    sink = SecurityAuditSink(db_path=db_path)
    evaluator = SecurityAnomalyEvaluator(sink=sink)

    posture, alerts = evaluator.evaluate()
    assert posture.threat_index == 5
    assert posture.classification == "NORMAL"
    assert len(alerts) == 0
    assert posture.failed_auths_15m == 0


def test_anomaly_evaluator_brute_force_and_break_glass(tmp_path):
    db_path = tmp_path / "security-audit.sqlite3"
    sink = SecurityAuditSink(db_path=db_path)
    evaluator = SecurityAnomalyEvaluator(sink=sink)

    # Emit 6 failed auth events from same IP
    for i in range(6):
        evt = SecurityEvent(
            component=Component.BACKEND,
            event_type=EventType.AUTH_FAILURE,
            severity=Severity.HIGH,
            outcome=Outcome.DENIED,
            source=SourceContext(ip="192.168.1.55"),
            actor=ActorContext(type=ActorType.ANONYMOUS, id="target_user"),
        )
        sink.emit_critical(evt)

    posture, alerts = evaluator.evaluate()
    assert posture.failed_auths_15m == 6
    # Should detect both brute_force_ip and brute_force_user
    rules = [a.rule for a in alerts]
    assert "brute_force_ip" in rules
    assert "brute_force_user" in rules
    assert posture.threat_index > 20
    assert posture.classification in ("ELEVATED", "HIGH", "CRITICAL")

    # Now emit break-glass event
    bg_evt = SecurityEvent(
        component=Component.DAEMON,
        event_type=EventType.ADMIN_ACTION,
        severity=Severity.CRITICAL,
        outcome=Outcome.SUCCESS,
        actor=ActorContext(type=ActorType.BREAK_GLASS, id="emergency_admin"),
    )
    sink.emit_critical(bg_evt)

    posture2, alerts2 = evaluator.evaluate()
    rules2 = [a.rule for a in alerts2]
    assert "break_glass" in rules2
    assert posture2.threat_index >= 75
    assert posture2.classification == "CRITICAL"


def test_anomaly_evaluator_lockdown_mode(tmp_path):
    db_path = tmp_path / "security-audit.sqlite3"
    sink = SecurityAuditSink(db_path=db_path)
    evaluator = SecurityAnomalyEvaluator(sink=sink)

    posture, _ = evaluator.evaluate(lockdown_enabled=True)
    assert posture.classification == "LOCKDOWN"
    assert posture.lockdown_enabled is True
