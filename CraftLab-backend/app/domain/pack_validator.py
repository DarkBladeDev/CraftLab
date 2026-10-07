import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class ConflictItemInfo(BaseModel):
    source: str
    item_id: str
    display_name: str
    material: str
    custom_model_data: int
    link: Optional[str] = None


class CollisionDetail(BaseModel):
    type: str  # e.g. "custom_model_data_collision", "texture_collision", "item_model_collision"
    severity: str  # "error", "warning"
    material: str
    custom_model_data: Optional[int] = None
    item_model: Optional[str] = None
    path: Optional[str] = None
    items: List[ConflictItemInfo] = Field(default_factory=list)
    message: str


class PreflightReport(BaseModel):
    is_valid: bool
    has_warnings: bool
    conflicts: List[CollisionDetail] = Field(default_factory=list)
    warnings: List[CollisionDetail] = Field(default_factory=list)
    summary: Dict[str, Any] = Field(default_factory=dict)


class PreflightValidator:
    """Validates pack sources and studio items to detect conflicts before compilation."""

    @staticmethod
    def extract_overrides_from_model_json(file_path: Path) -> List[Tuple[int, str]]:
        """Extracts (custom_model_data, model_name) list from a vanilla model JSON overrides block."""
        overrides: List[Tuple[int, str]] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                for override in data.get("overrides", []):
                    pred = override.get("predicate", {})
                    if "custom_model_data" in pred:
                        cmd = int(pred["custom_model_data"])
                        model = override.get("model", "")
                        overrides.append((cmd, model))
        except Exception:
            pass
        return overrides

    @staticmethod
    def extract_cases_from_item_definition_json(file_path: Path) -> List[Tuple[int, str]]:
        """Extracts (custom_model_data, model_name) list from modern 1.21.2+ ItemDefinition V2 json."""
        results: List[Tuple[int, str]] = []
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                model_obj = data.get("model", {})
                if isinstance(model_obj, dict) and model_obj.get("type") in ("minecraft:select", "select"):
                    prop = model_obj.get("property", "")
                    if "custom_model_data" in prop:
                        for case in model_obj.get("cases", []):
                            when = case.get("when")
                            target = case.get("model", {})
                            target_model = target.get("model", "") if isinstance(target, dict) else ""
                            if isinstance(when, list):
                                for w in when:
                                    try:
                                        results.append((int(w), target_model))
                                    except (ValueError, TypeError):
                                        pass
                            elif when is not None:
                                try:
                                    results.append((int(when), target_model))
                                except (ValueError, TypeError):
                                    pass
        except Exception:
            pass
        return results

    @classmethod
    def validate(
        cls,
        studio_items: List[Any],
        sources: Optional[List[Any]] = None,
        base_dir: Optional[Path] = None
    ) -> PreflightReport:
        conflicts: List[CollisionDetail] = []
        warnings: List[CollisionDetail] = []

        # Map (material, cmd) -> list of occurrences
        cmd_index: Dict[Tuple[str, int], List[ConflictItemInfo]] = {}
        # Map item_model -> list of occurrences
        item_model_index: Dict[str, List[ConflictItemInfo]] = {}

        # 1. Index Studio items
        for item in studio_items:
            # Handle ItemModel, ItemDefinition, or dict
            item_id = getattr(item, "id", None) or (item.get("id") if isinstance(item, dict) else None)
            material = getattr(item, "material", None) or (item.get("material") if isinstance(item, dict) else None)
            cmd = getattr(item, "custom_model_data", None) or (item.get("custom_model_data") if isinstance(item, dict) else None)
            item_model_val = getattr(item, "item_model", None) or (item.get("item_model") if isinstance(item, dict) else None)
            display_name = getattr(item, "display_name", None) or (item.get("display_name") if isinstance(item, dict) else None) or item_id

            if not item_id or not material:
                continue

            mat_key = material.strip().upper()
            cmd_int = int(cmd) if cmd is not None else 0

            if cmd is not None:
                info = ConflictItemInfo(
                    source="Studio",
                    item_id=item_id,
                    display_name=display_name,
                    material=mat_key,
                    custom_model_data=cmd_int,
                    link=f"/studio?item={item_id}"
                )
                cmd_index.setdefault((mat_key, cmd_int), []).append(info)

            effective_item_model = item_model_val.strip().lower() if item_model_val else f"studio:{item_id}"
            im_info = ConflictItemInfo(
                source="Studio",
                item_id=item_id,
                display_name=display_name,
                material=mat_key,
                custom_model_data=cmd_int,
                link=f"/studio?item={item_id}"
            )
            item_model_index.setdefault(effective_item_model, []).append(im_info)

        # 2. Index sources on disk
        if sources:
            for src in sources:
                src_name = getattr(src, "name", None) or (src.get("name") if isinstance(src, dict) else "Unknown Source")
                src_path_str = getattr(src, "storage_path", None) or (src.get("storage_path") if isinstance(src, dict) else None)
                if not src_path_str:
                    continue

                src_path = Path(src_path_str)
                if not src_path.is_absolute() and base_dir:
                    src_path = base_dir / src_path

                if not src_path.exists() or not src_path.is_dir():
                    continue

                # Check legacy assets/minecraft/models/item/*.json
                item_models_dir = src_path / "assets" / "minecraft" / "models" / "item"
                if item_models_dir.exists():
                    for model_file in item_models_dir.glob("*.json"):
                        mat_name = model_file.stem.upper()
                        overrides = cls.extract_overrides_from_model_json(model_file)
                        for cmd_val, target_model in overrides:
                            info = ConflictItemInfo(
                                source=src_name,
                                item_id=target_model or model_file.stem,
                                display_name=target_model or model_file.stem,
                                material=mat_name,
                                custom_model_data=cmd_val,
                                link=f"/packs/sources?source={src_name}"
                            )
                            cmd_index.setdefault((mat_name, cmd_val), []).append(info)

                # Check modern assets/<namespace>/items/*.json (including overlays)
                search_roots = [src_path / "assets"]
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        if sub.name.startswith("overlay") and (sub / "assets").exists():
                            search_roots.append(sub / "assets")
                        elif sub.name == "overlays":
                            for nested in sub.iterdir():
                                if nested.is_dir() and (nested / "assets").exists():
                                    search_roots.append(nested / "assets")

                for assets_root in search_roots:
                    if not assets_root.exists():
                        continue
                    for ns_dir in assets_root.iterdir():
                        if not ns_dir.is_dir():
                            continue
                        ns_name = ns_dir.name
                        items_dir = ns_dir / "items"
                        if items_dir.exists() and items_dir.is_dir():
                            for item_file in items_dir.glob("*.json"):
                                item_id_key = f"{ns_name}:{item_file.stem}"
                                # Extract any select cases on CMD
                                modern_cases = cls.extract_cases_from_item_definition_json(item_file)
                                mat_name = item_file.stem.upper()
                                for cmd_val, target_model in modern_cases:
                                    info = ConflictItemInfo(
                                        source=src_name,
                                        item_id=target_model or item_id_key,
                                        display_name=target_model or item_id_key,
                                        material=mat_name,
                                        custom_model_data=cmd_val,
                                        link=f"/packs/sources?source={src_name}"
                                    )
                                    cmd_index.setdefault((mat_name, cmd_val), []).append(info)

                                if ns_name != "minecraft":
                                    im_info = ConflictItemInfo(
                                        source=src_name,
                                        item_id=item_id_key,
                                        display_name=item_id_key,
                                        material=item_file.stem.upper(),
                                        custom_model_data=0,
                                        link=f"/packs/sources?source={src_name}"
                                    )
                                    item_model_index.setdefault(item_id_key, []).append(im_info)

        # 3. Detect collisions in cmd_index
        total_items_checked = sum(len(items) for items in cmd_index.values()) + sum(len(items) for items in item_model_index.values())
        for (mat, cmd_val), items in cmd_index.items():
            if len(items) > 1:
                sources_involved = {item.source for item in items}
                collision = CollisionDetail(
                    type="custom_model_data_collision",
                    severity="error",
                    material=mat,
                    custom_model_data=cmd_val,
                    items=items,
                    message=f"CustomModelData #{cmd_val} on {mat} is used by {len(items)} items across sources ({', '.join(sources_involved)})"
                )
                conflicts.append(collision)

        # 4. Detect collisions in item_model_index
        for model_id, items in item_model_index.items():
            if len(items) > 1:
                sources_involved = {item.source for item in items}
                collision = CollisionDetail(
                    type="item_model_collision",
                    severity="error",
                    material=items[0].material if items else "UNKNOWN",
                    item_model=model_id,
                    path=model_id,
                    items=items,
                    message=f"item_model identifier '{model_id}' is used by {len(items)} items across sources ({', '.join(sources_involved)})"
                )
                conflicts.append(collision)

        total_cmd_entries = sum(len(items) for items in cmd_index.values())
        total_item_models = sum(len(items) for items in item_model_index.values())

        is_valid = len(conflicts) == 0
        has_warnings = len(warnings) > 0

        summary = {
            "total_cmd_indexed": total_cmd_entries,
            "total_item_models_indexed": total_item_models,
            "total_items_checked": total_cmd_entries + total_item_models,
            "unique_material_cmd_pairs": len(cmd_index),
            "unique_item_models": len(item_model_index),
            "collisions_count": len(conflicts),
            "warnings_count": len(warnings)
        }

        return PreflightReport(
            is_valid=is_valid,
            has_warnings=has_warnings,
            conflicts=conflicts,
            warnings=warnings,
            summary=summary
        )
