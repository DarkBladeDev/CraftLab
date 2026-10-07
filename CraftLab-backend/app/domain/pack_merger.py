import json
import os
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ItemModelMapping:
    """Canonical model mapping bridging Legacy (1.21.0-1.21.1) and Modern (1.21.2+) models."""
    material: str  # Upper-case vanilla material, e.g. "DIAMOND_SWORD"
    custom_model_data: int  # Numeric CMD selector
    model_path: str  # Resource location, e.g. "studio:item/ruby_sword"
    item_model: Optional[str] = None  # Modern 1.21.2+ item_model identifier, e.g. "studio:items/ruby_sword"


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
        for k in ("parent", "textures", "display"):
            if k in overlay:
                merged[k] = overlay[k]

        overrides_map: Dict[int, Dict[str, Any]] = {}
        for ov in base.get("overrides", []):
            cmd = ov.get("predicate", {}).get("custom_model_data")
            if cmd is not None:
                overrides_map[int(cmd)] = ov

        for ov in overlay.get("overrides", []):
            cmd = ov.get("predicate", {}).get("custom_model_data")
            if cmd is not None:
                overrides_map[int(cmd)] = ov

        sorted_overrides = [overrides_map[cmd] for cmd in sorted(overrides_map.keys())]
        merged["overrides"] = sorted_overrides
        return merged

    @staticmethod
    def merge_item_definition_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges modern 1.21.2+ Item Definition V2 JSONs, combining select cases."""
        merged = dict(base)
        base_model = base.get("model", {})
        overlay_model = overlay.get("model", {})

        if (
            isinstance(base_model, dict)
            and isinstance(overlay_model, dict)
            and base_model.get("type") in ("minecraft:select", "select")
            and overlay_model.get("type") in ("minecraft:select", "select")
            and "custom_model_data" in base_model.get("property", "")
            and "custom_model_data" in overlay_model.get("property", "")
        ):
            cases_map: Dict[str, Dict[str, Any]] = {}
            for c in base_model.get("cases", []):
                w = c.get("when")
                if w is not None:
                    cases_map[str(w)] = c

            for c in overlay_model.get("cases", []):
                w = c.get("when")
                if w is not None:
                    cases_map[str(w)] = c

            # Sort cases by integer when if possible, else string
            def sort_key(item):
                k = item[0]
                try:
                    return (0, int(k))
                except ValueError:
                    return (1, k)

            sorted_cases = [cases_map[k] for k, _ in sorted(cases_map.items(), key=sort_key)]

            merged_model = dict(base_model)
            merged_model.update(overlay_model)
            merged_model["cases"] = sorted_cases
            merged["model"] = merged_model
            return merged

        # Fallback: overlay values replace base
        merged.update(overlay)
        return merged

    @classmethod
    def extract_mappings_from_model_json(cls, material: str, data: Dict[str, Any]) -> List[ItemModelMapping]:
        """Extracts canonical mappings from a legacy models/item/*.json overrides block."""
        mappings: List[ItemModelMapping] = []
        for ov in data.get("overrides", []):
            cmd = ov.get("predicate", {}).get("custom_model_data")
            model = ov.get("model", "")
            if cmd is not None and model:
                mappings.append(ItemModelMapping(
                    material=material.upper(),
                    custom_model_data=int(cmd),
                    model_path=model
                ))
        return mappings

    @classmethod
    def extract_mappings_from_item_definition_json(cls, material: str, data: Dict[str, Any]) -> List[ItemModelMapping]:
        """Extracts canonical mappings from a modern items/*.json definition."""
        mappings: List[ItemModelMapping] = []
        model_obj = data.get("model", {})
        if isinstance(model_obj, dict) and model_obj.get("type") in ("minecraft:select", "select"):
            if "custom_model_data" in model_obj.get("property", ""):
                for c in model_obj.get("cases", []):
                    when = c.get("when")
                    target = c.get("model", {})
                    target_model = target.get("model", "") if isinstance(target, dict) else ""
                    if when is not None and target_model:
                        when_list = when if isinstance(when, list) else [when]
                        for w in when_list:
                            try:
                                mappings.append(ItemModelMapping(
                                    material=material.upper(),
                                    custom_model_data=int(w),
                                    model_path=target_model
                                ))
                            except (ValueError, TypeError):
                                pass
        return mappings

    @classmethod
    def build_legacy_item_model(
        cls,
        material: str,
        mappings: List[ItemModelMapping],
        base_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Builds a legacy models/item/<material>.json structure with overrides."""
        mat_lower = material.lower()
        res = dict(base_dict) if base_dict else {
            "parent": "item/handheld" if any(w in material for w in ("SWORD", "AXE", "HOE", "SHOVEL", "PICKAXE")) else "item/generated",
            "textures": {"layer0": f"minecraft:item/{mat_lower}"}
        }

        # Build overrides from mappings
        overrides_map: Dict[int, Dict[str, Any]] = {}
        for ov in res.get("overrides", []):
            cmd = ov.get("predicate", {}).get("custom_model_data")
            if cmd is not None:
                overrides_map[int(cmd)] = ov

        for m in mappings:
            overrides_map[m.custom_model_data] = {
                "predicate": {"custom_model_data": m.custom_model_data},
                "model": m.model_path
            }

        res["overrides"] = [overrides_map[cmd] for cmd in sorted(overrides_map.keys())]
        return res

    @classmethod
    def build_modern_item_definition(
        cls,
        material: str,
        mappings: List[ItemModelMapping],
        base_dict: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Builds a modern items/<material>.json ItemDefinition conforming to vanilla-mcdoc."""
        mat_lower = material.lower()
        cases_map: Dict[str, Dict[str, Any]] = {}

        if base_dict and isinstance(base_dict.get("model"), dict):
            for c in base_dict["model"].get("cases", []):
                w = c.get("when")
                if w is not None:
                    cases_map[str(w)] = c

        for m in mappings:
            cases_map[str(m.custom_model_data)] = {
                "when": str(m.custom_model_data),
                "model": {
                    "type": "minecraft:model",
                    "model": m.model_path
                }
            }

        def sort_key(item):
            k = item[0]
            try:
                return (0, int(k))
            except ValueError:
                return (1, k)

        sorted_cases = [cases_map[k] for k, _ in sorted(cases_map.items(), key=sort_key)]

        return {
            "model": {
                "type": "minecraft:select",
                "property": "minecraft:custom_model_data",
                "cases": sorted_cases,
                "fallback": {
                    "type": "minecraft:model",
                    "model": f"minecraft:item/{mat_lower}"
                }
            }
        }

    @classmethod
    def apply_dual_projection(
        cls,
        output_dir: Path,
        overlay_dir_name: str = "overlay_v1_21_2"
    ):
        """
        Cross-projects legacy models/item/<mat>.json and modern items/<mat>.json across base and overlay.
        Ensures both 1.21.1 clients and 1.21.2-1.21.11 clients receive complete definitions.
        """
        legacy_models_dir = output_dir / "assets" / "minecraft" / "models" / "item"
        modern_overlay_items_dir = output_dir / overlay_dir_name / "assets" / "minecraft" / "items"
        alt_overlay_items_dir = output_dir / "overlays" / overlay_dir_name / "assets" / "minecraft" / "items"

        # Material -> List[ItemModelMapping]
        collected_mappings: Dict[str, Dict[int, ItemModelMapping]] = {}
        legacy_bases: Dict[str, Dict[str, Any]] = {}
        modern_bases: Dict[str, Dict[str, Any]] = {}

        # 1. Harvest from legacy base
        if legacy_models_dir.exists():
            for f in legacy_models_dir.glob("*.json"):
                mat = f.stem.upper()
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    legacy_bases[mat] = data
                    for m in cls.extract_mappings_from_model_json(mat, data):
                        collected_mappings.setdefault(mat, {})[m.custom_model_data] = m
                except Exception:
                    pass

        # 2. Harvest from modern overlay (check both root overlay and nested overlays/)
        for overlay_check_dir in (modern_overlay_items_dir, alt_overlay_items_dir):
            if overlay_check_dir.exists():
                for f in overlay_check_dir.glob("*.json"):
                    mat = f.stem.upper()
                    try:
                        data = json.loads(f.read_text(encoding="utf-8"))
                        modern_bases[mat] = data
                        for m in cls.extract_mappings_from_item_definition_json(mat, data):
                            collected_mappings.setdefault(mat, {})[m.custom_model_data] = m
                    except Exception:
                        pass

        # 3. Harvest from modern base (if a modern pack put items/ in base assets/minecraft/items)
        base_items_dir = output_dir / "assets" / "minecraft" / "items"
        if base_items_dir.exists():
            for f in base_items_dir.glob("*.json"):
                mat = f.stem.upper()
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    for m in cls.extract_mappings_from_item_definition_json(mat, data):
                        collected_mappings.setdefault(mat, {})[m.custom_model_data] = m
                except Exception:
                    pass

        if not collected_mappings:
            return

        # 4. Generate/synchronize both legacy base and modern overlay
        legacy_models_dir.mkdir(parents=True, exist_ok=True)
        modern_overlay_items_dir.mkdir(parents=True, exist_ok=True)

        for mat, mapping_dict in collected_mappings.items():
            mappings = list(mapping_dict.values())

            # Synthesize legacy base
            legacy_content = cls.build_legacy_item_model(mat, mappings, legacy_bases.get(mat))
            legacy_file = legacy_models_dir / f"{mat.lower()}.json"
            legacy_file.write_text(json.dumps(legacy_content, indent=2), encoding="utf-8")

            # Synthesize modern overlay
            modern_content = cls.build_modern_item_definition(mat, mappings, modern_bases.get(mat))
            modern_file = modern_overlay_items_dir / f"{mat.lower()}.json"
            modern_file.write_text(json.dumps(modern_content, indent=2), encoding="utf-8")

    @classmethod
    def merge_file(cls, dest_file: Path, src_file: Path):
        """Applies semantic merge or file overwrite depending on the path."""
        rel_path = src_file.name.lower()
        parent_name = src_file.parent.name.lower()

        if not dest_file.exists():
            dest_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dest_file)
            return

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

        elif parent_name == "item" and rel_path.endswith(".json") and "models" in str(dest_file):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_item_model_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        elif parent_name == "items" and rel_path.endswith(".json"):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_item_definition_json(base_data, overlay_data)
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
        description: str = "Universal Multi-Version Resource Pack (1.21.1 - 1.21.11)"
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

        # 2. Apply Dual Projection (ensures both legacy models/item and overlay items/ exist)
        cls.apply_dual_projection(output_dir, overlay_dir_name="overlay_v1_21_2")

        # 3. Ensure multi-version pack.mcmeta exists
        mcmeta_path = output_dir / "pack.mcmeta"
        mcmeta_content = {
            "pack": {
                "pack_format": pack_format,
                "description": description,
                "supported_formats": {
                    "min_inclusive": 34,
                    "max_inclusive": 65
                },
                "min_format": 34,
                "max_format": 65
            },
            "overlays": {
                "entries": [
                    {
                        "formats": {
                            "min_inclusive": 42,
                            "max_inclusive": 65
                        },
                        "min_format": 42,
                        "max_format": 65,
                        "directory": "overlay_v1_21_2"
                    }
                ]
            }
        }
        mcmeta_path.write_text(json.dumps(mcmeta_content, indent=2), encoding="utf-8")

        # 4. Generate summary
        total_textures = len(list(output_dir.glob("assets/*/textures/**/*.png")))
        total_models = len(list(output_dir.glob("assets/*/models/**/*.json")))
        total_items_definitions = (
            len(list(output_dir.glob("overlay_*/assets/*/items/**/*.json"))) +
            len(list(output_dir.glob("overlays/*/assets/*/items/**/*.json"))) +
            len(list(output_dir.glob("assets/*/items/**/*.json")))
        )
        total_sounds = len(list(output_dir.glob("assets/*/sounds/**/*.ogg")))
        total_fonts = len(list(output_dir.glob("assets/*/font/**/*.json")))

        return {
            "total_textures": total_textures,
            "total_models": total_models,
            "total_items_definitions": total_items_definitions,
            "total_sounds": total_sounds,
            "total_fonts": total_fonts,
            "pack_format": pack_format,
            "is_hybrid_multiversion": True
        }
