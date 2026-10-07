import pytest
from app.core.database import AsyncSessionLocal, init_db
from app.domain.pack_sources import PackRepository


@pytest.mark.asyncio
async def test_pack_repository_crud():
    await init_db()
    async with AsyncSessionLocal() as session:
        # Create source
        src = await PackRepository.create_or_update_source(
            db=session,
            source_id="src-test-studio",
            name="Studio Items",
            source_type="studio",
            storage_path="/data/packs/sources/studio",
            layer_priority=30,
            meta_info={"author": "admin"}
        )
        assert src.id == "src-test-studio"
        assert src.layer_priority == 30

        # Update source
        updated = await PackRepository.create_or_update_source(
            db=session,
            source_id="src-test-studio",
            name="Studio Custom Items",
            source_type="studio",
            storage_path="/data/packs/sources/studio",
            layer_priority=50,
            meta_info={"author": "admin", "v": 2}
        )
        assert updated.name == "Studio Custom Items"
        assert updated.layer_priority == 50

        # List sources ordered by layer_priority descending
        src2 = await PackRepository.create_or_update_source(
            db=session,
            source_id="src-test-plugin",
            name="Oraxen Plugin Pack",
            source_type="agent",
            plugin="oraxen",
            storage_path="/data/packs/sources/oraxen",
            layer_priority=20
        )

        sources = await PackRepository.list_sources(db=session)
        ids = [s.id for s in sources]
        assert "src-test-studio" in ids
        assert "src-test-plugin" in ids
        # Check ordering: priority 50 must be before priority 20
        idx_studio = ids.index("src-test-studio")
        idx_plugin = ids.index("src-test-plugin")
        assert idx_studio < idx_plugin

        # Get single source
        fetched = await PackRepository.get_source(db=session, source_id="src-test-plugin")
        assert fetched is not None
        assert fetched.plugin == "oraxen"

        # Record compiled pack
        pack = await PackRepository.record_compiled_pack(
            db=session,
            pack_id="pack-test-1",
            pack_name="resourcepack-main.zip",
            storage_path="/data/packs/dist/resourcepack-main.zip",
            file_size=1024,
            sha1_hash="a9993e364706816aba3e25717850c26c9cd0d89d",
            pack_format=34,
            build_summary={"textures": 10, "models": 5}
        )
        assert pack.id == "pack-test-1"
        assert pack.sha1_hash == "a9993e364706816aba3e25717850c26c9cd0d89d"

        # Fetch latest compiled pack
        latest = await PackRepository.get_latest_compiled_pack(db=session)
        assert latest is not None
        assert latest.id == "pack-test-1"

        # Cleanup
        del_res = await PackRepository.delete_source(db=session, source_id="src-test-studio")
        assert del_res is True
        del_res2 = await PackRepository.delete_source(db=session, source_id="src-test-plugin")
        assert del_res2 is True
