# Tasks: Fix Paper Agent Props Mechanics

## 1. Item Model Reflection and ItemStack Assembly Fix

- [x] 1.1 Refactor `Paper121ItemAdapter.applyItemModel` to reflectively invoke `setItemModel` via the public `org.bukkit.inventory.meta.ItemMeta.class` interface, sanitize namespaced keys, and log warnings on unexpected reflection errors. Verify with unit tests in `Paper121ItemAdapterTest`.
- [x] 1.2 Update `PropPlaceBreakListener.createPropItemStack` to apply the sanitized `item_model` with fallback handling, ensuring prop ItemStacks in hands and hotbar render custom 3D models rather than plain white wool. Verify with `./gradlew test`.

## 2. Multi-Block Hitbox Offsets, Cardinal Rotation & Spatial Checks

- [x] 2.1 Implement cardinal coordinate rotation utility for integer hitbox offsets `[dx, dy, dz]` based on horizontal yaw (0°, 90°, 180°, 270°). Verify with a dedicated unit test covering all 4 cardinal angles and preset shapes (1x1, 1x2, 2x1, 2x2).
- [x] 2.2 Add pre-placement clearance check in `PropPlaceBreakListener` verifying that all rotated hitbox destination blocks are air or replaceable (`block.isReplaceable()`), canceling placement if any offset is obstructed. Verify with unit test.
- [x] 2.3 Update prop placement logic to place collision blocks (`BARRIER` for solid or `STRUCTURE_VOID` for passable) across all rotated offsets, and maintain a bidirectional `blockToInstance` spatial index in `PropManager`. Verify multi-block registration.

## 3. Display Packet Despawn Lifecycle & Multi-Block Teardown

- [x] 3.1 Invert destruction sequence in `PropManager` and `PropPlaceBreakListener` so `broadcastDestroy` dispatches `WrapperPlayServerDestroyEntities` packets to all viewing players before removing the entity ID mapping from memory. Verify despawn packet emission.
- [x] 3.2 Update `onBlockBreak` to look up the prop from any occupied block in `blockToInstance`, revert all occupied collision blocks across the rotated footprint to `AIR`, and clean up memory and disk instances. Verify complete teardown.

## 4. Seat Mechanics, Interaction & Storage Updates

- [x] 4.1 Update `PropInteractionListener` to locate the prop from any clicked collision block and spawn the invisible seat entity centered above the interacted block with calibrated seat and lay height offsets. Verify sitting and lying poses.
- [x] 4.2 Update `PropStorage` to include `block_model` in `prop_definitions` table and implement safe `ALTER TABLE` checks in `initDatabase()`. Verify schema loading and tests in `PropStorageTest`.

## 5. Backend Real-Time Prop Synchronization

- [x] 5.1 Update `CraftLab-backend/app/api/blocks.py` to broadcast `create_or_update_block` envelopes to connected agents via `AgentSessionManager` upon saving in Block Studio. Verify API tests in `test_blocks_api.py`.
