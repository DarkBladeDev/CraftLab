from typing import Dict, Any, Optional, Callable, Awaitable, List
from craftlab_ctl.core.paths import CtlPaths
from craftlab_ctl.core.models import StepEvent


class VetoException(Exception):
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


class Context:
    def __init__(
        self,
        paths: CtlPaths,
        caller_id: str = "local",
        step_callback: Optional[Callable[[StepEvent], Awaitable[None]]] = None,
        emit_callback: Optional[Callable[[str, Dict[str, Any]], Awaitable[None]]] = None,
    ):
        self.paths = paths
        self.caller_id = caller_id
        self._step_callback = step_callback
        self._emit_callback = emit_callback
        self.steps: List[StepEvent] = []

    async def step(self, name: str, status: str = "ok", message: Optional[str] = None) -> None:
        event = StepEvent(step=name, status=status, message=message)
        self.steps.append(event)
        if self._step_callback:
            await self._step_callback(event)

    async def emit(self, event_name: str, **data) -> None:
        if self._emit_callback:
            await self._emit_callback(event_name, data)
