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
        args = mock_run.call_args[0][0]
        assert "--no-index" in args
        assert "--find-links" in args
        assert str(paths.wheels_dir) in args
