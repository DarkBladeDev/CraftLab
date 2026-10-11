# Technical Design: Creative Assets Lab & Equipment Models (1.21.2+)

## Context

CraftLab currently provides separate studio environments for custom items (`ItemStudio`) and custom blocks/props (`BlockStudio`), alongside an asset workspace and a multi-version resource pack compiler supporting 1.21.2-1.21.4 overlays and atlases. However, Minecraft 1.21.2+ introduces a declarative format for equipment models (`models/equipment/<id>.json`), while servers routinely configure custom font glyphs, spatial sound events (`sounds.json`), and particle VFX (`particles/<id>.json`). Administrators previously lacked visual tools for these asset domains, leading to manual JSON file crafting and PUA character collisions.

See `proposal.md` for motivation and `specs/` for normative requirement definitions.

## Goals / Non-Goals

**Goals:**
- Provide a unified, minimalist frontend workspace (`CreativeAssetsLabView`) organizing Glyphs, Equipment (1.21.2+), Sound Events, and Particles into dedicated tabs.
- Automate Private Use Area (PUA) character allocation (`\uE000`–`\uF8FF`) while allowing manual hexadecimal override with collision detection.
- Provide interactive preview environments (Minecraft Chat & Tablist simulator, 2D/3D paper doll mannequin for armor layers, 60 FPS HTML5 canvas particle emitter).
- Support automated audio channel inspection (Mono vs. Stereo warning) and a 1-click backend downmixer (`(L+R)/2`) to guarantee 3D distance attenuation.
- Seamlessly wire equipment models into `ItemStudio` (`minecraft:equippable`) and sound events/particles into `BlockStudio` prop states.
- Support bidirectional synchronization between visual form controls and a schema-validated Monaco/JSON raw drawer.

**Non-Goals:**
- Full 3D skeletal rigging or complex entity model animation (handled by standard block/prop display entities).
- External DAW audio mastering or multi-track audio editing (only channel downmixing and metadata parameter adjustments).
- Dynamic shader authoring from scratch (shaders remain managed by the 1.21.4 pipeline).

## Decisions

### 1. Unified Creative Assets Hub with Sub-Module Navigation
- **Decision**: Introduce a single top-level tab "Creative Assets Lab" in `App.tsx` with pill-based segmented sub-module navigation, rather than four separate top-level navigation tabs.
- **Rationale**: Keeps the primary navigation clean and prevents cluttering the top bar, while grouping all multimedia asset authoring tools logically.
- **Alternatives Considered**: 
  - *Separate top-level tabs*: Clutters the header navbar and fragments asset workflows.
  - *Burying inside Asset Explorer*: The Asset Explorer is a raw file manager; adding interactive simulators and studio forms there dilutes its file browser focus.

### 2. PUA Unicode Allocation Strategy & Conflict Registry
- **Decision**: Maintain a workspace registry of allocated PUA characters (`\uE000`–`\uF8FF`). On sprite creation, automatically assign the lowest unassigned codepoint. Allow authors to override the hexadecimal code (`E001`–`F8FF`) while validating format and alerting on collisions in real time.
- **Rationale**: Eliminates character overlapping between different rank badges and emotes, while respecting existing server font setups (e.g. pre-configured LuckPerms / TAB setups).
- **Alternatives Considered**:
  - *Strict auto-only allocation*: Blocks administrators who already have established PUA mappings in production servers.
  - *Pure manual input*: Increases human error and accidental collisions.

### 3. Audio Diagnostics & Stereo-to-Mono Downmixing
- **Decision**: Probe uploaded `.ogg` audio files using backend stream inspection (e.g. `mutagen` or standard audio headers). When 2 channels are detected, show a warning badge and provide a backend downmix endpoint `/api/v1/assets/creative/sounds/convert-mono` applying `(L + R) / 2`.
- **Rationale**: Minecraft 3D audio strictly requires 1-channel Mono for positional distance attenuation. Stereo plays at 100% volume in both ears of every player in range, causing severe audio bugs. An automated downmixer spares users from using external tools like Audacity.
- **Alternatives Considered**:
  - *Silent auto-conversion*: Might discard intentional stereo tracks (such as ambient background music or global UI jingles).
  - *Warning-only without converter*: Forces users to leave CraftLab to convert files manually.

### 4. 1.21.2+ Equipment Model Descriptors & Layer Stacking
- **Decision**: Generate canonical `assets/<namespace>/models/equipment/<id>.json` descriptors with an array of layer objects (`humanoid`, `humanoid_leggings`, `wings`), dyeable overlay masks, and automatic generation of the `minecraft:equippable` component tag.
- **Rationale**: In Minecraft 1.21.2+, equipment rendering is fully decoupled from vanilla texture overrides. Generating the exact equipment JSON and linking it directly to `ItemStudio` eliminates legacy shader hacks.
- **Alternatives Considered**:
  - *Relying on CustomModelData predicate overrides*: Deprecated and incompatible with 1.21.2+ equipment armor rendering.

### 5. Dual Visual & Schema Drawer Architecture
- **Decision**: Visual form controls drive the underlying state and automatically scaffold files on disk. A slide-out/toggle "Schema & Raw JSON" drawer displays the generated JSON with Monaco/syntax editor, allowing two-way updates with Minecraft 1.21.2+ JSON schema validation.
- **Rationale**: Provides beginner-friendly zero-boilerplate asset creation while giving advanced technical pack developers complete control to edit raw JSON attributes.

## Risks / Trade-offs

- **[Risk] High PUA codepoint usage in massive server packs**: A single server with hundreds of custom icons might exhaust `\uE000`–`\uF8FF`.
  - *Mitigation*: The PUA range contains 6,400 available characters (`57344` to `63743`), which is more than sufficient for typical server badge and emote counts. The allocator provides a visual counter of remaining available codepoints.
- **[Risk] Lossy channel downmixing on stereo tracks with phase cancellation**: Phase-inverted stereo tracks might cancel out audio content during downmixing.
  - *Mitigation*: Standard symmetric downmixing `(L + R) / 2` with normalization prevents clipping. CraftLab maintains the original file in history before conversion so users can revert if desired.
- **[Risk] Sync latency between Visual and Raw modes**: Manual JSON edits could corrupt visual form state if invalid.
  - *Mitigation*: The schema drawer strictly validates JSON syntax and schema requirements before updating the active memory state.

## Migration Plan

1. **Deploy Frontend & Backend Components**: The new tabs and endpoints live in parallel with existing studios without altering existing item or block records.
2. **Backwards Compatibility**: Existing `ItemStudio` and `BlockStudio` definitions remain fully valid; the new equipment and sound triggers are purely additive optional fields.
3. **Pack Compiler Ingestion**: The compiler automatically detects `models/equipment/`, `font/`, `sounds.json`, and `particles/` in the workspace authoring layer and packages them into compiled outputs and versioned overlays.
