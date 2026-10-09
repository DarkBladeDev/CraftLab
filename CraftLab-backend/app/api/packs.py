import os
import json
import shutil
import uuid
import zipfile
import hashlib
from pathlib import Path
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request, Response
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.core.database import get_db
from app.models.entities import ItemModel, TargetModel, BlockModel
from app.domain.pack_sources import PackRepository, PackSourceSchema, CompiledPackSchema
from app.domain.pack_validator import PreflightValidator, PreflightReport
from app.domain.pack_merger import SemanticMerger, ItemModelMapping
from app.domain.pack_compiler import DeterministicPackCompiler
from app.gateway.manager import gateway_manager
from app.domain.workspace import (
    ensure_workspace_initialized,
    safe_resolve_workspace_path,
    validate_minecraft_identifier,
    build_workspace_tree,
    get_workspace_metadata,
    get_default_workspace_dir,
    resolve_resource_location,
)

router = APIRouter(prefix="/api/v1/packs", tags=["packs"])
public_router = APIRouter(prefix="/api/v1/packs", tags=["packs"])

from app.core.config import settings

BASE_DATA_DIR = settings.paths.packs_dir
SOURCES_DIR = BASE_DATA_DIR / "sources"
DIST_DIR = BASE_DATA_DIR / "dist"
BUILD_TMP_DIR = BASE_DATA_DIR / "tmp"


def safe_extract_zip(zip_file_path: Path, target_dir: Path):
    target_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_file_path, "r") as zf:
        resolved_target = target_dir.resolve()
        for member in zf.infolist():
            member_path = (target_dir / member.filename).resolve()
            if not str(member_path).startswith(str(resolved_target)):
                raise ValueError(f"Unsafe file path in zip: {member.filename}")
        zf.extractall(target_dir)


class BuildPackRequest(BaseModel):
    target_id: Optional[str] = None
    pack_format: int = 34
    description: str = "Minecraft Content Platform Resource Pack"
    force: bool = False


class WriteWorkspaceFileRequest(BaseModel):
    path: str
    content: str


class CreateWorkspaceDirRequest(BaseModel):
    path: str


class RenameWorkspacePathRequest(BaseModel):
    old_path: str
    new_path: str


class WorkspaceConfigSchema(BaseModel):
    description: str = "CraftLab Workspace Pack"
    pack_format: int = 34
    min_inclusive: int = 34
    max_inclusive: int = 65


class UpdatePackSourceRequest(BaseModel):
    name: Optional[str] = None
    layer_priority: Optional[int] = None
    is_active: Optional[bool] = None


@router.get("/sources")
async def list_sources(
    target_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    sources = await PackRepository.list_sources(db, target_id=target_id)
    return [
        {
            "id": s.id,
            "target_id": s.target_id,
            "name": s.name,
            "source_type": s.source_type,
            "plugin": s.plugin,
            "layer_priority": s.layer_priority,
            "storage_path": s.storage_path,
            "sha1_hash": s.sha1_hash,
            "meta_info": s.meta_info,
            "is_active": s.is_active,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None
        }
        for s in sources
    ]


@router.post("/sources/upload")
async def upload_source_zip(
    file: UploadFile = File(...),
    name: str = Form(...),
    layer_priority: int = Form(10),
    target_id: Optional[str] = Form(None),
    plugin: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db)
):
    source_id = f"src-{uuid.uuid4().hex[:8]}"
    source_storage_dir = SOURCES_DIR / source_id
    source_storage_dir.mkdir(parents=True, exist_ok=True)

    temp_zip = source_storage_dir / "uploaded.zip"
    sha1 = hashlib.sha1()

    with open(temp_zip, "wb") as buffer:
        while chunk := await file.read(65536):
            sha1.update(chunk)
            buffer.write(chunk)

    sha1_hex = sha1.hexdigest()

    try:
        safe_extract_zip(temp_zip, source_storage_dir / "contents")
    except Exception as e:
        shutil.rmtree(source_storage_dir, ignore_errors=True)
        raise HTTPException(status_code=400, detail=f"Invalid or corrupted zip archive: {str(e)}")

    record = await PackRepository.create_or_update_source(
        db=db,
        source_id=source_id,
        name=name,
        source_type="upload",
        storage_path=str(source_storage_dir / "contents"),
        target_id=target_id,
        plugin=plugin,
        layer_priority=layer_priority,
        sha1_hash=sha1_hex,
        meta_info={"filename": file.filename, "file_size": temp_zip.stat().st_size}
    )

    return {
        "id": record.id,
        "name": record.name,
        "layer_priority": record.layer_priority,
        "sha1_hash": record.sha1_hash,
        "storage_path": record.storage_path
    }


