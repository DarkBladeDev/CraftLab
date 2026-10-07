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
