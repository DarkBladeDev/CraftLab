# Proposal: Equipment Shaders Legacy Compatibility (< 1.21.2)

## Why

Minecraft 1.21.2+ introduced the native `equipment` models system (`assets/<namespace>/equipment/<id>.json`) and the `minecraft:equippable` component, allowing custom armor textures to be bound directly to items. However, clients running versions prior to 1.21.2 (such as 1.20.0 through 1.21.1) lack native engine support for custom worn body armor textures via `CustomModelData` alone. In multi-version networks (using ViaVersion/Geyser or running 1.20-1.21.1 servers), players on legacy clients cannot see custom armor on player bodies, seeing only vanilla armor or losing visual fidelity.

This change introduces full Level 2 backward compatibility for equipment models via an adapted **LessFancyPants Core Shader pipeline**, automated vertical texture atlas synthesis, workspace compatibility profiles, and synchronized `CustomModelData` + `dyed_color` auto-assignment.

## What Changes

- **Adapted LessFancyPants Core Shader Integration**: Embed an optimized GLSL vertex/fragment core shader (`rendertype_armor_cutout_no_cull`) that decodes 24-bit RGB vertex color tints and reprojects texture coordinates across a vertical atlas in $O(1)$ constant time without per-pixel fragment branching.
- **Automated Vertical Armor Atlas Stitcher**: During resource pack compilation, dynamically assemble all canonical `humanoid` (layer 1) and `humanoid_leggings` (layer 2) equipment textures into composite vertical atlas sheets (`textures/models/armor/leather_layer_1.png` and `leather_layer_2.png`), injecting `#define TOTAL_LAYERS` into the shader.
- **Workspace Compatibility Profiles**: Add a configuration setting to pack and workspace manifests (`compatibility_profile`: `modern_native`, `hybrid_shaders`, `hybrid_trims`) to govern whether legacy shader assets and atlases are compiled or omitted.
- **Item Studio Hybrid Equipment Binding**: In `hybrid_shaders` mode, items configured with `minecraft:equippable` automatically derive/link a unique `custom_model_data` integer, a 24-bit RGB `dyed_color` corresponding to the shader atlas layer index, a `LEATHER_*` base material with compensating combat attribute modifiers, and `ItemFlag.HIDE_DYE`.
- **Creative Assets Lab Multi-Version Diagnostics**: Display legacy shader layer allocation (ID, RGB hex, atlas slot index) alongside the 1.21.2+ canonical `asset_id` in the Equipment Model inspector.
- **Paper Plugin Runtime Multi-Version Fallback**: In `CraftLab-plugin`, when running on servers or serving clients without native `getEquippable` support, apply `CustomModelData`, `dyed_color`, and simulated armor/toughness attribute modifiers so legacy players experience the custom armor visuals and stats seamlessly.

## Capabilities

### Modified Capabilities

- `resource-pack-pipeline`: Adds automated vertical armor atlas synthesis (`leather_layer_1.png` / `leather_layer_2.png`), dynamic LessFancyPants core shader injection into root assets for clients 1.20-1.21.3 with 1.21.4 overlay isolation, and compatibility profile resolution.
- `item-studio`: Adds hybrid equipment binding logic in Item Studio that auto-assigns legacy `custom_model_data`, RGB `dyed_color`, base material fallback, and attribute modifier compensation for equipment items when `hybrid_shaders` is active.
- `creative-assets-lab`: Adds legacy shader metadata inspector (layer ID, RGB hex, atlas height, compatibility badges) to the Equipment Model editor in Creative Assets Lab.
- `paper-agent-adapter`: Extends item component application to support legacy equippable runtime fallbacks (`custom_model_data` + `dyed_color` + armor attribute modifiers) when native Paper `EquippableComponent` is unavailable.

## Impact

- **Backend**:
  - `CraftLab-backend/app/domain/pack_merger.py`: Implements `ArmorAtlasStitcher` and updates compilation pipeline to stitch leather armor layers and inject the core shader into root assets while keeping `overlay_v1_21_4` clean.
  - `CraftLab-backend/app/domain/pack_compiler.py`: Supports `compatibility_profile` in `pack.mcmeta` and build summaries.
  - `CraftLab-backend/app/domain/equipment.py`: Calculates deterministic shader layer indices and RGB values from equipment registry.
  - `CraftLab-backend/app/domain/items.py` & `app/api/items.py`: Hybrid item validation and auto-derivation.
- **Frontend**:
  - `CraftLab-frontend/src/views/CreativeView.tsx` & Equipment editor: Shows legacy shader ID badge and RGB hex code.
  - `CraftLab-frontend/src/views/ItemStudioView.tsx`: Displays multi-version status banner and legacy fallback controls.
  - Workspace / Pack Settings modal: Selector for `compatibility_profile`.
- **Plugin**:
  - `CraftLab-plugin/.../adapters/components/EquippableComponentApplier.java` & `Paper121ItemAdapter.java`: Applies leather dye color and simulated attributes when `getEquippable()` is not present or hybrid metadata is provided.
