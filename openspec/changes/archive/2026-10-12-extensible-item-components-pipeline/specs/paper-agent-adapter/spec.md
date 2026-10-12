# Spec Delta

## MODIFIED Requirements

### Requirement: Paper 1.21 Component Item Assembly
The Paper adapter SHALL assemble native Paper 1.21 ItemStacks using an extensible Data Component pipeline, applying `custom_model_data` for baseline 1.21.1 compatibility, `item_model` when running on Paper 1.21.2+, and delegating all entries in the `components` mapping to registered `ItemComponentApplier` instances (including full `minecraft:equippable` properties, `minecraft:attribute_modifiers`, and `minecraft:enchantments`), persist deployed items in local storage, and serve them via the `/mcp give` command.

#### Scenario: Item compilation and local persistence
- **WHEN** the Paper adapter handles `create_or_update_item`
- **THEN** it maps the canonical JSON definition to a native Paper 1.21 ItemStack, persists the definition in local storage, and records the item in the active item registry

#### Scenario: Giving item to player via command
- **WHEN** an operator runs `/mcp give <player> <item_id>` for an existing deployed item
- **THEN** the plugin retrieves the item definition from the active registry and gives the assembled ItemStack with correct name, lore, model data, and components to the target player

#### Scenario: Applying hybrid item_model and custom_model_data
- **WHEN** an item contains both `custom_model_data` and `item_model`
- **THEN** the adapter sets `ItemMeta.setCustomModelData` and, if available on the runtime Paper server version (1.21.2+), sets the native `item_model` component key

#### Scenario: Assembling prop ItemStack with item_model
- **WHEN** the agent creates an ItemStack for a prop with an `item_model` identifier
- **THEN** the adapter parses the namespaced key, invokes `setItemModel` using public interface reflection without throwing accessibility exceptions, embeds the persistent data container `mcp:prop_id` key, and avoids falling back to default un-modeled white wool

#### Scenario: Applying equippable component on Paper 1.21.2+
- **WHEN** an item contains `minecraft:equippable` with slot, `asset_id` (or fallback `model`), and optional fields (`camera_overlay`, `equip_sound`, `allowed_entities`, `dispensable`, `swappable`, `damage_on_hurt`, `can_be_sheared`) on a Paper 1.21.2+ server
- **THEN** the adapter reflectively obtains `EquippableComponent` from `ItemMeta`, sets the target slot enum, configures the asset model namespaced key, applies all configured optional attributes, and updates the `ItemMeta` so that the component is active in-game

#### Scenario: Safe equippable degradation on Paper 1.21.0 - 1.21.1
- **WHEN** an item contains `minecraft:equippable` on a Paper 1.21.0 or 1.21.1 server where equippable components are unsupported
- **THEN** the adapter safely skips equippable application without throwing `NoSuchMethodException` or `ClassNotFoundException`, allowing the item stack to compile with remaining baseline properties

#### Scenario: Applying attribute modifiers and enchantments
- **WHEN** an item contains `minecraft:attribute_modifiers` or `minecraft:enchantments`
- **THEN** the adapter delegates to the respective component appliers to apply attribute modifiers and enchantments with unrestricted levels to the `ItemMeta`
