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
