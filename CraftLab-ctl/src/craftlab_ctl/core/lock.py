import asyncio
from typing import Optional


class LockError(Exception):
    pass


class OperationLock:
    def __init__(self):
        self._lock = asyncio.Lock()
        self._current_operation: Optional[str] = None

    @property
    def current_operation(self) -> Optional[str]:
        return self._current_operation

    @property
    def is_locked(self) -> bool:
        return self._lock.locked()

    async def acquire(self, operation_name: str) -> None:
        if self._lock.locked():
            raise LockError(
                f"Another mutating operation is currently running: '{self._current_operation}'"
            )
        await self._lock.acquire()
        self._current_operation = operation_name

    def release(self) -> None:
        if self._lock.locked():
            self._current_operation = None
            self._lock.release()
