# Paper Agent and Adapter

## Purpose
The Paper Agent and Adapter capability provides the in-server runtime execution environment via a lightweight Paper plugin, managing outbound connectivity, environment discovery, local state persistence, and native Paper item manipulation.

## Requirements

### Requirement: Outbound Connectivity and Agent Bootstrap
The agent plugin MUST initiate an outbound TLS WebSocket connection to the configured control plane gateway, maintaining resilient reconnections without requiring inbound open ports on the server.

#### Scenario: Agent bootstrap and connection
- **WHEN** the Paper server starts with valid control plane configuration
- **THEN** the plugin initiates an outbound connection, completes authentication, and begins sending periodic heartbeats

#### Scenario: Automatic reconnection on disconnect
- **WHEN** network connectivity between the agent and gateway is interrupted
- **THEN** the agent attempts exponential backoff reconnections and resynchronizes its session journal upon reconnecting

### Requirement: Paper Item Adapter Execution
The agent MUST include a Paper adapter capable of translating canonical item definitions into native Paper item components and persisting them on the server.

#### Scenario: Applying an item definition
- **WHEN** the agent receives an allowlisted `create_or_update_item` operation
- **THEN** the Paper adapter parses material, display name, lore, and custom model data, updates the local item storage, and verifies the resulting item representation

#### Scenario: Local item persistence across restarts
- **WHEN** the Paper server restarts
- **THEN** the plugin loads previously deployed items from its local persistent storage without requiring an active control plane connection during boot

### Requirement: In-Game Verification Command
The agent MUST provide a dedicated, permission-gated verification command for server administrators to inspect and test deployed items in-game.

#### Scenario: Giving a deployed custom item to a player
- **WHEN** an authorized server operator executes `/mcp give <item_id>`
- **THEN** the plugin instantiates the deployed item with all configured components and places it into the operator's inventory

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

### Requirement: Oraxen Runtime Inspection and Discovery
The Paper agent SHALL provide a soft-dependency adapter hook for Oraxen that inspects registered Oraxen items at runtime and serializes them into protocol catalog manifests.

#### Scenario: Discovering registered Oraxen items
- **WHEN** Oraxen is present and enabled on the Paper server and a catalog scan is triggered
- **THEN** the Oraxen adapter queries registered items, extracting identifier, base material, display name, lore, custom model data, and configuration attributes

#### Scenario: Graceful degradation when Oraxen is absent
- **WHEN** the agent runs on a server without Oraxen installed
- **THEN** the agent initializes without error and reports zero Oraxen items without throwing class loading exceptions

### Requirement: Bidirectional Oraxen Export and Hot-Reload
The Paper agent adapter SHALL support writing platform-deployed item definitions into Oraxen YAML configuration files and triggering an Oraxen reload.

#### Scenario: Exporting deployed item to Oraxen configuration
- **WHEN** the agent receives an item deployment payload with export target `oraxen`
- **THEN** it generates or updates the item definition in `plugins/Oraxen/items/platform_items.yml` and executes Oraxen's reload routine to register the changes

### Requirement: Plugin Resource Pack Discovery and Synchronization
The Paper agent SHALL discover local resource packs generated by installed third-party plugins (such as Oraxen) and synchronize them to the control plane.

#### Scenario: Local pack sync on plugin reload
- **WHEN** Oraxen finishes reloading and updating its local pack archive in `plugins/Oraxen/pack/`
- **THEN** the Paper agent detects the updated pack and uploads the snapshot to the control plane

### Requirement: In-Game Client Resource Pack Prompting
The Paper agent MUST store the latest compiled resource pack URL and SHA-1 hash received from the control plane and prompt newly joined players with the resource pack packet.

#### Scenario: Player joins server with active resource pack
- **WHEN** a player joins the server and an active resource pack URL and hash are configured
- **THEN** the agent sends `player.setResourcePack(url, sha1, required, prompt)` to the player during the join sequence

### Requirement: Administrative Resource Pack Reload Command
The Paper agent SHALL register the command `/mcp reloadpack` allowing administrators and players to re-prompt the active resource pack without restarting the server.

#### Scenario: Player executes self reload
- **WHEN** a player executes `/mcp reloadpack`
- **THEN** the agent sends the active resource pack packet to that player

#### Scenario: Admin executes mass reload
- **WHEN** an administrator with permission `mcp.admin.reloadpack` executes `/mcp reloadpack all`
- **THEN** the agent sends the active resource pack packet to all currently connected players on the server

### Requirement: Virtual Display Entity Engine via PacketEvents
The Paper agent SHALL integrate PacketEvents 2.14.0 to render lightweight, virtual `ItemDisplay` entities to players within tracking range ($\le 32$ blocks) without creating ticking entities in the Minecraft server world.

