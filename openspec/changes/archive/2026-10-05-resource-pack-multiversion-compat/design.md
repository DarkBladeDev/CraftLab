# Design: Multi-Version Resource Pack Compatibility (1.21.1 - 1.21.11)

## Context

The resource pack pipeline currently emits a single legacy resource pack structure targeting Minecraft 1.21.0 - 1.21.1 using `pack_format: 34` and `models/item/<material>.json` overrides. In Minecraft 1.21.2+, Mojang deprecated item model overrides in favor of Item Models V2 (`items/<material>.json`) with `select` properties and introduced native `item_model` data components. Minecraft supports resource pack overlays via `pack.mcmeta` allowing a single zip file to deliver version-specific assets. Official schemas from `vanilla-mcdoc` define the syntax for `item_definition` and `pack.mcmeta`. See `proposal.md` for motivation.

## Goals / Non-Goals

**Goals:**
- Implement a Universal Hybrid Pack ZIP structure using Mojang's native `overlays` mechanism supporting Minecraft 1.21.1 through 1.21.11 without duplicate texture/sound asset overhead.
- Build an intermediate Canonical Item Model AST and Dual-Projection Compiler that emits both legacy `models/item/<mat>.json` overrides (for 1.21.1 clients) and modern `items/<mat>.json` Item Definitions (for 1.21.2 - 1.21.11 clients) conforming to `vanilla-mcdoc` schemas.
- Enable bidirectional model translation during pack source ingestion (converting legacy plugin packs like Oraxen to modern definitions and vice-versa).
- Add `item_model` namespaced identifier support to the Content Model, Item Studio UI, and Pre-flight Conflict Validator.
- Enable runtime-aware `item_model` component assembly in the Paper agent for Paper 1.21.2+ servers with graceful fallback to `custom_model_data` on 1.21.1.

**Non-Goals:**
- Creating separate ZIP distribution endpoints for each individual Minecraft version (we use a single Universal Hybrid Pack).
- Supporting pre-1.21 Minecraft versions (e.g., 1.20.4 or older).
- Transpiling complex blockstates or entity models; the multi-version generator focuses on item models and item definitions.

## Decisions

### 1. Universal Pack Overlays over Per-Target ZIPs
- **Decision**: Produce a single zip archive with `pack_format: 34`, `supported_formats: {"min_inclusive": 34, "max_inclusive": 65}`, and `overlays: [{"directory": "overlay_v1_21_2", "formats": {"min_inclusive": 42, "max_inclusive": 65}}]`.
- **Rationale**: Server networks commonly deploy ViaVersion/ViaBackwards where players on 1.21.1 and 1.21.4 connect to the same server simultaneously. A single hybrid pack allows both versions to see custom textures without maintaining separate target endpoints.
- **Alternatives Considered**: Per-target compilation would create simpler ZIPs but break players on multi-version proxy networks.

### 2. Common Root Assets with Overlay-Only Dispatch Files
- **Decision**: Place all `.png` textures, `.ogg` sounds, font definitions, and geometric models under the root `assets/` directory. Place only version-divergent dispatch files (`assets/minecraft/items/*.json`) in `overlays/overlay_v1_21_2/`.
- **Rationale**: 1.21.2+ clients inherit root assets when applying overlays. Duplicating textures inside the overlay would double the download size of the pack.
- **Alternatives Considered**: Duplicating the entire pack tree inside `overlays/` was rejected due to bandwidth and storage cost.

### 3. Intermediate Canonical AST for Dual Projection
- **Decision**: Define `ItemModelMapping` AST in `pack_merger.py`:
  ```python
  @dataclass
  class ItemModelMapping:
      material: str
      custom_model_data: int
      model_path: str
      item_model_id: Optional[str] = None
  ```
  During merging, both `models/item/<mat>.json` and `items/<mat>.json` are ingested into this AST. The compiler then projects:
  - **Base Layer**: `models/item/<mat>.json` with sorted `overrides`.
  - **Overlay Layer**: `items/<mat>.json` with `type: "minecraft:select"` on `property: "minecraft:custom_model_data"` and `cases` mapping each integer to `{ "type": "minecraft:model", "model": model_path }`.
- **Rationale**: Ensures deterministic, identical model behavior across both client generations and permits bidirectional pack ingestion from either legacy or modern third-party sources.

### 4. Optional `item_model` with Automatic Fallback Derivation
- **Decision**: In `ItemDefinition` schemas, allow `item_model: Optional[str]`. If omitted, derive it as `<namespace>:<item_id>` for modern item definition files, while using `custom_model_data` as the primary cross-version selector.
- **Rationale**: Provides native 1.21.2+ component support while maintaining 100% backward compatibility for existing draft items and legacy clients.

### 5. Reflective ItemMeta Assembly in Paper Agent
- **Decision**: In `paper-agent`'s `PaperItemAdapter`, always invoke `meta.setCustomModelData(cmd)`. Use reflection to detect if `setItemModel(NamespacedKey)` or `DataComponentTypes.ITEM_MODEL` exists on the runtime Paper server before calling it.
- **Rationale**: Enables the single compiled `paper-agent.jar` to run smoothly on Paper 1.21.1 without throwing `NoSuchMethodError`, while unlocking native item model component delivery on Paper 1.21.2 - 1.21.11.

## Risks / Trade-offs

- **[Risk]** Mojang adjustments to `item_definition` format in subversions (e.g. 1.21.6 `oversized_in_gui`, 1.21.11 `swap_animation_scale`).
  - *Mitigation*: Base the JSON structure on `vanilla-mcdoc` canonical schemas, omitting optional animation scale fields unless explicitly configured.
- **[Risk]** Third-party packs containing conflicting or partial definitions across both legacy and modern paths.
  - *Mitigation*: Extend `PreflightValidator` to inspect both `models/item/` and `items/` and report colliding identifiers across all active layers.
