import tempfile
from pathlib import Path
import pytest
from craftlab_ctl.core import (
    get_paths,
    DangerLevel,
    CheckStatus,
    CheckResult,
    OperationResult,
    AuditEvent,
    AuditLogger,
    OperationLock,
    LockError,
)


def test_paths_initialization():
    with tempfile.TemporaryDirectory() as tmpdir:
        home = Path(tmpdir)
        paths = get_paths(home=home)
        assert paths.home == home
        assert paths.config_dir.exists()
        assert paths.data_dir.exists()
        assert paths.state_dir.exists()
        assert paths.run_dir.exists()
        assert paths.logs_dir.exists()


def test_audit_logger():
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        logger = AuditLogger(state_dir=state_dir)
        event = AuditEvent(
            caller_id="uid:1000",
            command="start",
            parameters={"env": "prod"},
            outcome="success",
        )
        logger.log(event)
        events = logger.read_events()
        assert len(events) == 1
        assert events[0].command == "start"
        assert events[0].caller_id == "uid:1000"
        assert events[0].outcome == "success"


@pytest.mark.asyncio
async def test_operation_lock():
    lock = OperationLock()
    assert not lock.is_locked
    await lock.acquire("update")
    assert lock.is_locked
    assert lock.current_operation == "update"

    with pytest.raises(LockError) as exc_info:
        await lock.acquire("maintenance")
    assert "Another mutating operation is currently running" in str(exc_info.value)

    lock.release()
    assert not lock.is_locked

    await lock.acquire("maintenance")
    assert lock.is_locked
    lock.release()