#### Scenario: Player enters prop tracking range
- **WHEN** a player moves within 32 blocks of a placed virtual prop
- **THEN** the agent sends PacketEvents spawn and metadata packets for an `ITEM_DISPLAY` entity configured with the prop's model and transform

#### Scenario: Player leaves prop tracking range
- **WHEN** a player moves further than 32 blocks from a placed virtual prop
- **THEN** the agent sends PacketEvents entity destroy packets to remove the display from that player's client

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

### Requirement: Local SQLite Prop Instance Persistence
The Paper agent SHALL persist placed prop instances in a local SQLite database (`plugins/McpAgent/data/props.db`) and automatically restore and track them across server restarts.

#### Scenario: Server restart restoration
- **WHEN** the Paper server starts up
- **THEN** the agent initializes the local SQLite database, loads all stored prop instances into the spatial chunk index, and serves them to joining players

### Requirement: Real-Time Prop Definition Synchronization
The platform SHALL synchronize prop definitions from the control plane to connected Paper server agents over WebSocket in real time upon modification in Studio, updating local agent cache and SQLite storage without requiring a full revision deployment or manual server reload.

#### Scenario: Saving prop definition in Block Studio
- **WHEN** an administrator saves or modifies a prop definition in Block Studio
- **THEN** the backend dispatches a `create_or_update_block` envelope to all online target agents, and each connected agent registers and persists the updated definition including hitbox offsets, models, and seat height

### Requirement: State-Driven PacketEvents Display Model Swapping
The Paper agent SHALL transition placed prop instances between defined states upon player right-click interaction, dispatching PacketEvents metadata packets (`WrapperPlayServerEntityMetadata`) updating the `ITEM_DISPLAY` item model for all players tracking the prop without despawning or respawning the virtual entity.

#### Scenario: Interacting with stateful prop triggers model swap
- **WHEN** a player right-clicks any collision block of a prop in state `"off"` whose transition target is `"on"`
- **THEN** the agent updates the instance state to `"on"`, computes the `block_model` associated with `"on"`, broadcasts `WrapperPlayServerEntityMetadata` to all tracking players, and plays the state entry sound at the prop location

#### Scenario: Cooldown enforcement prevents interaction spam
- **WHEN** a player interacts with a prop within 250 milliseconds (5 server ticks) of the prior interaction on the same prop
- **THEN** the agent ignores the repeated interaction, preventing packet flooding and redundant database updates

### Requirement: Dynamic Prop Lighting via Paper 1.21 Light Blocks
The Paper agent SHALL manage Minecraft 1.21 `Material.LIGHT` blocks corresponding to active prop states, placing light blocks at the prop base or adjacent air offsets when a state specifies `light_level > 0`, restoring air when transitioned to 0, and removing all light blocks when the prop is broken.

#### Scenario: Toggling lamp state places and removes light block
- **WHEN** a prop transitions to a state with `light_level: 14`
- **THEN** the agent places a `Material.LIGHT` block with light level 14 at the configured or adjacent air offset
- **WHEN** the prop subsequently transitions to a state with `light_level: 0`
- **THEN** the agent clears the light block by setting the position back to `Material.AIR`

#### Scenario: Breaking prop cleans up active light block
- **WHEN** a player breaks a placed prop that currently has an active light block
- **THEN** the agent clears both the collision blocks and the active light block from the world

### Requirement: Synchronized World Hitbox Swapping with Safe Ejection
The Paper agent SHALL update placed collision blocks when a state transition alters the prop's hitbox type between solid and passable, and SHALL perform safe eviction by applying a smooth velocity impulse to any entity occupying the bounding box before placing solid barrier blocks.

#### Scenario: Opening door changes collision to passable
- **WHEN** a door prop transitions from `"closed"` (`hitbox_type: solid`) to `"open"` (`hitbox_type: passable`)
- **THEN** the agent replaces the barrier collision blocks with passable blocks (`AIR` or `STRUCTURE_VOID`)

#### Scenario: Closing door performs safe ejection on occupying player
- **WHEN** a door prop transitions from `"open"` to `"closed"` and a player is detected within the collision bounding box
- **THEN** the agent applies a normalized horizontal velocity push away from the prop center before setting the block to `Material.BARRIER`, preventing the player from suffocating or getting trapped

### Requirement: Prop Instance State Persistence in SQLite
The Paper agent SHALL persist each placed prop's `current_state` in the local SQLite database (`placed_props`), restoring the active state, visual model, and light block configuration across server restarts.

#### Scenario: Restoring prop state across server restart
- **WHEN** the server restarts with placed props stored in SQLite with diverse states (e.g. some lamps "on", some "off")
- **THEN** the agent loads each instance's `current_state`, renders the corresponding state's `block_model` to joining players, and restores active light blocks in the world

#### Scenario: Asynchronous state update on interaction
- **WHEN** a prop instance transitions to a new state
- **THEN** the agent updates its in-memory tracking immediately and executes an asynchronous SQLite update to persist `current_state`



