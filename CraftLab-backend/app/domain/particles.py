import json
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple

IDENTIFIER_REGEX = re.compile(r"^[a-z0-9_.-]+$")


def validate_identifier(name: str) -> bool:
    return bool(name and IDENTIFIER_REGEX.match(name))


def get_particles_dir(workspace_dir: Path, namespace: str = "craftlab") -> Path:
    return workspace_dir / "assets" / namespace / "particles"


def get_particle_path(workspace_dir: Path, particle_id: str, namespace: str = "craftlab") -> Path:
    return get_particles_dir(workspace_dir, namespace) / f"{particle_id}.json"


def validate_particle_definition(data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    if not isinstance(data, dict):
        return False, "Particle definition must be a JSON object"

    textures = data.get("textures")
    if not isinstance(textures, list) or len(textures) == 0:
        return False, "Particle definition must contain a non-empty 'textures' array"

    for idx, tex in enumerate(textures):
        if not isinstance(tex, str) or not tex.strip():
            return False, f"Texture at index {idx} must be a valid resource location string"

    return True, None


def list_particles(workspace_dir: Path, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
    results: List[Dict[str, Any]] = []
    assets_dir = workspace_dir / "assets"
    if not assets_dir.exists():
        return results

    namespaces = [assets_dir / namespace] if namespace else [d for d in assets_dir.iterdir() if d.is_dir()]

    for ns_dir in namespaces:
        ns_name = ns_dir.name
        part_dir = ns_dir / "particles"
        if not part_dir.exists():
            continue

        for part_file in part_dir.glob("*.json"):
            try:
                data = json.loads(part_file.read_text(encoding="utf-8"))
                valid, err = validate_particle_definition(data)
                part_id = part_file.stem
                results.append({
                    "id": part_id,
                    "namespace": ns_name,
                    "resource_location": f"{ns_name}:{part_id}",
                    "textures": data.get("textures", []),
                    "emitter": data.get("_emitter", {}),
                    "is_valid": valid,
                    "file_path": str(part_file.relative_to(workspace_dir)).replace("\\", "/")
                })
            except Exception:
                continue

    return results


def get_particle(workspace_dir: Path, particle_id: str, namespace: str = "craftlab") -> Optional[Dict[str, Any]]:
    path = get_particle_path(workspace_dir, particle_id, namespace)
    if not path.exists():
        return None

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        valid, err = validate_particle_definition(data)
        return {
            "id": particle_id,
            "namespace": namespace,
            "resource_location": f"{namespace}:{particle_id}",
            "textures": data.get("textures", []),
            "emitter": data.get("_emitter", {}),
            "is_valid": valid,
            "schema_error": err,
            "raw_json": json.dumps(data, indent=2)
        }
    except Exception:
        return None


def save_particle(
    workspace_dir: Path,
    particle_id: str,
    textures: List[str],
    emitter_params: Optional[Dict[str, Any]] = None,
    namespace: str = "craftlab"
) -> Dict[str, Any]:
    if not validate_identifier(particle_id):
        raise ValueError(f"Invalid particle identifier '{particle_id}'. Must be lowercase letters, numbers, underscores, dots, hyphens.")

    payload = {"textures": textures}
    if emitter_params:
        payload["_emitter"] = emitter_params

    valid, err = validate_particle_definition(payload)
    if not valid:
        raise ValueError(f"Particle validation error: {err}")

    target_path = get_particle_path(workspace_dir, particle_id, namespace)
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return {
        "id": particle_id,
        "namespace": namespace,
        "resource_location": f"{namespace}:{particle_id}",
        "textures": textures,
        "emitter": emitter_params or {},
        "command": generate_particle_command(particle_id, namespace=namespace)
    }


def delete_particle(workspace_dir: Path, particle_id: str, namespace: str = "craftlab") -> bool:
    target_path = get_particle_path(workspace_dir, particle_id, namespace)
    if target_path.exists():
        target_path.unlink()
        return True
    return False


def generate_particle_command(
    particle_id: str,
    count: int = 15,
    speed: float = 0.05,
    spread: Tuple[float, float, float] = (0.3, 0.5, 0.3),
    namespace: str = "craftlab"
) -> str:
    sx, sy, sz = spread
    return f"/particle {namespace}:{particle_id} ~ ~1 ~ {sx:.1f} {sy:.1f} {sz:.1f} {speed} {count}"
