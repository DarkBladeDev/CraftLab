# Spec Delta: Item Studio

## ADDED Requirements

### Requirement: Hybrid Profile Legacy Equipment Synthesis and Binding
The Item Studio editor SHALL provide automated legacy attribute derivation and synchronization when an item binds the `minecraft:equippable` component and the active workspace profile is `hybrid_shaders`. The system MUST automatically assign an available `custom_model_data` integer, derive the 24-bit RGB `dyed_color` corresponding to the bound equipment model's shader atlas layer index, configure the base material to the matching leather armor slot (`LEATHER_HELMET`, `LEATHER_CHESTPLATE`, `LEATHER_LEGGINGS`, `LEATHER_BOOTS`) when a non-leather material is selected without legacy support, apply compensating `minecraft:attribute_modifiers` (providing armor defense and toughness values matching the requested tier), and append `HIDE_DYE` to `item_flags` so that dye details remain hidden from item tooltips.

#### Scenario: Binding equippable item in hybrid shader mode
- **WHEN** author binds an equipment model (e.g. `craftlab:ruby_armor`) to a custom chestplate item in `hybrid_shaders` mode
- **THEN** editor automatically populates `custom_model_data`, computes and sets the `dyed_color` RGB value for the shader atlas slot, populates compensating armor attribute modifiers, and displays a multi-version compatibility badge

#### Scenario: Visual compatibility indicator in item editor
- **WHEN** user inspects an item with equippable binding in Item Studio
- **THEN** editor displays a dual status badge showing "1.21.2+ Native Equippable" and "1.20-1.21.1 Core Shader Fallback" with the calculated RGB hex code and CMD index

#### Scenario: Disabling legacy synthesis in modern mode
- **WHEN** workspace profile is set to `modern_native`
- **THEN** editor preserves the original base material (e.g. `NETHERITE_CHESTPLATE`) without forcing leather material conversion or synthetic `dyed_color` attributes
