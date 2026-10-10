import pytest
from pydantic import ValidationError
from app.domain.blocks import BlockDefinition


def test_valid_block_definition():
    block = BlockDefinition(
        id="oak_chair",
        display_name="<yellow>Oak Chair</yellow>",
        mode="display_prop",
        item_model="studio:furniture/oak_chair",
        scale=[1.0, 1.0, 1.0],
        translation=[0.0, 0.0, 0.0],
        hitbox_type="solid",
        hitbox_offsets=[[0, 0, 0]],
        interaction_type="seat",
        seat_height=0.45,
        hardness=1.5,
        tool_type="AXE",
        drop_item_id="oak_chair_item"
    )
    assert block.id == "oak_chair"
    assert block.display_name == "<yellow>Oak Chair</yellow>"
    assert block.mode == "display_prop"
    assert block.interaction_type == "seat"
    assert block.seat_height == 0.45
    canonical = block.to_canonical_dict()
    assert canonical["id"] == "oak_chair"
    assert canonical["mode"] == "display_prop"
    assert canonical["seat_height"] == 0.45
    assert canonical["hitbox_offsets"] == [[0, 0, 0]]


def test_invalid_block_id_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="Oak Chair Invalid Name",
            display_name="Chair"
        )


def test_invalid_mode_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="chair",
            display_name="Chair",
            mode="unsupported_mode"
        )


def test_invalid_scale_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="chair",
            display_name="Chair",
            scale=[1.0, -0.5, 1.0]
        )
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="chair",
            display_name="Chair",
            scale=[1.0, 1.0]
        )


def test_invalid_hitbox_type_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="chair",
            display_name="Chair",
            hitbox_type="liquid"
        )


def test_invalid_item_model_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="chair",
            display_name="Chair",
            item_model="invalid_model_format"
        )


def test_multi_block_hitbox_sorting():
    block = BlockDefinition(
        id="long_bench",
        display_name="Long Bench",
        hitbox_offsets=[[0, 0, 1], [0, 0, 0]]
    )
    canonical = block.to_canonical_dict()
    assert canonical["hitbox_offsets"] == [[0, 0, 0], [0, 0, 1]]


def test_dual_model_block_definition():
    block = BlockDefinition(
        id="grand_sofa",
        display_name="Grand Sofa",
        item_model="studio:items/grand_sofa",
        block_model="studio:props/grand_sofa_3d",
        interaction_type="lay",
        seat_height=0.3
    )
    assert block.item_model == "studio:items/grand_sofa"
    assert block.block_model == "studio:props/grand_sofa_3d"
    assert block.interaction_type == "lay"
    canonical = block.to_canonical_dict()
    assert canonical["item_model"] == "studio:items/grand_sofa"
    assert canonical["block_model"] == "studio:props/grand_sofa_3d"
    assert canonical["interaction_type"] == "lay"


def test_block_model_fallback_to_item_model():
    block = BlockDefinition(
        id="simple_chair",
        display_name="Simple Chair",
        item_model="studio:furniture/chair"
    )
    assert block.block_model == "studio:furniture/chair"
    canonical = block.to_canonical_dict()
    assert canonical["block_model"] == "studio:furniture/chair"


def test_multi_state_prop_validation():
    block = BlockDefinition(
        id="vintage_lamp",
        display_name="Vintage Lamp",
        default_state="off",
        states={
            "off": {
                "name": "Apagada",
                "block_model": "studio:props/lamp_off",
                "light_level": 0,
                "next_state": "on"
            },
            "on": {
                "name": "Encendida",
                "block_model": "studio:props/lamp_on",
                "light_level": 14,
                "sound": {
                    "key": "block.wooden_button.click_on",
                    "volume": 0.8,
                    "pitch": 1.0
                },
                "next_state": "off"
            }
        }
    )
    assert block.default_state == "off"
    assert len(block.states) == 2
    assert block.states["on"].light_level == 14
    assert block.states["on"].sound.key == "block.wooden_button.click_on"
    canonical = block.to_canonical_dict()
    assert canonical["default_state"] == "off"
    assert "off" in canonical["states"]
    assert "on" in canonical["states"]
    assert canonical["states"]["on"]["light_level"] == 14


def test_invalid_light_level_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="faulty_lamp",
            display_name="Faulty Lamp",
            states={
                "on": {
                    "block_model": "studio:props/lamp_on",
                    "light_level": 16
                }
            }
        )


def test_dangling_next_state_rejected():
    with pytest.raises(ValidationError):
        BlockDefinition(
            id="faulty_switch",
            display_name="Faulty Switch",
            states={
                "off": {
                    "block_model": "studio:props/switch_off",
                    "next_state": "invalid_state_key"
                }
            }
        )


def test_backward_compatibility_empty_states():
    block = BlockDefinition(
        id="classic_chair",
        display_name="Classic Chair",
        item_model="studio:furniture/chair"
    )
    assert block.default_state == "default"
    assert block.states == {}
    canonical = block.to_canonical_dict()
    assert canonical["states"] == {}

