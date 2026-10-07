import inspect
from typing import List, Dict, Any, Callable, Optional, Awaitable
from craftlab_ctl.core.models import DangerLevel, CheckResult
from craftlab_ctl.sdk.context import Context


class CommandDefinition:
    def __init__(
        self,
        name: str,
        plugin_name: str,
        func: Callable,
        mutates: bool,
        danger: DangerLevel,
        runs_in: str,
        description: str,
        parameters: Dict[str, Any],
    ):
        self.name = name
        self.plugin_name = plugin_name
        self.func = func
        self.mutates = mutates
        self.danger = danger
        self.runs_in = runs_in
        self.description = description
        self.parameters = parameters

    def to_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "plugin": self.plugin_name,
            "mutates": self.mutates,
            "danger": self.danger.value if hasattr(self.danger, "value") else str(self.danger),
            "runs_in": self.runs_in,
            "description": self.description,
            "parameters": self.parameters,
        }


class HookDefinition:
    def __init__(self, event: str, plugin_name: str, func: Callable, priority: int = 100):
        self.event = event
        self.plugin_name = plugin_name
        self.func = func
        self.priority = priority


class CheckDefinition:
    def __init__(self, check_id: str, plugin_name: str, func: Callable):
        self.check_id = check_id
        self.plugin_name = plugin_name
        self.func = func


class Plugin:
    name: str = "base"
    sdk_version: int = 1
    requires: List[str] = []

    def __init__(self):
        self.commands: List[CommandDefinition] = []
        self.hooks: List[HookDefinition] = []
        self.checks: List[CheckDefinition] = []
        self._introspect()

    def _introspect(self):
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if not callable(attr):
                continue

            if getattr(attr, "__is_craftctl_command__", False):
                cmd_def = CommandDefinition(
                    name=attr.__command_name__,
                    plugin_name=self.name,
                    func=attr,
                    mutates=attr.__command_mutates__,
                    danger=attr.__command_danger__,
                    runs_in=attr.__command_runs_in__,
                    description=attr.__command_doc__,
                    parameters=attr.__command_parameters__,
                )
                self.commands.append(cmd_def)

            if getattr(attr, "__is_craftctl_hook__", False):
                hook_def = HookDefinition(
                    event=attr.__hook_event__,
                    plugin_name=self.name,
                    func=attr,
                    priority=attr.__hook_priority__,
                )
                self.hooks.append(hook_def)

            if getattr(attr, "__is_craftctl_check__", False):
                check_def = CheckDefinition(
                    check_id=attr.__check_id__,
                    plugin_name=self.name,
                    func=attr,
                )
                self.checks.append(check_def)

    async def setup(self, ctx: Context) -> None:
        """Called when plugin is initialized."""
        pass
