# Proposal: Prop State Machine, Audio/Visual FX, and Dynamic Hitboxes

## Why

Custom furniture props in CraftLab are currently static single-model displays with fixed interaction types (`seat`, `lay`, or `none`). Modern Minecraft creators require interactive props—such as lamps that turn on/off, doors/gates that open and close, campfires that ignite, and cyclic switches—with visual model switching, dynamic lighting, auditory feedback, and passable hitboxes when opened. Introducing a dedicated state machine with model swapping, Paper 1.21 light block management, and dynamic collision handling elevates CraftLab's furniture engine into a full-featured interactive prop platform.

## What Changes

- **Multi-State Prop Model**: Support defining multiple named states per prop (e.g. `off`, `on`, `open`, `closed`) with distinct `block_model` bindings, `light_level` (0–15), entry sounds, and explicit transition targets (`next_state` or cyclic toggles).
- **State-Driven PacketEvents Visual Updates**: Upon player interaction, update the virtual `ItemDisplay` item metadata instantly via PacketEvents (`WrapperPlayServerEntityMetadata`) to render the state's `block_model` without entity despawn/respawn flickering.
- **Dynamic Light Engine**: Manage Minecraft 1.21 `Material.LIGHT` blocks tied to prop states, applying configured light levels with smart adjacent placement for solid props and automatic cleanup on prop break.
- **Dynamic World Hitboxes & Safe Ejection**: Allow states to override collision (e.g. `solid` when closed, `passable` when open). Include safe entity eviction (smooth velocity push) to prevent players from suffocating or becoming trapped inside barrier blocks when a prop closes.
- **Local SQLite State Persistence**: Extend Paper agent's `placed_props` table with `current_state` to seamlessly restore prop states, light blocks, and models across server restarts.
- **Studio Interface Expansion**: Add a "States & Variants" tab in Block Studio to configure states, model selectors, light levels, sound effects, and transitions.

## Capabilities

### Modified Capabilities
- `block-studio`: Add requirements for authoring prop states, assigning per-state block models, configuring light levels (0–15), assigning entry sounds, and setting state-specific collision overrides.
- `content-model`: Extend canonical block and prop schema to validate and store `default_state` and a typed `states` mapping containing state models, audiovisual properties, and transitions.
- `paper-agent-adapter`: Add requirements for handling player interaction state transitions, dispatching PacketEvents metadata packets for model swaps, placing/removing `Material.LIGHT` blocks, executing safe-ejection dynamic hitbox toggles, and persisting `current_state` in `props.db`.

## Impact

- **Frontend**: `BlockStudio.tsx`, `client.ts` (Block interface extended with `default_state` and `states`).
- **Backend**: `app/models/block.py` (`states` JSON column), `app/domain/blocks.py` (validation and defaults).
- **Paper Plugin**: `PropDefinition.java`, `PropInstance.java`, `PropStorage.java` (DB schema migration), `PropManager.java` (metadata packets, light blocks, cooldowns), `PropInteractionListener.java` (state transitions, sound triggers, safe eviction), `PropPlaceBreakListener.java` (light cleanup).
- **Database**: SQLite migration adding `current_state TEXT DEFAULT 'default'` to `placed_props`.
