# Design: Prop State Machine, Audio/Visual FX, and Dynamic Hitboxes

## Context

CraftLab currently renders custom furniture and props using virtual `ItemDisplay` entities tracked by PacketEvents 2.14.0 in Paper 1.21 ([PropManager.java](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/CraftLab-plugin/src/main/java/com/mcp/agent/props/PropManager.java)). Placed instances are stored in a local SQLite database ([PropStorage.java](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/CraftLab-plugin/src/main/java/com/mcp/agent/props/PropStorage.java)), and interactions are handled via right-clicks on barrier hitboxes ([PropInteractionListener.java](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/CraftLab-plugin/src/main/java/com/mcp/agent/props/PropInteractionListener.java)).

Currently, each prop has a single static `block_model` and supports only `seat` or `lay` interactions. See [proposal.md](file:///c:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/openspec/changes/prop-state-machine-and-interactions/proposal.md) for the motivations to introduce state machines, dynamic lighting, audio feedback, and dynamic hitboxes.

## Goals / Non-Goals

**Goals:**
- Provide a clean state machine model (`default_state` and a map of `states`) for custom props.
- Perform instant, zero-flicker model swapping via PacketEvents metadata packets upon state transition.
- Manage Paper 1.21 `Material.LIGHT` blocks seamlessly for props with dynamic light levels (0–15).
- Allow stateful hitbox transitions (`solid` $\leftrightarrow$ `passable`) with safe entity eviction to prevent player suffocation.
- Persist active prop states in Paper's local SQLite database without cross-network latency.
- Provide a visual "States & Variants" tab in Block Studio for authoring states and transitions.

**Non-Goals:**
- Client-side modded collision volumes (vanilla clients are supported exclusively).
- Multi-slot storage / virtual container GUIs (deferred to Phase 2; this change establishes the underlying state machine prerequisite).
- Complex continuous mathematical matrix interpolation (Blockbench model swapping satisfies requirements with 0 runtime math and maximum model compatibility).
- Per-player private collision gating via fragile NMS layers (world-synchronized barriers with safe eviction are prioritized).

## Decisions

### Decision 1: Model Swapping over Matrix Interpolation
- **Approach**: Each state explicitly binds a `block_model` (e.g. `lamp_off` vs `lamp_on`, `door_closed` vs `door_open`). When transitioning, the displayed item in the `ItemDisplay` entity metadata is updated to point to the new model.
- **Rationale**: Standard practice in Minecraft modeling tools (Blockbench). Works reliably for complex multi-bone objects, eliminates quaternion rotation math and network synchronization drift, and requires 0 continuous server tick updates.
- **Alternative Considered**: Display entity transformation lerping (`interpolation_duration`). Rejected for phase 1 due to unnecessary complexity when distinct models already capture the visual differences (such as open vs closed lids).

### Decision 2: PacketEvents Metadata Updates for Display Entities
- **Approach**: Use `WrapperPlayServerEntityMetadata` modifying index 23 (ItemStack `ITEM_MODEL` component) for all players tracking the prop within 32 blocks.
- **Rationale**: Updating metadata preserves the entity ID and position, resulting in instantaneous visual switching with zero white entity flashing or respawn overhead.
- **Alternative Considered**: Despawning and respawning the display entity. Rejected because despawning causes visual glitches and breaks tracking lists.

### Decision 3: Paper 1.21 `Material.LIGHT` Management
- **Approach**: When a state specifies `light_level > 0`, set a `Material.LIGHT` block with BlockData `Levelled.setLevel(level)`.
  - If prop is passable: placed directly at the prop base block.
  - If prop is solid: placed at the adjacent free block (typically `y + 1`).
  - When transitioning to 0 or broken: reset to `Material.AIR`.
- **Rationale**: Paper 1.21 supports native `Material.LIGHT` without custom packets or phantom light glitches.

### Decision 4: Synchronized Hitbox Swapping with Velocity Ejection
- **Approach**: When a prop transitions to `passable`, set collision blocks to `AIR` or `STRUCTURE_VOID`. When transitioning back to `solid`, inspect occupying players using `world.getNearbyEntities()` and apply a horizontal impulse vector away from the prop center before setting `BARRIER`.
- **Rationale**: Eliminates player suffocation and physics entrapment without requiring brittle NMS movement hooks.

### Decision 5: SQLite Database Schema Migration
- **Approach**: In `PropStorage.java`, execute `ALTER TABLE placed_props ADD COLUMN current_state TEXT DEFAULT 'default'`.
- **Rationale**: Backward compatible with all existing placed props. Prop instances load their saved state on server boot and maintain synchronization across restarts.

### Decision 6: Frontend State Machine Studio in BlockStudio.tsx
- **Approach**: Add a "States & Variants" tab within the prop editor. Authors can toggle between states, assign block models, configure light levels, sound keys, and transition targets.
- **Rationale**: Consistent with the current 3-column studio UX, keeping simple props easy to configure while providing full depth for advanced stateful props.

## Risks / Trade-offs

- **[Interaction Spam / Click Macros]** → Enforce an in-memory 250ms (5 ticks) cooldown per prop instance in `PropInteractionListener` before processing subsequent state transitions.
- **[Ghost Light Blocks on Crash / Disconnect]** → Index active light block coordinates in `PropManager` memory and verify/clean orphaned light blocks on server startup and prop destruction.
- **[Barrier Collision Entrapment]** → Compute a normalized vector `(player.pos - prop.center).normalize().multiply(0.4)` and apply as velocity prior to block replacement.
- **[Backward Compatibility with Single-State Props]** → Props lacking a `states` map fall back to top-level `block_model` and `hitbox_type`, initializing `current_state = "default"`.

## Migration Plan

1. Database migration in `PropStorage.java` runs automatically on plugin start (`ALTER TABLE placed_props ADD COLUMN current_state TEXT DEFAULT 'default'`).
2. Existing JSON prop definitions remain valid without schema breakage.
3. No breaking changes for connected server agents or existing resource packs.