@router.patch("/sources/{source_id}")
async def update_source_endpoint(
    source_id: str,
    req: UpdatePackSourceRequest,
    db: AsyncSession = Depends(get_db)
):
    source = await PackRepository.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail=f"Pack source '{source_id}' not found")

    if req.name is not None and req.name.strip():
        source.name = req.name.strip()
    if req.layer_priority is not None:
        source.layer_priority = req.layer_priority
    if req.is_active is not None:
        source.is_active = req.is_active

    await db.commit()
    await db.refresh(source)
    return {
        "id": source.id,
        "name": source.name,
        "layer_priority": source.layer_priority,
        "is_active": source.is_active,
        "source_type": source.source_type,
        "plugin": source.plugin,
    }


@router.delete("/sources/{source_id}")
async def delete_source(source_id: str, db: AsyncSession = Depends(get_db)):
    source = await PackRepository.get_source(db, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Pack source not found")

    # Clean up directory
    try:
        source_dir = Path(source.storage_path).parent
        if source_dir.exists() and "sources" in str(source_dir):
            shutil.rmtree(source_dir, ignore_errors=True)
    except Exception:
        pass

    success = await PackRepository.delete_source(db, source_id)
    return {"success": success}


# ---------------------------------------------------------
# Workspace Pack Filesystem & Metadata Endpoints
# ---------------------------------------------------------

@router.get("/workspace/tree")
async def get_workspace_tree_endpoint():
    workspace_dir = ensure_workspace_initialized()
    return build_workspace_tree(workspace_dir)


@router.get("/workspace/file")
async def get_workspace_file_endpoint(path: str, raw: bool = False):
    workspace_dir = ensure_workspace_initialized()
    try:
        target_path = safe_resolve_workspace_path(workspace_dir, path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not target_path.exists() or not target_path.is_file():
        raise HTTPException(status_code=404, detail=f"File '{path}' not found")

    ext = target_path.suffix.lower()
    if raw or ext in [".png", ".ogg"]:
        media_type = "image/png" if ext == ".png" else ("audio/ogg" if ext == ".ogg" else "application/octet-stream")
        return FileResponse(path=target_path, media_type=media_type)

    try:
        content = target_path.read_text(encoding="utf-8")
        return {"path": path, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")


@router.put("/workspace/file")
async def write_workspace_file_endpoint(req: WriteWorkspaceFileRequest):
    workspace_dir = ensure_workspace_initialized()
    try:
        target_path = safe_resolve_workspace_path(workspace_dir, req.path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    ext = target_path.suffix.lower()
    if ext == ".json":
        try:
            json.loads(req.content)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSON syntax: {str(e)}")

    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(req.content, encoding="utf-8")
    return {"success": True, "path": req.path, "size": len(req.content)}


@router.post("/workspace/directory")
async def create_workspace_directory_endpoint(req: CreateWorkspaceDirRequest):
    workspace_dir = ensure_workspace_initialized()
    clean_path = req.path.replace("\\", "/").strip("/")
    if not clean_path:
        raise HTTPException(status_code=400, detail="Directory path cannot be empty")

    segments = clean_path.split("/")
    for seg in segments:
        if not validate_minecraft_identifier(seg):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid directory segment '{seg}'. Must be lowercase and match ^[a-z0-9_.-]+$"
            )

    try:
        target_path = safe_resolve_workspace_path(workspace_dir, clean_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    target_path.mkdir(parents=True, exist_ok=True)
    return {"success": True, "path": clean_path}


@router.post("/workspace/rename")
async def rename_workspace_path_endpoint(req: RenameWorkspacePathRequest):
    workspace_dir = ensure_workspace_initialized()
    clean_old = req.old_path.replace("\\", "/").strip("/")
    clean_new = req.new_path.replace("\\", "/").strip("/")
    if not clean_old or not clean_new:
        raise HTTPException(status_code=400, detail="Paths cannot be empty")
    if clean_old == clean_new:
        return {"success": True, "old_path": clean_old, "new_path": clean_new}

    segments = clean_new.split("/")
    for i, seg in enumerate(segments):
        if i == len(segments) - 1 and "." in seg:
            stem = seg.split(".", 1)[0]
            if not validate_minecraft_identifier(stem):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file stem '{stem}'. Must be lowercase and match ^[a-z0-9_.-]+$"
                )
        else:
            if not validate_minecraft_identifier(seg):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid path segment '{seg}'. Must be lowercase and match ^[a-z0-9_.-]+$"
                )

    try:
        old_target = safe_resolve_workspace_path(workspace_dir, clean_old)
        new_target = safe_resolve_workspace_path(workspace_dir, clean_new)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not old_target.exists():
        raise HTTPException(status_code=404, detail=f"Source path '{clean_old}' not found")
    if new_target.exists():
        raise HTTPException(status_code=409, detail=f"Destination path '{clean_new}' already exists")

    new_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(old_target), str(new_target))
    return {"success": True, "old_path": clean_old, "new_path": clean_new}


@router.post("/workspace/upload")
async def upload_workspace_file_endpoint(
    file: UploadFile = File(...),
    directory: str = Form("")
):
    workspace_dir = ensure_workspace_initialized()
    clean_dir = directory.replace("\\", "/").strip("/")

    if clean_dir:
        for seg in clean_dir.split("/"):
            if not validate_minecraft_identifier(seg):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid directory segment '{seg}'. Must match ^[a-z0-9_.-]+$"
                )

    try:
        target_dir = safe_resolve_workspace_path(workspace_dir, clean_dir)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    target_dir.mkdir(parents=True, exist_ok=True)

    filename = file.filename
    stem = filename.split(".", 1)[0]
    if not validate_minecraft_identifier(stem):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file name '{filename}'. Stem '{stem}' must be lowercase and match ^[a-z0-9_.-]+$"
        )

    target_file = target_dir / filename
    with open(target_file, "wb") as buffer:
        while chunk := await file.read(65536):
            buffer.write(chunk)

    rel_path = str(target_file.resolve().relative_to(workspace_dir.resolve())).replace("\\", "/")
    return {"success": True, "path": rel_path, "filename": filename}


