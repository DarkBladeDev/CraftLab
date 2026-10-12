from typing import Optional, List, Dict, Any, Union
from pathlib import Path
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Form
from pydantic import BaseModel, Field

from app.domain.workspace import get_default_workspace_dir, safe_resolve_workspace_path
from app.domain.glyphs import (
    scan_registered_glyphs,
    get_allocated_pua_hexes,
    allocate_next_pua,
    validate_pua_hex,
    register_glyph,
    delete_glyph,
)
from app.domain.equipment import (
    list_equipment_models,
    get_equipment_model,
    save_equipment_model,
    delete_equipment_model,
    generate_equippable_component,
)
from app.domain.sound_events import (
    list_sound_events,
    save_sound_event,
    delete_sound_event,
    probe_audio_channels,
    convert_audio_to_mono,
)
from app.domain.particles import (
    list_particles,
    get_particle,
    save_particle,
    delete_particle,
    generate_particle_command,
)

router = APIRouter(prefix="/api/v1/assets/creative", tags=["creative-assets"])


# --- Schemas ---

class GlyphRegisterRequest(BaseModel):
    id: str
    file: str
    hex: Optional[str] = None
    height: int = 8
    ascent: int = 7
    namespace: str = "craftlab"
    font_name: str = "default"


class EquipmentModelRequest(BaseModel):
    id: str
    layers: Union[Dict[str, List[Dict[str, Any]]], List[Dict[str, Any]]]
    namespace: str = "craftlab"


class SoundEventRequest(BaseModel):
    id: str
    category: str = "master"
    subtitle: Optional[str] = None
    sounds: List[Any]
    namespace: str = "craftlab"


class ParticleRequest(BaseModel):
    id: str
    textures: List[str]
    emitter: Optional[Dict[str, Any]] = None
    namespace: str = "craftlab"


# --- Glyphs Endpoints ---

