from typing import List, Optional
import re
from pydantic import BaseModel, Field, field_validator


class ItemDefinition(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier (slug) for the item", min_length=1, max_length=64)
    material: str = Field(..., description="Vanilla Minecraft material name, e.g. DIAMOND_SWORD")
    display_name: str = Field(..., description="Display name, supports MiniMessage or plain text", min_length=1)
    lore: List[str] = Field(default_factory=list, description="List of lore lines")
    custom_model_data: Optional[int] = Field(default=None, description="Custom model data integer for resource packs", ge=0)
    item_model: Optional[str] = Field(default=None, description="Namespaced item model identifier (e.g. 'studio:ruby_sword') for Minecraft 1.21.2+")
    item_flags: List[str] = Field(default_factory=list, description="Item flags such as HIDE_ATTRIBUTES")
    amount: int = Field(default=1, ge=1, le=64, description="Stack size count (1-64)")
    components: dict = Field(default_factory=dict, description="Minecraft 1.21 Data Components mapping")
    export_format: str = Field(default="native", description="Export target adapter: native, oraxen, nexo")
    plugin_properties: dict = Field(default_factory=dict, description="Structured plugin-specific properties")
    raw_extensions: Optional[str] = Field(default=None, description="Raw YAML/JSON extensions snippet")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Item id must be lowercase alphanumeric with dashes or underscores only")
        return v

    @field_validator("item_model")
    @classmethod
    def validate_item_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if not re.match(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", cleaned):
                raise ValueError("Item model must be a valid namespaced key (e.g. 'studio:ruby_sword')")
            return cleaned
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
            "components": self.components,
            "custom_model_data": self.custom_model_data,
            "display_name": self.display_name,
            "export_format": self.export_format,
            "id": self.id,
            "item_flags": sorted(self.item_flags),
            "item_model": self.item_model,
            "lore": list(self.lore),
            "material": self.material,
            "plugin_properties": self.plugin_properties,
            "raw_extensions": self.raw_extensions,
        }
