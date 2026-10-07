from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.entities import PackSourceModel, CompiledPackModel


class PackSourceSchema(BaseModel):
    id: str
    target_id: Optional[str] = None
    name: str
    source_type: str  # "studio", "upload", "agent"
    plugin: Optional[str] = None
    layer_priority: int = 10
    storage_path: str
    sha1_hash: Optional[str] = None
    meta_info: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class CompiledPackSchema(BaseModel):
    id: str
    target_id: Optional[str] = None
    pack_name: str
    storage_path: str
    file_size: int = 0
    sha1_hash: str
    pack_format: int = 34
    build_summary: Dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class PackRepository:
    @staticmethod
    async def create_or_update_source(
        db: AsyncSession,
        source_id: str,
        name: str,
        source_type: str,
        storage_path: str,
        target_id: Optional[str] = None,
        plugin: Optional[str] = None,
        layer_priority: int = 10,
        sha1_hash: Optional[str] = None,
        meta_info: Optional[Dict[str, Any]] = None,
        is_active: bool = True
    ) -> PackSourceModel:
        query = select(PackSourceModel).where(PackSourceModel.id == source_id)
        result = await db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            existing.name = name
            existing.source_type = source_type
            existing.target_id = target_id
            existing.plugin = plugin
            existing.layer_priority = layer_priority
            existing.storage_path = storage_path
            existing.sha1_hash = sha1_hash
            if meta_info is not None:
                existing.meta_info = meta_info
            existing.is_active = is_active
            await db.commit()
            await db.refresh(existing)
            return existing

        new_source = PackSourceModel(
            id=source_id,
            target_id=target_id,
            name=name,
            source_type=source_type,
            plugin=plugin,
            layer_priority=layer_priority,
            storage_path=storage_path,
            sha1_hash=sha1_hash,
            meta_info=meta_info or {},
            is_active=is_active
        )
        db.add(new_source)
        await db.commit()
        await db.refresh(new_source)
        return new_source

    @staticmethod
    async def list_sources(
        db: AsyncSession,
        target_id: Optional[str] = None,
        active_only: bool = True
    ) -> List[PackSourceModel]:
        query = select(PackSourceModel)
        if target_id is not None:
            query = query.where((PackSourceModel.target_id == target_id) | (PackSourceModel.target_id.is_(None)))
        if active_only:
            query = query.where(PackSourceModel.is_active.is_(True))
        query = query.order_by(desc(PackSourceModel.layer_priority), PackSourceModel.name)
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def get_source(db: AsyncSession, source_id: str) -> Optional[PackSourceModel]:
        result = await db.execute(select(PackSourceModel).where(PackSourceModel.id == source_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def delete_source(db: AsyncSession, source_id: str) -> bool:
        result = await db.execute(select(PackSourceModel).where(PackSourceModel.id == source_id))
        item = result.scalar_one_or_none()
        if item:
            await db.delete(item)
            await db.commit()
            return True
        return False

    @staticmethod
    async def record_compiled_pack(
        db: AsyncSession,
        pack_id: str,
        pack_name: str,
        storage_path: str,
        file_size: int,
        sha1_hash: str,
        pack_format: int = 34,
        target_id: Optional[str] = None,
        build_summary: Optional[Dict[str, Any]] = None
    ) -> CompiledPackModel:
        new_pack = CompiledPackModel(
            id=pack_id,
            target_id=target_id,
            pack_name=pack_name,
            storage_path=storage_path,
            file_size=file_size,
            sha1_hash=sha1_hash,
            pack_format=pack_format,
            build_summary=build_summary or {},
            is_active=True
        )
        db.add(new_pack)
        await db.commit()
        await db.refresh(new_pack)
        return new_pack

    @staticmethod
    async def get_latest_compiled_pack(
        db: AsyncSession,
        target_id: Optional[str] = None
    ) -> Optional[CompiledPackModel]:
        query = select(CompiledPackModel).where(CompiledPackModel.is_active.is_(True))
        if target_id is not None:
            query = query.where((CompiledPackModel.target_id == target_id) | (CompiledPackModel.target_id.is_(None)))
        query = query.order_by(desc(CompiledPackModel.created_at)).limit(1)
        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_compiled_packs(
        db: AsyncSession,
        target_id: Optional[str] = None
    ) -> List[CompiledPackModel]:
        query = select(CompiledPackModel)
        if target_id is not None:
            query = query.where((CompiledPackModel.target_id == target_id) | (CompiledPackModel.target_id.is_(None)))
        query = query.order_by(desc(CompiledPackModel.created_at))
        result = await db.execute(query)
        return list(result.scalars().all())
