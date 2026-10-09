# Proposal: Fix Paper Agent Props Mechanics

## Why
When placing and interacting with virtual display props via the Paper agent, four critical issues degrade runtime fidelity: multi-block hitbox presets are not placed nor spatially pre-checked, virtual ItemDisplay entities do not despawn upon destruction due to an inverted cleanup race condition, prop ItemStacks fall back to vanilla white wool due to reflection access restrictions on `ItemMeta`, and seat heights fail to apply correctly during interaction. Resolving these issues ensures that furniture, benches, beds, and decorative props exhibit correct multi-block collisions, proper despawn cycles, authentic hand-held models, and accurate seating/lying heights.

## What Changes
- **Multi-Block Hitbox Dimension Presets with Cardinal Rotation**: Transform all configured `hitbox_offsets` according to player cardinal yaw (0°, 90°, 180°, 270°) and place collision blocks (`BARRIER` for solid, `STRUCTURE_VOID` for passable) across all occupied blocks.
- **Spatial Pre-Placement Clearance Checks**: Verify that all destination blocks across the rotated hitbox footprint are replaceable or air before placing a prop. Block placement if any hitbox block is obstructed.
- **Bi-directional Multi-Block Spatial Indexing**: Maintain an in-memory block-to-prop mapping so that breaking or right-clicking any collision block belonging to a multi-block prop correctly resolves the parent prop instance.
- **Fixed Display Despawn Lifecycle**: Dispatch `WrapperPlayServerDestroyEntities` packets to all viewing players *before* removing the entity ID mapping from memory, ensuring display entities are immediately despawned when broken.
- **Multi-Block Collision Teardown**: Revert all occupied collision blocks across the prop footprint to `AIR` when any of its hitbox blocks is broken.
- **Accessible Item Model Reflection**: Invoke `setItemModel` via the public `org.bukkit.inventory.meta.ItemMeta.class` interface rather than `meta.getClass()` to prevent Java 21 `IllegalAccessException` errors, with graceful parsing for namespaced keys and explicit warning logging.
- **Seat & Lay Height Mechanics**: Calculate mount location relative to the clicked block with calibrated pelvic and lying offsets, and persist `block_model` in SQLite.
- **Real-Time Prop Sync**: Push prop definition updates from `CraftLab-backend` to connected agents over WebSocket when saved in Studio, eliminating stale configuration desyncs.

## Capabilities

### New Capabilities
None.

### Modified Capabilities
- `paper-agent-adapter`: Update requirements for multi-block hitbox placement with cardinal rotation, spatial clearance pre-checks, destruction packet dispatch lifecycle, robust `item_model` component application on ItemStacks, and seat height positioning with hot-reload synchronization.

## Impact
- **CraftLab-plugin**: `PropPlaceBreakListener.java`, `PropManager.java`, `PropInteractionListener.java`, `PropStorage.java`, `Paper121ItemAdapter.java`.
- **CraftLab-backend**: `app/api/blocks.py` (propagate updates to connected agents via WebSocket session manager).
- **Network / Protocol**: Real-time `create_or_update_block` event dispatch upon Studio save.
- **Storage**: `props.db` schema migration ensuring `block_model` and `seat_height` columns exist and are loaded.
