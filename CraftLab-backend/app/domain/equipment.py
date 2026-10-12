import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple, Union

VALID_LAYER_TYPES = {
    "humanoid",
    "humanoid_leggings",
    "wings",
    "wolf_body",
    "horse_body",
    "llama_body",
    "pig_saddle",
    "strider_saddle",
    "camel_saddle",
    "horse_saddle",
    "donkey_saddle",
    "mule_saddle",
    "skeleton_horse_saddle",
    "zombie_horse_saddle",
    "happy_ghast_body",
    "nautilus_body",
    "nautilus_saddle",
    "camel_husk_saddle",
    "humanoid_baby",
    # Legacy aliases for backwards compatibility
    "wolf",
    "horse",
    "llama",
}

CANONICAL_LAYER_TYPES = {
    "humanoid",
    "humanoid_leggings",
    "wings",
    "wolf_body",
    "horse_body",
    "llama_body",
    "pig_saddle",
    "strider_saddle",
    "camel_saddle",
    "horse_saddle",
    "donkey_saddle",
    "mule_saddle",
    "skeleton_horse_saddle",
    "zombie_horse_saddle",
    "happy_ghast_body",
    "nautilus_body",
    "nautilus_saddle",
    "camel_husk_saddle",
    "humanoid_baby",
}

LEGACY_TYPE_MAP = {
    "wolf": "wolf_body",
    "horse": "horse_body",
    "llama": "llama_body",
}

VALID_EQUIPMENT_SLOTS = {
    "head",
    "chest",
    "legs",
    "feet",
    "body",
    "mainhand",
    "offhand",
    "saddle",
}

IDENTIFIER_REGEX = re.compile(r"^[a-z0-9_.-]+$")


def validate_identifier(name: str) -> bool:
    return bool(name and IDENTIFIER_REGEX.match(name))


def get_equipment_models_dir(workspace_dir: Path, namespace: str = "craftlab") -> Path:
    """Returns canonical Minecraft 1.21.4+ equipment models directory."""
    return workspace_dir / "assets" / namespace / "equipment"


def get_legacy_equipment_models_dir(workspace_dir: Path, namespace: str = "craftlab") -> Path:
    """Returns legacy 1.21.2 snapshot equipment directory under models/."""
    return workspace_dir / "assets" / namespace / "models" / "equipment"


