# Proposal

## Why

The platform currently specializes in custom item definitions and resource pack item models. Expanding beyond items into custom 3D blocks and furniture props is essential for builders and server creators. Spawning physical world entities (`ItemDisplay`) in Minecraft Paper causes server tick lag (MSPT degradation) and world save file bloat. By utilizing PacketEvents 2.14.0, the platform can manage lightweight virtual packet-based display entities with zero server-tick overhead, invisible barrier collision anchors, 4-way horizontal placement rotation, native sit interactions, and local SQLite persistence.

## What Changes

- **Backend Dedicated Block Domain & Collection**: Introduce canonical `BlockDefinition` with support for `display_prop` (virtual packet-based) and `noteblock` modes, dedicated SQL persistence (`blocks` table), and CRUD endpoints at `/api/v1/blocks`.
- **Dual-Collection Deterministic Revision Hashing**: Extend project revision snapshotting and SHA-256 canonical hashing across both `items` and `blocks` collections.
- **Block Studio Web UI**: Create a dedicated "Block Studio" workspace in the frontend for visual configuration of custom blocks, transform controls (scale, translation), hitbox grids, drop items, and seat mechanics.
- **PacketEvents 2.14.0 Virtual Prop Engine in Paper Agent**:
  - Integrate PacketEvents 2.14.0 into `paper-agent`.
  - Implement a spatial chunk index (`PropManager`) with distance-based tracking culling ($\le 32$ blocks).
  - Handle block placement with automatic 4-way horizontal yaw rotation (quaternions) and barrier collision placement.
  - Implement native "Sit" interaction handling via temporary dummy vehicle entities on right-click, dismounting cleanly on sneak (SHIFT) with sound effects.
  - Persist placed props in local SQLite database (`plugins/McpAgent/data/props.db`).

## Capabilities

### New Capabilities
- `block-studio`: Visual authoring, 3D transform tuning (scale, translation), hitbox grid definition, and interaction mechanics (seat/storage/etc.) for custom blocks and props.

### Modified Capabilities
- `content-model`: Support canonical `BlockDefinition` alongside items, with dedicated storage and multi-collection canonical revision hashing.
- `paper-agent-adapter`: Add PacketEvents 2.14.0 virtual display entity engine, placement/break lifecycle with barrier anchors, local SQLite prop storage, and interactive sit mechanic.

## Impact

- **Backend**:
  - New domain module `backend/app/domain/blocks.py`.
  - New database entity `backend/app/models/block.py` and migration.
  - New API router `backend/app/api/blocks.py`.
  - Updated revision hashing in `backend/app/domain/revisions.py`.
- **Paper Agent**:
  - Added repository and dependency for `com.github.retrooper:packetevents-spigot:2.14.0` in `paper-agent/build.gradle.kts`.
  - New prop manager, packet listeners, and SQLite storage in `paper-agent/`.
- **Frontend**:
  - New navigation item and view `BlockStudio` with 3D transform controls, hitbox configuration, and drop item selection.
