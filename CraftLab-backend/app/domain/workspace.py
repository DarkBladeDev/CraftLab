import os
import re
import json
import struct
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple


MINECRAFT_IDENTIFIER_REGEX = re.compile(r"^[a-z0-9_.-]+$")


def get_default_workspace_dir() -> Path:
    from app.core.config import settings
    return (settings.paths.packs_dir / "workspace").resolve()


def validate_minecraft_identifier(name: str) -> bool:
    """
    Validates whether a file/directory name adheres to Minecraft naming conventions:
    lowercase, digits, underscores, dots, hyphens only.
    """
    if not name or not MINECRAFT_IDENTIFIER_REGEX.match(name):
        return False
    return True


def safe_resolve_workspace_path(workspace_dir: Path, relative_path: str) -> Path:
    """
    Safely resolves a relative path within the workspace directory.
    Prevents path traversal attacks outside the workspace directory.
    """
    normalized = relative_path.replace("\\", "/").lstrip("/")
    resolved_workspace = workspace_dir.resolve()
    target_path = (resolved_workspace / normalized).resolve()
    if not str(target_path).startswith(str(resolved_workspace)):
        raise ValueError(f"Access denied: path traversal detected for '{relative_path}'")
    return target_path


def ensure_workspace_initialized(workspace_dir: Optional[Path] = None) -> Path:
    """
    Ensures that the workspace pack directory exists and contains initial scaffolding.
    If the directory does not exist or is empty, creates pack.mcmeta and standard asset directories.
    """
    if workspace_dir is None:
        workspace_dir = get_default_workspace_dir()
    workspace_dir = workspace_dir.resolve()

    workspace_dir.mkdir(parents=True, exist_ok=True)

    # Check if empty (or only hidden files)
    contents = [f for f in workspace_dir.iterdir() if not f.name.startswith(".")]
    if not contents:
        # Create pack.mcmeta
        mcmeta_path = workspace_dir / "pack.mcmeta"
        mcmeta_data = {
            "pack": {
                "pack_format": 34,
                "supported_formats": {
                    "min_inclusive": 34,
                    "max_inclusive": 65
                },
                "min_format": 34,
                "max_format": 65,
                "description": "CraftLab Workspace Pack"
            }
        }
        mcmeta_path.write_text(json.dumps(mcmeta_data, indent=2), encoding="utf-8")

        # Create standard directory scaffolding
        scaffold_dirs = [
            workspace_dir / "assets" / "minecraft" / "textures" / "item",
            workspace_dir / "assets" / "minecraft" / "textures" / "block",
            workspace_dir / "assets" / "minecraft" / "models" / "item",
            workspace_dir / "assets" / "minecraft" / "models" / "block",
            workspace_dir / "assets" / "minecraft" / "items",
            workspace_dir / "assets" / "minecraft" / "sounds",
        ]
        for d in scaffold_dirs:
            d.mkdir(parents=True, exist_ok=True)

    return workspace_dir


