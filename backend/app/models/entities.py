from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TargetModel(Base):
    __tablename__ = "targets"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    secret = Column(String, nullable=False)
    status = Column(String, default="offline", nullable=False)  # offline, online
    environment_metadata = Column(JSON, default=dict)
    last_seen_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class ItemModel(Base):
    __tablename__ = "items"

    id = Column(String, primary_key=True, index=True)
    material = Column(String, nullable=False)
    display_name = Column(String, nullable=False)
    lore = Column(JSON, default=list)
    custom_model_data = Column(Integer, nullable=True)
    item_flags = Column(JSON, default=list)
    amount = Column(Integer, default=1)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class RevisionModel(Base):
    __tablename__ = "revisions"

    id = Column(String, primary_key=True, index=True)
    revision_number = Column(Integer, nullable=False, unique=True)
    revision_hash = Column(String, nullable=False)
    items_snapshot = Column(JSON, nullable=False, default=list)
    created_at = Column(DateTime, default=utcnow)


class DeploymentPlanModel(Base):
    __tablename__ = "deployment_plans"

    id = Column(String, primary_key=True, index=True)
    plan_hash = Column(String, nullable=False)
    revision_id = Column(String, ForeignKey("revisions.id"), nullable=False)
    target_id = Column(String, ForeignKey("targets.id"), nullable=False)
    operations = Column(JSON, nullable=False, default=list)
    status = Column(String, default="draft", nullable=False)  # draft, approved, applied, failed
    created_at = Column(DateTime, default=utcnow)

    revision = relationship("RevisionModel")
    target = relationship("TargetModel")


class DeploymentModel(Base):
    __tablename__ = "deployments"

    id = Column(String, primary_key=True, index=True)
    plan_id = Column(String, ForeignKey("deployment_plans.id"), nullable=False)
    status = Column(String, default="pending", nullable=False)  # pending, executing, applied, failed
    execution_log = Column(JSON, default=list)
    executed_at = Column(DateTime, default=utcnow)

    plan = relationship("DeploymentPlanModel")
