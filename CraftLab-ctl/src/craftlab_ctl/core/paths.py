import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel


class CtlPaths(BaseModel):
    home: Path
    config_dir: Path
    data_dir: Path
    state_dir: Path
    run_dir: Path
    logs_dir: Path
    packs_dir: Path
    releases_dir: Optional[Path] = None
    cache_dir: Optional[Path] = None
    wheels_dir: Optional[Path] = None
    downloads_dir: Optional[Path] = None

    def model_post_init(self, __context: object) -> None:
        if self.releases_dir is None:
            self.releases_dir = self.home / "releases"
        if self.cache_dir is None:
            self.cache_dir = self.home / "cache"
        if self.wheels_dir is None:
            self.wheels_dir = self.cache_dir / "wheels"
        if self.downloads_dir is None:
            self.downloads_dir = self.cache_dir / "downloads"

    def ensure_directories(self) -> None:
        for d in (
            self.config_dir,
            self.data_dir,
            self.state_dir,
            self.run_dir,
            self.logs_dir,
            self.packs_dir,
            self.releases_dir,
            self.cache_dir,
            self.wheels_dir,
            self.downloads_dir,
        ):
            d.mkdir(parents=True, exist_ok=True)

    @property
    def auth_db_path(self) -> Path:
        return self.data_dir / "auth.db"

    @property
    def current_pointer_path(self) -> Path:
        return self.home / "current"

    @property
    def current_release_file(self) -> Path:
        return self.state_dir / "current_release.txt"

    @property
    def active_release_version(self) -> Optional[str]:
        # 1. Check symlink or junction at home / "current"
        pointer = self.current_pointer_path
        if pointer.is_symlink():
            try:
                target = pointer.resolve()
                return target.name
            except Exception:
                pass
        # 2. Check current_release.txt
        rel_file = self.current_release_file
        if rel_file.exists():
            v = rel_file.read_text(encoding="utf-8").strip()
            if v:
                return v
        return None

    @property
    def active_release_dir(self) -> Optional[Path]:
        ver = self.active_release_version
        if ver:
            candidate = self.releases_dir / ver
            if candidate.exists() and candidate.is_dir():
                return candidate
        # If current is an actual directory
        pointer = self.current_pointer_path
        if pointer.exists() and pointer.is_dir():
            return pointer.resolve()
        return None

    @property
    def app_backend_dir(self) -> Path:
        active = self.active_release_dir
        if active:
            cand = active / "backend"
            if cand.exists():
                return cand
        # Fallback to dev checkout
        dev_backend = self.home / "CraftLab-backend"
        if dev_backend.exists():
            return dev_backend
        dev_backend_old = self.home / "backend"
        return dev_backend_old if dev_backend_old.exists() else self.home

    @property
    def app_frontend_dist_dir(self) -> Path:
        active = self.active_release_dir
        if active:
            cand = active / "frontend_dist"
            if cand.exists():
                return cand
        # Fallback to dev checkout
        dev_dist = self.home / "CraftLab-frontend" / "dist"
        if dev_dist.exists():
            return dev_dist
        dev_dist_old = self.home / "frontend" / "dist"
        return dev_dist_old

    def set_active_release(self, version: str) -> None:
        norm = version.lstrip("v")
        target_dir = self.releases_dir / f"v{norm}"
        if not target_dir.exists():
            target_dir = self.releases_dir / norm
        if not target_dir.exists():
            raise FileNotFoundError(f"Release directory for version '{version}' does not exist under {self.releases_dir}")

        actual_version_name = target_dir.name
        # Persist to current_release.txt
        self.current_release_file.write_text(actual_version_name, encoding="utf-8")

        # Attempt atomic symlink swap if supported
        pointer = self.current_pointer_path
        tmp_pointer = self.home / "current_tmp"
        try:
            if tmp_pointer.exists() or tmp_pointer.is_symlink():
                tmp_pointer.unlink(missing_ok=True)
            os.symlink(target_dir, tmp_pointer, target_is_directory=True)
            if pointer.exists() or pointer.is_symlink():
                if sys.platform == "win32" and not pointer.is_symlink():
                    # on Windows non-symlink dir replace can fail
                    pass
                else:
                    os.replace(tmp_pointer, pointer)
            else:
                os.replace(tmp_pointer, pointer)
        except (OSError, PermissionError):
            # Safe fallback: current_release.txt is already written and resolves correctly
            if tmp_pointer.exists():
                tmp_pointer.unlink(missing_ok=True)

    def get_installed_releases(self) -> List[str]:
        if not self.releases_dir.exists():
            return []
        versions = []
        for item in self.releases_dir.iterdir():
            if item.is_dir() and (item / "backend" / "main.py").exists():
                versions.append(item.name)
        # Sort by creation time or name
        return sorted(versions)


def resolve_home(env_home: Optional[str] = None) -> Path:
    if env_home:
        return Path(env_home).resolve()
    if os.getenv("CRAFTLAB_HOME"):
        return Path(os.getenv("CRAFTLAB_HOME")).resolve()
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
        releases_dir=resolved_home / "releases",
        cache_dir=resolved_home / "cache",
        wheels_dir=resolved_home / "cache" / "wheels",
        downloads_dir=resolved_home / "cache" / "downloads",
    )
    paths.ensure_directories()
    return paths
