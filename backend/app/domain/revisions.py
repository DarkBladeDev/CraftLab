import hashlib
import json
import uuid
from typing import List, Dict, Any
from app.domain.items import ItemDefinition


def compute_revision_hash(items: List[ItemDefinition]) -> str:
    """
    Computes a deterministic SHA-256 hash across canonical item representations.
    Items are sorted by their identifier, and dictionary keys are sorted canonically.
    """
    sorted_items = sorted(items, key=lambda i: i.id)
    canonical_list = [item.to_canonical_dict() for item in sorted_items]
    serialized = json.dumps(canonical_list, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def create_revision_snapshot(items: List[ItemDefinition], revision_number: int) -> Dict[str, Any]:
    """
    Creates an immutable revision payload dictionary.
    """
    rev_hash = compute_revision_hash(items)
    snapshot = [item.to_canonical_dict() for item in sorted(items, key=lambda i: i.id)]
    return {
        "id": f"rev-{uuid.uuid4().hex[:12]}",
        "revision_number": revision_number,
        "revision_hash": rev_hash,
        "items_snapshot": snapshot
    }
