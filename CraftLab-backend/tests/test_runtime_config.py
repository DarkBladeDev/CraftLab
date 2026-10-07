import os
import tempfile
from pathlib import Path
import pytest
from app.core.config import load_settings, resolve_home


def test_default_config_resolution():
    with tempfile.TemporaryDirectory() as tmpdir:
        home = Path(tmpdir)
        settings = load_settings(home=home)
        assert settings.server.host == "127.0.0.1"
        assert settings.server.port == 8000
        assert settings.paths.home == home
        assert settings.paths.data_dir == home / "data"
        assert settings.paths.config_dir == home / "config"
        assert settings.paths.run_dir == home / "run"
        assert settings.paths.logs_dir == home / "logs"
        assert settings.paths.packs_dir == home / "data" / "packs"
        assert "sqlite+aiosqlite:///" in settings.database_url
        assert settings.paths.data_dir.exists()


def test_craftlab_toml_loading():
    with tempfile.TemporaryDirectory() as tmpdir:
        home = Path(tmpdir)
        config_dir = home / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_file = config_dir / "craftlab.toml"
        config_file.write_text(
            """
[server]
host = "0.0.0.0"
port = 9000
cors_origins = ["http://example.com"]

[database]
url = "postgresql+asyncpg://user:pass@localhost:5432/craftlab"
""",
            encoding="utf-8",
        )

        settings = load_settings(home=home)
        assert settings.server.host == "0.0.0.0"
        assert settings.server.port == 9000
        assert settings.server.cors_origins == ["http://example.com"]
        assert settings.database_url == "postgresql+asyncpg://user:pass@localhost:5432/craftlab"


def test_environment_variable_override():
    with tempfile.TemporaryDirectory() as tmpdir:
        home = Path(tmpdir)
        os.environ["CRAFTLAB_HOST"] = "192.168.1.100"
        os.environ["CRAFTLAB_PORT"] = "9999"
        os.environ["CRAFTLAB_DATABASE_URL"] = "sqlite+aiosqlite:///custom/path.db"
        try:
            settings = load_settings(home=home)
            assert settings.server.host == "192.168.1.100"
            assert settings.server.port == 9999
            assert settings.database_url == "sqlite+aiosqlite:///custom/path.db"
        finally:
            del os.environ["CRAFTLAB_HOST"]
            del os.environ["CRAFTLAB_PORT"]
            del os.environ["CRAFTLAB_DATABASE_URL"]


def test_canonical_path_resolution():
    from app.core.database import DATABASE_URL
    from app.api.packs import BASE_DATA_DIR
    from app.domain.workspace import get_default_workspace_dir
    from app.core.config import settings

    assert DATABASE_URL == settings.database_url
    assert BASE_DATA_DIR == settings.paths.packs_dir
    assert get_default_workspace_dir() == (settings.paths.packs_dir / "workspace").resolve()

