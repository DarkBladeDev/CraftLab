import pytest
from pydantic import ValidationError
from app.domain.items import ItemDefinition


def test_valid_item_definition():
    item = ItemDefinition(
        id="ruby_sword",
        material="diamond_sword",
        display_name="<red>Ruby Sword</red>",
        lore=["<gray>Sharp and deadly</gray>"],
        custom_model_data=1001,
        item_flags=["HIDE_ATTRIBUTES"],
        amount=1
    )
    assert item.id == "ruby_sword"
    assert item.material == "DIAMOND_SWORD"
    assert item.custom_model_data == 1001
    assert item.components == {}
    canonical = item.to_canonical_dict()
    assert canonical["id"] == "ruby_sword"
    assert canonical["material"] == "DIAMOND_SWORD"
    assert canonical["components"] == {}


def test_item_definition_with_121_components():
    item = ItemDefinition(
        id="ignis_blade",
        material="NETHERITE_SWORD",
        display_name="<gradient:#ff0000:#ffaa00>Ignis Blade</gradient>",
        components={
            "minecraft:attribute_modifiers": [
                {"type": "generic.attack_damage", "amount": 14.0, "slot": "mainhand"}
            ],
            "minecraft:enchantments": {"sharpness": 5}
        }
    )
    assert item.components["minecraft:enchantments"]["sharpness"] == 5
    canonical = item.to_canonical_dict()
    assert "minecraft:attribute_modifiers" in canonical["components"]


def test_invalid_item_id_rejected():
    with pytest.raises(ValidationError):
        ItemDefinition(
            id="Ruby Sword Invalid",
            material="DIAMOND_SWORD",
            display_name="Ruby Sword"
        )


def test_negative_custom_model_data_rejected():
    with pytest.raises(ValidationError):
        ItemDefinition(
            id="ruby_sword",
            material="DIAMOND_SWORD",
            display_name="Ruby Sword",
            custom_model_data=-5
        )


def test_invalid_material_rejected():
    with pytest.raises(ValidationError):
        ItemDefinition(
            id="ruby_sword",
            material="DIAMOND SWORD WITH SPACES!",
            display_name="Ruby Sword"
        )