@router.delete("/workspace/file")
async def delete_workspace_file_endpoint(path: str):
    workspace_dir = ensure_workspace_initialized()
    clean_path = path.replace("\\", "/").strip("/")
    if not clean_path or clean_path == ".":
        raise HTTPException(status_code=400, detail="Cannot delete root workspace directory")

    try:
        target_path = safe_resolve_workspace_path(workspace_dir, clean_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Path '{clean_path}' not found")

    if target_path.is_dir():
        shutil.rmtree(target_path, ignore_errors=True)
    else:
        target_path.unlink()

    return {"success": True, "path": clean_path}


@router.get("/workspace/metadata")
async def get_workspace_metadata_endpoint(path: str):
    workspace_dir = ensure_workspace_initialized()
    try:
        meta = get_workspace_metadata(workspace_dir, path)
        return meta
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/workspace/config")
async def get_workspace_config_endpoint():
    workspace_dir = ensure_workspace_initialized()
    mcmeta_path = workspace_dir / "pack.mcmeta"
    if not mcmeta_path.exists():
        return {
            "description": "CraftLab Workspace Pack",
            "pack_format": 34,
            "min_inclusive": 34,
            "max_inclusive": 65,
        }

    try:
        data = json.loads(mcmeta_path.read_text(encoding="utf-8"))
        pack = data.get("pack", {})
        supported = pack.get("supported_formats", {})
        if isinstance(supported, dict):
            min_inc = supported.get("min_inclusive", pack.get("min_format", 34))
            max_inc = supported.get("max_inclusive", pack.get("max_format", 65))
        elif isinstance(supported, list) and len(supported) == 2:
            min_inc, max_inc = supported[0], supported[1]
        else:
            min_inc = pack.get("min_format", pack.get("pack_format", 34))
            max_inc = pack.get("max_format", pack.get("pack_format", 65))

        desc = pack.get("description", "CraftLab Workspace Pack")
        if isinstance(desc, dict):
            desc = desc.get("text", "")

        return {
            "description": str(desc),
            "pack_format": int(pack.get("pack_format", 34)),
            "min_inclusive": int(min_inc),
            "max_inclusive": int(max_inc),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to read pack.mcmeta: {str(e)}")


@router.put("/workspace/config")
async def update_workspace_config_endpoint(req: WorkspaceConfigSchema):
    workspace_dir = ensure_workspace_initialized()
    mcmeta_path = workspace_dir / "pack.mcmeta"
    data = {}
    if mcmeta_path.exists():
        try:
            data = json.loads(mcmeta_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}

    if "pack" not in data or not isinstance(data["pack"], dict):
        data["pack"] = {}

    data["pack"]["description"] = req.description
    data["pack"]["pack_format"] = req.pack_format
    data["pack"]["min_format"] = req.min_inclusive
    data["pack"]["max_format"] = req.max_inclusive
    data["pack"]["supported_formats"] = {
        "min_inclusive": req.min_inclusive,
        "max_inclusive": req.max_inclusive,
    }

    mcmeta_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    return {
        "description": req.description,
        "pack_format": req.pack_format,
        "min_inclusive": req.min_inclusive,
        "max_inclusive": req.max_inclusive,
    }


@router.post("/preflight", response_model=PreflightReport)
async def run_preflight_check(
    target_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Studio items
    res = await db.execute(select(ItemModel))
    items = res.scalars().all()

    # 2. Fetch active pack sources + workspace pack
    sources = await PackRepository.list_sources(db, target_id=target_id)
    workspace_dir = ensure_workspace_initialized()
    all_sources = list(sources)
    if workspace_dir.exists():
        class WorkspaceSourceWrapper:
            id = "workspace"
            name = "Workspace Pack"
            storage_path = str(workspace_dir)
            layer_priority = 90
        all_sources.append(WorkspaceSourceWrapper())

    # 3. Validate
    report = PreflightValidator.validate(
        studio_items=items,
        sources=all_sources
    )
    return report


@router.post("/build")
async def build_resource_pack(
    request_data: BuildPackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Studio items & pack sources & blocks
    res = await db.execute(select(ItemModel))
    items = res.scalars().all()
    res_blocks = await db.execute(select(BlockModel))
    blocks = res_blocks.scalars().all()
    sources = await PackRepository.list_sources(db, target_id=request_data.target_id)

    # 2. Pre-flight check
    report = PreflightValidator.validate(studio_items=items, sources=sources)
    if not report.is_valid and not request_data.force:
        return Response(
            content=report.model_dump_json(),
            status_code=409,
            media_type="application/json"
        )

    # 3. Setup build directories
    pack_id = f"pack-{uuid.uuid4().hex[:8]}"
    stage_dir = BUILD_TMP_DIR / pack_id
    stage_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Sort sources ascending by priority so higher layers overwrite lower layers
        ordered_sources = sorted(sources, key=lambda s: s.layer_priority)
        source_dirs = [Path(s.storage_path) for s in ordered_sources if Path(s.storage_path).exists()]

        # Generate Studio Item Layer
        studio_layer_dir = stage_dir / "studio_layer"
        studio_layer_dir.mkdir(parents=True, exist_ok=True)

        # Build dual projection for studio items (Legacy Base + Modern Overlay)
        materials_with_cmd: Dict[str, List[ItemModel]] = {}
        for it in items:
            if it.material and it.custom_model_data is not None:
                mat = it.material.strip().upper()
                materials_with_cmd.setdefault(mat, []).append(it)

        def resolve_model_path(identifier: Optional[str], default_id: str) -> str:
            if not identifier:
                return f"studio:item/{default_id}"
            if ":" not in identifier:
                return f"studio:item/{identifier}"
            ns, name = identifier.split(":", 1)
            if "/" in name:
                return identifier
            return f"{ns}:item/{name}"

        for mat, mat_items in materials_with_cmd.items():
            mappings = [
                ItemModelMapping(
                    material=mat,
                    custom_model_data=it.custom_model_data,
                    model_path=resolve_model_path(it.item_model, it.id),
                    item_model=it.item_model
                )
                for it in mat_items
            ]

            # 1. Legacy base model: assets/minecraft/models/item/{mat.lower()}.json
            legacy_file = studio_layer_dir / "assets" / "minecraft" / "models" / "item" / f"{mat.lower()}.json"
            legacy_file.parent.mkdir(parents=True, exist_ok=True)
            legacy_model_data = SemanticMerger.build_legacy_item_model(mat, mappings)
            import json
            legacy_file.write_text(json.dumps(legacy_model_data, indent=2), encoding="utf-8")

            # 2. Modern overlay definition: overlay_v1_21_2/assets/minecraft/items/{mat.lower()}.json
            modern_file = studio_layer_dir / "overlay_v1_21_2" / "assets" / "minecraft" / "items" / f"{mat.lower()}.json"
            modern_file.parent.mkdir(parents=True, exist_ok=True)
            modern_def_data = SemanticMerger.build_modern_item_definition(mat, mappings)
            modern_file.write_text(json.dumps(modern_def_data, indent=2), encoding="utf-8")

        # 3. Dedicated item_model definitions and root geometry models
        def emit_item_definition(identifier: str, target_model: str):
            """Writes ItemDefinition to both overlay and base items/ with path aliases."""
            if ":" not in identifier:
                return
            ns, name = identifier.split(":", 1)
            def_body = json.dumps({
                "model": {
                    "type": "minecraft:model",
                    "model": target_model
                }
            }, indent=2)

            file_names = [name]
            if name.startswith("item/"):
                file_names.append(name[5:])
            elif "/" not in name:
                file_names.append(f"item/{name}")

            for fname in file_names:
                for base_sub in ["overlay_v1_21_2", ""]:
                    if base_sub:
                        target_f = studio_layer_dir / base_sub / "assets" / ns / "items" / f"{fname}.json"
                    else:
                        target_f = studio_layer_dir / "assets" / ns / "items" / f"{fname}.json"
                    target_f.parent.mkdir(parents=True, exist_ok=True)
                    target_f.write_text(def_body, encoding="utf-8")

        for it in items:
            mat = (it.material or "PAPER").strip().upper()
            if it.item_model:
                target_m = resolve_model_path(it.item_model, it.id)
                emit_item_definition(it.item_model, target_m)
            else:
                target_m = f"studio:item/{it.id}"
                emit_item_definition(f"studio:{it.id}", target_m)

            if target_m.startswith("studio:item/"):
                geom_file = studio_layer_dir / "assets" / "studio" / "models" / "item" / f"{it.id}.json"
                if not geom_file.exists():
                    geom_file.parent.mkdir(parents=True, exist_ok=True)
                    geom_file.write_text(json.dumps({
                        "parent": "item/handheld" if any(w in mat for w in ("SWORD", "AXE", "HOE", "SHOVEL", "PICKAXE")) else "item/generated",
                        "textures": {
                            "layer0": f"minecraft:item/{mat.lower()}"
                        }
                    }, indent=2), encoding="utf-8")

        for b in blocks:
            if b.item_model:
                target_m = resolve_model_path(b.item_model, b.id)
                emit_item_definition(b.item_model, target_m)

        # Workspace Pack layer has high precedence
        workspace_dir = ensure_workspace_initialized()
        if workspace_dir.exists():
            source_dirs.append(workspace_dir)

        # Studio layer has highest priority
        source_dirs.append(studio_layer_dir)

        # 4. Merge all layers into merged_output
        merged_dir = stage_dir / "merged"
        summary = SemanticMerger.merge_layers_to_directory(
            ordered_source_dirs=source_dirs,
            output_dir=merged_dir,
            pack_format=request_data.pack_format,
            description=request_data.description
        )

        # 5. Compile to deterministic ZIP
        DIST_DIR.mkdir(parents=True, exist_ok=True)
        pack_filename = f"resourcepack-{request_data.target_id or 'main'}.zip"
        dest_zip_path = DIST_DIR / pack_filename

        sha1_hex, file_size = DeterministicPackCompiler.compile_directory_to_zip(
            source_dir=merged_dir,
            output_zip_path=dest_zip_path
        )

        # 6. Record in DB
        compiled_record = await PackRepository.record_compiled_pack(
            db=db,
            pack_id=pack_id,
            pack_name=pack_filename,
            storage_path=str(dest_zip_path),
            file_size=file_size,
            sha1_hash=sha1_hex,
            pack_format=request_data.pack_format,
            target_id=request_data.target_id,
            build_summary=summary
        )

        # 7. Formulate public download URL
        base_public_url = os.getenv("MCP_PUBLIC_URL")
        if not base_public_url:
            host = request.headers.get("host", "localhost:8000")
            scheme = request.url.scheme
            base_public_url = f"{scheme}://{host}"

        target_slug = request_data.target_id or "main"
        download_url = f"{base_public_url.rstrip('/')}/api/v1/packs/{target_slug}/download"

        # 8. Notify Agent if target is connected
        if request_data.target_id:
            try:
                from app.protocol.envelope import MessageEnvelope
                ready_envelope = MessageEnvelope(
                    protocolVersion="1.0",
                    messageType="event",
                    targetId=request_data.target_id,
                    payload={
                        "type": "resource_pack:ready",
                        "url": download_url,
                        "sha1": sha1_hex,
                        "required": False,
                        "prompt": request_data.description
                    }
                )
                await gateway_manager.send_to_target(request_data.target_id, ready_envelope)
            except Exception as e:
                import logging
                logging.getLogger("mcp.packs").error(f"Failed to notify agent: {e}")

        return {
            "pack_id": compiled_record.id,
            "target_id": compiled_record.target_id,
            "pack_name": compiled_record.pack_name,
            "sha1_hash": compiled_record.sha1_hash,
            "file_size": compiled_record.file_size,
            "download_url": download_url,
            "build_summary": compiled_record.build_summary
        }
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        try:
            Path("build_error.log").write_text(err_msg, encoding="utf-8")
        except Exception:
            pass
        raise e
    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)


@public_router.get("/{target_id}/download")
async def download_resource_pack(
    target_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # Lookup compiled pack for target_id or global fallback
    pack = await PackRepository.get_latest_compiled_pack(db, target_id=target_id)
    if not pack or not Path(pack.storage_path).exists():
        # Fallback to any latest compiled pack
        pack = await PackRepository.get_latest_compiled_pack(db, target_id=None)
        if not pack or not Path(pack.storage_path).exists():
            raise HTTPException(status_code=404, detail="No active resource pack compiled for this target")

    # Check ETag / If-None-Match
    client_etag = request.headers.get("if-none-match")
    if client_etag and client_etag.strip('"') == pack.sha1_hash:
        return Response(status_code=304)

    return FileResponse(
        path=pack.storage_path,
        media_type="application/zip",
        headers={
            "ETag": f'"{pack.sha1_hash}"',
            "Cache-Control": "public, max-age=86400",
            "Content-Disposition": f'attachment; filename="{pack.pack_name}"'
        }
    )


@public_router.get("/{target_id}/latest")
async def get_latest_pack_info(
    target_id: str,
    db: AsyncSession = Depends(get_db)
):
    pack = await PackRepository.get_latest_compiled_pack(db, target_id=target_id)
    if not pack:
        raise HTTPException(status_code=404, detail="No compiled pack found")
    return {
        "id": pack.id,
        "target_id": pack.target_id,
        "pack_name": pack.pack_name,
        "sha1_hash": pack.sha1_hash,
        "file_size": pack.file_size,
        "pack_format": pack.pack_format,
        "build_summary": pack.build_summary,
        "created_at": pack.created_at.isoformat() if pack.created_at else None
    }
