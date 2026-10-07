import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from craftlab_ctl.core.paths import CtlPaths


def maintenance_file(paths: CtlPaths) -> Path:
    return paths.state_dir / "maintenance.json"


def is_maintenance_enabled(paths: CtlPaths) -> bool:
    mf = maintenance_file(paths)
    if not mf.exists():
        return False
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
        return bool(data.get("enabled", False))
    except Exception:
        return False


def get_maintenance_status(paths: CtlPaths) -> Dict[str, Any]:
    mf = maintenance_file(paths)
    if not mf.exists():
        return {"enabled": False, "message": "", "enabled_at": None}
    try:
        data = json.loads(mf.read_text(encoding="utf-8"))
        return {
            "enabled": bool(data.get("enabled", False)),
            "message": data.get("message", ""),
            "enabled_at": data.get("enabled_at"),
        }
    except Exception:
        return {"enabled": False, "message": "", "enabled_at": None}


def set_maintenance(paths: CtlPaths, enabled: bool, message: str = "") -> None:
    mf = maintenance_file(paths)
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    if enabled:
        data = {
            "enabled": True,
            "message": message or "CraftLab is temporarily under maintenance",
            "enabled_at": datetime.now(timezone.utc).isoformat(),
        }
        mf.write_text(json.dumps(data, indent=2), encoding="utf-8")
    else:
        if mf.exists():
            mf.unlink(missing_ok=True)


def prune_releases(
    paths: CtlPaths,
    max_keep: int = 3,
    protect_versions: Optional[List[str]] = None,
) -> List[str]:
    """Delete oldest release directories if total installed releases exceeds max_keep.
    
    Returns list of pruned release names.
    """
    if not paths.releases_dir.exists():
        return []

    protect = set(protect_versions or [])
    active_ver = paths.active_release_version
    if active_ver:
        protect.add(active_ver)
        protect.add(f"v{active_ver.lstrip('v')}")
        protect.add(active_ver.lstrip("v"))

    installed = []
    for item in paths.releases_dir.iterdir():
        if item.is_dir() and (item / "manifest.json").exists() or (item / "backend").exists():
            installed.append(item)

    if len(installed) <= max_keep:
        return []

    # Sort oldest first by modification/creation time
    installed.sort(key=lambda p: p.stat().st_mtime)

    pruned = []
    # Retain the newest max_keep releases
    to_check = installed[: len(installed) - max_keep]
    for rel_dir in to_check:
        if rel_dir.name in protect:
            continue
        try:
            shutil.rmtree(rel_dir)
            pruned.append(rel_dir.name)
        except Exception:
            pass

    return pruned
