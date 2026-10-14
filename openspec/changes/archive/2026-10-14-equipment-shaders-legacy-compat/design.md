# Technical Design: Equipment Shaders Legacy Compatibility (< 1.21.2)

## Context

See `proposal.md` for problem background and motivation.

Currently, CraftLab authoring supports modern Minecraft 1.21.4+ equipment descriptors (`assets/<namespace>/equipment/<id>.json`), maintains an automatic mirror under `overlay_v1_21_2/assets/<namespace>/models/equipment/<id>.json` for 1.21.2-1.21.3 clients, and routes modern shader programs to `overlay_v1_21_4`.

However, clients on versions prior to 1.21.2 (1.20.0 through 1.21.1) do not support the `minecraft:equippable` component or `equipment` JSON descriptors, and Minecraft's vanilla render engine does not evaluate `CustomModelData` when drawing armor textures onto humanoid player armatures. To support legacy clients on multi-version servers, CraftLab bridges the gap using an adapted **LessFancyPants Core Shader pipeline** combined with automated vertical atlas stitching and item metadata projection.

## Goals / Non-Goals

**Goals:**
- Provide full Level 2 visual parity (body armor textures) for Minecraft 1.20.0 - 1.21.1 clients without requiring client-side mods (pure vanilla client compatibility).
- Embed an adapted fork of **LessFancyPants** utilizing GLSL vertex shader UV transformations for $O(1)$ constant-time execution without fragment shader loop overhead.
- Automatically stitch referenced `humanoid` and `humanoid_leggings` textures into vertical atlas sheets (`leather_layer_1.png` and `leather_layer_2.png`) during pack compilation.
- Introduce workspace-level `compatibility_profile` configuration (`modern_native`, `hybrid_shaders`, `hybrid_trims`) to control asset compilation and packaging.
- Synchronize Item Studio and backend item definitions so that equippable items auto-derive `custom_model_data`, 24-bit RGB `dyed_color`, `LEATHER_*` material conversion, and combat attribute modifiers when hybrid mode is active.
- Support runtime fallback in `CraftLab-plugin` on Paper servers running versions prior to 1.21.2.

**Non-Goals:**
- Custom 3D cube geometry on chest, legs, or feet for pre-1.21.2 clients (vanilla humanoid armature is rigid; 3D geometry is strictly restricted to helmet/head slot via CMD).
- Dynamic tinting/dyeing of custom armor textures in legacy mode (LessFancyPants deliberately replaces tinting with constant-color sampling for performance and atlas capacity).
- Bypassing third-party shaderpacks (Iris/OptiFine): when external shaders replace the Minecraft Core Shader pipeline, core shaders are deactivated by the client mod; this is a known engine constraint.

## Decisions

### 1. Adapted LessFancyPants Fork over Original FancyPants
- **Decision**: Adopt Godlander's LessFancyPants architecture for the injected `rendertype_armor_cutout_no_cull` core shader.
- **Rationale**:
  - Original FancyPants runs color-decoding and texture coordinate calculations inside the fragment shader (`.fsh`) on every pixel, introducing branch conditions and texture lookups per rendered fragment.
  - LessFancyPants performs the entire coordinate transformation in the vertex shader (`.vsh`), which runs only once per polygon vertex (~100 times per entity).
  - The fragment shader simply samples the texture at the precalculated UV coordinate and performs alpha cutout discarding, avoiding frame drops even with dozens of armored entities on screen.
- **Alternatives Considered**: Custom GLSL shader from scratch (redundant effort when LessFancyPants is battle-tested in the community); Armor Trims only (does not allow full custom texture artwork, only trim palettes).

### 2. Automated Vertical Atlas Stitcher in `pack_merger.py`
- **Decision**: Implement `ArmorAtlasStitcher` inside `CraftLab-backend/app/domain/pack_merger.py` that automatically stacks layer textures vertically.
- **Rationale**:
  - A standard armor layer is 64x32 (or 64x64). By stacking textures vertically, $N$ equipment models produce an image of $64 \times (32 \times (N + 1))$.
  - Slot 0 ($Y \in [0, 1/(N+1)]$) contains vanilla leather armor for un-modded leather items.
  - Slots $1 \dots N$ contain custom equipment model textures.
  - The vertex shader formula calculates:
    $$\text{out\_texCoord.y} = \frac{\text{UV0.y} + \text{float}(ID - 1)}{\text{float}(TOTAL\_LAYERS)}$$
  - The backend dynamically injects `#define TOTAL_LAYERS <count>` into `rendertype_armor_cutout_no_cull.vsh` upon packaging.

### 3. Deterministic 24-bit Color & ID Allocation
- **Decision**: Allocate sequential 1-based IDs ($1, 2, 3 \dots$) mapped directly to RGB colors for leather items.
- **Rationale**:
  - Minecraft leather armor encodes color as an integer in `display.color` (or `minecraft:dyed_color.rgb`): $\text{Color} = R \cdot 65536 + G \cdot 256 + B$.
  - In GLSL, `in vec4 Color` yields normalized components $R, G, B \in [0.0, 1.0]$.
  - The vertex shader decodes:
    $$\text{int ID} = \text{int}(\text{round}(\text{Color.r} \times 255.0)) + \text{int}(\text{round}(\text{Color.g} \times 255.0)) \times 256 + \dots$$
  - ID 1 maps to RGB `#000001` (R:0, G:0, B:1). ID 2 maps to `#000002`, up to $16,777,215$ possible IDs.
  - In Item Studio, this RGB integer is automatically populated without manual hex calculations.

