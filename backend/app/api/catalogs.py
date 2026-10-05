from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db, AsyncSessionLocal
from app.domain.catalogs import (
    VanillaCatalogService,
    get_discovered_items_for_target
)
from app.gateway.manager import gateway_manager

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])


@router.get("/vanilla")
async def get_vanilla_catalog(
    category: Optional[str] = Query(None, description="Filter by category (combat, tools, armor, blocks, items, food, redstone)"),
    search: Optional[str] = Query(None, description="Search query string")
):
    categories = VanillaCatalogService.get_categories()
    items = VanillaCatalogService.search(category=category, search=search)
    return {
        "categories": categories,
        "count": len(items),
        "items": items
    }


@router.get("/targets/{target_id}/items")
async def get_target_discovered_items(
    target_id: str,
    source: Optional[str] = Query(None, description="Filter by source plugin, e.g. oraxen, nexo"),
    search: Optional[str] = Query(None, description="Search query string"),
    db: AsyncSession = Depends(get_db)
):
    items = await get_discovered_items_for_target(db, target_id, source=source, search=search)
    return [
        {
            "id": it.id,
            "target_id": it.target_id,
            "source": it.source,
            "item_id": it.item_id,
            "material": it.material,
            "display_name": it.display_name,
            "lore": it.lore or [],
            "custom_model_data": it.custom_model_data,
            "item_flags": it.item_flags or [],
            "raw_properties": it.raw_properties or {},
            "synced_at": it.synced_at.isoformat() if it.synced_at else None
        }
        for it in items
    ]


@router.post("/targets/{target_id}/sync")
async def sync_target_catalog(target_id: str):
    if not gateway_manager.is_online(target_id):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Target '{target_id}' is offline and cannot perform live catalog sync."
        )

    try:
        res = await gateway_manager.refresh_catalog(target_id, AsyncSessionLocal)
        return {
            "status": "success",
            "target_id": target_id,
            "result": res
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to refresh catalog from target: {str(e)}"
        )


import json
from pathlib import Path

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas" / "plugins"


@router.get("/schemas")
async def list_plugin_schemas():
    if not SCHEMAS_DIR.exists():
        return []
    schemas = []
    for schema_file in SCHEMAS_DIR.glob("*.json"):
        try:
            with open(schema_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                schemas.append({
                    "id": data.get("id", schema_file.stem),
                    "plugin": data.get("plugin", ""),
                    "name": data.get("name", ""),
                    "version": data.get("version", "")
                })
        except Exception:
            continue
    return schemas


@router.get("/schemas/{schema_id}")
async def get_plugin_schema(schema_id: str):
    schema_path = SCHEMAS_DIR / f"{schema_id}.json"
    if not schema_path.exists():
        # Also check without suffix or as plugin name
        matched = list(SCHEMAS_DIR.glob(f"*{schema_id}*.json"))
        if matched:
            schema_path = matched[0]
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Plugin configuration schema '{schema_id}' not found."
            )

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading schema file: {str(e)}"
        )
