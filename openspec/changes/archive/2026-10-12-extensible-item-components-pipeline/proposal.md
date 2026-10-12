# Proposal: Extensible Item Components Pipeline & Full Equippable Support

## Why

While CraftLab allows authoring Minecraft 1.21 data components like `minecraft:equippable`, `minecraft:attribute_modifiers`, and `minecraft:enchantments` in the Web Studio, deployed items served in-game via `/mcp give` lack the `minecraft:equippable` component and other item data components. This occurs because `Paper121ItemAdapter` in `CraftLab-plugin` currently only extracts legacy fields (`display_name`, `lore`, `custom_model_data`, `item_flags`) and the modern `item_model`, completely ignoring the item's `components` dictionary.

To resolve this issue and prepare CraftLab for modern Minecraft item authoring, the Paper agent requires a modular, extensible item component architecture that applies data components to native Bukkit `ItemStack` / `ItemMeta` with multi-version reflection safety across Paper 1.21.0 to 1.21.4+, featuring complete support for all required and optional `minecraft:equippable` properties.

## What Changes

- **Extensible Component Pipeline in Paper Plugin**: Introduce an `ItemComponentApplier` interface and an `ItemComponentRegistry` in `CraftLab-plugin` that dynamically maps component identifiers to specialized appliers.
- **Full `minecraft:equippable` Support**: Implement `EquippableComponentApplier` supporting all standard fields:
  - `slot`: `EquipmentSlot` (`HEAD`, `CHEST`, `LEGS`, `FEET`, `BODY`, `SADDLE`, `HAND`, `OFF_HAND`).
  - `asset_id` (with fallback to `model`): `NamespacedKey` via `setModel`.
  - `camera_overlay`: optional `NamespacedKey` via `setCameraOverlay`.
  - `equip_sound`: optional `Sound` or `NamespacedKey` via `setEquipSound`.
  - `allowed_entities`: optional collection or tag of `EntityType` via `setAllowedEntities`.
  - Boolean flags: `dispensable`, `swappable`, `damage_on_hurt`, and `can_be_sheared`.
- **Attribute Modifiers and Enchantments Appliers**: Implement `AttributeModifiersComponentApplier` (`minecraft:attribute_modifiers`) and `EnchantmentsComponentApplier` (`minecraft:enchantments`) so that existing Item Studio component fields are applied to in-game items.
- **Multi-Version Reflection & Safe Degradation**: Protect Paper 1.21.0 - 1.21.1 runtimes by reflectively querying component availability (`isSupported()`) to prevent `NoClassDefFoundError` or `NoSuchMethodError`.
- **Frontend Item Studio Equippable Controls**: Expand `ComponentBuilder.tsx` in `CraftLab-frontend` with an Advanced Options drawer allowing authors to configure `camera_overlay`, `equip_sound`, `allowed_entities`, and boolean behavioral flags.

## Capabilities

### New Capabilities
*(None - existing capabilities are modified)*

### Modified Capabilities
- `paper-agent-adapter`: Expand `Paper121ItemAdapter` to process the `components` map using a pluggable `ItemComponentRegistry`, applying `minecraft:equippable` with all fields, `minecraft:attribute_modifiers`, and `minecraft:enchantments` with multi-version runtime safety.
- `item-studio`: Expand the `minecraft:equippable` component authoring UI in `ComponentBuilder` to support all optional fields (`camera_overlay`, `equip_sound`, `allowed_entities`, `dispensable`, `swappable`, `damage_on_hurt`, `can_be_sheared`).

## Impact

- **Paper Plugin (`CraftLab-plugin`)**: New package `com.mcp.agent.adapters.components` with `ItemComponentApplier`, `ItemComponentRegistry`, and dedicated applier classes. `Paper121ItemAdapter.compile()` delegates component application to the registry.
- **Frontend (`CraftLab-frontend`)**: `ComponentBuilder.tsx` updated with advanced equippable fields; TypeScript interfaces in `client.ts` updated if needed.
- **Backend (`CraftLab-backend`)**: Existing generic `components: dict` in `ItemDefinition` already handles arbitrary component payloads without schema modification.
- **Compatibility**: Retains 100% backward compatibility on Paper 1.21.0 - 1.21.1 where `ItemMeta.getEquippable` is not present, while unlocking full native equippable and component support on Paper 1.21.2+.
