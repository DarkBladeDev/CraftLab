from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.models.entities import TargetModel
from app.gateway.manager import gateway_manager

router = APIRouter(prefix="/api/targets", tags=["targets"])


class CreateTargetRequest(BaseModel):
    id: str
    name: str
    secret: str = "dev-secret"


@router.get("", response_model=List[dict])
async def list_targets(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TargetModel))
    targets = result.scalars().all()
    return [
        {
            "id": t.id,
            "name": t.name,
            "status": "online" if gateway_manager.is_online(t.id) else t.status,
            "environment_metadata": t.environment_metadata or {},
            "last_seen_at": t.last_seen_at.isoformat() if t.last_seen_at else None,
            "created_at": t.created_at.isoformat() if t.created_at else None
        }
        for t in targets
    ]


@router.post("", response_model=dict)
async def register_target(req: CreateTargetRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(TargetModel).where(TargetModel.id == req.id))
    existing = result.scalar_one_or_none()
    if existing:
        existing.name = req.name
        existing.secret = req.secret
    else:
        new_target = TargetModel(
            id=req.id,
            name=req.name,
            secret=req.secret,
            status="offline",
            environment_metadata={}
        )
        db.add(new_target)
    await db.commit()
    return {"id": req.id, "name": req.name, "status": "registered"}