def resolve_resource_location(relative_path: str) -> Dict[str, Any]:
    """
    Computes the canonical Minecraft Resource Location (namespace:path) and category
    based on relative file path within a resource pack.

    Examples:
      - assets/craftlab/textures/item/ruby.png -> craftlab:item/ruby (category: texture)
      - assets/craftlab/models/item/ruby.json -> craftlab:item/ruby (category: model)
      - assets/craftlab/items/ruby.json -> craftlab:ruby (category: item_definition)
      - assets/craftlab/sounds/weapon/slash.ogg -> craftlab:weapon/slash (category: sound)
      - assets/minecraft/font/custom.json -> minecraft:custom (category: font)
      - pack.mcmeta -> None (category: manifest)
    """
    clean_path = relative_path.replace("\\", "/").strip("/")
    parts = clean_path.split("/")

    overlay = None
    if parts and parts[0].startswith("overlay_"):
        overlay = parts[0]
        parts = parts[1:]

    if not parts:
        return {
            "relative_path": clean_path,
            "category": "unknown",
            "namespace": None,
            "resource_location": None,
            "overlay": overlay
        }

    # Top-level manifest
    if len(parts) == 1 and parts[0] == "pack.mcmeta":
        return {
            "relative_path": clean_path,
            "category": "manifest",
            "namespace": None,
            "resource_location": None,
            "overlay": overlay
        }

    if parts[0] != "assets" or len(parts) < 3:
        category = "manifest" if parts[-1].endswith(".mcmeta") else "other"
        return {
            "relative_path": clean_path,
            "category": category,
            "namespace": None,
            "resource_location": None,
            "overlay": overlay
        }

    namespace = parts[1]
    asset_category_dir = parts[2]
    subpath_parts = parts[3:]
    filename = subpath_parts[-1] if subpath_parts else parts[2]
    filename_stem = filename.split(".", 1)[0] if "." in filename else filename

    subpath_without_ext = "/".join(subpath_parts[:-1] + [filename_stem]) if len(subpath_parts) > 1 else filename_stem

    resource_loc = None
    category = "other"

    if asset_category_dir == "textures":
        category = "texture"
        resource_loc = f"{namespace}:{subpath_without_ext}"
    elif asset_category_dir == "models":
        category = "model"
        resource_loc = f"{namespace}:{subpath_without_ext}"
    elif asset_category_dir == "items":
        # Minecraft 1.21.2+ Item Definitions
        category = "item_definition"
        resource_loc = f"{namespace}:{subpath_without_ext}"
    elif asset_category_dir == "sounds":
        category = "sound"
        resource_loc = f"{namespace}:{subpath_without_ext}"
    elif asset_category_dir == "font":
        category = "font"
        resource_loc = f"{namespace}:{subpath_without_ext}"
    elif asset_category_dir == "lang":
        category = "lang"
        resource_loc = f"{namespace}:{filename_stem}"
    elif asset_category_dir == "blockstates":
        category = "blockstate"
        resource_loc = f"{namespace}:{subpath_without_ext}"
    else:
        category = "other"
        resource_loc = f"{namespace}:{asset_category_dir}/{subpath_without_ext}"

    # Helpful formatted helper strings
    item_model_component = f'item_model="{resource_loc}"' if resource_loc else None
    json_layer_reference = f'"layer0": "{resource_loc}"' if resource_loc else None
    give_command = f'/give @p diamond_sword[item_model="{resource_loc}"]' if resource_loc else None

    return {
        "relative_path": clean_path,
        "category": category,
        "namespace": namespace,
        "resource_location": resource_loc,
        "overlay": overlay,
        "item_model_component": item_model_component,
        "json_layer_reference": json_layer_reference,
        "give_command": give_command
    }


def parse_png_dimensions(file_bytes: bytes) -> Optional[Tuple[int, int]]:
    """
    Parses PNG width and height directly from PNG IHDR chunk without third-party dependencies.
    """
    if len(file_bytes) < 24:
        return None
    # PNG signature: 89 50 4E 47 0D 0A 1A 0A
    if file_bytes[:8] != b'\x89PNG\r\n\x1a\n':
        return None
    try:
        # IHDR chunk is located at offset 12..24; width and height are big-endian uint32 at 16..24
        width, height = struct.unpack(">II", file_bytes[16:24])
        return width, height
    except Exception:
        return None


