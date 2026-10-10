import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.entities import BlockModel
from app.domain.blocks import BlockDefinition
from app.gateway.manager import gateway_manager
from app.protocol.envelope import MessageEnvelope

router = APIRouter(prefix="/api/v1/blocks", tags=["blocks"])
legacy_router = APIRouter(prefix="/api/blocks", tags=["blocks"])


def _serialize_block_model(b: BlockModel) -> dict:
    return {
        "id": b.id,
        "display_name": b.display_name,
        "mode": b.mode or "display_prop",
        "item_model": b.item_model,
        "block_model": getattr(b, "block_model", None) or b.item_model,
        "scale": b.scale or [1.0, 1.0, 1.0],
        "translation": b.translation or [0.0, 0.0, 0.0],
        "hitbox_type": b.hitbox_type or "solid",
        "hitbox_offsets": b.hitbox_offsets or [[0, 0, 0]],
        "interaction_type": b.interaction_type or "none",
        "seat_height": b.seat_height if b.seat_height is not None else 0.5,
        "hardness": b.hardness if b.hardness is not None else 1.0,
        "tool_type": b.tool_type or "AXE",
        "drop_item_id": b.drop_item_id,
        "plugin_properties": b.plugin_properties or {},
        "default_state": getattr(b, "default_state", None) or "default",
        "states": getattr(b, "states", None) or {},
    }


@router.get("", response_model=List[dict])
@legacy_router.get("", response_model=List[dict])
async def list_blocks(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlockModel))
    blocks = result.scalars().all()
    return [_serialize_block_model(b) for b in blocks]


@router.get("/{block_id}", response_model=dict)
@legacy_router.get("/{block_id}", response_model=dict)
async def get_block(block_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlockModel).where(BlockModel.id == block_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")
    return _serialize_block_model(existing)


@router.post("", response_model=dict)
@legacy_router.post("", response_model=dict)
async def create_or_update_block(block_in: BlockDefinition, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlockModel).where(BlockModel.id == block_in.id))
    existing = result.scalar_one_or_none()
    states_dict = {
        k: (v.model_dump() if hasattr(v, "model_dump") else v)
        for k, v in block_in.states.items()
    }

    if existing:
        existing.display_name = block_in.display_name
        existing.mode = block_in.mode
        existing.item_model = block_in.item_model
        existing.block_model = block_in.block_model or block_in.item_model
        existing.scale = block_in.scale
        existing.translation = block_in.translation
        existing.hitbox_type = block_in.hitbox_type
        existing.hitbox_offsets = block_in.hitbox_offsets
        existing.interaction_type = block_in.interaction_type
        existing.seat_height = block_in.seat_height
        existing.hardness = block_in.hardness
        existing.tool_type = block_in.tool_type
        existing.drop_item_id = block_in.drop_item_id
        existing.plugin_properties = block_in.plugin_properties
        existing.default_state = block_in.default_state
        existing.states = states_dict
    else:
        new_block = BlockModel(
            id=block_in.id,
            display_name=block_in.display_name,
            mode=block_in.mode,
            item_model=block_in.item_model,
            block_model=block_in.block_model or block_in.item_model,
            scale=block_in.scale,
            translation=block_in.translation,
            hitbox_type=block_in.hitbox_type,
            hitbox_offsets=block_in.hitbox_offsets,
            interaction_type=block_in.interaction_type,
            seat_height=block_in.seat_height,
            hardness=block_in.hardness,
            tool_type=block_in.tool_type,
            drop_item_id=block_in.drop_item_id,
            plugin_properties=block_in.plugin_properties,
            default_state=block_in.default_state,
            states=states_dict,
        )
        db.add(new_block)

    await db.commit()

    # Real-time broadcast to connected agents
    target_block = existing if existing else new_block
    block_dict = _serialize_block_model(target_block)
    try:
        online_targets = gateway_manager.get_online_targets()
        for target_id in online_targets:
            op_id = f"op-block-{uuid.uuid4().hex[:8]}"
            envelope_payload = {
                "action": "create_or_update_block",
                "operationId": op_id,
                "resourceKind": "block",
                "resourceId": block_in.id,
                "payload": block_dict,
                "block": block_dict,
                "prop": block_dict,
            }
            envelope = MessageEnvelope(
                messageType="request",
                messageId=f"msg-{uuid.uuid4().hex[:8]}",
                correlationId=op_id,
                targetId=target_id,
                payload=envelope_payload
            )
            await gateway_manager.send_to_target(target_id, envelope)
    except Exception:
        pass

    return block_in.model_dump()


@router.put("/{block_id}", response_model=dict)
@legacy_router.put("/{block_id}", response_model=dict)
async def update_block(block_id: str, block_in: BlockDefinition, db: AsyncSession = Depends(get_db)):
    if block_in.id != block_id:
        raise HTTPException(status_code=400, detail="Block ID in path does not match body")
    return await create_or_update_block(block_in, db)


@router.delete("/{block_id}")
@legacy_router.delete("/{block_id}")
async def delete_block(block_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(BlockModel).where(BlockModel.id == block_id))
    existing = result.scalar_one_or_none()
    if not existing:
        raise HTTPException(status_code=404, detail="Block not found")
    await db.delete(existing)
    await db.commit()
    return {"status": "deleted", "id": block_id}
