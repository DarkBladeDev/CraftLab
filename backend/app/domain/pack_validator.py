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
    type: str  # e.g. "custom_model_data_collision", "texture_collision"
    severity: str  # "error", "warning"
    material: str
    custom_model_data: Optional[int] = None
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

        # 1. Index Studio items
        for item in studio_items:
            # Handle ItemModel, ItemDefinition, or dict
            item_id = getattr(item, "id", None) or (item.get("id") if isinstance(item, dict) else None)
            material = getattr(item, "material", None) or (item.get("material") if isinstance(item, dict) else None)
            cmd = getattr(item, "custom_model_data", None) or (item.get("custom_model_data") if isinstance(item, dict) else None)
            display_name = getattr(item, "display_name", None) or (item.get("display_name") if isinstance(item, dict) else None) or item_id

            if not item_id or not material or cmd is None:
                continue

            mat_key = material.strip().upper()
            cmd_int = int(cmd)
            info = ConflictItemInfo(
                source="Studio",
                item_id=item_id,
                display_name=display_name,
                material=mat_key,
                custom_model_data=cmd_int,
                link=f"/studio?item={item_id}"
            )
            cmd_index.setdefault((mat_key, cmd_int), []).append(info)

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

                # Check assets/minecraft/models/item/*.json
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

        # 3. Detect collisions in cmd_index
        total_items_checked = sum(len(items) for items in cmd_index.values())
        for (mat, cmd_val), items in cmd_index.items():
            if len(items) > 1:
                # We have a collision!
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

        is_valid = len(conflicts) == 0
        has_warnings = len(warnings) > 0

        summary = {
            "total_cmd_indexed": total_items_checked,
            "unique_material_cmd_pairs": len(cmd_index),
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
