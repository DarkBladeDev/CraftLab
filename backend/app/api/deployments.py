import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from app.core.database import get_db
from app.models.entities import TargetModel, RevisionModel, DeploymentPlanModel, DeploymentModel
from app.domain.deployment import generate_deployment_plan
from app.gateway.manager import gateway_manager
from app.protocol.envelope import MessageEnvelope

router = APIRouter(prefix="/api/deployments", tags=["deployments"])


class CreatePlanRequest(BaseModel):
    revision_id: str
    target_id: str


@router.post("/plans", response_model=dict)
async def create_plan(req: CreatePlanRequest, db: AsyncSession = Depends(get_db)):
    rev_res = await db.execute(select(RevisionModel).where(RevisionModel.id == req.revision_id))
    revision = rev_res.scalar_one_or_none()
    if not revision:
        raise HTTPException(status_code=404, detail="Revision not found")

    target_res = await db.execute(select(TargetModel).where(TargetModel.id == req.target_id))
    target = target_res.scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=404, detail="Target server not found")

    plan = generate_deployment_plan(revision, target)
    db.add(plan)
    await db.commit()

    return {
        "id": plan.id,
        "plan_hash": plan.plan_hash,
        "revision_id": plan.revision_id,
        "target_id": plan.target_id,
        "status": plan.status,
        "operations": plan.operations
    }


@router.get("/plans/{plan_id}", response_model=dict)
async def get_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DeploymentPlanModel).where(DeploymentPlanModel.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Deployment plan not found")

    return {
        "id": plan.id,
        "plan_hash": plan.plan_hash,
        "revision_id": plan.revision_id,
        "target_id": plan.target_id,
        "status": plan.status,
        "operations": plan.operations,
        "created_at": plan.created_at.isoformat() if plan.created_at else None
    }


@router.post("/plans/{plan_id}/approve", response_model=dict)
async def approve_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DeploymentPlanModel).where(DeploymentPlanModel.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Deployment plan not found")

    if plan.status == "applied":
        raise HTTPException(status_code=400, detail="Plan has already been applied")

    plan.status = "approved"
    await db.commit()
    return {"id": plan.id, "status": "approved", "plan_hash": plan.plan_hash}


@router.post("/plans/{plan_id}/execute", response_model=dict)
async def execute_plan(plan_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(DeploymentPlanModel).where(DeploymentPlanModel.id == plan_id))
    plan = res.scalar_one_or_none()
    if not plan:
        raise HTTPException(status_code=404, detail="Deployment plan not found")

    if plan.status != "approved":
        raise HTTPException(status_code=400, detail=f"Cannot execute plan with status '{plan.status}'. Approval required.")

    if not gateway_manager.is_online(plan.target_id):
        raise HTTPException(status_code=503, detail=f"Target server '{plan.target_id}' is offline.")

    deployment_id = f"dep-{uuid.uuid4().hex[:12]}"
    deployment = DeploymentModel(
        id=deployment_id,
        plan_id=plan.id,
        status="executing",
        execution_log=[]
    )
    db.add(deployment)
    await db.commit()

    execution_log: List[Dict[str, Any]] = []
    has_failure = False

    for op in plan.operations:
        op_id = op["operationId"]
        envelope = MessageEnvelope(
            messageType="request",
            messageId=f"msg-{uuid.uuid4().hex[:8]}",
            correlationId=op_id,
            targetId=plan.target_id,
            payload={
                "action": op["action"],
                "operationId": op_id,
                "item": op["payload"]
            }
        )

        try:
            result = await gateway_manager.send_request(plan.target_id, envelope, timeout=10.0)
            execution_log.append({
                "operationId": op_id,
                "action": op["action"],
                "status": "success",
                "result": result
            })
        except Exception as e:
            has_failure = True
            execution_log.append({
                "operationId": op_id,
                "action": op["action"],
                "status": "failed",
                "error": str(e)
            })
            break

    deployment.execution_log = execution_log
    if has_failure:
        deployment.status = "failed"
        plan.status = "failed"
    else:
        deployment.status = "applied"
        plan.status = "applied"

    await db.commit()

    return {
        "deployment_id": deployment.id,
        "plan_id": plan.id,
        "status": deployment.status,
        "log": execution_log
    }
