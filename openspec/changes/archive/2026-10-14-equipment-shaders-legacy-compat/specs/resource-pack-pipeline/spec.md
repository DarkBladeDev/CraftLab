# Spec Delta: Resource Pack Pipeline

## ADDED Requirements

### Requirement: Legacy Armor Core Shader and Vertical Atlas Synthesis
The pack compiler and merger engine SHALL provide automated vertical armor atlas synthesis and core shader packaging for clients prior to Minecraft 1.21.2 when the workspace compatibility profile is configured to `hybrid_shaders`. The engine MUST discover all canonical equipment model descriptors (`assets/<namespace>/equipment/<id>.json`), collect their referenced `humanoid` (layer 1) and `humanoid_leggings` (layer 2) texture PNG files, dynamically stitch them into vertical atlas sheets placed at `assets/minecraft/textures/models/armor/leather_layer_1.png` and `leather_layer_2.png`, assign a deterministic 1-based layer index $k \in [1, N]$ mapped to a 24-bit RGB value to each equipment model, and inject an adapted LessFancyPants GLSL core shader (`rendertype_armor_cutout_no_cull.json`, `.vsh`, `.fsh`) into root assets (`assets/minecraft/shaders/core/`) targeting client formats 34 through 45 (1.20.0 to 1.21.3) with `#define TOTAL_LAYERS` dynamically configured, while strictly omitting legacy shaders from `overlay_v1_21_4`.

#### Scenario: Vertical armor atlas generation
- **WHEN** pack compilation is triggered with 3 custom equipment models in `hybrid_shaders` mode
- **THEN** compiler produces `leather_layer_1.png` and `leather_layer_2.png` vertically stacking the base leather texture followed by the 3 custom armor textures with height matching `64 * (total_layers)` (or equivalent base resolution multiple) and injects the corresponding layer mappings into the build summary

#### Scenario: LessFancyPants core shader injection
- **WHEN** compiler runs in `hybrid_shaders` mode
- **THEN** root assets contain `shaders/core/rendertype_armor_cutout_no_cull.vsh` with constant-time vertex UV remapping and `shaders/core/rendertype_armor_cutout_no_cull.fsh` with lightweight cutout sampling, while modern `overlay_v1_21_4` remains free of legacy shaders

#### Scenario: Shader omission in modern-only mode
- **WHEN** workspace compatibility profile is set to `modern_native`
- **THEN** compiler stages canonical equipment descriptors in root and `overlay_v1_21_2` without synthesizing `leather_layer_*.png` vertical atlases and without injecting legacy core shaders

### Requirement: Workspace Pack Compatibility Profile Resolution
The resource pack compiler MUST support a `compatibility_profile` configuration in workspace pack manifests with three distinct options: `modern_native` (1.21.2+ canonical descriptors only), `hybrid_shaders` (native descriptors alongside legacy LessFancyPants core shaders and stitched leather atlases), and `hybrid_trims` (native descriptors alongside armor trim fallbacks), persisting the active profile in `data/packs/workspace/manifest.json` and exposing it in compilation metadata.

#### Scenario: Resolving default compatibility profile
- **WHEN** a workspace does not define an explicit `compatibility_profile`
- **THEN** system defaults to `hybrid_shaders` to ensure backward compatibility for legacy clients

#### Scenario: Changing compatibility profile
- **WHEN** an operator selects `modern_native` in workspace settings
- **THEN** subsequent pack builds omit legacy armor shaders and stitched leather atlases, packaging only canonical 1.21.2+ equipment descriptors and item definitions
