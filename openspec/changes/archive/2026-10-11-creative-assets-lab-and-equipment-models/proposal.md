# Proposal: Creative Assets Lab & Equipment Models (1.21.2+)

## Why

Modern Minecraft servers (1.21.2+) require sophisticated multimedia assets beyond standalone items and blocks—including declarative equipment models, custom armor layers, rank prefix glyphs in chat/tablists, 3D spatialized sound events, and particle VFX. Currently, server administrators must author complex Minecraft JSON files, manage unicode font codepoints, and configure directory structures by hand, causing configuration errors and PUA collisions. Establishing a unified "Creative Assets Lab" eliminates boilerplate file wrangling while providing interactive simulators, schema-validated manual overrides, and cross-studio integration across CraftLab.

## What Changes

- Introduce a new top-level workspace tab **Creative Assets Lab** in `CraftLab-frontend` with a minimalist pill navigation bar across four dedicated sub-modules: Glyphs & Rank Prefixes, Equipment & Armor (1.21.2+), Sound Events (SFX), and Particles & VFX.
- Implement an automated Private Use Area (PUA) Unicode allocator (`\uE000`–`\uF8FF`) in `CraftLab-backend` with collision prevention, manual hexadecimal override validation, baseline ascent/height aligner, and in-browser Chat/Tablist simulators.
- Implement a 1.21.2+ Equipment Model builder (`assets/<namespace>/models/equipment/<id>.json`) supporting humanoid and humanoid_leggings layers, dyeable overlay masks, 2D/3D paper doll mannequin preview, and dynamic integration with `Item Studio` via the `minecraft:equippable` component.
- Implement a Sound Events Studio managing `assets/<namespace>/sounds.json`, multi-clip variations (pitch, volume, weights), automated channel probe (mono vs. stereo warning badge), and a 1-click backend downmix converter (`(L+R)/2`) ensuring 3D spatial attenuation in Minecraft.
- Implement a Particle & VFX Studio managing `assets/<namespace>/particles/<id>.json`, sprite frames, a real-time 60 FPS HTML5 canvas particle emitter simulator, and in-game `/particle` command generation.
- Implement a universal **Visual Editor vs. Schema & Raw JSON Inspector** drawer offering two-way synchronization and live Minecraft JSON schema validation.
- Extend `resource-pack-pipeline` to compile and package equipment models, font providers, audio manifests, and particle definitions into unified pack builds and overlays.
- Extend `item-studio` to bind equipment models directly into `minecraft:equippable` components.
- Extend `block-studio` to select registered sound events and particle triggers directly in prop state transitions.

## Capabilities

### New Capabilities
- `creative-assets-lab`: Unified visual workspace and backend service for authoring, testing, and managing rank prefix glyphs, 1.21.2+ equipment models, spatialized sound events, and particle VFX.

### Modified Capabilities
- `resource-pack-pipeline`: Compiles and merges 1.21.2+ equipment models, custom font bitmap providers, sound event registries (`sounds.json`), and particle definitions into root assets and versioned overlays.
- `item-studio`: Integrates 1.21.2+ equipment model references into the `minecraft:equippable` item component builder with autocomplete and validation.
- `block-studio`: Binds registered sound events and particle VFX emitters to custom block and furniture prop state machine transitions.

## Impact

- **Frontend (`CraftLab-frontend`)**: Adds `CreativeAssetsLabView.tsx` with 4 tab components (`GlyphStudioTab`, `EquipmentStudioTab`, `SoundStudioTab`, `ParticleStudioTab`), updates `App.tsx` navigation, enhances `ComponentBuilder.tsx` in Item Studio, and updates `BlockStudio.tsx` prop states.
- **Backend (`CraftLab-backend`)**: Adds `app/api/creative.py`, domain modules `app/domain/glyphs.py`, `app/domain/equipment.py`, `app/domain/sound_events.py`, and `app/domain/particles.py`. Adds audio channel inspection and mono downmixing endpoint.
- **Pipeline (`pack_compiler.py`)**: Extends semantic merging and packaging for equipment models, fonts, sounds, and particle definitions.
- **Dependencies**: Uses standard Python audio libraries (e.g. `wave`/`mutagen`/`scipy` or native downmixing) without breaking existing external dependencies.
