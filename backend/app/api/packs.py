import os
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
from app.models.entities import ItemModel, TargetModel
from app.domain.pack_sources import PackRepository, PackSourceSchema, CompiledPackSchema
from app.domain.pack_validator import PreflightValidator, PreflightReport
from app.domain.pack_merger import SemanticMerger, ItemModelMapping
from app.domain.pack_compiler import DeterministicPackCompiler
from app.gateway.manager import gateway_manager

router = APIRouter(prefix="/api/v1/packs", tags=["packs"])

BASE_DATA_DIR = Path(os.getenv("MCP_DATA_DIR", "data/packs"))
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


@router.post("/preflight", response_model=PreflightReport)
async def run_preflight_check(
    target_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Studio items
    res = await db.execute(select(ItemModel))
    items = res.scalars().all()

    # 2. Fetch active pack sources
    sources = await PackRepository.list_sources(db, target_id=target_id)

    # 3. Validate
    report = PreflightValidator.validate(
        studio_items=items,
        sources=sources
    )
    return report


@router.post("/build")
async def build_resource_pack(
    request_data: BuildPackRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    # 1. Fetch Studio items & pack sources
    res = await db.execute(select(ItemModel))
    items = res.scalars().all()
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

        for mat, mat_items in materials_with_cmd.items():
            mappings = [
                ItemModelMapping(
                    material=mat,
                    custom_model_data=it.custom_model_data,
                    model_path=f"studio:item/{it.id}",
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
            for it in mat_items:
                im_target = it.item_model or f"studio:{it.id}"
                if ":" in im_target:
                    ns, name = im_target.split(":", 1)
                    im_file = studio_layer_dir / "overlay_v1_21_2" / "assets" / ns / "items" / f"{name}.json"
                    im_file.parent.mkdir(parents=True, exist_ok=True)
                    im_file.write_text(json.dumps({
                        "model": {
                            "type": "minecraft:model",
                            "model": f"studio:item/{it.id}"
                        }
                    }, indent=2), encoding="utf-8")

                # Shared root geometric model
                geom_file = studio_layer_dir / "assets" / "studio" / "models" / "item" / f"{it.id}.json"
                if not geom_file.exists():
                    geom_file.parent.mkdir(parents=True, exist_ok=True)
                    geom_file.write_text(json.dumps({
                        "parent": "item/handheld" if any(w in mat for w in ("SWORD", "AXE", "HOE", "SHOVEL", "PICKAXE")) else "item/generated",
                        "textures": {
                            "layer0": f"minecraft:item/{mat.lower()}"
                        }
                    }, indent=2), encoding="utf-8")

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

    finally:
        shutil.rmtree(stage_dir, ignore_errors=True)


@router.get("/{target_id}/download")
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


@router.get("/{target_id}/latest")
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
