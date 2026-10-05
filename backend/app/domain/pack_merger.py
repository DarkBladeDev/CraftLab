import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional


class SemanticMerger:
    """Handles semantic deep-merging of Minecraft resource pack configuration files and models."""

    @staticmethod
    def merge_sounds_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merges sounds.json dictionaries by sound event key."""
        merged = dict(base)
        for key, value in overlay.items():
            if key not in merged:
                merged[key] = value
            else:
                # If both are dicts, shallow merge their properties
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged_event = dict(merged[key])
                    merged_event.update(value)
                    merged[key] = merged_event
                else:
                    merged[key] = value
        return merged

    @staticmethod
    def merge_font_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges font JSON files by concatenating and deduplicating providers."""
        merged = dict(base)
        base_providers = list(base.get("providers", []))
        overlay_providers = list(overlay.get("providers", []))

        # Concatenate and deduplicate by string representation
        seen = set()
        merged_providers = []

        for p in base_providers + overlay_providers:
            key = json.dumps(p, sort_keys=True)
            if key not in seen:
                seen.add(key)
                merged_providers.append(p)

        merged["providers"] = merged_providers
        return merged

    @staticmethod
    def merge_atlas_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges texture atlas JSONs by combining sources."""
        merged = dict(base)
        base_sources = list(base.get("sources", []))
        overlay_sources = list(overlay.get("sources", []))

        seen = set()
        merged_sources = []
        for s in base_sources + overlay_sources:
            key = json.dumps(s, sort_keys=True)
            if key not in seen:
                seen.add(key)
                merged_sources.append(s)

        merged["sources"] = merged_sources
        return merged

    @staticmethod
    def merge_lang_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges translation key-value mappings."""
        merged = dict(base)
        merged.update(overlay)
        return merged

    @staticmethod
    def merge_item_model_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges vanilla item model overrides, sorting them by custom_model_data."""
        merged = dict(base)
        # Inherit top-level properties from overlay if present
        for k in ("parent", "textures", "display"):
            if k in overlay:
                merged[k] = overlay[k]

        # Combine overrides
        overrides_map: Dict[int, Dict[str, Any]] = {}

        # 1. Base overrides
        for ov in base.get("overrides", []):
            cmd = ov.get("predicate", {}).get("custom_model_data")
            if cmd is not None:
                overrides_map[int(cmd)] = ov

        # 2. Overlay overrides (overwrites base if same CMD)
        for ov in overlay.get("overrides", []):
            cmd = ov.get("predicate", {}).get("custom_model_data")
            if cmd is not None:
                overrides_map[int(cmd)] = ov

        # Re-sort overrides by custom_model_data ascending
        sorted_overrides = [overrides_map[cmd] for cmd in sorted(overrides_map.keys())]
        merged["overrides"] = sorted_overrides
        return merged

    @classmethod
    def merge_file(cls, dest_file: Path, src_file: Path):
        """Applies semantic merge or file overwrite depending on the path."""
        rel_path = src_file.name.lower()
        parent_name = src_file.parent.name.lower()

        # Check if destination exists
        if not dest_file.exists():
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            return

        # Both files exist: determine merge strategy
        if rel_path == "sounds.json":
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_sounds_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        elif parent_name == "font" and rel_path.endswith(".json"):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_font_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        elif parent_name == "atlases" and rel_path.endswith(".json"):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_atlas_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        elif parent_name == "lang" and rel_path.endswith(".json"):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_lang_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        elif parent_name == "item" and rel_path.endswith(".json") and "minecraft" in str(dest_file):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_item_model_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        # Default fallback: overwrite with higher priority overlay
        shutil.copy2(src_file, dest_file)

    @classmethod
    def merge_layers_to_directory(
        cls,
        ordered_source_dirs: List[Path],
        output_dir: Path,
        pack_format: int = 34,
        description: str = "Minecraft Content Platform Resource Pack"
    ) -> Dict[str, Any]:
        """Merges multiple layer source directories in order (lowest to highest priority) into output_dir."""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 1. Merge each layer
        for src_dir in ordered_source_dirs:
            if not src_dir.exists() or not src_dir.is_dir():
                continue
            for root, _, files in os.walk(src_dir):
                root_path = Path(root)
                rel_root = root_path.relative_to(src_dir)
                for file_name in files:
                    src_file = root_path / file_name
                    dest_file = output_dir / rel_root / file_name
                    cls.merge_file(dest_file, src_file)

        # 2. Ensure pack.mcmeta exists
        mcmeta_path = output_dir / "pack.mcmeta"
        if not mcmeta_path.exists():
            mcmeta_content = {
                "pack": {
                    "pack_format": pack_format,
                    "description": description
                }
            }
            mcmeta_path.write_text(json.dumps(mcmeta_content, indent=2), encoding="utf-8")

        # 3. Generate summary
        total_textures = len(list(output_dir.glob("assets/*/textures/**/*.png")))
        total_models = len(list(output_dir.glob("assets/*/models/**/*.json")))
        total_sounds = len(list(output_dir.glob("assets/*/sounds/**/*.ogg")))
        total_fonts = len(list(output_dir.glob("assets/*/font/**/*.json")))

        return {
            "total_textures": total_textures,
            "total_models": total_models,
            "total_sounds": total_sounds,
            "total_fonts": total_fonts,
            "pack_format": pack_format
        }
