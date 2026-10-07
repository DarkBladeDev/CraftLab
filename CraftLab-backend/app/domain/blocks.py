from typing import List, Optional
import re
from pydantic import BaseModel, Field, field_validator


class BlockDefinition(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier (slug) for the block/prop", min_length=1, max_length=64)
    display_name: str = Field(..., description="Display name, supports MiniMessage or plain text", min_length=1)
    mode: str = Field(default="display_prop", description="Block implementation mode: display_prop or noteblock")
    item_model: Optional[str] = Field(default=None, description="Namespaced item model identifier (e.g. 'studio:furniture/oak_chair')")
    scale: List[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0], description="Scale factors [x, y, z]")
    translation: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0], description="Anchor translation offsets [x, y, z]")
    hitbox_type: str = Field(default="solid", description="Collision hitbox type: solid or passable")
    hitbox_offsets: List[List[int]] = Field(default_factory=lambda: [[0, 0, 0]], description="Relative grid offsets [x, y, z] occupied by collision")
    interaction_type: Optional[str] = Field(default="none", description="Interaction behavior: none, seat, etc.")
    seat_height: float = Field(default=0.5, description="Y height offset where a player sits when interaction_type is seat")
    hardness: float = Field(default=1.0, ge=0.0, description="Block breaking hardness")
    tool_type: str = Field(default="AXE", description="Optimal harvest tool: AXE, PICKAXE, SHOVEL, etc.")
    drop_item_id: Optional[str] = Field(default=None, description="Item identifier dropped upon destruction")
    plugin_properties: dict = Field(default_factory=dict, description="Structured plugin-specific properties")

    @field_validator("id")
    @classmethod
    def validate_id(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError("Block id must be lowercase alphanumeric with dashes or underscores only")
        return v

    @field_validator("mode")
    @classmethod
    def validate_mode(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ("display_prop", "noteblock"):
            raise ValueError("Mode must be either 'display_prop' or 'noteblock'")
        return cleaned

    @field_validator("hitbox_type")
    @classmethod
    def validate_hitbox_type(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if cleaned not in ("solid", "passable"):
            raise ValueError("Hitbox type must be either 'solid' or 'passable'")
        return cleaned

    @field_validator("scale")
    @classmethod
    def validate_scale(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("Scale must be a 3-element list [x, y, z]")
        for val in v:
            if val < 0.0:
                raise ValueError("Scale components must be non-negative")
        return v

    @field_validator("translation")
    @classmethod
    def validate_translation(cls, v: List[float]) -> List[float]:
        if len(v) != 3:
            raise ValueError("Translation must be a 3-element list [x, y, z]")
        return v

    @field_validator("item_model")
    @classmethod
    def validate_item_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if not re.match(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", cleaned):
                raise ValueError("Item model must be a valid namespaced key (e.g. 'studio:furniture/oak_chair')")
            return cleaned
        return v

    def to_canonical_dict(self) -> dict:
        """Returns sorted, deterministic dictionary representation for canonical hashing."""
        return {
            "display_name": self.display_name,
            "drop_item_id": self.drop_item_id,
            "hardness": round(self.hardness, 4),
            "hitbox_offsets": sorted([list(offset) for offset in self.hitbox_offsets]),
            "hitbox_type": self.hitbox_type,
            "id": self.id,
            "interaction_type": self.interaction_type,
            "item_model": self.item_model,
            "mode": self.mode,
            "plugin_properties": self.plugin_properties,
            "scale": [round(float(s), 4) for s in self.scale],
            "seat_height": round(float(self.seat_height), 4),
            "tool_type": self.tool_type.upper(),
            "translation": [round(float(t), 4) for t in self.translation],
        }
