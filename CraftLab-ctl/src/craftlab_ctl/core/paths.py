import os
import sys
from pathlib import Path
from typing import Optional
from pydantic import BaseModel


class CtlPaths(BaseModel):
    home: Path
    config_dir: Path
    data_dir: Path
    state_dir: Path
    run_dir: Path
    logs_dir: Path
    packs_dir: Path

    def ensure_directories(self) -> None:
        for d in (
            self.config_dir,
            self.data_dir,
            self.state_dir,
            self.run_dir,
            self.logs_dir,
            self.packs_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def auth_db_path(self) -> Path:
        return self.data_dir / "auth.db"


def resolve_home(env_home: Optional[str] = None) -> Path:
    if env_home:
        return Path(env_home).resolve()
    if os.getenv("CRAFTLAB_HOME"):
        return Path(os.getenv("CRAFTLAB_HOME")).resolve()
    # If not set, check parent of CraftLab-ctl directory (the repo root)
    current_file = Path(__file__).resolve()
    # current_file: CraftLab-ctl/src/craftlab_ctl/core/paths.py -> parents: [core, craftlab_ctl, src, CraftLab-ctl, repo_root]
    repo_root = current_file.parents[4]
    return repo_root


def get_paths(home: Optional[Path] = None) -> CtlPaths:
    resolved_home = home or resolve_home()
    if "pytest" not in sys.modules and "PYTEST_CURRENT_TEST" not in os.environ:
        env_file = resolved_home / ".env"
        if env_file.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(env_file)
            except ImportError:
                pass
    paths = CtlPaths(
        home=resolved_home,
        config_dir=resolved_home / "config",
        data_dir=resolved_home / "data",
        state_dir=resolved_home / "state",
        run_dir=resolved_home / "run",
        logs_dir=resolved_home / "logs",
        packs_dir=resolved_home / "data" / "packs",
    )
    paths.ensure_directories()
    return paths
