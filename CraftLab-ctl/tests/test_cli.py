from click.testing import CliRunner
from craftlab_ctl.cli import cli


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "CraftLab Control CLI (craftctl)" in result.output
    assert "start" in result.output
    assert "stop" in result.output
    assert "restart" in result.output
    assert "status" in result.output
    assert "doctor" in result.output
    assert "daemon" in result.output
    assert "update" in result.output
    assert "rollback" in result.output
    assert "releases" in result.output
    assert "maintenance" in result.output


def test_cli_update_help():
    runner = CliRunner()
    result = runner.invoke(cli, ["update", "--help"])
    assert result.exit_code == 0
    assert "Manage application updates and release lifecycle" in result.output
    assert "check" in result.output
    assert "prepare" in result.output
    assert "apply" in result.output
    assert "run" in result.output


def test_cli_releases_local():
    runner = CliRunner()
    result = runner.invoke(cli, ["releases"])
    assert result.exit_code == 0
    assert "Installed Releases" in result.output
    assert "Active release" in result.output


def test_cli_maintenance_local():
    runner = CliRunner()
    res_status = runner.invoke(cli, ["maintenance", "status"])
    assert res_status.exit_code == 0
    assert "Maintenance status" in res_status.output

    res_enable = runner.invoke(cli, ["maintenance", "enable", "-m", "Testing maintenance"])
    assert res_enable.exit_code == 0
    assert "Maintenance status: ENABLED" in res_enable.output or "Maintenance mode enabled" in res_enable.output

    res_disable = runner.invoke(cli, ["maintenance", "disable"])
    assert res_disable.exit_code == 0
    assert "Maintenance status: DISABLED" in res_disable.output or "Maintenance mode disabled" in res_disable.output


def test_cli_doctor_local():
    runner = CliRunner()
    result = runner.invoke(cli, ["doctor"])
    assert result.exit_code == 0
    assert "CraftLab System Doctor" in result.output
    assert "env.directories" in result.output


def test_cli_daemon_status():
    runner = CliRunner()
    result = runner.invoke(cli, ["daemon", "status"])
    assert result.exit_code == 0
    assert "craftctld daemon is" in result.output


def test_cli_remote_flags_error_handling():
    runner = CliRunner()
    # Test remote with unavailable server
    result = runner.invoke(cli, ["--server", "http://127.0.0.1:59999", "--token", "fake_token", "status"])
    assert result.exit_code == 1
    assert "Remote execution error" in result.output

