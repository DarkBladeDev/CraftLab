# Spec Delta: Paper Agent and Adapter

## MODIFIED Requirements

### Requirement: Paper 1.21 Component Item Assembly
The Paper adapter SHALL assemble native Paper 1.21 ItemStacks using modern item data components, applying `custom_model_data` for baseline 1.21.1 compatibility and `item_model` component data when running on Paper 1.21.2+, persist deployed items to `items.json`, and serve them via the `/mcp give` command.

#### Scenario: Item compilation and local persistence
- **WHEN** the Paper adapter handles `create_or_update_item`
- **THEN** it maps the canonical JSON definition to a native Paper 1.21 ItemStack, persists the definition in `items.json`, and records the item in the active item registry

#### Scenario: Giving item to player via command
- **WHEN** an operator runs `/mcp give <player> <item_id>` for an existing deployed item
- **THEN** the plugin retrieves the item definition from the active registry and gives the assembled ItemStack with correct name, lore, model data, and components to the target player

#### Scenario: Applying hybrid item_model and custom_model_data
- **WHEN** an item contains both `custom_model_data` and `item_model`
- **THEN** the adapter sets `ItemMeta.setCustomModelData` and, if available on the runtime Paper server version (1.21.2+), sets the native `item_model` component key
