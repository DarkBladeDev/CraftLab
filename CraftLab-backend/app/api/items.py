from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.entities import ItemModel, RevisionModel, BlockModel
from app.domain.items import ItemDefinition
from app.domain.blocks import BlockDefinition
from app.domain.revisions import create_revision_snapshot

router = APIRouter(prefix="/api/items", tags=["items"])


@router.get("", response_model=List[dict])
async def list_items(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel))
    items = result.scalars().all()
    return [
        {
            "id": i.id,
            "material": i.material,
            "display_name": i.display_name,
            "lore": i.lore,
            "custom_model_data": i.custom_model_data,
            "item_model": i.item_model,
            "item_flags": i.item_flags,
            "amount": i.amount,
            "components": i.components or {},
            "export_format": i.export_format or "native",
            "plugin_properties": i.plugin_properties or {},
            "raw_extensions": i.raw_extensions,
        }
        for i in items
    ]


@router.post("", response_model=dict)
async def create_or_update_item(item_in: ItemDefinition, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_in.id))
    existing = result.scalar_one_or_none()

    if existing:
        existing.material = item_in.material
        existing.display_name = item_in.display_name
        existing.lore = item_in.lore
        existing.custom_model_data = item_in.custom_model_data
        existing.item_model = item_in.item_model
        existing.item_flags = item_in.item_flags
        existing.amount = item_in.amount
        existing.components = item_in.components
        existing.export_format = item_in.export_format
        existing.plugin_properties = item_in.plugin_properties
        existing.raw_extensions = item_in.raw_extensions
    else:
        new_item = ItemModel(
            id=item_in.id,
            material=item_in.material,
            display_name=item_in.display_name,
            lore=item_in.lore,
            custom_model_data=item_in.custom_model_data,
            item_model=item_in.item_model,
            item_flags=item_in.item_flags,
            amount=item_in.amount,
            components=item_in.components,
            export_format=item_in.export_format,
            plugin_properties=item_in.plugin_properties,
            raw_extensions=item_in.raw_extensions
        )
        db.add(new_item)

    await db.commit()
    return item_in.model_dump()


@router.delete("/{item_id}")
async def delete_item(item_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel).where(ItemModel.id == item_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Item not found")
    await db.delete(existing)
    await db.commit()
    return {"status": "deleted", "id": item_id}


revisions_router = APIRouter(prefix="/api/revisions", tags=["revisions"])


@revisions_router.get("", response_model=List[dict])
async def list_revisions(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RevisionModel).order_by(RevisionModel.revision_number.desc()))
    revisions = result.scalars().all()
    return [
        {
            "id": r.id,
            "revision_number": r.revision_number,
            "revision_hash": r.revision_hash,
            "items_count": len(r.items_snapshot),
            "blocks_count": len(r.blocks_snapshot) if r.blocks_snapshot else 0,
            "created_at": r.created_at.isoformat() if r.created_at else None
        }
        for r in revisions
    ]


@revisions_router.post("", response_model=dict)
async def create_revision_from_current(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(ItemModel))
    items = result.scalars().all()
    if not items:
        raise HTTPException(status_code=400, detail="Cannot create revision with 0 items")

    domain_items = [
        ItemDefinition(
            id=i.id,
            material=i.material,
            display_name=i.display_name,
            lore=i.lore or [],
            custom_model_data=i.custom_model_data,
            item_model=i.item_model,
            item_flags=i.item_flags or [],
            amount=i.amount,
            components=i.components or {},
            export_format=i.export_format or "native",
            plugin_properties=i.plugin_properties or {},
            raw_extensions=i.raw_extensions
        )
        for i in items
    ]

    count_res = await db.execute(select(func.count(RevisionModel.id)))
    rev_count = count_res.scalar() or 0
    next_number = rev_count + 1

    b_result = await db.execute(select(BlockModel))
    blocks = b_result.scalars().all()
    domain_blocks = [
        BlockDefinition(
            id=b.id,
            display_name=b.display_name,
            mode=b.mode or "display_prop",
            item_model=b.item_model,
            scale=b.scale or [1.0, 1.0, 1.0],
            translation=b.translation or [0.0, 0.0, 0.0],
            hitbox_type=b.hitbox_type or "solid",
            hitbox_offsets=b.hitbox_offsets or [[0, 0, 0]],
            interaction_type=b.interaction_type or "none",
            seat_height=b.seat_height if b.seat_height is not None else 0.5,
            hardness=b.hardness if b.hardness is not None else 1.0,
            tool_type=b.tool_type or "AXE",
            drop_item_id=b.drop_item_id,
            plugin_properties=b.plugin_properties or {},
        )
        for b in blocks
    ]

    snapshot = create_revision_snapshot(domain_items, next_number, domain_blocks)
    rev_model = RevisionModel(
        id=snapshot["id"],
        revision_number=snapshot["revision_number"],
        revision_hash=snapshot["revision_hash"],
        items_snapshot=snapshot["items_snapshot"],
        blocks_snapshot=snapshot["blocks_snapshot"],
    )
    db.add(rev_model)
    await db.commit()
    return {
        "id": rev_model.id,
        "revision_number": rev_model.revision_number,
        "revision_hash": rev_model.revision_hash,
        "items_count": len(rev_model.items_snapshot),
        "blocks_count": len(rev_model.blocks_snapshot),
    }
