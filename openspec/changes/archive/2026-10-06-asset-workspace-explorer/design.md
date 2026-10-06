# Design: Asset Workspace Explorer

## Context

CraftLab manages Minecraft 1.21 resource packs through external uploaded ZIP sources (`data/packs/sources/`) and dynamically synthesized database layers for items and blocks (`backend/app/domain/pack_merger.py`). However, authors currently have no dedicated filesystem space to directly author, inspect, and organize raw custom textures, handcrafted JSON models, 1.21.2+ item definitions, and sound effects.

This design introduces a persistent workspace pack directory (`data/packs/workspace/`), a comprehensive REST API for filesystem manipulation and metadata analysis, and a responsive 3-panel UI aligned with the user wireframe.

## Goals / Non-Goals

**Goals:**
- Provide a persistent filesystem workspace at `data/packs/workspace/` that auto-initializes with standard Minecraft resource pack scaffolding (`pack.mcmeta` and `assets/minecraft/` subdirectories) if empty.
- Implement a 3-panel workspace interface:
  1. **Resource Explorer (Left)**: Hierarchical file tree with search/category filtering, folder creation, asset upload, and deletion.
  2. **Content Viewer (Top-Right)**: Nearest-neighbor pixelated PNG viewer with zoom (1x to 8x) and alpha grid, direct JSON editor with live syntax checking, formatting, and `Ctrl+S` save, plus an HTML5 OGG audio player.
  3. **Metadata Viewer (Bottom-Right)**: Dynamic Minecraft Resource Location resolution (`namespace:path`), one-click copy options, file specs, and cross-reference dependency integrity checks.
- Integrate the workspace pack layer into `build_resource_pack` and pre-flight validation.
- Provide an Asset Picker modal in `ItemEditor.tsx` to directly browse and select workspace models and textures.

**Non-Goals:**
- In-browser 3D vertex mesh modeling (Blockbench replacement); the viewer edits raw JSON models and previews textures.
- In-browser raster paint tool; users author PNGs in external software and upload/drop them into the explorer.
- Modifying packs outside the workspace folder (uploaded third-party sources remain immutable).

## Decisions

### 1. Physical Filesystem Workspace Storage vs. Database Blobs
- **Decision**: Store workspace assets directly on disk at `data/packs/workspace/`.
- **Rationale**: Minecraft resource packs are fundamentally directory hierarchies. Storing files on disk allows standard CLI utilities, external editors, and the existing `SemanticMerger` to treat the workspace as a standard directory layer without deserializing database blobs.
- **Alternatives Considered**: Storing files in an SQLite table (`workspace_files`). Rejected due to unnecessary blob overhead, impedance mismatch with directory mergers, and inability to inspect files directly on the host.

### 2. Layer Precedence in Pack Compilation
- **Decision**: When `build_resource_pack` executes, layers are ordered:
  1. Ingested external sources (`data/packs/sources/*`) by layer priority (ascending).
  2. **Workspace Pack (`data/packs/workspace/`)** (high priority).
  3. **Studio Database Projections** (`studio_layer`, highest priority).
- **Rationale**: Assets authored in the workspace override third-party base packs, while live items explicitly customized in Studio UI take precedence over raw static files.

### 3. Dynamic Minecraft Resource Location Calculation
- **Decision**: Calculate Resource Locations purely from relative paths according to Minecraft 1.21 conventions:
  - `assets/<namespace>/textures/<path>.png` $\rightarrow$ `<namespace>:<path>`
  - `assets/<namespace>/models/<path>.json` $\rightarrow$ `<namespace>:<path>`
  - `assets/<namespace>/items/<path>.json` $\rightarrow$ `<namespace>:<path>` (1.21.2+ Item Definitions)
  - `assets/<namespace>/sounds/<path>.ogg` $\rightarrow$ `<namespace>:<path>`
  - `assets/<namespace>/font/<path>.json` $\rightarrow$ `<namespace>:<path>`
- **Rationale**: Centralizing this logic ensures consistency between the Metadata Viewer, one-click copy buttons, and the Studio Asset Picker.

### 4. Controlled Filesystem Mutation and Security
- **Decision**:
  - Restrict operations strictly to `data/packs/workspace/` using `Path(target).resolve().is_relative_to(WORKSPACE_DIR.resolve())` to prevent path traversal attacks.
  - Enforce Minecraft naming conventions (`^[a-z0-9_.-]+$`) on all folder creations, renames, and uploads.
  - Require valid JSON parsing on the backend before writing `.json` files.

### 5. Content Viewer Architecture
- **Decision**:
  - Textures: Rendered with CSS `image-rendering: pixelated` inside a zoomable container (1x, 2x, 4x, 8x, Fit) with a CSS checkered transparency background and toggleable 16x16 / 32x32 UV grid overlay.
  - JSON Files: Native React code editor component with line numbers, 2-space indentation formatting, instant `try { JSON.parse() }` syntax linting banner, and keyboard listener for `Ctrl+S` / `Cmd+S`.
  - Audio: HTML5 `<audio>` element with play/pause, seek, and volume slider.

```
+-----------------------------------------------------------------------------------+
| FRONTEND COMPONENT TREE                                                           |
+-----------------------------------------------------------------------------------+
| App.tsx                                                                           |
|   └── AssetWorkspaceView                                                          |
|         ├── ResourceExplorer (Tree, Search, Filter, Upload, New Folder)           |
|         │     └── TreeItemNode (recursive file/folder list)                       |
|         ├── ContentViewer (Context-sensitive display)                             |
|         │     ├── ImageViewer (pixelated canvas, zoom 1x-8x, alpha grid)          |
|         │     ├── JsonCodeEditor (syntax lint, format, Ctrl+S save)               |
|         │     └── AudioPlayer (HTML5 OGG stream)                                  |
|         └── MetadataViewer                                                        |
|               ├── ResourceLocationCard (calculated string, multi-copy actions)   |
|               ├── AssetStatsCard (size, dimensions, type)                         |
|               └── CrossReferencesCard (referencing models, missing textures)      |
+-----------------------------------------------------------------------------------+
```

## Risks / Trade-offs

- **[Risk] User attempts directory traversal (`../../etc/passwd`)**:
  - **Mitigation**: Backend sanitizes and verifies that all resolved paths are strictly children of `data/packs/workspace/`.
- **[Risk] Malformed JSON breaks the compiled resource pack**:
  - **Mitigation**: Frontend performs live syntax checking with an error alert, and backend validates `json.loads()` before persisting changes.
- **[Risk] Concurrent edits to files**:
  - **Mitigation**: The workspace is a single-operator local tool; file writes are atomic and return the latest file metadata.
