import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

VALID_LAYER_TYPES = {
    "humanoid",
    "humanoid_leggings",
    "wings",
    "wolf",
    "horse",
    "llama",
    "humanoid_baby"
}

VALID_EQUIPMENT_SLOTS = {
    "head",
    "chest",
    "legs",
    "feet",
    "mainhand",
    "offhand"
}

IDENTIFIER_REGEX = re.compile(r"^[a-z0-9_.-]+$")


def validate_identifier(name: str) -> bool:
    return bool(name and IDENTIFIER_REGEX.match(name))


def get_equipment_models_dir(workspace_dir: Path, namespace: str = "craftlab") -> Path:
    return workspace_dir / "assets" / namespace / "models" / "equipment"


def get_equipment_model_path(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> Path:
    return get_equipment_models_dir(workspace_dir, namespace) / f"{equipment_id}.json"


def validate_equipment_model_schema(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validates a dictionary against the Minecraft 1.21.2+ equipment model descriptor schema.
    """
    if not isinstance(data, dict):
        return False, "Equipment descriptor must be a JSON object"

    layers = data.get("layers")
    if not isinstance(layers, list) or len(layers) == 0:
        return False, "Equipment model must define a non-empty 'layers' list"

    for idx, layer in enumerate(layers):
        if not isinstance(layer, dict):
            return False, f"Layer at index {idx} must be a JSON object"

        texture = layer.get("texture")
        if not texture or not isinstance(texture, str):
            return False, f"Layer at index {idx} is missing a valid 'texture' resource location string"

        layer_type = layer.get("type")
        if layer_type is not None and layer_type not in VALID_LAYER_TYPES:
            return False, f"Layer at index {idx} has invalid type '{layer_type}'. Valid types: {sorted(list(VALID_LAYER_TYPES))}"

        dyeable = layer.get("dyeable")
        if dyeable is not None and not isinstance(dyeable, (bool, dict)):
            return False, f"Layer at index {idx} 'dyeable' must be boolean or dict object"

    return True, None


def list_equipment_models(workspace_dir: Path, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Discovers all 1.21.2+ equipment model definitions in the workspace.
    """
    results: List[Dict[str, Any]] = []
    assets_dir = workspace_dir / "assets"
    if not assets_dir.exists():
        return results

    namespaces = [assets_dir / namespace] if namespace else [d for d in assets_dir.iterdir() if d.is_dir()]

    for ns_dir in namespaces:
        ns_name = ns_dir.name
        eq_dir = ns_dir / "models" / "equipment"
        if not eq_dir.exists():
            continue

        for eq_file in eq_dir.glob("*.json"):
            try:
                data = json.loads(eq_file.read_text(encoding="utf-8"))
                valid, _ = validate_equipment_model_schema(data)
                model_id = eq_file.stem
                results.append({
                    "id": model_id,
                    "namespace": ns_name,
                    "resource_location": f"{ns_name}:{model_id}",
                    "layers": data.get("layers", []),
                    "is_valid": valid,
                    "file_path": str(eq_file.relative_to(workspace_dir)).replace("\\", "/")
                })
            except Exception:
                continue

    return results


def get_equipment_model(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> Optional[Dict[str, Any]]:
    target_path = get_equipment_model_path(workspace_dir, equipment_id, namespace)
    if not target_path.exists():
        return None

    try:
        data = json.loads(target_path.read_text(encoding="utf-8"))
        valid, err = validate_equipment_model_schema(data)
        return {
            "id": equipment_id,
            "namespace": namespace,
            "resource_location": f"{namespace}:{equipment_id}",
            "layers": data.get("layers", []),
            "is_valid": valid,
            "schema_error": err,
            "raw_json": json.dumps(data, indent=2)
        }
    except Exception:
        return None


def save_equipment_model(
    workspace_dir: Path,
    equipment_id: str,
    layers: List[Dict[str, Any]],
    namespace: str = "craftlab"
) -> Dict[str, Any]:
    if not validate_identifier(equipment_id):
        raise ValueError(f"Invalid equipment identifier '{equipment_id}'. Must be lowercase, numbers, underscores, dots, hyphens.")

    payload = {"layers": layers}
    valid, err = validate_equipment_model_schema(payload)
    if not valid:
        raise ValueError(f"Equipment schema validation error: {err}")

    target_path = get_equipment_model_path(workspace_dir, equipment_id, namespace)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "id": equipment_id,
        "namespace": namespace,
        "resource_location": f"{namespace}:{equipment_id}",
        "layers": layers,
        "equippable_component": {
            "slot": "chest",
            "model": f"{namespace}:{equipment_id}"
        }
    }


def delete_equipment_model(workspace_dir: Path, equipment_id: str, namespace: str = "craftlab") -> bool:
    target_path = get_equipment_model_path(workspace_dir, equipment_id, namespace)
    if target_path.exists():
        target_path.unlink()
        return True
    return False


def generate_equippable_component(
    equipment_id: str,
    slot: str = "chest",
    namespace: str = "craftlab"
) -> Dict[str, Any]:
    if slot not in VALID_EQUIPMENT_SLOTS:
        raise ValueError(f"Invalid equipment slot '{slot}'. Valid slots: {sorted(list(VALID_EQUIPMENT_SLOTS))}")

    return {
        "minecraft:equippable": {
            "slot": slot,
            "model": f"{namespace}:{equipment_id}"
        }
    }
