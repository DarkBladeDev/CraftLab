# Design: Fix Paper Agent Props Mechanics

## Context
See `proposal.md` for background and problem motivation.
Currently, `CraftLab-plugin` handles virtual props with three main components:
1. `PropManager`: Manages PacketEvents virtual `ITEM_DISPLAY` entities, spatial chunk indexing, and packet dispatching.
2. `PropPlaceBreakListener`: Handles player placement (`PlayerInteractEvent`) and breaking (`BlockBreakEvent`). Currently hardcodes single-block `BARRIER` placement and triggers destruction in an inverted sequence where entity IDs are evicted before packets are sent.
3. `Paper121ItemAdapter`: Applies modern item components via Java reflection on `meta.getClass()`, which triggers an `IllegalAccessException` in Java 21 on CraftBukkit package-private classes.
4. `PropInteractionListener`: Handles right-click sitting and lying poses via temporary marker `ArmorStand` vehicles.
5. `CraftLab-backend`: Persists props in `mcp.db`, but does not notify connected agents via WebSocket upon REST API changes.

## Goals / Non-Goals

**Goals:**
- Provide true multi-block collision matching the configured `hitbox_offsets` preset (1x1, 1x2, 2x1, 2x2, or custom).
- Transform hitbox offsets using exact 4-way cardinal rotation to match ItemDisplay orientation.
- Validate spatial clearance across all target blocks before placing any collision blocks.
- Ensure all viewing players receive despawn packets when a prop is broken.
- Clear all collision blocks belonging to a prop upon destruction.
- Reliably apply the `item_model` component to prop `ItemStack` instances using public interface reflection.
- Support calibrated seat and lay vertical offsets relative to the interacted block surface.
- Sincronize prop definitions in real time from backend to agent upon Block Studio save.

**Non-Goals:**
- Arbitrary free-angle rotation for hitboxes (Minecraft collision blocks must align to the integer block grid; yaw remains clamped to the 4 cardinal directions: 0°, 90°, 180°, 270°).
- Continuous tick-based collision meshes (Paper utilizes native `BARRIER` and `STRUCTURE_VOID` blocks).

## Decisions

### Decision 1: Exact Cardinal Offset Rotation Table
Instead of floating point trigonometric calculations that risk rounding errors on the integer block grid, we define an exact cardinal coordinate transform for any local offset `[dx, dy, dz]`:

```
Sur (0°):   rx =  dx,  ry = dy,  rz =  dz
Oeste (90°): rx =  dz,  ry = dy,  rz = -dx
Norte (180°): rx = -dx, ry = dy,  rz = -dz
Este (270°): rx = -dz,  ry = dy,  rz =  dx
```
*Rationale:* Guarantees exact integer coordinate alignment corresponding precisely to `calculateRotationQuaternion(yaw)` used by PacketEvents.
*Alternatives considered:* Floating point vector math with `Math.round()` — rejected due to drift at boundary angles.

### Decision 2: In-Memory Multi-Block Spatial Lookup
`PropManager` will maintain a thread-safe bidirectional map:
```java
Map<BlockLocation, UUID> blockToInstance = new ConcurrentHashMap<>();
```
When a prop is placed or loaded from disk, all rotated offsets are calculated and registered in this map.
*Rationale:* Enables $O(1)$ lookup when a player breaks or right-clicks *any* block belonging to a multi-block prop, not just the anchor block.
*Alternatives considered:* Searching all instances within distance on every block event — rejected due to performance overhead on servers with many props.

### Decision 3: Invert Teardown Sequence to Guarantee Despawn Packets
Refactor destruction in `PropPlaceBreakListener` and `PropManager`:
1. Retrieve `entityId` and active viewing players for the instance.
2. Broadcast `WrapperPlayServerDestroyEntities(entityId)` to all tracking players in the world.
3. Clean up collision blocks: iterate over all occupied block positions and set each to `Material.AIR`.
4. Evict instance from memory (`instancesById`, `blockToInstance`, `chunkSpatialIndex`, `instanceToEntityId`).
5. Delete instance from SQLite.
*Rationale:* Eliminates the silent early-return in `broadcastDestroy` caused by premature `instanceToEntityId.remove()`.

### Decision 4: Reflective Invocation via Public `ItemMeta` Interface
Replace:
```java
meta.getClass().getMethod("setItemModel", NamespacedKey.class);
```
with:
```java
Method method = org.bukkit.inventory.meta.ItemMeta.class.getMethod("setItemModel", org.bukkit.NamespacedKey.class);
method.setAccessible(true);
method.invoke(meta, key);
```
With resilient parsing:
- Handle `namespace:key` or infer `minecraft:` prefix if colon is missing.
- Log descriptive warning if an unexpected reflection error occurs rather than swallowing exceptions.
*Rationale:* Invoking through the public interface circumvents Java 21 package-access restrictions on CraftBukkit's internal `CraftMetaItem`.

### Decision 5: Real-Time Prop Sync on Studio Save
In `CraftLab-backend` (`app/api/blocks.py`), after `db.commit()` on `POST /api/blocks`:
- Retrieve active `AgentSessionManager`.
- Construct an envelope with `action: "create_or_update_block"` and payload containing the canonical block dictionary.
- Broadcast to all connected online agent targets.
*Rationale:* Ensures that changes made in the web UI (such as editing seat height, hitbox presets, or models) immediately reflect on the live test server without requiring a server reboot or revision deployment.

### Decision 6: SQLite Schema Migration in `PropStorage`
In `PropStorage.initDatabase()`:
- Ensure table definition includes `block_model TEXT`.
- Execute non-destructive column checks (`ALTER TABLE prop_definitions ADD COLUMN block_model TEXT`, etc.) if upgrading an existing `props.db`.

## Risks / Trade-offs

- **[Risk]** Existing server `props.db` contains legacy rows missing `block_model` or `hitbox_offsets`.
  - *Mitigation:* `mapDefinition()` falls back gracefully (e.g. `block_model = item_model`, default offset `[[0,0,0]]`).
- **[Risk]** Obstruction during placement when player clicks near complex geometry.
  - *Mitigation:* Check all blocks with `block.isReplaceable() || block.getType().isAir()`. If blocked, inform player via action bar / chat message and cancel event.
- **[Risk]** Player sitting while server reloads or shuts down leaving orphan ArmorStands.
  - *Mitigation:* `ArmorStand.setPersistent(false)` is already set; active seats are tracked and removed in `onDisable()`.
