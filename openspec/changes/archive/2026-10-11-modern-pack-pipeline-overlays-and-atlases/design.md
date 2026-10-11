# Design

## Context

See [proposal.md](file:///C:/Users/antua/OneDrive/Documentos/Programming/MISC/MinecraftResourceManager/openspec/changes/modern-pack-pipeline-overlays-and-atlases/proposal.md) for background and motivation.

Currently, CraftLab's resource pack pipeline (`CraftLab-backend/app/domain/`) consists of:
- `DeterministicPackCompiler`: Generates bit-identical zip archives with SHA-1 hashing, but hardcodes `pack_format: 34`, `max_inclusive: 65`, and a single overlay `overlay_v1_21_2` covering formats 42 to 65.
- `SemanticMerger`: Merges `sounds.json`, `font/*.json`, `lang/*.json`, `models/item/*.json`, and `items/*.json`. It performs naive exact-string deduplication on `atlases/*.json` sources, and treats all other assets (including `.vsh`, `.fsh`, and shader JSONs) as raw file overwrites via `shutil.copy2`.
- `PreflightValidator`: Scans for CustomModelData overlaps and `item_model` collisions, but lacks checks for shader collisions, missing texture files referenced by models, or texture dimension anomalies.

Minecraft 1.21.2 and 1.21.4 require distinct asset handling: 1.21.2 introduced Item Definition V2 (`items/*.json`), while 1.21.4 introduced breaking core shader vertex format refactoring.

## Goals / Non-Goals

**Goals:**
- Implement a cumulative, multi-version overlay architecture: Root (formats 34..41), `overlay_v1_21_2` (formats 42..`max_inclusive`), and `overlay_v1_21_4` (formats 46..`max_inclusive`).
- Support dynamic, operator-configurable `max_inclusive` bounds across API and compiler endpoints.
- Build `PackManifestInspector` to inspect incoming `pack.mcmeta` on external zip uploads/agent syncs and remap arbitrary overlay directories to canonical targets.
- Extend `PreflightValidator` with core shader collision checks and physical texture reference integrity verification (verifying that every texture path declared in a model exists on disk, power-of-two mipmap validation, animated spritesheet `.png.mcmeta` verification).
- Build `AtlasSynthesizer` to automatically scan model texture locations and inject deduplicated, grouped `directory` sources into `assets/minecraft/atlases/blocks.json` and `assets/minecraft/atlases/gui.json`.
- Implement `ShaderRouter` to stage legacy shaders (1.21.0 - 1.21.3) in root assets and modernized 1.21.4+ shaders in `overlay_v1_21_4`.

**Non-Goals:**
- Automated GLSL AST merging or deep syntax unification of conflicting shaders (shader conflicts will be audited with warnings and resolved deterministically by layer priority).
- Third-party mod-specific shader formats (e.g. Iris/OptiFine shaderpack pipelines; this focuses exclusively on vanilla client resource pack shaders).
- Modifying client-side runtime behavior.

## Decisions

### Decision 1: Cumulative Overlay Stacking with Version Naming
- **Choice**: Root -> `overlay_v1_21_2` -> `overlay_v1_21_4`.
- **Rationale**: Vanilla Minecraft processes overlays in listed order. Clients on 1.21.2-1.21.3 get modern item definitions from `overlay_v1_21_2`. Clients on 1.21.4+ inherit modern item definitions from `overlay_v1_21_2` and subsequently receive modern shader definitions from `overlay_v1_21_4`. This eliminates file duplication between overlays while preserving version isolation.
- **Alternatives Considered**:
  - *Strict Version-Bracketed Overlays* (e.g. separate 42-45 and 46-65 folders): Would require duplicating all `items/*.json` definitions inside the 1.21.4 folder, inflating pack size.

### Decision 2: Ingested Manifest Inspection & Overlay Remapping (`PackManifestInspector`)
- **Choice**: When a pack source is ingested, inspect `pack.mcmeta`. If `overlays.entries` exist, index each entry's format range and map the files into canonical targets:
  - Formats $\le 41 \rightarrow$ Root (`assets/`)
  - $42 \le \text{format} \le 45 \rightarrow$ `overlay_v1_21_2/assets/`
  - $\text{format} \ge 46 \rightarrow$ `overlay_v1_21_4/assets/`
- **Rationale**: External tools and community packs use non-standard overlay folder names (e.g., `overlay_18`, `v2`, `items_42`). Blind folder extraction breaks overlay resolution in CraftLab.
- **Alternatives Considered**:
  - *Raw extraction*: Retains foreign folder names, requiring CraftLab to generate chaotic `pack.mcmeta` files with mismatched overlays.

### Decision 3: Texture Atlas Auto-Synthesis (`AtlasSynthesizer`)
- **Choice**: During compilation, scan all model textures (`models/**/*.json` and `items/**/*.json`). Collect unique namespaces and first directory segments (e.g., `studio:item`, `studio:props`, `itemsadder:custom`). For each custom namespace discovered, synthesize `directory` sources in `assets/minecraft/atlases/blocks.json`:
  ```json
  {
    "type": "directory",
    "source": "<namespace>:<dir>",
    "prefix": "<dir>/"
  }
  ```
  Also scan for `textures/gui/sprites/**` across layers and inject corresponding directory sources into `assets/minecraft/atlases/gui.json`.
- **Rationale**: In modern Minecraft, textures under custom namespaces are completely ignored by the GPU sprite stitcher unless explicitly registered in `atlases/blocks.json` or `atlases/gui.json`. Auto-synthesis eliminates the dreaded "missing sprite / black-and-magenta checkerboard" bug automatically.
- **Alternatives Considered**:
  - *Injecting individual `single` sources*: Can generate thousands of lines in `blocks.json`, slowing client atlas stitch parsing. Grouped `directory` sources are compact and efficient.

### Decision 4: Shader Conflict Auditing & Version Classification
- **Choice**:
  1. Pre-flight check scans active layers for overlapping files under `assets/*/shaders/core/**`. If multiple layers supply the same program, log a `warning` with layer details.
  2. `ShaderRouter` examines shader JSON definitions and GLSL headers/version directives: files targeting 1.21.4+ are staged in `overlay_v1_21_4/assets/minecraft/shaders/core/`, while legacy shaders remain in root assets.
- **Rationale**: 1.21.4 clients crash when loading 1.21.0-1.21.3 core shaders due to vertex format incompatibilities. Isolating them inside the 1.21.4 overlay protects both legacy and modern clients.

### Decision 5: Texture & Mipmap Pre-Flight Auditor
- **Choice**: Verify that every texture resource location string declared in any JSON model resolves to a concrete `.png` file in one of the active layers. Inspect PNG header bytes (width, height) to ensure power-of-two dimensions (16, 32, 64, 128, etc.) for mipmap rendering safety, and flag vertical spritesheets lacking `.png.mcmeta`.
- **Rationale**: Catches broken models and corrupted textures before client deployment rather than requiring manual game client log inspection.

## Risks / Trade-offs

- **[Risk] Deeply nested texture paths under custom namespaces**: If a model uses `studio:sub/nested/dir/texture`, a naive top-level directory source might misalign prefixes.
  - *Mitigation*: The directory scanner parses the path up to the parent folder of the texture, constructing accurate `source` and `prefix` pairs, falling back to a `single` source if prefixing is ambiguous.
- **[Risk] Performance overhead during pre-flight check with thousands of textures**:
  - *Mitigation*: Index physical files once using an in-memory `Set[str]` during layer staging, providing $O(1)$ existence lookups for all model texture references.
- **[Risk] Operators using non-standard snapshot client versions**:
  - *Mitigation*: Operator-configurable `max_inclusive` parameter in the build request and workspace configuration ensures forward compatibility without code changes.
