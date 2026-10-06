# Spec Delta

## ADDED Requirements

### Requirement: Virtual Display Entity Engine via PacketEvents
The Paper agent SHALL integrate PacketEvents 2.14.0 to render lightweight, virtual `ItemDisplay` entities to players within tracking range ($\le 32$ blocks) without creating ticking entities in the Minecraft server world.

#### Scenario: Player enters prop tracking range
- **WHEN** a player moves within 32 blocks of a placed virtual prop
- **THEN** the agent sends PacketEvents spawn and metadata packets for an `ITEM_DISPLAY` entity configured with the prop's model and transform

#### Scenario: Player leaves prop tracking range
- **WHEN** a player moves further than 32 blocks from a placed virtual prop
- **THEN** the agent sends PacketEvents entity destroy packets to remove the display from that player's client

### Requirement: Prop Placement with 4-Way Cardinal Rotation and Barrier Collisions
The Paper agent SHALL handle prop placement by calculating the player's horizontal cardinal facing (North, South, East, West), applying the corresponding quaternion rotation, and placing invisible barrier collision blocks at the anchor offsets.

#### Scenario: Placing a directional chair prop
- **WHEN** a player right-clicks a solid surface with a prop item while facing South
- **THEN** the agent places a barrier collision block tagged with the prop instance ID, calculates a 0-degree yaw rotation quaternion, registers the prop instance, and broadcasts the virtual display packet

#### Scenario: Breaking a placed prop
- **WHEN** a player breaks a barrier block associated with a registered prop
- **THEN** the agent cancels the vanilla barrier drop, spawns the configured `drop_item_id`, cleans up all associated collision offsets, removes the prop from memory and disk, and sends destroy packets to nearby players

### Requirement: Prop Interaction and Native Sit Mechanics
The Paper agent SHALL support interactive props, allowing players to sit on props designated with `interaction_type: "seat"` upon right-clicking.

#### Scenario: Player sits on chair
- **WHEN** a player right-clicks a chair prop barrier block
- **THEN** the agent spawns a temporary invisible seat vehicle at the configured seat height offset, mounts the player, and plays an interaction sound effect

#### Scenario: Player dismounts from chair
- **WHEN** a sitting player presses sneak (SHIFT) or dismounts
- **THEN** the agent immediately removes the temporary seat vehicle and teleports the player slightly forward to prevent collision trapping

### Requirement: Local SQLite Prop Instance Persistence
The Paper agent SHALL persist placed prop instances in a local SQLite database (`plugins/McpAgent/data/props.db`) and automatically restore and track them across server restarts.

#### Scenario: Server restart restoration
- **WHEN** the Paper server starts up
- **THEN** the agent initializes the local SQLite database, loads all stored prop instances into the spatial chunk index, and serves them to joining players
