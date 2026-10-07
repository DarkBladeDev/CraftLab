from app.domain.items import ItemDefinition
from app.domain.blocks import BlockDefinition
from app.domain.revisions import compute_revision_hash, create_revision_snapshot


def test_deterministic_revision_hash():
    item1 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        lore=["Legendary weapon"],
        custom_model_data=1001
    )
    item2 = ItemDefinition(
        id="sapphire_pickaxe",
        material="DIAMOND_PICKAXE",
        display_name="Sapphire Pickaxe",
        lore=["Mines bedrock"],
        custom_model_data=1002
    )

    # Order in list shouldn't matter
    hash_forward = compute_revision_hash([item1, item2])
    hash_reversed = compute_revision_hash([item2, item1])

    assert hash_forward == hash_reversed
    assert len(hash_forward) == 64


def test_revision_hash_with_blocks_deterministic():
    item = ItemDefinition(id="ruby_sword", material="DIAMOND_SWORD", display_name="Ruby Sword")
    block1 = BlockDefinition(id="oak_chair", display_name="Oak Chair", mode="display_prop")
    block2 = BlockDefinition(id="oak_table", display_name="Oak Table", mode="display_prop")

    hash_forward = compute_revision_hash([item], [block1, block2])
    hash_reversed = compute_revision_hash([item], [block2, block1])

    assert hash_forward == hash_reversed
    assert len(hash_forward) == 64


def test_revision_hash_changes_on_block_change():
    item = ItemDefinition(id="ruby_sword", material="DIAMOND_SWORD", display_name="Ruby Sword")
    block_v1 = BlockDefinition(id="oak_chair", display_name="Oak Chair", scale=[1.0, 1.0, 1.0])
    block_v2 = BlockDefinition(id="oak_chair", display_name="Oak Chair", scale=[1.5, 1.5, 1.5])

    hash1 = compute_revision_hash([item], [block_v1])
    hash2 = compute_revision_hash([item], [block_v2])

    assert hash1 != hash2


def test_revision_hash_changes_on_content_change():
    item_v1 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        lore=["Old lore"]
    )
    item_v2 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        lore=["New updated lore"]
    )

    hash1 = compute_revision_hash([item_v1])
    hash2 = compute_revision_hash([item_v2])

    assert hash1 != hash2


def test_create_revision_snapshot():
    item = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword"
    )
    block = BlockDefinition(
        id="oak_chair",
        display_name="Oak Chair"
    )
    snapshot = create_revision_snapshot([item], revision_number=1, blocks=[block])
    assert snapshot["revision_number"] == 1
    assert snapshot["id"].startswith("rev-")
    assert snapshot["revision_hash"] == compute_revision_hash([item], [block])
    assert len(snapshot["items_snapshot"]) == 1
    assert len(snapshot["blocks_snapshot"]) == 1
    assert snapshot["blocks_snapshot"][0]["id"] == "oak_chair"


def test_revision_hash_changes_on_component_change():
    item_v1 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        components={}
    )
    item_v2 = ItemDefinition(
        id="ruby_sword",
        material="DIAMOND_SWORD",
        display_name="Ruby Sword",
        components={"minecraft:enchantments": {"sharpness": 5}}
    )
    assert compute_revision_hash([item_v1]) != compute_revision_hash([item_v2])
