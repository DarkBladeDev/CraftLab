import hashlib
import json
import uuid
from typing import List, Dict, Any
from app.models.entities import RevisionModel, TargetModel, DeploymentPlanModel


def compute_plan_hash(revision_hash: str, target_id: str, operations: List[Dict[str, Any]]) -> str:
    content = {
        "revision_hash": revision_hash,
        "target_id": target_id,
        "operations": operations
    }
    serialized = json.dumps(content, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def generate_deployment_plan(revision: RevisionModel, target: TargetModel) -> DeploymentPlanModel:
    operations = []
    for item in (revision.items_snapshot or []):
        op = {
            "operationId": f"op-{uuid.uuid4().hex[:8]}",
            "action": "create_or_update_item",
            "resourceKind": "item",
            "resourceId": item["id"],
            "payload": item
        }
        operations.append(op)

    for block in (revision.blocks_snapshot or []):
        op = {
            "operationId": f"op-{uuid.uuid4().hex[:8]}",
            "action": "create_or_update_block",
            "resourceKind": "block",
            "resourceId": block["id"],
            "payload": block
        }
        operations.append(op)

    plan_hash = compute_plan_hash(revision.revision_hash, target.id, operations)
    plan_id = f"plan-{uuid.uuid4().hex[:12]}"

    return DeploymentPlanModel(
        id=plan_id,
        plan_hash=plan_hash,
        revision_id=revision.id,
        target_id=target.id,
        operations=operations,
        status="draft"
    )