@router.get("/glyphs")
async def get_glyphs(namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    glyphs = scan_registered_glyphs(workspace, namespace)
    used_hexes = list(get_allocated_pua_hexes(workspace, namespace))
    next_hex = allocate_next_pua(set(used_hexes))
    return {
        "glyphs": glyphs,
        "allocated_pua_hexes": sorted(used_hexes),
        "next_available_hex": next_hex,
        "count": len(glyphs)
    }


@router.post("/glyphs")
async def create_or_update_glyph(req: GlyphRegisterRequest):
    workspace = get_default_workspace_dir()
    try:
        saved = register_glyph(
            workspace_dir=workspace,
            glyph_id=req.id,
            file_ref=req.file,
            hex_code=req.hex,
            height=req.height,
            ascent=req.ascent,
            namespace=req.namespace,
            font_name=req.font_name
        )
        return saved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/glyphs/validate-hex")
async def check_glyph_hex(hex: str, current_hex: Optional[str] = None):
    workspace = get_default_workspace_dir()
    used = get_allocated_pua_hexes(workspace)
    valid, msg = validate_pua_hex(hex, used, current_hex)
    return {
        "valid": valid,
        "hex": msg if valid else None,
        "message": None if valid else msg
    }


@router.delete("/glyphs/{hex_code}")
async def remove_glyph(hex_code: str, namespace: str = "craftlab", font_name: str = "default"):
    workspace = get_default_workspace_dir()
    deleted = delete_glyph(workspace, hex_code, namespace, font_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Glyph not found")
    return {"status": "deleted", "hex": hex_code}


# --- Namespaces Endpoint ---

@router.get("/namespaces")
async def get_creative_namespaces():
    workspace = get_default_workspace_dir()
    assets_dir = workspace / "assets"
    if not assets_dir.exists():
        return ["craftlab"]
    discovered = [d.name for d in assets_dir.iterdir() if d.is_dir() and not d.name.startswith(".")]
    if "craftlab" not in discovered:
        discovered.insert(0, "craftlab")
    return sorted(list(set(discovered)))


# --- Equipment Models Endpoints ---

@router.get("/equipment")
async def get_all_equipment_models(namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    return list_equipment_models(workspace, namespace)


@router.get("/equipment/{equipment_id}")
async def get_single_equipment_model(equipment_id: str, namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    effective_ns = namespace or "craftlab"
    if ":" in equipment_id:
        parsed_ns, parsed_id = equipment_id.split(":", 1)
        if parsed_ns.strip():
            effective_ns = parsed_ns.strip()
        equipment_id = parsed_id.strip()
    item = get_equipment_model(workspace, equipment_id, effective_ns)
    if not item:
        raise HTTPException(status_code=404, detail="Equipment model not found")
    return item


@router.post("/equipment")
async def create_or_update_equipment_model(req: EquipmentModelRequest):
    workspace = get_default_workspace_dir()
    try:
        ns = req.namespace
        eq_id = req.id
        if ":" in req.id:
            parsed_ns, parsed_id = req.id.split(":", 1)
            if parsed_ns.strip():
                ns = parsed_ns.strip()
            eq_id = parsed_id.strip()
        saved = save_equipment_model(
            workspace_dir=workspace,
            equipment_id=eq_id,
            layers=req.layers,
            namespace=ns
        )
        return saved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/equipment/{equipment_id}")
async def remove_equipment_model(equipment_id: str, namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    effective_ns = namespace or "craftlab"
    if ":" in equipment_id:
        parsed_ns, parsed_id = equipment_id.split(":", 1)
        if parsed_ns.strip():
            effective_ns = parsed_ns.strip()
        equipment_id = parsed_id.strip()
    deleted = delete_equipment_model(workspace, equipment_id, effective_ns)
    if not deleted:
        raise HTTPException(status_code=404, detail="Equipment model not found")
    return {"status": "deleted", "id": equipment_id, "namespace": effective_ns}


# --- Sound Events Endpoints ---

@router.get("/sounds")
async def get_all_sound_events(namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    return list_sound_events(workspace, namespace)


@router.post("/sounds")
async def create_or_update_sound_event(req: SoundEventRequest):
    workspace = get_default_workspace_dir()
    try:
        ns = req.namespace
        snd_id = req.id
        if ":" in req.id:
            parsed_ns, parsed_id = req.id.split(":", 1)
            if parsed_ns.strip():
                ns = parsed_ns.strip()
            snd_id = parsed_id.strip()
        saved = save_sound_event(
            workspace_dir=workspace,
            event_id=snd_id,
            event_data={
                "category": req.category,
                "subtitle": req.subtitle,
                "sounds": req.sounds
            },
            namespace=ns
        )
        return saved
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sounds/{event_id}")
async def remove_sound_event(event_id: str, namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    effective_ns = namespace or "craftlab"
    if ":" in event_id:
        parsed_ns, parsed_id = event_id.split(":", 1)
        if parsed_ns.strip():
            effective_ns = parsed_ns.strip()
        event_id = parsed_id.strip()
    deleted = delete_sound_event(workspace, event_id, effective_ns)
    if not deleted:
        raise HTTPException(status_code=404, detail="Sound event not found")
    return {"status": "deleted", "id": event_id, "namespace": effective_ns}


class AudioPathRequest(BaseModel):
    relative_path: str


@router.post("/sounds/probe")
async def probe_audio(req: AudioPathRequest):
    workspace = get_default_workspace_dir()
    try:
        target_path = safe_resolve_workspace_path(workspace, req.relative_path)
        return probe_audio_channels(target_path)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/sounds/convert-mono")
async def convert_audio_mono(req: AudioPathRequest):
    workspace = get_default_workspace_dir()
    try:
        target_path = safe_resolve_workspace_path(workspace, req.relative_path)
        converted_path = convert_audio_to_mono(target_path)
        probe = probe_audio_channels(converted_path)
        return {
            "status": "converted",
            "file": req.relative_path,
            "probe": probe
        }
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Audio file not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# --- Particles Endpoints ---

@router.get("/particles")
async def get_all_particles(namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    return list_particles(workspace, namespace)


@router.get("/particles/{particle_id}")
async def get_single_particle(particle_id: str, namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    effective_ns = namespace or "craftlab"
    if ":" in particle_id:
        parsed_ns, parsed_id = particle_id.split(":", 1)
        if parsed_ns.strip():
            effective_ns = parsed_ns.strip()
        particle_id = parsed_id.strip()
    item = get_particle(workspace, particle_id, effective_ns)
    if not item:
        raise HTTPException(status_code=404, detail="Particle definition not found")
    return item


@router.post("/particles")
async def create_or_update_particle(req: ParticleRequest):
    workspace = get_default_workspace_dir()
    try:
        ns = req.namespace
        part_id = req.id
        if ":" in req.id:
            parsed_ns, parsed_id = req.id.split(":", 1)
            if parsed_ns.strip():
                ns = parsed_ns.strip()
            part_id = parsed_id.strip()
        saved = save_particle(
            workspace_dir=workspace,
            particle_id=part_id,
            textures=req.textures,
            emitter_params=req.emitter,
            namespace=ns
        )
        return saved
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/particles/{particle_id}")
async def remove_particle(particle_id: str, namespace: Optional[str] = None):
    workspace = get_default_workspace_dir()
    effective_ns = namespace or "craftlab"
    if ":" in particle_id:
        parsed_ns, parsed_id = particle_id.split(":", 1)
        if parsed_ns.strip():
            effective_ns = parsed_ns.strip()
        particle_id = parsed_id.strip()
    deleted = delete_particle(workspace, particle_id, effective_ns)
    if not deleted:
        raise HTTPException(status_code=404, detail="Particle definition not found")
    return {"status": "deleted", "id": particle_id, "namespace": effective_ns}
