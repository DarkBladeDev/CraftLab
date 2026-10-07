import importlib.metadata
import inspect
from typing import Dict, List, Optional, Any
from craftlab_ctl.core.models import CheckResult
from craftlab_ctl.sdk.plugin import Plugin, CommandDefinition, HookDefinition, CheckDefinition
from craftlab_ctl.sdk.context import Context, VetoException

CURRENT_SDK_VERSION = 1


class PluginRegistryError(Exception):
    pass


class PluginRegistry:
    def __init__(self, supported_sdk_version: int = CURRENT_SDK_VERSION):
        self.supported_sdk_version = supported_sdk_version
        self.plugins: Dict[str, Plugin] = {}
        self.commands: Dict[str, CommandDefinition] = {}
        self.hooks: Dict[str, List[HookDefinition]] = {}
        self.checks: Dict[str, CheckDefinition] = {}

    def register_plugin(self, plugin: Plugin) -> None:
        if plugin.sdk_version != self.supported_sdk_version:
            raise PluginRegistryError(
                f"Plugin '{plugin.name}' SDK version {plugin.sdk_version} is incompatible "
                f"with supported SDK version {self.supported_sdk_version}"
            )

        self.plugins[plugin.name] = plugin

        for cmd in plugin.commands:
            key = f"{plugin.name}.{cmd.name}"
            self.commands[key] = cmd
            # Also register by simple name if not already registered
            if cmd.name not in self.commands:
                self.commands[cmd.name] = cmd

        for hook in plugin.hooks:
            if hook.event not in self.hooks:
                self.hooks[hook.event] = []
            self.hooks[hook.event].append(hook)
            # Sort hooks by priority ascending
            self.hooks[hook.event].sort(key=lambda h: h.priority)

        for chk in plugin.checks:
            self.checks[chk.check_id] = chk

    def discover_and_load(self, group: str = "craftlab_ctl.plugins") -> List[str]:
        loaded = []
        try:
            eps = importlib.metadata.entry_points(group=group)
        except Exception:
            eps = []

        for ep in eps:
            try:
                plugin_cls = ep.load()
                plugin_inst = plugin_cls()
                self.register_plugin(plugin_inst)
                loaded.append(plugin_inst.name)
            except Exception as e:
                # Log or keep note of incompatible/failed plugin
                print(f"Warning: Failed to load plugin entry point '{ep.name}': {e}")
        return loaded

    async def dispatch_hook(self, event_name: str, ctx: Context, **kwargs) -> None:
        hook_list = self.hooks.get(event_name, [])
        for h in hook_list:
            if inspect.iscoroutinefunction(h.func):
                await h.func(ctx, **kwargs)
            else:
                h.func(ctx, **kwargs)

    async def execute_checks(self, ctx: Context) -> List[CheckResult]:
        results: List[CheckResult] = []
        for check_id, chk in self.checks.items():
            try:
                if inspect.iscoroutinefunction(chk.func):
                    res = await chk.func(ctx)
                else:
                    res = chk.func(ctx)
                if isinstance(res, CheckResult):
                    results.append(res)
            except Exception as e:
                from craftlab_ctl.core.models import CheckStatus
                results.append(
                    CheckResult(
                        check_id=check_id,
                        status=CheckStatus.FAIL,
                        message=f"Check raised unhandled exception: {e}",
                    )
                )
        return results

    def get_command(self, name: str) -> Optional[CommandDefinition]:
        return self.commands.get(name)

    def list_command_schemas(self) -> List[Dict[str, Any]]:
        # Return unique commands
        seen = set()
        schemas = []
        for cmd in self.commands.values():
            if id(cmd) not in seen:
                seen.add(id(cmd))
                schemas.append(cmd.to_schema())
        return schemas