def build_workspace_tree(workspace_dir: Path, current_dir: Optional[Path] = None) -> Dict[str, Any]:
    """
    Recursively builds a tree dictionary of directories and files in workspace.
    """
    workspace_dir = workspace_dir.resolve()
    if current_dir is None:
        current_dir = workspace_dir
    else:
        current_dir = current_dir.resolve()

    rel_path = str(current_dir.relative_to(workspace_dir)).replace("\\", "/")
    if rel_path == ".":
        rel_path = ""

    node: Dict[str, Any] = {
        "name": current_dir.name or "workspace",
        "path": rel_path,
        "type": "directory",
        "children": []
    }

    try:
        entries = sorted(list(current_dir.iterdir()), key=lambda e: (e.is_file(), e.name.lower()))
    except Exception:
        return node

    for entry in entries:
        if entry.name.startswith("."):
            continue
        entry_rel = str(entry.resolve().relative_to(workspace_dir)).replace("\\", "/")
        if entry.is_dir():
            node["children"].append(build_workspace_tree(workspace_dir, entry))
        else:
            ext = entry.suffix.lower()
            file_size = entry.stat().st_size
            meta = resolve_resource_location(entry_rel)
            node["children"].append({
                "name": entry.name,
                "path": entry_rel,
                "type": "file",
                "size": file_size,
                "extension": ext,
                "category": meta["category"],
                "resource_location": meta["resource_location"]
            })

    return node


def get_workspace_metadata(workspace_dir: Path, relative_path: str) -> Dict[str, Any]:
    """
    Computes deep technical metadata, dimensions, and cross-references for a workspace file.
    """
    file_path = safe_resolve_workspace_path(workspace_dir, relative_path)
    if not file_path.exists() or not file_path.is_file():
        raise FileNotFoundError(f"File '{relative_path}' not found in workspace")

    stat = file_path.stat()
    file_bytes = file_path.read_bytes()
    rl_info = resolve_resource_location(relative_path)

    metadata: Dict[str, Any] = {
        "file_name": file_path.name,
        "relative_path": relative_path.replace("\\", "/"),
        "size_bytes": stat.st_size,
        "modified_at": stat.st_mtime,
        **rl_info,
        "diagnostics": {
            "dimensions": None,
            "is_square": None,
            "is_power_of_two": None,
            "missing_textures": [],
            "referenced_by_models": []
        }
    }

    # Image metadata
    if rl_info["category"] == "texture" or file_path.suffix.lower() == ".png":
        dims = parse_png_dimensions(file_bytes)
        if dims:
            w, h = dims
            is_square = (w == h)
            is_pow2 = (w > 0 and (w & (w - 1)) == 0) and (h > 0 and (h & (h - 1)) == 0)
            metadata["diagnostics"]["dimensions"] = {"width": w, "height": h}
            metadata["diagnostics"]["is_square"] = is_square
            metadata["diagnostics"]["is_power_of_two"] = is_pow2

        # Search for models referencing this texture
        target_rl = rl_info["resource_location"]
        if target_rl:
            referencing = []
            assets_dir = workspace_dir / "assets"
            if assets_dir.exists():
                for model_file in assets_dir.glob("**/models/**/*.json"):
                    try:
                        content = model_file.read_text(encoding="utf-8")
                        if target_rl in content:
                            referencing.append(str(model_file.resolve().relative_to(workspace_dir.resolve())).replace("\\", "/"))
                    except Exception:
                        pass
            metadata["diagnostics"]["referenced_by_models"] = referencing

    # Model metadata (inspect textures and find missing ones)
    elif rl_info["category"] in ("model", "item_definition") or file_path.suffix.lower() == ".json":
        try:
            model_json = json.loads(file_bytes.decode("utf-8"))
            textures_dict = model_json.get("textures", {})
            missing = []
            for slot, tex_ref in textures_dict.items():
                if isinstance(tex_ref, str) and not tex_ref.startswith("#"):
                    # Check if texture exists in workspace
                    # format: <namespace>:<path> or <path>
                    if ":" in tex_ref:
                        ns, subp = tex_ref.split(":", 1)
                    else:
                        ns, subp = "minecraft", tex_ref

                    expected_png = workspace_dir / "assets" / ns / "textures" / f"{subp}.png"
                    if not expected_png.exists():
                        missing.append({
                            "slot": slot,
                            "texture_ref": tex_ref,
                            "expected_path": f"assets/{ns}/textures/{subp}.png"
                        })
            metadata["diagnostics"]["missing_textures"] = missing
        except Exception:
            pass

    return metadata