### 4. Core Shader Scoping & 1.21.4 Isolation
- **Decision**: Place the legacy core shader files in `assets/minecraft/shaders/core/` in the root pack (formats 34–45, MC 1.20.0–1.21.3) and ensure `ShaderRouter` keeps `overlay_v1_21_4` clean of legacy shaders.
- **Rationale**:
  - Minecraft 1.21.4 overhauled vertex formats and core shader uniforms. Loading a 1.20-1.21.3 core shader in 1.21.4+ crashes the shader compiler.
  - Since 1.21.4 clients natively evaluate `assets/<ns>/equipment/<id>.json`, they do not need the shader hack.
  - Keeping legacy shaders in root and omitting them from `overlay_v1_21_4` guarantees zero collision across client versions.

### 5. Multi-Version Item Metadata and Attribute Compensation
- **Decision**: In `hybrid_shaders` mode, CraftLab items targeting equipment slots carry dual metadata:
  - **Modern**: `components["minecraft:equippable"] = {"slot": "chest", "asset_id": "craftlab:ruby"}`.
  - **Legacy**: `material = "LEATHER_CHESTPLATE"`, `custom_model_data = 1001`, `components["minecraft:dyed_color"] = {"rgb": 1}`, `item_flags = ["HIDE_DYE"]`, and `components["minecraft:attribute_modifiers"]` providing diamond/netherite defense stats.
- **Rationale**:
  - Legacy clients see custom icon in GUI (via CMD 1001), custom armor on body (via dye color 1 + shader), and proper defense stats (via attribute modifiers).
  - Modern 1.21.2+ clients ignore CMD and dye color, rendering the native `asset_id` directly.

## Architecture Diagram

```
+=============================================================================+
|                      CRAFTLAB ASSET AUTHORING WORKSPACE                     |
|                                                                             |
|  Creative Assets Lab:                        Item Studio:                   |
|  assets/craftlab/equipment/ruby.json         ID: ruby_chestplate            |
|  - humanoid: textures/.../ruby_layer_1.png   - equippable: craftlab:ruby    |
|  - humanoid_leggings: .../ruby_layer_2.png   - material: LEATHER_CHESTPLATE |
|  - shader_id: 1, color_rgb: #000001          - cmd: 1001, dyed_color: 1     |
+=============================================================================+
                                       |
                                       v
                     [pack_merger.py / Pack Compiler]
                    (Profile: hybrid_shaders / format 34)
                                       |
         +-----------------------------+-----------------------------+
         |                                                           |
         v                                                           v
  [Root Assets (1.20.0 - 1.21.3)]                         [overlay_v1_21_2 / 4]
  - assets/craftlab/equipment/ruby.json                   - overlay_v1_21_2:
  - assets/minecraft/textures/models/armor/                 assets/craftlab/models/
    leather_layer_1.png (Vertical Atlas)                    equipment/ruby.json
    leather_layer_2.png (Vertical Atlas)                  - overlay_v1_21_4:
  - assets/minecraft/shaders/core/                          Clean (no legacy shaders)
    rendertype_armor_cutout_no_cull.vsh                   - assets/craftlab/items/
    rendertype_armor_cutout_no_cull.fsh                     ruby_chestplate.json
  - assets/minecraft/models/item/
    leather_chestplate.json (CMD: 1001)
```

## Risks / Trade-offs

- **[Risk] Third-Party Shaders (Iris / OptiFine)**: When a player on `< 1.21.2` uses custom shaderpacks (Complementary, BSL), core shaders are bypassed.
  - *Mitigation*: The player still sees the custom item icon in inventory/hand via `CustomModelData`. CraftLab displays an informative compatibility warning in UI docs.
- **[Risk] OpenGL Texture Height Limits**: Very large numbers of armor sets could exceed maximum texture height.
  - *Mitigation*: At 64x32 per armor layer, an 8192px texture height accommodates 256 armor sets. CraftLab pre-flight validation checks atlas height and warns if approaching limits.
- **[Risk] Shader compilation failure across minor releases**:
  - *Mitigation*: The LessFancyPants GLSL code is tested for OpenGL 3.2 Core Profile spanning 1.20 through 1.21.3. For 1.21.4+, `ShaderRouter` isolates modern pipelines.

## Migration Plan

1. Workspaces without an explicit `compatibility_profile` default to `hybrid_shaders`, ensuring zero regression for existing multi-version server setups.
2. Existing equipment models in `assets/<namespace>/equipment/*.json` remain completely unchanged in format. The legacy atlas and shaders are synthesized dynamically during compilation.
3. Item definitions created prior to this change can be updated via a 1-click "Apply Legacy Compatibility Fallback" button in Item Studio.
