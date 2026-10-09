# Spec Delta

## MODIFIED Requirements

### Requirement: Prop Placement with 4-Way Cardinal Rotation and Barrier Collisions
The Paper agent SHALL handle prop placement by performing spatial clearance validation across all hitbox offsets, calculating the player's horizontal cardinal facing (North, South, East, West), applying cardinal offset rotation, and placing collision blocks matching the configured hitbox type across all occupied blocks. When a prop is broken, the agent MUST broadcast destroy packets to all viewing players before cleaning up tracking metadata and clear all associated collision blocks.

#### Scenario: Placing a directional chair prop
- **WHEN** a player right-clicks a solid surface with a prop item while facing South
- **THEN** the agent checks spatial clearance across all rotated offsets, places a barrier collision block tagged with the prop instance ID, calculates a 0-degree yaw rotation quaternion, registers the prop instance, and broadcasts the virtual display packet

#### Scenario: Breaking a placed prop
- **WHEN** a player breaks any collision block associated with a registered prop
- **THEN** the agent cancels the vanilla barrier drop, broadcasts `WrapperPlayServerDestroyEntities` to all viewing players before evicting the entity ID, spawns the configured `drop_item_id`, cleans up all associated collision offsets by setting them to AIR, and removes the prop from memory and disk

#### Scenario: Pre-placement spatial collision check
- **WHEN** a player attempts to place a prop with multi-block hitbox offsets where one or more target offset positions contain non-replaceable solid blocks
- **THEN** the agent cancels the placement event, preserves the player's held item, and emits no collision blocks or display packets

#### Scenario: Placing a directional multi-block prop
- **WHEN** a player places a prop having multi-block hitbox presets (such as 2x1 long or 2x2 table) while facing a cardinal direction
- **THEN** the agent rotates the local hitbox offsets around the Y axis according to the cardinal yaw, validates all block locations as clear, places collision blocks (`BARRIER` for solid or `STRUCTURE_VOID` for passable) across every offset, registers the multi-block locations in the spatial index, and broadcasts the virtual display packet

### Requirement: Prop Interaction and Native Sit Mechanics
The Paper agent SHALL support interactive props, allowing players to sit or lay down on props designated with `interaction_type: "seat"` or `interaction_type: "lay"` upon right-clicking any collision block belonging to the prop, applying calibrated vertical offsets relative to the interaction surface.

#### Scenario: Player sits on chair
- **WHEN** a player right-clicks any collision block of a chair prop configured with `interaction_type: "seat"`
- **THEN** the agent locates the prop instance via the multi-block spatial index, spawns a temporary invisible seat vehicle at the configured seat height offset above the interacted block base, mounts the player, and plays an interaction sound effect

#### Scenario: Player dismounts from chair
- **WHEN** a sitting or lying player presses sneak (SHIFT) or dismounts
- **THEN** the agent immediately removes the temporary seat vehicle, resets player pose if previously lying, and teleports the player slightly forward/upward to prevent collision trapping

#### Scenario: Player lies down on prop
- **WHEN** a player right-clicks any collision block of a prop configured with `interaction_type: "lay"`
- **THEN** the agent mounts the player on the temporary seat entity, dispatches `EntityPose.SLEEPING` metadata packets to the player and surrounding viewers, and maintains the lying orientation until dismount

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

#### Scenario: Assembling prop ItemStack with item_model
- **WHEN** the agent creates an ItemStack for a prop with an `item_model` identifier
- **THEN** the adapter parses the namespaced key, invokes `setItemModel` using public interface reflection without throwing accessibility exceptions, embeds the persistent data container `mcp:prop_id` key, and avoids falling back to default un-modeled white wool

## ADDED Requirements

### Requirement: Real-Time Prop Definition Synchronization
The platform SHALL synchronize prop definitions from the control plane to connected Paper server agents over WebSocket in real time upon modification in Studio, updating local agent cache and SQLite storage without requiring a full revision deployment or manual server reload.

#### Scenario: Saving prop definition in Block Studio
- **WHEN** an administrator saves or modifies a prop definition in Block Studio
- **THEN** the backend dispatches a `create_or_update_block` envelope to all online target agents, and each connected agent registers and persists the updated definition including hitbox offsets, models, and seat height