def get_equipment_model_path(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> Path:
    return get_equipment_models_dir(workspace_dir, namespace) / f"{equipment_id}.json"


def get_legacy_equipment_model_path(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> Path:
    return get_legacy_equipment_models_dir(workspace_dir, namespace) / f"{equipment_id}.json"


def normalize_legacy_equipment_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalizes legacy 1.21.2 snapshot descriptors (flat layers array with embedded 'type')
    to standard 1.21.4+ schema (layers object keyed by layer types).
    """
    if not isinstance(data, dict):
        return data

    layers_val = data.get("layers")
    if isinstance(layers_val, dict):
        # Normalize any legacy keys (e.g. wolf -> wolf_body)
        normalized_dict: Dict[str, List[Dict[str, Any]]] = {}
        for l_type, l_list in layers_val.items():
            canon_type = LEGACY_TYPE_MAP.get(l_type, l_type)
            if isinstance(l_list, list):
                normalized_dict[canon_type] = l_list
        result = dict(data)
        result["layers"] = normalized_dict
        return result

    if isinstance(layers_val, list):
        normalized_layers: Dict[str, List[Dict[str, Any]]] = {}
        for item in layers_val:
            if not isinstance(item, dict):
                continue
            raw_type = item.get("type", "humanoid")
            canon_type = LEGACY_TYPE_MAP.get(raw_type, raw_type)

            layer_entry: Dict[str, Any] = {"texture": item.get("texture", "")}
            raw_dyeable = item.get("dyeable")
            if isinstance(raw_dyeable, dict):
                layer_entry["dyeable"] = raw_dyeable
            elif raw_dyeable is True:
                layer_entry["dyeable"] = {}

            if "use_player_texture" in item:
                layer_entry["use_player_texture"] = bool(item["use_player_texture"])

            normalized_layers.setdefault(canon_type, []).append(layer_entry)

        result = dict(data)
        result["layers"] = normalized_layers
        return result

    return data


def validate_equipment_model_schema(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a dictionary against the Minecraft 1.21.4+ equipment model descriptor schema.
    Schema expects a root 'layers' object mapping layer types to non-empty lists of layer objects.
    """
    if not isinstance(data, dict):
        return False, "Equipment descriptor must be a JSON object"

    layers = data.get("layers")
    if not isinstance(layers, dict) or len(layers) == 0:
        return False, "Equipment model must define a non-empty 'layers' object keyed by layer types"

    for layer_type, layer_list in layers.items():
        if layer_type not in VALID_LAYER_TYPES:
            return False, f"Invalid layer type '{layer_type}'. Valid types: {sorted(list(CANONICAL_LAYER_TYPES))}"

        if not isinstance(layer_list, list) or len(layer_list) == 0:
            return False, f"Layer type '{layer_type}' must be a non-empty list of layer objects"

        for idx, layer in enumerate(layer_list):
            if not isinstance(layer, dict):
                return False, f"Layer at '{layer_type}[{idx}]' must be a JSON object"

            texture = layer.get("texture")
            if not texture or not isinstance(texture, str):
                return False, f"Layer at '{layer_type}[{idx}]' is missing a valid 'texture' resource location string"

            dyeable = layer.get("dyeable")
            if dyeable is not None:
                if not isinstance(dyeable, dict):
                    return False, f"Layer at '{layer_type}[{idx}]' 'dyeable' must be an object (or omitted)"
                color_when_undyed = dyeable.get("color_when_undyed")
                if color_when_undyed is not None and not isinstance(color_when_undyed, int):
                    return False, f"Layer at '{layer_type}[{idx}]' 'color_when_undyed' must be an integer RGB color"

            use_player_texture = layer.get("use_player_texture")
            if use_player_texture is not None and not isinstance(use_player_texture, bool):
                return False, f"Layer at '{layer_type}[{idx}]' 'use_player_texture' must be a boolean"

    return True, None


def list_equipment_models(workspace_dir: Path, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Discovers all 1.21.4+ equipment model definitions in the workspace, with transparent
    fallback ingestion for legacy models/equipment/*.json files.
    """
    results: List[Dict[str, Any]] = []
    seen_ids: set = set()
    assets_dir = workspace_dir / "assets"
    if not assets_dir.exists():
        return results

    namespaces = [assets_dir / namespace] if namespace else [d for d in assets_dir.iterdir() if d.is_dir()]

    for ns_dir in namespaces:
        ns_name = ns_dir.name

        # 1. Check canonical assets/<namespace>/equipment
        eq_dir = ns_dir / "equipment"
        if eq_dir.exists():
            for eq_file in eq_dir.glob("*.json"):
                try:
                    raw_data = json.loads(eq_file.read_text(encoding="utf-8"))
                    data = normalize_legacy_equipment_data(raw_data)
                    valid, _ = validate_equipment_model_schema(data)
                    model_id = eq_file.stem
                    seen_ids.add((ns_name, model_id))
                    results.append({
                        "id": model_id,
                        "namespace": ns_name,
                        "resource_location": f"{ns_name}:{model_id}",
                        "layers": data.get("layers", {}),
                        "is_valid": valid,
                        "file_path": str(eq_file.relative_to(workspace_dir)).replace("\\", "/")
                    })
                except Exception:
                    continue

        # 2. Check legacy assets/<namespace>/models/equipment if not already seen
        legacy_dir = ns_dir / "models" / "equipment"
        if legacy_dir.exists():
            for eq_file in legacy_dir.glob("*.json"):
                model_id = eq_file.stem
                if (ns_name, model_id) in seen_ids:
                    continue
                try:
                    raw_data = json.loads(eq_file.read_text(encoding="utf-8"))
                    data = normalize_legacy_equipment_data(raw_data)
                    valid, _ = validate_equipment_model_schema(data)
                    seen_ids.add((ns_name, model_id))
                    results.append({
                        "id": model_id,
                        "namespace": ns_name,
                        "resource_location": f"{ns_name}:{model_id}",
                        "layers": data.get("layers", {}),
                        "is_valid": valid,
                        "file_path": str(eq_file.relative_to(workspace_dir)).replace("\\", "/")
                    })
                except Exception:
                    continue

    return results


def get_equipment_model(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> Optional[Dict[str, Any]]:
    if ":" in equipment_id:
        parsed_ns, parsed_id = equipment_id.split(":", 1)
        if parsed_ns.strip():
            namespace = parsed_ns.strip()
        equipment_id = parsed_id.strip()

    target_path = get_equipment_model_path(workspace_dir, equipment_id, namespace)
    is_legacy = False
    if not target_path.exists():
        legacy_path = get_legacy_equipment_model_path(workspace_dir, equipment_id, namespace)
        if legacy_path.exists():
            target_path = legacy_path
            is_legacy = True
        else:
            return None

    try:
        raw_data = json.loads(target_path.read_text(encoding="utf-8"))
        data = normalize_legacy_equipment_data(raw_data)
        valid, err = validate_equipment_model_schema(data)
        return {
            "id": equipment_id,
            "namespace": namespace,
            "resource_location": f"{namespace}:{equipment_id}",
            "layers": data.get("layers", {}),
            "is_valid": valid,
            "schema_error": err,
            "is_legacy_path": is_legacy,
            "raw_json": json.dumps(data, indent=2)
        }
    except Exception:
        return None


def save_equipment_model(
    workspace_dir: Path,
    equipment_id: str,
    layers: Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]],
    namespace: str = "craftlab"
) -> Dict[str, Any]:
    if ":" in equipment_id:
        parsed_ns, parsed_id = equipment_id.split(":", 1)
        if parsed_ns.strip():
            namespace = parsed_ns.strip()
        equipment_id = parsed_id.strip()

    if not validate_identifier(namespace):
        raise ValueError(f"Invalid namespace '{namespace}'. Must be lowercase, numbers, underscores, dots, hyphens.")
    if not validate_identifier(equipment_id):
        raise ValueError(f"Invalid equipment identifier '{equipment_id}'. Must be lowercase, numbers, underscores, dots, hyphens.")

    # Normalize if given legacy flat list
    normalized_data = normalize_legacy_equipment_data({"layers": layers})
    payload = {"layers": normalized_data["layers"]}

    valid, err = validate_equipment_model_schema(payload)
    if not valid:
        raise ValueError(f"Equipment schema validation error: {err}")

    target_path = get_equipment_model_path(workspace_dir, equipment_id, namespace)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # Clean up legacy file if it existed
    legacy_path = get_legacy_equipment_model_path(workspace_dir, equipment_id, namespace)
    if legacy_path.exists():
        try:
            legacy_path.unlink()
        except Exception:
            pass

    return {
        "id": equipment_id,
        "namespace": namespace,
        "resource_location": f"{namespace}:{equipment_id}",
        "layers": payload["layers"],
        "equippable_component": {
            "slot": "chest",
            "asset_id": f"{namespace}:{equipment_id}"
        }
    }


def delete_equipment_model(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> bool:
    if ":" in equipment_id:
        parsed_ns, parsed_id = equipment_id.split(":", 1)
        if parsed_ns.strip():
            namespace = parsed_ns.strip()
        equipment_id = parsed_id.strip()

    deleted = False
    target_path = get_equipment_model_path(workspace_dir, equipment_id, namespace)
    if target_path.exists():
        target_path.unlink()
        deleted = True

    legacy_path = get_legacy_equipment_model_path(workspace_dir, equipment_id, namespace)
    if legacy_path.exists():
        legacy_path.unlink()
        deleted = True

    return deleted


def generate_equippable_component(
    equipment_id: str,
    slot: str = "chest",
    namespace: str = "craftlab"
) -> Dict[str, Any]:
    if ":" in equipment_id:
        parsed_ns, parsed_id = equipment_id.split(":", 1)
        if parsed_ns.strip():
            namespace = parsed_ns.strip()
        equipment_id = parsed_id.strip()

    if slot not in VALID_EQUIPMENT_SLOTS:
        raise ValueError(f"Invalid equipment slot '{slot}'. Valid slots: {sorted(list(VALID_EQUIPMENT_SLOTS))}")

    return {
        "minecraft:equippable": {
            "slot": slot,
            "asset_id": f"{namespace}:{equipment_id}"
        }
    }
