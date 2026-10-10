# Spec Delta: paper-agent-adapter

## ADDED Requirements

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
