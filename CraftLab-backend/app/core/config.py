import os
import sys
import tomllib
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field


class ServerSettings(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    cors_origins: List[str] = Field(default_factory=lambda: ["*"])
    auth_enabled: bool = False


class DatabaseSettings(BaseModel):
    url: Optional[str] = None


class PathsSettings(BaseModel):
    home: Path
    config_dir: Path
    data_dir: Path
    run_dir: Path
    logs_dir: Path
    packs_dir: Path


class Settings(BaseModel):
    server: ServerSettings = Field(default_factory=ServerSettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    paths: PathsSettings

    @property
    def database_url(self) -> str:
        if self.database.url:
            return self.database.url
        db_file = self.paths.data_dir / "mcp.db"
        return f"sqlite+aiosqlite:///{db_file.as_posix()}"


def resolve_home(env_home: Optional[str] = None) -> Path:
    if env_home:
        return Path(env_home).resolve()
    if os.getenv("CRAFTLAB_HOME"):
        return Path(os.getenv("CRAFTLAB_HOME")).resolve()

    current_file = Path(__file__).resolve()

    # 1. Source checkout in monorepo
    for parent in current_file.parents:
        if (parent / "CraftLab-backend").exists() and (parent / "CraftLab-ctl").exists():
            return parent
        if (parent / ".git").exists() and (parent / "CraftLab-backend").exists():
            return parent

    # 2. Release directory (<home>/releases/<version>/backend/app/core/config.py)
    for parent in current_file.parents:
        if parent.name == "releases":
            return parent.parent
        if (parent / "releases").is_dir() and (parent / "config").is_dir():
            return parent

    # 3. Current working directory if markers exist
    cwd = Path.cwd().resolve()
    for marker in ("config", "releases", "data", "ctl", "craftlab.toml", ".env"):
        if (cwd / marker).exists():
            return cwd

    # 4. Standard Linux installation paths
    for std_dir in (Path("/opt/craftlab"), Path("/var/lib/craftlab")):
        if std_dir.exists():
            return std_dir

    return current_file.parents[3]


def load_settings(home: Optional[Path] = None, config_file: Optional[Path] = None) -> Settings:
    resolved_home = home or resolve_home()
    if "pytest" not in sys.modules and "PYTEST_CURRENT_TEST" not in os.environ:
        env_file = resolved_home / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                pass

    config_dir = resolved_home / "config"
    data_dir = resolved_home / "data"
    run_dir = resolved_home / "run"
    logs_dir = resolved_home / "logs"
    packs_dir = data_dir / "packs"

    for d in (config_dir, data_dir, run_dir, logs_dir, packs_dir):
        d.mkdir(parents=True, exist_ok=True)

    paths = PathsSettings(
        home=resolved_home,
        config_dir=config_dir,
        data_dir=data_dir,
        run_dir=run_dir,
        logs_dir=logs_dir,
        packs_dir=packs_dir,
    )

    toml_data = {}
    target_config = config_file or (config_dir / "craftlab.toml")
    if target_config.exists():
        try:
            with open(target_config, "rb") as f:
                toml_data = tomllib.load(f)
        except Exception:
            toml_data = {}

    server_data = toml_data.get("server", {})
    database_data = toml_data.get("database", {})

    if os.getenv("CRAFTLAB_HOST"):
        server_data["host"] = os.getenv("CRAFTLAB_HOST")
    if os.getenv("CRAFTLAB_PORT"):
        server_data["port"] = int(os.getenv("CRAFTLAB_PORT"))
    if os.getenv("CRAFTLAB_AUTH_ENABLED"):
        server_data["auth_enabled"] = os.getenv("CRAFTLAB_AUTH_ENABLED").lower() in ("true", "1", "yes")
    if os.getenv("CRAFTLAB_DATABASE_URL"):
        database_data["url"] = os.getenv("CRAFTLAB_DATABASE_URL")

    return Settings(
        server=ServerSettings(**server_data),
        database=DatabaseSettings(**database_data),
        paths=paths,
    )


settings = load_settings()
