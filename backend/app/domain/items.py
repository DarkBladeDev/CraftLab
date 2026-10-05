from typing import List, Optional
import re
from pydantic import BaseModel, Field, field_validator


class ItemDefinition(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier (slug) for the item", min_length=1, max_length=64)
    material: str = Field(..., description="Vanilla Minecraft material name, e.g. DIAMOND_SWORD")
    display_name: str = Field(..., description="Display name, supports MiniMessage or plain text", min_length=1)
    lore: List[str] = Field(default_factory=list, description="List of lore lines")
    custom_model_data: Optional[int] = Field(default=None, description="Custom model data integer for resource packs", ge=0)
    item_flags: List[str] = Field(default_factory=list, description="Item flags such as HIDE_ATTRIBUTES")
    amount: int = Field(default=1, ge=1, le=64, description="Stack size count (1-64)")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Item id must be lowercase alphanumeric with dashes or underscores only")
        return v

    @field_validator("material")
    @classmethod
    def validate_material(cls, v: str) -> str:
        cleaned = v.strip().upper()
        if not re.match(r"^[A-Z0-9_]+$", cleaned):
            raise ValueError("Material must be uppercase alphanumeric with underscores (e.g. DIAMOND_SWORD)")
        return cleaned

    def to_canonical_dict(self) -> dict:
        """Returns sorted, deterministic dictionary representation for canonical hashing."""
        return {
            "amount": self.amount,
            "custom_model_data": self.custom_model_data,
            "display_name": self.display_name,
            "id": self.id,
            "item_flags": sorted(self.item_flags),
            "lore": list(self.lore),
            "material": self.material,
        }
