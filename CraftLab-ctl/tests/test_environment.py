import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

from craftlab_ctl.core.paths import get_paths
from craftlab_ctl.core.environment import (
    find_venv_python,
    is_venv_valid,
    provision_release_environment,
)


def test_find_venv_python_nonexistent(tmp_path: Path):
    non_existent = tmp_path / "fake_venv"
    assert find_venv_python(non_existent) is None
    assert not is_venv_valid(non_existent)


def test_find_venv_python_valid(tmp_path: Path):
    fake_venv = tmp_path / "mock_venv"
    if sys.platform == "win32":
        bin_dir = fake_venv / "Scripts"
        py_name = "python.exe"
    else:
        bin_dir = fake_venv / "bin"
        py_name = "python"

    bin_dir.mkdir(parents=True)
    fake_py = bin_dir / py_name
    fake_py.write_text("#!/bin/sh\n", encoding="utf-8")

    found = find_venv_python(fake_venv)
    assert found == fake_py
    assert is_venv_valid(fake_venv)


def test_provision_release_environment_offline(tmp_path: Path):
    paths = get_paths(home=tmp_path)
    release_dir = paths.releases_dir / "v1.0.0"
    release_dir.mkdir(parents=True)

    # Mock fake venv structure
    fake_venv = release_dir / ".venv"
    if sys.platform == "win32":
        bin_dir = fake_venv / "Scripts"
        py_name = "python.exe"
    else:
        bin_dir = fake_venv / "bin"
        py_name = "python"
    bin_dir.mkdir(parents=True)
    fake_py = bin_dir / py_name
    fake_py.write_text("#!/bin/sh", encoding="utf-8")

    # Empty requirements file
    req_file = release_dir / "requirements.txt"
    req_file.write_text("", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        res_py = provision_release_environment(
            paths=paths,
            release_dir=release_dir,
            offline_only=True,
        )
        assert res_py == fake_py
        assert mock_run.called
        # Check that --no-index and --find-links with wheels_dir were used
        pip_calls = [call[0][0] for call in mock_run.call_args_list if "pip" in call[0][0]]
        assert len(pip_calls) > 0
        args = pip_calls[0]
        assert "--no-index" in args
        assert "--find-links" in args
        assert str(paths.wheels_dir) in args


def test_companion_packages_installed_from_wheels(tmp_path: Path):
    paths = get_paths(home=tmp_path)
    release_dir = paths.releases_dir / "v1.0.0"
    release_dir.mkdir(parents=True)

    fake_venv = release_dir / ".venv"
    bin_dir = fake_venv / ("Scripts" if sys.platform == "win32" else "bin")
    bin_dir.mkdir(parents=True)
    fake_py = bin_dir / ("python.exe" if sys.platform == "win32" else "python")
    fake_py.write_text("#!/bin/sh", encoding="utf-8")

    # Add mock wheels to paths.wheels_dir
    paths.wheels_dir.mkdir(parents=True, exist_ok=True)
    (paths.wheels_dir / "craftlab_security-0.1.0-py3-none-any.whl").write_text("whl1", encoding="utf-8")
    (paths.wheels_dir / "craftlab_ctl-0.6.0-py3-none-any.whl").write_text("whl2", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        # Import checks fail (returncode=1), but pip installs succeed (returncode=0)
        def mock_subprocess(cmd, **kwargs):
            cmd_str = " ".join(cmd)
            if "-c" in cmd and "import" in cmd_str:
                return MagicMock(returncode=1)
            return MagicMock(returncode=0)

        mock_run.side_effect = mock_subprocess

        res_py = provision_release_environment(
            paths=paths,
            release_dir=release_dir,
            offline_only=True,
        )
        assert res_py == fake_py

        # Verify pip install calls for companion packages
        pip_calls = [" ".join(call[0][0]) for call in mock_run.call_args_list if "pip" in call[0][0]]
        assert any("craftlab-security" in c for c in pip_calls)
        assert any("craftlab-ctl" in c for c in pip_calls)


def test_bundled_wheels_synced_from_release(tmp_path: Path):
    paths = get_paths(home=tmp_path)
    release_dir = paths.releases_dir / "v1.0.0"
    release_dir.mkdir(parents=True)

    # Release contains bundled wheels
    bundled_wheels = release_dir / "wheels"
    bundled_wheels.mkdir()
    (bundled_wheels / "craftlab_security-0.1.0-py3-none-any.whl").write_text("whl_data", encoding="utf-8")

    fake_venv = release_dir / ".venv"
    bin_dir = fake_venv / ("Scripts" if sys.platform == "win32" else "bin")
    bin_dir.mkdir(parents=True)
    fake_py = bin_dir / ("python.exe" if sys.platform == "win32" else "python")
    fake_py.write_text("#!/bin/sh", encoding="utf-8")

    with patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0)
        provision_release_environment(paths=paths, release_dir=release_dir, offline_only=True)

    # Verify wheel was copied to shared wheels_dir
    assert (paths.wheels_dir / "craftlab_security-0.1.0-py3-none-any.whl").exists()

