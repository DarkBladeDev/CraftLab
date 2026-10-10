from datetime import datetime, timezone
from sqlalchemy import Column, String, Float, DateTime, JSON
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class BlockModel(Base):
    __tablename__ = "blocks"

    id = Column(String, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    mode = Column(String, default="display_prop", nullable=False)
    item_model = Column(String, nullable=True)
    block_model = Column(String, nullable=True)
    scale = Column(JSON, default=lambda: [1.0, 1.0, 1.0])
    translation = Column(JSON, default=lambda: [0.0, 0.0, 0.0])
    hitbox_type = Column(String, default="solid", nullable=False)
    hitbox_offsets = Column(JSON, default=lambda: [[0, 0, 0]])
    interaction_type = Column(String, default="none", nullable=True)
    seat_height = Column(Float, default=0.5, nullable=False)
    hardness = Column(Float, default=1.0, nullable=False)
    tool_type = Column(String, default="AXE", nullable=False)
    drop_item_id = Column(String, nullable=True)
    plugin_properties = Column(JSON, default=dict)
    default_state = Column(String, default="default", nullable=True)
    states = Column(JSON, default=dict)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
