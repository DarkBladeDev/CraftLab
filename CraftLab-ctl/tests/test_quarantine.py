import time
from datetime import datetime, timezone, timedelta
from craftlab_ctl.core.quarantine import IpQuarantineManager, QuarantineEntry


def test_quarantine_lifecycle(tmp_path):
    manager = IpQuarantineManager(state_dir=tmp_path)
    assert manager.is_quarantined("192.168.1.50") is False

    entry = manager.quarantine("192.168.1.50", duration_minutes=10, reason="Failed login spike", actor="admin:alice")
    assert entry.ip == "192.168.1.50"
    assert entry.reason == "Failed login spike"
    assert entry.quarantined_by == "admin:alice"
    assert manager.is_quarantined("192.168.1.50") is True

    active = manager.get_active_quarantines()
    assert len(active) == 1
    assert active[0].ip == "192.168.1.50"

    # Persistence verification
    manager2 = IpQuarantineManager(state_dir=tmp_path)
    assert manager2.is_quarantined("192.168.1.50") is True

    # Unquarantine
    assert manager2.unquarantine("192.168.1.50") is True
    assert manager2.is_quarantined("192.168.1.50") is False
    assert len(manager2.get_active_quarantines()) == 0


def test_quarantine_expiration(tmp_path):
    manager = IpQuarantineManager(state_dir=tmp_path)
    # Manually insert expired entry
    past = (datetime.now(timezone.utc) - timedelta(minutes=5)).isoformat()
    manager._entries["10.0.0.99"] = QuarantineEntry(
        ip="10.0.0.99",
        expires_at=past,
        reason="Old attack",
    )
    manager.save()

    assert manager.is_quarantined("10.0.0.99") is False
    assert len(manager.get_active_quarantines()) == 0
