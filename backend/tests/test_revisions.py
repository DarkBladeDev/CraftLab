from app.domain.items import ItemDefinition
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
    snapshot = create_revision_snapshot([item], revision_number=1)
    assert snapshot["revision_number"] == 1
    assert snapshot["id"].startswith("rev-")
    assert snapshot["revision_hash"] == compute_revision_hash([item])
    assert len(snapshot["items_snapshot"]) == 1
