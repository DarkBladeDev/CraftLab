# Proposal: Multi-Version Resource Pack Compatibility (1.21.1 - 1.21.11)

## Why

Minecraft 1.21 introduced significant architectural shifts in resource pack formatting and item model definitions:
1. Minecraft 1.21.0 - 1.21.1 (Pack Format 34) relies on legacy `models/item/<material>.json` predicate overrides using `custom_model_data`.
2. Minecraft 1.21.2 through 1.21.11 (Pack Formats 42, 46, and onwards) introduced Item Models V2 (`items/<material>.json` item definitions) and native `item_model` data components, while deprecating legacy overrides.

Servers running across or bridging versions 1.21.1 to 1.21.11 (via ViaVersion or multi-version proxies) face broken models or missing textures if resource packs target only one format. This change implements a Universal Hybrid Resource Pack pipeline utilizing Mojang's native `overlays` mechanism, dual-projection AST synthesis, and `item_model` component support in the Studio and Paper agent.

## What Changes

- **Universal Multi-Version Pack Generation**: Emit a unified resource pack `.zip` configured with `pack_format: 34`, `supported_formats: {"min_inclusive": 34, "max_inclusive": 65}`, and `overlays` targeting 1.21.2 - 1.21.11 (`overlay_v1_21_2`).
- **Shared Assets Layering**: Keep audio, fonts, and textures in the common root `assets/` directory while housing version-specific item definitions (`items/*.json`) inside the overlay directory to prevent archive bloat.
- **Dual-Projection Item Model Synthesizer**: Create a canonical model AST and bidirectional translation engine that compiles both legacy `models/item/<mat>.json` overrides and modern `items/<mat>.json` definitions (compliant with `vanilla-mcdoc` specs).
- **Studio `item_model` Support**: Add `item_model` namespaced identifier support to the Content Model and Item Studio UI, with automatic derivation when omitted.
- **Multi-Version Pre-Flight Conflict Detection**: Extend pre-flight checks to detect collisions on both `(material, custom_model_data)` tuples and `item_model` identifiers.
- **Paper Agent Hybrid Item Assembly**: Update the Paper agent to set `custom_model_data` and reflectively apply `item_model` on Paper runtimes supporting modern item components.

## Capabilities

### Modified Capabilities
- `resource-pack-pipeline`: Adds Universal Hybrid Pack compilation with `pack.mcmeta` overlays, bidirectional format translation during ingestion, and dual-projection synthesis.
- `content-model`: Adds the `item_model` component to item definition schemas and persistence.
- `item-studio`: Exposes `item_model` configuration and multi-version compatibility indicators in the UI.
- `paper-agent-adapter`: Extends item deployment with runtime-aware `item_model` component assembly alongside `custom_model_data`.

## Impact

- **Backend**:
  - `backend/app/models/entities.py` & `backend/app/models/content.py`: Support `item_model` in item schemas.
  - `backend/app/domain/pack_merger.py`: Support AST-based dual projection and `items/*.json` semantic merging.
  - `backend/app/domain/pack_compiler.py`: Generate overlay-enabled `pack.mcmeta`.
  - `backend/app/domain/pack_validator.py`: Validate `item_model` key uniqueness and syntax against `vanilla-mcdoc`.
- **Frontend**:
  - `frontend/src/features/studio/`: Add `item_model` field input and compatibility badge.
  - `frontend/src/features/packs/`: Display overlay layers and version range indicators.
- **Paper Agent**:
  - `paper-agent/src/main/java/com/mcp/agent/item/`: Assemble modern `item_model` component when running on Paper 1.21.2+.
- **Dependencies**: No new external dependencies required; leverage existing `vanilla-mcdoc` schemas for test fixtures and validation.
