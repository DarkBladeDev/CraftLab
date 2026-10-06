# Design

## Context

The system currently manages custom items through `ItemDefinition`, persists them via SQLite, snapshots them into deterministic revision hashes, and deploys them to a Paper 1.21.x server agent via WebSocket protocol. The Paper agent applies item components natively or via Oraxen.

See [proposal.md](proposal.md) for motivation and background.

## Goals / Non-Goals

**Goals:**
- Provide a dedicated "Block Studio" workflow in the frontend and backend for creating and managing custom blocks and props.
- Implement zero-tick-lag virtual display entities in `paper-agent` using PacketEvents 2.14.0.
- Provide physical collision hitboxes via invisible barrier blocks supporting single-block and multi-block relative offsets.
- Support automatic 4-way cardinal rotation (0°, 90°, 180°, 270°) upon placement using quaternion calculations.
- Support interactive sit mechanics for chairs and sofas via temporary dummy vehicles.
- Persist placed props in local SQLite database at `plugins/McpAgent/data/props.db`.
- Maintain deterministic canonical revision hashing across both items and blocks.

**Non-Goals:**
- Client-side modded custom blocks (Fabric/Forge): The solution remains 100% vanilla Minecraft client compatible.
- Complex hierarchical bone animations (e.g. ModelEngine-style active mobs): Focus is on static/semi-static furniture and blocks.
- Real ticking world entities: No persistent entity entries in chunk save files.

## Decisions

### Decision 1: Dedicated Domain Collection (`BlockDefinition`) vs Polymorphic Resource
- **Choice**: Dedicated `BlockDefinition` domain model, dedicated SQLAlchemy `BlockModel` (`blocks` table), and dedicated `/api/v1/blocks` router.
- **Rationale**: Keeps Pydantic schemas strict and type-safe. Enables clean separation in the UI between "Item Studio" and "Block Studio" while allowing future studios (Sound Studio, Entity Studio) to follow the exact same proven pattern.
- **Alternatives considered**: Single polymorphic `resources` table with JSON payloads. Rejected because it weakens SQL schema guarantees and complicates query filtering.

### Decision 2: PacketEvents 2.14.0 Virtual Entities vs World Entities or NMS
- **Choice**: PacketEvents 2.14.0 emitting `WrapperPlayServerSpawnEntity` (`ITEM_DISPLAY`) and `WrapperPlayServerEntityMetadata`.
- **Rationale**: Spawning real `world.spawnEntity(location, ItemDisplay.class)` creates server-side ticking entities that degrade server MSPT and bloat chunk region files. Raw NMS is fragile across minor Minecraft updates. PacketEvents provides a stable, cross-version packet abstraction that renders 100% client-side with zero server tick cost.
- **Alternatives considered**: Raw Mojang mapped NMS packets. Rejected due to maintenance fragility on future Paper builds.

### Decision 3: Cardinal 4-Direction Placement via Quaternions
- **Choice**: Quantize player horizontal yaw into 4 cardinal directions (North = 180°, South = 0°, West = 90°, East = 270°) upon block placement. Calculate the display transformation `left_rotation` quaternion:
  $q = [0,\; \sin(\theta/2),\; 0,\; \cos(\theta/2)]$.
- **Rationale**: Furniture items should align with the grid and face the player naturally when placed.

### Decision 4: Barrier Collision Anchors with PersistentDataContainer
- **Choice**: Place invisible `BARRIER` blocks in the world at the prop's anchor and relative hitbox offsets. Store the prop instance UUID in the barrier tile or chunk PDC (`mcp:prop_id`).
- **Rationale**: Prevents players from walking through props without requiring physical mob entities. Canceling the barrier break event allows dropping the custom prop item and destroying the virtual display simultaneously.

### Decision 5: Hybrid Temporary Seat Vehicle for "Sit" Interactions
- **Choice**: When a player right-clicks a prop with `interaction_type: "seat"`, spawn a temporary invisible marker `ArmorStand` at $(X + 0.5, Y + \text{seat\_height}, Z + 0.5)$ and add the player as a passenger. Upon `EntityDismountEvent` (player presses SHIFT), immediately destroy the temporary vehicle and teleport the player slightly forward.
- **Rationale**: Minecraft client camera and movement prediction require a vehicle entity to sit cleanly. Keeping the seat vehicle temporary (only alive while a player sits) prevents world entity accumulation while keeping the 3D model itself 100% virtual packet-based.

### Decision 6: Local SQLite Persistence at `plugins/McpAgent/data/props.db`
- **Choice**: Store placed prop records (UUID, block_id, world, x, y, z, yaw, placed_at) in a local SQLite file.
- **Rationale**: Allows the Paper server to immediately rebuild the spatial chunk index and restore all virtual props upon reboot even if the backend control plane is momentarily offline.

### Decision 7: Multi-Collection Deterministic Revision Hashing
- **Choice**: Update `revisions.py` to sort both `items` by ID and `blocks` by ID, compute their canonical JSON dictionaries, and SHA-256 hash the combined payload:
  `hash(json([canonical_items, canonical_blocks]))`.
- **Rationale**: Ensures revisions remain tamper-evident and track changes to blocks as first-class citizens.

## Risks / Trade-offs

- **[Risk] Packet desync when player teleports quickly**
  - *Mitigation*: Listen to `PlayerMoveEvent` and chunk load/unload events. When a player moves into range ($< 32$ blocks), spawn packets are sent; when leaving ($> 32$ blocks), destroy packets are sent.
- **[Risk] Creative mode players seeing barrier particles**
  - *Mitigation*: In vanilla Minecraft, barriers are only visible if the player is holding a barrier item in hand. Under normal gameplay, the barrier is completely invisible.
- **[Risk] Multi-block props placed near chunk boundaries**
  - *Mitigation*: Hitbox offset coordinates are calculated as absolute world block locations and validated for replaceable space before placing.

## Migration Plan

1. Backend: Run SQLite database upgrade to create `blocks` table.
2. Paper Agent: Add `packetevents-spigot` dependency in Gradle build script and ensure `data/` folder exists for `props.db`.
3. Backward compatibility: Existing revisions containing only items remain valid; the new revision hash algorithm incorporates empty block lists gracefully for legacy snapshots.
