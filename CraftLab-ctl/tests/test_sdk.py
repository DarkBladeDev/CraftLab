import pytest
from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.core.models import DangerLevel, CheckResult, CheckStatus, OperationResult
from craftlab_ctl.sdk import (
    Plugin,
    command,
    hook,
    check,
    Context,
    VetoException,
    PluginRegistry,
    PluginRegistryError,
)


class MockLifecyclePlugin(Plugin):
    name = "mock_lifecycle"
    sdk_version = 1

    @command(mutates=True, danger=DangerLevel.DISRUPTIVE)
    async def start(self, ctx: Context, port: int = 8000, force: bool = False) -> OperationResult:
        """Start the application process."""
        await ctx.step("starting_process")
        return OperationResult.ok(port=port, force=force)

    @hook("app.before_start", priority=50)
    async def before_start_hook(self, ctx: Context, **kwargs):
        if kwargs.get("blocked"):
            raise VetoException("Starting is blocked by policy")

    @check("system.health")
    def health_check(self, ctx: Context) -> CheckResult:
        return CheckResult(
            check_id="system.health",
            status=CheckStatus.PASS,
            message="System is healthy",
        )


class IncompatiblePlugin(Plugin):
    name = "incompatible"
    sdk_version = 999


def test_command_schema_generation():
    plugin = MockLifecyclePlugin()
    assert len(plugin.commands) == 1
    cmd = plugin.commands[0]
    assert cmd.name == "start"
    assert cmd.mutates is True
    assert cmd.danger == DangerLevel.DISRUPTIVE
    assert cmd.description == "Start the application process."
    assert "port" in cmd.parameters
    assert cmd.parameters["port"]["type"] == "integer"
    assert cmd.parameters["port"]["default"] == 8000
    assert "force" in cmd.parameters
    assert cmd.parameters["force"]["type"] == "boolean"
    assert cmd.parameters["force"]["default"] is False


@pytest.mark.asyncio
async def test_plugin_registry_and_veto_hook():
    registry = PluginRegistry()
    plugin = MockLifecyclePlugin()
    registry.register_plugin(plugin)

    assert "mock_lifecycle.start" in registry.commands
    assert "start" in registry.commands

    ctx = Context(paths=get_paths())

    # Dispatch hook without block
    await registry.dispatch_hook("app.before_start", ctx, blocked=False)

    # Dispatch hook with block -> should raise VetoException
    with pytest.raises(VetoException) as exc_info:
        await registry.dispatch_hook("app.before_start", ctx, blocked=True)
    assert exc_info.value.reason == "Starting is blocked by policy"


@pytest.mark.asyncio
async def test_plugin_checks_execution():
    registry = PluginRegistry()
    plugin = MockLifecyclePlugin()
    registry.register_plugin(plugin)

    ctx = Context(paths=get_paths())
    results = await registry.execute_checks(ctx)
    assert len(results) == 1
    assert results[0].check_id == "system.health"
    assert results[0].status == CheckStatus.PASS


def test_incompatible_plugin_rejected():
    registry = PluginRegistry(supported_sdk_version=1)
    bad_plugin = IncompatiblePlugin()
    with pytest.raises(PluginRegistryError) as exc_info:
        registry.register_plugin(bad_plugin)
    assert "incompatible with supported SDK version" in str(exc_info.value)
