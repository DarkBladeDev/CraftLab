import json
import os
import re
import shutil
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class ItemModelMapping:
    """Canonical model mapping bridging Legacy (1.21.0-1.21.1) and Modern (1.21.2+) models."""
    material: str  # Upper-case vanilla material, e.g. "DIAMOND_SWORD"
    custom_model_data: int  # Numeric CMD selector
    model_path: str  # Resource location, e.g. "studio:item/ruby_sword"
    item_model: Optional[str] = None  # Modern 1.21.2+ item_model identifier, e.g. "studio:items/ruby_sword"


class PackManifestInspector:
    """Parses pack.mcmeta on ingested packs and normalizes external overlay structures into canonical CraftLab overlays."""

    CANONICAL_ROOT = "root"
    CANONICAL_V1_21_2 = "overlay_v1_21_2"
    CANONICAL_V1_21_4 = "overlay_v1_21_4"

    @classmethod
    def resolve_format_range(cls, formats_val: Any) -> Tuple[Optional[int], Optional[int]]:
        """Extracts (min_format, max_format) from a formats value (int, dict, or list)."""
        if isinstance(formats_val, int):
            return formats_val, formats_val
        elif isinstance(formats_val, dict):
            min_f = formats_val.get("min_inclusive")
            max_f = formats_val.get("max_inclusive")
            return min_f, max_f
        elif isinstance(formats_val, list) and formats_val:
            try:
                ints = [int(x) for x in formats_val]
                return min(ints), max(ints)
            except Exception:
                return None, None
        return None, None

    @classmethod
    def map_range_to_canonical_target(cls, min_format: Optional[int], max_format: Optional[int]) -> str:
        """
        Maps a format range to CraftLab canonical target directory:
        - min_format >= 46: overlay_v1_21_4
        - min_format >= 42: overlay_v1_21_2
        - otherwise: root
        """
        if min_format is not None:
            if min_format >= 46:
                return cls.CANONICAL_V1_21_4
            if min_format >= 42:
                return cls.CANONICAL_V1_21_2
        return cls.CANONICAL_ROOT

    @classmethod
    def parse_manifest(cls, source_dir: Path) -> Dict[str, Any]:
        """Reads and parses pack.mcmeta from source_dir if present."""
        mcmeta_path = source_dir / "pack.mcmeta"
        if not mcmeta_path.exists():
            return {}
        try:
            return json.loads(mcmeta_path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    @classmethod
    def normalize_extracted_pack(cls, source_dir: Path) -> List[Dict[str, Any]]:
        """
        Inspects source_dir for pack.mcmeta overlays.
        Remaps any foreign overlay directories into canonical directories (overlay_v1_21_2, overlay_v1_21_4, or root).
        Returns a list of mapping actions performed.
        """
        data = cls.parse_manifest(source_dir)
        overlays = data.get("overlays", {}).get("entries", [])
        if not overlays or not isinstance(overlays, list):
            return []

        actions: List[Dict[str, Any]] = []

        for entry in overlays:
            if not isinstance(entry, dict):
                continue
            dir_name = entry.get("directory")
            if not dir_name:
                continue

            formats_val = entry.get("formats")
            min_f, max_f = cls.resolve_format_range(formats_val)
            if min_f is None:
                min_f = entry.get("min_format")
            if max_f is None:
                max_f = entry.get("max_format")

            canonical_target = cls.map_range_to_canonical_target(min_f, max_f)

            source_overlay_dir = source_dir / dir_name
            if not source_overlay_dir.exists() or not source_overlay_dir.is_dir():
                alt_source_dir = source_dir / "overlays" / dir_name
                if alt_source_dir.exists() and alt_source_dir.is_dir():
                    source_overlay_dir = alt_source_dir
                else:
                    continue

            if canonical_target == dir_name or (canonical_target == cls.CANONICAL_ROOT and dir_name == "assets"):
                continue

            if canonical_target == cls.CANONICAL_ROOT:
                target_overlay_dir = source_dir / "assets"
            else:
                target_overlay_dir = source_dir / canonical_target

            target_overlay_dir.mkdir(parents=True, exist_ok=True)

            for root, _, files in os.walk(source_overlay_dir):
                root_path = Path(root)
                rel_root = root_path.relative_to(source_overlay_dir)
                for f in files:
                    s_file = root_path / f
                    d_file = target_overlay_dir / rel_root / f
                    d_file.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(s_file, d_file)

            shutil.rmtree(source_overlay_dir, ignore_errors=True)

            actions.append({
                "original_directory": dir_name,
                "canonical_target": canonical_target,
                "min_format": min_f,
                "max_format": max_f
            })

        return actions


class AtlasSynthesizer:
    """Discovers custom namespaces from models and textures and auto-synthesizes blocks.json and gui.json atlases."""

    @classmethod
    def collect_texture_references_from_models(cls, directory: Path) -> Set[str]:
        """Scans directory for JSON models and item definitions and returns all referenced texture strings."""
        refs: Set[str] = set()
        for root, _, files in os.walk(directory):
            root_p = Path(root)
            for f in files:
                if f.lower().endswith(".json"):
                    file_p = root_p / f
                    try:
                        data = json.loads(file_p.read_text(encoding="utf-8"))
                        tex_dict = data.get("textures", {})
                        if isinstance(tex_dict, dict):
                            for v in tex_dict.values():
                                if isinstance(v, str) and not v.startswith("#"):
                                    refs.add(v.strip())
                    except Exception:
                        pass
        return refs

    @classmethod
    def collect_gui_sprite_namespaces(cls, directory: Path) -> Set[str]:
        """Finds namespaces containing GUI sprites under textures/gui/sprites/."""
        namespaces: Set[str] = set()
        for assets_dir in directory.glob("**/assets/*"):
            if assets_dir.is_dir():
                ns = assets_dir.name
                sprites_dir = assets_dir / "textures" / "gui" / "sprites"
                if sprites_dir.exists() and any(sprites_dir.iterdir()):
                    namespaces.add(ns)
        return namespaces

    @classmethod
    def synthesize_blocks_atlas_sources(cls, texture_refs: Set[str]) -> List[Dict[str, Any]]:
        """Generates compact directory and single sources for blocks.json from texture references."""
        sources: List[Dict[str, Any]] = []
        seen_dirs: Set[Tuple[str, str]] = set()

        for ref in sorted(texture_refs):
            if ":" not in ref:
                continue
            ns, path_part = ref.split(":", 1)
            if ns == "minecraft":
                continue

            if "/" in path_part:
                first_seg = path_part.split("/")[0]
                dir_key = (f"{ns}:{first_seg}", f"{first_seg}/")
                if dir_key not in seen_dirs:
                    seen_dirs.add(dir_key)
                    sources.append({
                        "type": "directory",
                        "source": dir_key[0],
                        "prefix": dir_key[1]
                    })
            else:
                sources.append({
                    "type": "single",
                    "resource": ref
                })
        return sources

    @classmethod
    def synthesize_gui_atlas_sources(cls, gui_namespaces: Set[str]) -> List[Dict[str, Any]]:
        """Generates directory sources for gui.json from discovered GUI sprite namespaces."""
        sources: List[Dict[str, Any]] = []
        for ns in sorted(gui_namespaces):
            if ns == "minecraft":
                sources.append({
                    "type": "directory",
                    "source": "gui/sprites",
                    "prefix": ""
                })
            else:
                sources.append({
                    "type": "directory",
                    "source": f"{ns}:gui/sprites",
                    "prefix": ""
                })
        return sources

    @classmethod
    def consolidate_sources(cls, existing_sources: List[Dict[str, Any]], new_sources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Combines and deduplicates atlas sources, pruning single sources covered by directory sources."""
        all_sources = list(existing_sources) + list(new_sources)
        seen_json = set()
        unique_sources: List[Dict[str, Any]] = []

        for s in all_sources:
            s_key = json.dumps(s, sort_keys=True)
            if s_key not in seen_json:
                seen_json.add(s_key)
                unique_sources.append(s)

        dir_prefixes: List[Tuple[str, str]] = []
        for s in unique_sources:
            if s.get("type") == "directory":
                src_val = s.get("source", "")
                prefix = s.get("prefix", "")
                ns = src_val.split(":")[0] if ":" in src_val else "minecraft"
                dir_prefixes.append((ns, prefix))

        consolidated: List[Dict[str, Any]] = []
        for s in unique_sources:
            if s.get("type") == "single":
                res = s.get("resource", "")
                ns, path_part = res.split(":", 1) if ":" in res else ("minecraft", res)
                covered = any(d_ns == ns and path_part.startswith(d_prefix) for d_ns, d_prefix in dir_prefixes if d_prefix)
                if not covered:
                    consolidated.append(s)
            else:
                consolidated.append(s)

        return consolidated


class ShaderRouter:
    """
    Classifies core shaders and routes 1.21.4+ modern shader programs to overlay_v1_21_4.
    Preserves legacy core shaders (1.21.0 - 1.21.3) in the root assets directory.
    """

    @classmethod
    def _check_content_is_modern(cls, suffix: str, content: str) -> bool:
        if suffix == ".json":
            try:
                data = json.loads(content)
                if isinstance(data, dict):
                    if data.get("format") and int(data["format"]) >= 46:
                        return True
                    if data.get("min_format") and int(data["min_format"]) >= 46:
                        return True
                    if data.get("pack_format") and int(data["pack_format"]) >= 46:
                        return True
                    ver = str(data.get("version", ""))
                    if "1.21.4" in ver or "46" in ver:
                        return True
                    target = str(data.get("target", ""))
                    if "1.21.4" in target or "46" in target:
                        return True
            except Exception:
                pass
            if any(k in content for k in ("1.21.4", "format 46", "format: 46", "min_format: 46", "pack_format: 46")):
                return True

        elif suffix in (".vsh", ".fsh", ".glsl"):
            if any(k in content for k in ("1.21.4", "format 46", "format: 46", "v1.21.4", "MC_VERSION 12104")):
                return True
            m = re.search(r"#version\s+(\d+)", content)
            if m:
                try:
                    ver_num = int(m.group(1))
                    if ver_num > 150:
                        return True
                except ValueError:
                    pass

        return False

    @classmethod
    def is_modern_shader(cls, file_path: Path, content: Optional[str] = None) -> bool:
        """
        Determines whether a shader file (.vsh, .fsh, .json) targets Minecraft 1.21.4+ (format 46+).
        Checks directory location, explicit format/version fields, GLSL version headers,
        and sibling companion files for the shader program.
        """
        parts_lower = [p.lower() for p in file_path.parts]
        if "overlay_v1_21_4" in parts_lower:
            return True
        if any(marker in file_path.name.lower() or marker in parts_lower for marker in ("1.21.4", "format_46", "format46")):
            return True

        # Check file content
        suffix = file_path.suffix.lower()
        if content is None and file_path.exists() and file_path.is_file():
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                content = ""

        if content and cls._check_content_is_modern(suffix, content):
            return True

        # Check companion files with the same stem in the same folder
        if file_path.exists() and file_path.is_file():
            stem = file_path.stem
            parent = file_path.parent
            for ext in (".json", ".vsh", ".fsh"):
                if ext == suffix:
                    continue
                sibling = parent / f"{stem}{ext}"
                if sibling.exists():
                    try:
                        sib_content = sibling.read_text(encoding="utf-8", errors="ignore")
                        if cls._check_content_is_modern(ext, sib_content):
                            return True
                    except Exception:
                        pass

        return False

    @classmethod
    def resolve_destination(
        cls,
        src_file: Path,
        rel_root: Path,
        output_dir: Path,
        target_overlay: str = "overlay_v1_21_4"
    ) -> Path:
        """
        Resolves the target destination file for a source file.
        If the file is a core shader (.vsh, .fsh, .json) targeting 1.21.4+ and not already
        in an overlay, routes it to overlay_v1_21_4/assets/minecraft/shaders/core/...
        """
        norm_parts = [p.lower() for p in rel_root.parts]
        # If already inside an overlay directory, preserve its relative path
        if any(p.startswith("overlay_") or p.startswith("overlays") for p in norm_parts):
            return output_dir / rel_root / src_file.name

        # Check if located under shaders/core
        if "shaders" in norm_parts and "core" in norm_parts and src_file.suffix.lower() in (".vsh", ".fsh", ".json"):
            if cls.is_modern_shader(src_file):
                return output_dir / target_overlay / rel_root / src_file.name

        return output_dir / rel_root / src_file.name

    @classmethod
    def route_shaders_in_directory(
        cls,
        output_dir: Path,
        target_overlay: str = "overlay_v1_21_4"
    ) -> List[Dict[str, Any]]:
        """
        Scans root assets for modern 1.21.4+ shaders and relocates them to overlay_v1_21_4.
        """
        routed: List[Dict[str, Any]] = []
        root_shaders_dirs = list(output_dir.glob("assets/*/shaders/core"))
        for s_dir in root_shaders_dirs:
            if not s_dir.exists() or not s_dir.is_dir():
                continue

            programs: Dict[str, List[Path]] = {}
            for f in list(s_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in (".vsh", ".fsh", ".json"):
                    programs.setdefault(f.stem, []).append(f)

            for stem, files in programs.items():
                if any(cls.is_modern_shader(f) for f in files):
                    for f in files:
                        rel = f.relative_to(output_dir)
                        target_file = output_dir / target_overlay / rel
                        target_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(f), str(target_file))
                        routed.append({
                            "program": stem,
                            "file": f.name,
                            "from": str(f),
                            "to": str(target_file)
                        })
        return routed


class SemanticMerger:
    """Handles semantic deep-merging of Minecraft resource pack configuration files and models."""

    @staticmethod
    def merge_sounds_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Deep merges sounds.json dictionaries by sound event key and combines sound variants."""
        merged = dict(base)
        for key, value in overlay.items():
            if key not in merged:
                merged[key] = value
            else:
                if isinstance(merged[key], dict) and isinstance(value, dict):
                    merged_event = dict(merged[key])
                    merged_event.update(value)
                    base_sounds = merged[key].get("sounds", [])
                    overlay_sounds = value.get("sounds", [])
                    if isinstance(base_sounds, list) and isinstance(overlay_sounds, list):
                        combined = list(base_sounds)
                        seen_names = {s.get("name") if isinstance(s, dict) else s for s in base_sounds}
                        for s in overlay_sounds:
                            s_name = s.get("name") if isinstance(s, dict) else s
                            if s_name not in seen_names:
                                combined.append(s)
                                seen_names.add(s_name)
                        merged_event["sounds"] = combined
                    merged[key] = merged_event
                else:
                    merged[key] = value
        return merged

    @staticmethod
    def merge_font_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges font JSON files by concatenating and deduplicating providers by character."""
        merged = dict(base)
        base_providers = list(base.get("providers", []))
        overlay_providers = list(overlay.get("providers", []))

        overlay_chars = set()
        for p in overlay_providers:
            for row in p.get("chars", []):
                for ch in row:
                    if ch:
                        overlay_chars.add(ch)

        merged_providers = []
        for p in base_providers:
            chars = p.get("chars", [])
            has_conflict = any(ch in overlay_chars for row in chars for ch in row if ch)
            if not has_conflict:
                merged_providers.append(p)

        merged_providers.extend(overlay_providers)
        merged["providers"] = merged_providers
        return merged

    @staticmethod
    def merge_particles_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges particle definition JSONs combining texture lists."""
        merged = dict(base)
        base_textures = list(base.get("textures", []))
        overlay_textures = list(overlay.get("textures", []))
        seen = set(base_textures)
        combined = list(base_textures)
        for t in overlay_textures:
            if t not in seen:
                combined.append(t)
                seen.add(t)
        merged["textures"] = combined
        if "_emitter" in overlay:
            merged["_emitter"] = overlay["_emitter"]
        return merged

    @staticmethod
    def merge_equipment_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges 1.21.4+ equipment model descriptors."""
        from app.domain.equipment import normalize_legacy_equipment_data
        base_norm = normalize_legacy_equipment_data(base)
        overlay_norm = normalize_legacy_equipment_data(overlay)

        merged = dict(base_norm)
        base_layers = dict(base_norm.get("layers", {}))
        overlay_layers = dict(overlay_norm.get("layers", {}))

        for l_type, l_list in overlay_layers.items():
            base_layers[l_type] = l_list
        merged["layers"] = base_layers

        for k, v in overlay_norm.items():
            if k != "layers":
                merged[k] = v
        return merged

    @staticmethod
    def merge_atlas_json(base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """Merges texture atlas JSONs by combining and consolidating sources."""
        merged = dict(base)
        base_sources = list(base.get("sources", []))
        overlay_sources = list(overlay.get("sources", []))

        merged["sources"] = AtlasSynthesizer.consolidate_sources(base_sources, overlay_sources)
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

        # 2. Harvest from modern overlays (check overlay_v1_21_2, overlay_v1_21_4, and nested overlays/)
        overlay_dirs_to_check = [
            modern_overlay_items_dir,
            alt_overlay_items_dir,
            output_dir / "overlay_v1_21_4" / "assets" / "minecraft" / "items",
            output_dir / "overlays" / "overlay_v1_21_4" / "assets" / "minecraft" / "items",
        ]
        for ov_dir in output_dir.glob("overlay_*"):
            if ov_dir.is_dir():
                overlay_dirs_to_check.append(ov_dir / "assets" / "minecraft" / "items")
        for ov_dir in output_dir.glob("overlays/*"):
            if ov_dir.is_dir():
                overlay_dirs_to_check.append(ov_dir / "assets" / "minecraft" / "items")

        seen_dirs = set()
        for overlay_check_dir in overlay_dirs_to_check:
            dir_str = str(overlay_check_dir.resolve()) if overlay_check_dir.exists() else str(overlay_check_dir)
            if dir_str in seen_dirs:
                continue
            seen_dirs.add(dir_str)
            if overlay_check_dir.exists() and overlay_check_dir.is_dir():
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

        elif parent_name == "particles" and rel_path.endswith(".json"):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_particles_json(base_data, overlay_data)
                dest_file.write_text(json.dumps(merged, indent=2), encoding="utf-8")
                return
            except Exception:
                pass

        elif parent_name == "equipment" and rel_path.endswith(".json"):
            try:
                base_data = json.loads(dest_file.read_text(encoding="utf-8"))
                overlay_data = json.loads(src_file.read_text(encoding="utf-8"))
                merged = cls.merge_equipment_json(base_data, overlay_data)
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
        max_inclusive: int = 65,
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
                    dest_file = ShaderRouter.resolve_destination(src_file, rel_root, output_dir)
                    cls.merge_file(dest_file, src_file)

        # 2. Shader Routing Sweep (ensures modern 1.21.4+ shaders in root assets are relocated)
        ShaderRouter.route_shaders_in_directory(output_dir, target_overlay="overlay_v1_21_4")

        # 3. Apply Dual Projection (ensures both legacy models/item and overlay items/ exist)
        cls.apply_dual_projection(output_dir, overlay_dir_name="overlay_v1_21_2")

        # 4. Auto-synthesize texture atlases (blocks.json and gui.json)
        cls.auto_synthesize_atlases(output_dir)

        # 4b. Project custom namespace font/default.json bitmap providers into assets/minecraft/font/default.json
        cls.project_custom_namespace_fonts(output_dir)

        # Stage canonical equipment models into overlay_v1_21_2 as legacy models/equipment/*.json mirror
        overlay_eq_dir = output_dir / "overlay_v1_21_2"
        for eq_file in output_dir.glob("assets/*/equipment/*.json"):
            rel_parts = eq_file.relative_to(output_dir).parts
            if len(rel_parts) >= 4 and rel_parts[0] == "assets" and rel_parts[2] == "equipment":
                ns = rel_parts[1]
                fname = rel_parts[3]
                target_overlay_file = overlay_eq_dir / "assets" / ns / "models" / "equipment" / fname
                target_overlay_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_overlay_file.exists():
                    shutil.copy2(eq_file, target_overlay_file)

        # Also support any legacy models/equipment/*.json files
        for legacy_eq in output_dir.glob("assets/*/models/equipment/*.json"):
            rel_parts = legacy_eq.relative_to(output_dir).parts
            if len(rel_parts) >= 5 and rel_parts[0] == "assets" and rel_parts[2] == "models" and rel_parts[3] == "equipment":
                ns = rel_parts[1]
                fname = rel_parts[4]
                canonical_dest = output_dir / "assets" / ns / "equipment" / fname
                if not canonical_dest.exists():
                    canonical_dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(legacy_eq, canonical_dest)
                target_overlay_file = overlay_eq_dir / "assets" / ns / "models" / "equipment" / fname
                target_overlay_file.parent.mkdir(parents=True, exist_ok=True)
                if not target_overlay_file.exists():
                    shutil.copy2(legacy_eq, target_overlay_file)

        # 5. Ensure multi-version pack.mcmeta exists
        from app.domain.pack_compiler import DeterministicPackCompiler
        DeterministicPackCompiler.write_multiversion_mcmeta(
            target_dir=output_dir,
            pack_format=pack_format,
            max_inclusive=max_inclusive,
            description=description
        )

        # 6. Generate summary
        total_textures = len(list(output_dir.glob("assets/*/textures/**/*.png")))
        total_models = len(list(output_dir.glob("assets/*/models/**/*.json")))
        total_items_definitions = (
            len(list(output_dir.glob("overlay_*/assets/*/items/**/*.json"))) +
            len(list(output_dir.glob("overlays/*/assets/*/items/**/*.json"))) +
            len(list(output_dir.glob("assets/*/items/**/*.json")))
        )
        total_sounds = len(list(output_dir.glob("assets/*/sounds/**/*.ogg")))
        total_fonts = len(list(output_dir.glob("assets/*/font/**/*.json")))
        total_equipment = len(set(
            [f.stem for f in output_dir.glob("assets/*/equipment/*.json")] +
            [f.stem for f in output_dir.glob("assets/*/models/equipment/*.json")]
        ))
        total_particles = len(list(output_dir.glob("assets/*/particles/*.json")))

        return {
            "total_textures": total_textures,
            "total_models": total_models,
            "total_items_definitions": total_items_definitions,
            "total_sounds": total_sounds,
            "total_fonts": total_fonts,
            "total_equipment": total_equipment,
            "total_particles": total_particles,
            "pack_format": pack_format,
            "is_hybrid_multiversion": True
        }

    @classmethod
    def project_custom_namespace_fonts(cls, output_dir: Path):
        """
        Projects bitmap font providers from custom namespace assets/<ns>/font/default.json
        into assets/minecraft/font/default.json with normalized '<ns>:' file references so
        raw PUA characters (e.g. from PlaceholderAPI) render directly in Minecraft's default font.
        """
        projected_providers: List[Dict[str, Any]] = []
        for font_file in sorted(output_dir.glob("assets/*/font/default.json")):
            rel_parts = font_file.relative_to(output_dir).parts
            if len(rel_parts) < 4 or rel_parts[0] != "assets":
                continue
            ns = rel_parts[1]
            if ns == "minecraft":
                continue

            try:
                font_data = json.loads(font_file.read_text(encoding="utf-8"))
            except Exception:
                continue

            for p in font_data.get("providers", []):
                if not isinstance(p, dict) or p.get("type") != "bitmap":
                    continue
                proj_p = dict(p)
                file_ref = str(proj_p.get("file", "")).strip()
                if file_ref and ":" not in file_ref:
                    proj_p["file"] = f"{ns}:{file_ref}"
                projected_providers.append(proj_p)

        if not projected_providers:
            return

        mc_font_path = output_dir / "assets" / "minecraft" / "font" / "default.json"
        base_mc_font: Dict[str, Any] = {"providers": []}
        if mc_font_path.exists():
            try:
                base_mc_font = json.loads(mc_font_path.read_text(encoding="utf-8"))
            except Exception:
                base_mc_font = {"providers": []}

        merged_mc_font = cls.merge_font_json(base_mc_font, {"providers": projected_providers})
        mc_font_path.parent.mkdir(parents=True, exist_ok=True)
        mc_font_path.write_text(json.dumps(merged_mc_font, indent=2, ensure_ascii=False), encoding="utf-8")

    @classmethod
    def auto_synthesize_atlases(cls, output_dir: Path):
        """Auto-discovers custom texture references and GUI sprites, injecting minimal atlas sources into blocks.json and gui.json."""
        # 1. Blocks Atlas
        texture_refs = AtlasSynthesizer.collect_texture_references_from_models(output_dir)
        new_block_sources = AtlasSynthesizer.synthesize_blocks_atlas_sources(texture_refs)
        if new_block_sources:
            blocks_atlas_path = output_dir / "assets" / "minecraft" / "atlases" / "blocks.json"
            base_blocks = {}
            if blocks_atlas_path.exists():
                try:
                    base_blocks = json.loads(blocks_atlas_path.read_text(encoding="utf-8"))
                except Exception:
                    base_blocks = {}
            merged_blocks = cls.merge_atlas_json(base_blocks, {"sources": new_block_sources})
            blocks_atlas_path.parent.mkdir(parents=True, exist_ok=True)
            blocks_atlas_path.write_text(json.dumps(merged_blocks, indent=2), encoding="utf-8")

        # 2. GUI Atlas
        gui_namespaces = AtlasSynthesizer.collect_gui_sprite_namespaces(output_dir)
        new_gui_sources = AtlasSynthesizer.synthesize_gui_atlas_sources(gui_namespaces)
        if new_gui_sources:
            gui_atlas_path = output_dir / "assets" / "minecraft" / "atlases" / "gui.json"
            base_gui = {}
            if gui_atlas_path.exists():
                try:
                    base_gui = json.loads(gui_atlas_path.read_text(encoding="utf-8"))
                except Exception:
                    base_gui = {}
            merged_gui = cls.merge_atlas_json(base_gui, {"sources": new_gui_sources})
            gui_atlas_path.parent.mkdir(parents=True, exist_ok=True)
            gui_atlas_path.write_text(json.dumps(merged_gui, indent=2), encoding="utf-8")


PackMerger = SemanticMerger
