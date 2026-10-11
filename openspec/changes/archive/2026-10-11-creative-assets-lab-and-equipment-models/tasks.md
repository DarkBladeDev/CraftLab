# Tasks: Creative Assets Lab & Equipment Models (1.21.2+)

## 1. Backend Domain Services & Creative REST API

- [x] 1.1 Implement PUA Unicode Allocator in `app/domain/glyphs.py` supporting workspace font scanning, automatic allocation in `\uE000`–`\uF8FF`, manual hex collision detection, and verify with unit tests in `tests/test_glyphs.py`.
- [x] 1.2 Implement 1.21.2+ Equipment Model builder in `app/domain/equipment.py` with schema validation for layer types (`humanoid`, `humanoid_leggings`, `wings`), dyeable overlay masks, and verify with unit tests in `tests/test_equipment.py`.
- [x] 1.3 Implement Sound Events domain and audio probe in `app/domain/sound_events.py` managing `sounds.json`, channel inspection (mono vs. stereo), and symmetric channel downmix `(L+R)/2` to mono `.ogg`, and verify with unit tests in `tests/test_sound_events.py`.
- [x] 1.4 Implement Particle VFX domain in `app/domain/particles.py` generating `particles/<id>.json` and validating sprite texture paths, and verify with unit tests in `tests/test_particles.py`.
- [x] 1.5 Implement REST API router `app/api/creative.py` exposing endpoints for Glyphs, Equipment, Sounds (with `/convert-mono`), and Particles, register it in `app/api/__init__.py`, and verify with API test suite in `tests/test_creative_api.py`.

## 2. Resource Pack Pipeline & Semantic Merging Integration

- [x] 2.1 Extend `app/domain/pack_compiler.py` and `pack_merger.py` to package 1.21.2+ equipment models into `models/equipment/<id>.json` across root and `overlay_v1_21_2`, and verify layer texture pre-flight checks in `tests/test_pack_compiler.py`.
- [x] 2.2 Extend merger engine to perform semantic deduplication of `font/*.json` bitmap providers without PUA collisions, merge multi-sample `sounds.json` audio events, package `particles/*.json`, and verify with pipeline tests.

## 3. Frontend Creative Assets Lab UI & Sub-Modules

- [x] 3.1 Create `CreativeAssetsLabView.tsx` with segmented pill sub-module navigation, register the "Creative Assets Lab" tab in `App.tsx` with Rose/Pink branding, and verify layout rendering.
- [x] 3.2 Implement `GlyphStudioTab.tsx` with sprite upload, automatic PUA allocator, manual hexadecimal override with real-time collision badge, and live Minecraft Chat & Tablist simulators.
- [x] 3.3 Implement `EquipmentStudioTab.tsx` with layer stack management, dyeable toggles, 2D/3D paper doll mannequin preview, and one-click `minecraft:equippable` component generator.
- [x] 3.4 Implement `SoundStudioTab.tsx` with sound event authoring, multi-sample pitch/volume variations, stereo audio warning badge, and 1-click "Convert to Mono" action.
- [x] 3.5 Implement `ParticleStudioTab.tsx` with sprite definition editor, real-time 60 FPS HTML5 canvas emitter simulator, and in-game `/particle` command builder.
- [x] 3.6 Implement `RawSchemaEditor.tsx` drawer supporting bidirectional synchronization between visual form state and Minecraft 1.21.2+ JSON schema validation.

## 4. Cross-Studio Integrations & End-to-End Verification

- [x] 4.1 Update `ComponentBuilder.tsx` in Item Studio to support `minecraft:equippable` component authoring with equipment model autocomplete populated from Creative Assets Lab.
- [x] 4.2 Update `BlockStudio.tsx` prop state editor to bind sound events and particle VFX triggers to prop state machine transitions.
- [x] 4.3 Run full monorepo test suite (`pytest` for backend, `npm run build` / `npm test` for frontend) and verify full end-to-end creative workflow.
