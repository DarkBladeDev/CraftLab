# Spec Delta: Item Studio

## ADDED Requirements

### Requirement: Multi-Version Item Model Configuration Editor
The Studio editor SHALL provide input controls for configuring modern `item_model` namespaced identifiers alongside classic `custom_model_data`, displaying version compatibility indicators (1.21.1 legacy fallback vs 1.21.2+ modern definition) in real-time.

#### Scenario: Editing item_model identifier
- **WHEN** an author enters a custom `item_model` key in the studio item editor
- **THEN** the editor validates the format and shows active compatibility for both 1.21.1 and 1.21.2+ clients

#### Scenario: Auto-generating item_model from custom model data
- **WHEN** an author leaves `item_model` empty but defines `custom_model_data`
- **THEN** the editor displays the auto-derived identifier placeholder used for the 1.21.2+ overlay projection

## MODIFIED Requirements

### Requirement: Minecraft 1.21 Inventory Slot and Sprite Visualization
The system SHALL render an authentic Minecraft 3D beveled inventory slot displaying the crisp 16x16 PNG pixel-art sprite of the selected material, item stack count, and Custom Model Data / Item Model indicator.

#### Scenario: Rendering vanilla 1.21 material sprite
- **WHEN** an item has a valid Minecraft material such as `NETHERITE_SWORD` or `MACE`
- **THEN** the slot displays the corresponding 16x16 pixel-art PNG sprite scaled with nearest-neighbor crisp pixel rendering

#### Scenario: Displaying stack count and Custom Model Data badge
- **WHEN** an item defines an amount greater than 1 or a Custom Model Data value
- **THEN** the slot displays the stack count number in the lower right corner and an indicator badge for the Custom Model Data

#### Scenario: Displaying item_model badge
- **WHEN** an item defines an explicit `item_model` identifier
- **THEN** the slot displays a modern model indicator badge alongside the CMD badge
