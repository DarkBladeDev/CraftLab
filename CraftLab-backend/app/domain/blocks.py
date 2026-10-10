from typing import List, Optional, Dict
import re
from pydantic import BaseModel, Field, field_validator, model_validator


class PropStateSound(BaseModel):
    key: str = Field(..., description="Sound event identifier e.g. 'block.wooden_button.click_on'")
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    pitch: float = Field(default=1.0, ge=0.5, le=2.0)


class PropStateDefinition(BaseModel):
    name: Optional[str] = Field(default=None, description="Human readable state label")
    block_model: Optional[str] = Field(default=None, description="Namespaced block model identifier for this state")
    light_level: int = Field(default=0, ge=0, le=15, description="Light level between 0 and 15")
    sound: Optional[PropStateSound] = Field(default=None, description="Sound effect played on entry")
    hitbox_type: Optional[str] = Field(default=None, description="Optional collision override: solid or passable")
    next_state: Optional[str] = Field(default=None, description="Target state key on interaction")

    @field_validator("hitbox_type")
    @classmethod
    def validate_hitbox_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            cleaned = v.strip().lower()
            if cleaned not in ("solid", "passable"):
                raise ValueError("Hitbox type must be either 'solid' or 'passable'")
            return cleaned
        return None

    @field_validator("block_model")
    @classmethod
    def validate_block_model(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            cleaned = v.strip().lower()
            if not re.match(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", cleaned):
                raise ValueError("Model identifier must be a valid namespaced key (e.g. 'studio:furniture/oak_chair')")
            return cleaned
        return None


class BlockDefinition(BaseModel):
    id: str = Field(..., description="Unique alphanumeric identifier (slug) for the block/prop", min_length=1, max_length=64)
    display_name: str = Field(..., description="Display name, supports MiniMessage or plain text", min_length=1)
    mode: str = Field(default="display_prop", description="Block implementation mode: display_prop or noteblock")
    item_model: Optional[str] = Field(default=None, description="Namespaced item model identifier (e.g. 'studio:furniture/oak_chair')")
    block_model: Optional[str] = Field(default=None, description="Namespaced block model identifier for 3D placed display")
    scale: List[float] = Field(default_factory=lambda: [1.0, 1.0, 1.0], description="Scale factors [x, y, z]")
    translation: List[float] = Field(default_factory=lambda: [0.0, 0.0, 0.0], description="Anchor translation offsets [x, y, z]")
    hitbox_type: str = Field(default="solid", description="Collision hitbox type: solid or passable")
    hitbox_offsets: List[List[int]] = Field(default_factory=lambda: [[0, 0, 0]], description="Relative grid offsets [x, y, z] occupied by collision")
    interaction_type: Optional[str] = Field(default="none", description="Interaction behavior: none, seat, lay, etc.")
    seat_height: float = Field(default=0.5, description="Y height offset where a player sits/lays when interaction_type is seat/lay")
    hardness: float = Field(default=1.0, ge=0.0, description="Block breaking hardness")
    tool_type: str = Field(default="AXE", description="Optimal harvest tool: AXE, PICKAXE, SHOVEL, etc.")
    drop_item_id: Optional[str] = Field(default=None, description="Item identifier dropped upon destruction")
    plugin_properties: dict = Field(default_factory=dict, description="Structured plugin-specific properties")
    default_state: str = Field(default="default", description="Active initial state key")
    states: Dict[str, PropStateDefinition] = Field(default_factory=dict, description="Named prop states mapping")

    @model_validator(mode="after")
    def validate_block_and_states(self):
        if not self.block_model and self.item_model:
            self.block_model = self.item_model
        if self.states:
            if self.default_state not in self.states:
                if "default" in self.states:
                    self.default_state = "default"
                elif len(self.states) > 0:
                    if self.default_state == "default":
                        self.default_state = next(iter(self.states.keys()))
                    else:
                        raise ValueError(f"default_state '{self.default_state}' not found in defined states: {list(self.states.keys())}")
            for state_key, state_def in self.states.items():
                if state_def.next_state and state_def.next_state not in self.states:
                    raise ValueError(f"State '{state_key}' points to non-existent next_state '{state_def.next_state}'")
        return self

    @field_validator("interaction_type")
    @classmethod
    def validate_interaction_type(cls, v: Optional[str]) -> str:
        if not v:
            return "none"
        cleaned = v.strip().lower()
        if cleaned not in ("none", "seat", "lay", "container", "custom"):
            raise ValueError("Interaction type must be one of: 'none', 'seat', 'lay', 'container', 'custom'")
        return cleaned

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

    @field_validator("item_model", "block_model")
    @classmethod
    def validate_model_identifier(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            cleaned = v.strip().lower()
            if not re.match(r"^[a-z0-9_.-]+:[a-z0-9_./-]+$", cleaned):
                raise ValueError("Model identifier must be a valid namespaced key (e.g. 'studio:furniture/oak_chair')")
            return cleaned
        return None

    def to_canonical_dict(self) -> dict:
        """Returns sorted, deterministic dictionary representation for canonical hashing."""
        states_dict = {}
        for k in sorted(self.states.keys()):
            s = self.states[k]
            states_dict[k] = {
                "block_model": s.block_model,
                "hitbox_type": s.hitbox_type,
                "light_level": s.light_level,
                "name": s.name,
                "next_state": s.next_state,
                "sound": {
                    "key": s.sound.key,
                    "pitch": round(float(s.sound.pitch), 4),
                    "volume": round(float(s.sound.volume), 4),
                } if s.sound else None,
            }

        return {
            "block_model": self.block_model or self.item_model,
            "default_state": self.default_state,
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
            "states": states_dict,
            "tool_type": self.tool_type.upper(),
            "translation": [round(float(t), 4) for t in self.translation],
        }
