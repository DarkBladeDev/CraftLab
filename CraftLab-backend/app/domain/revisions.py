import hashlib
import json
import uuid
from typing import List, Dict, Any, Optional
from app.domain.items import ItemDefinition
from app.domain.blocks import BlockDefinition


def compute_revision_hash(
    items: List[ItemDefinition],
    blocks: Optional[List[BlockDefinition]] = None
) -> str:
    """
    Computes a deterministic SHA-256 hash across canonical item and block representations.
    Items and blocks are sorted by their identifier, and dictionary keys are sorted canonically.
    """
    sorted_items = sorted(items, key=lambda i: i.id)
    sorted_blocks = sorted(blocks or [], key=lambda b: b.id)
    canonical_items = [item.to_canonical_dict() for item in sorted_items]
    canonical_blocks = [block.to_canonical_dict() for block in sorted_blocks]
    combined_payload = {
        "blocks": canonical_blocks,
        "items": canonical_items
    }
    serialized = json.dumps(combined_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_revision_snapshot(
    items: List[ItemDefinition],
    revision_number: int,
    blocks: Optional[List[BlockDefinition]] = None
) -> Dict[str, Any]:
    """
    Creates an immutable revision payload dictionary across items and blocks.
    """
    blist = blocks or []
    rev_hash = compute_revision_hash(items, blist)
    items_snapshot = [item.to_canonical_dict() for item in sorted(items, key=lambda i: i.id)]
    blocks_snapshot = [block.to_canonical_dict() for block in sorted(blist, key=lambda b: b.id)]
    return {
        "id": f"rev-{uuid.uuid4().hex[:12]}",
        "revision_number": revision_number,
        "revision_hash": rev_hash,
        "items_snapshot": items_snapshot,
        "blocks_snapshot": blocks_snapshot
    }
