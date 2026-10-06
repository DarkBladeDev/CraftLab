# Proposal

## Why

Creators and server developers configuring custom items, blocks, and virtual props in CraftLab need direct, fine-grained control over raw resource pack assets (textures, geometric JSON models, modern 1.21.2+ item definitions, and sound files). Currently, assets are split between automated database generators and opaque external ZIP archives without a dedicated workspace folder or visual filesystem inspector. Furthermore, manually typing Minecraft resource locations (`namespace:path`) is error-prone due to Minecraft's varying folder prefix and file extension stripping conventions across asset types.

Introducing a dedicated **Asset Workspace Explorer** provides a 3-panel visual workbench (Resource Explorer, Content Viewer, Metadata Viewer) for browsing and authoring assets in an editable workspace pack, auto-resolving accurate Minecraft Resource Locations, validating JSON syntax in real time, and seamlessly integrating with the compiler pipeline and item studios.

## What Changes

- **Dedicated Project Workspace Pack**: Create and manage a persistent workspace directory at `data/packs/workspace/`. Automatically initialize it with standard Minecraft resource pack scaffolding (`pack.mcmeta` and `assets/minecraft/` directories) when empty.
- **Resource Pack Build Pipeline Integration**: Include the workspace pack as a high-priority authoring layer in the automated `build_resource_pack` and pre-flight validation workflow, ensuring workspace assets are deterministically compiled into distribution ZIPs.
- **REST API for Workspace Assets**: Endpoints for directory tree enumeration, file upload/download, folder creation with Minecraft-safe naming validation (`^[a-z0-9_.-]+$`), deletion, direct JSON content reading and saving, and Minecraft metadata calculation.
- **3-Panel Asset Workspace Interface**:
  - **Resource Explorer (Left)**: Hierarchical file tree with expand/collapse, search and asset type filters (textures, models, sounds), safe folder creation, and drag-and-drop file upload.
  - **Content Viewer (Top-Right)**: Adaptive preview & editor panel featuring nearest-neighbor pixelated PNG zoom (1x-8x) with alpha grid, direct JSON text editor with line numbers, real-time syntax error linting, formatting, and `Ctrl+S` save, plus an audio player for OGG sound files.
  - **Metadata Viewer (Bottom-Right)**: Dynamic Minecraft Resource Location (`namespace:path`) calculator that accounts for Minecraft's prefix/extension stripping rules per asset type, accompanied by 1-click copy buttons (Resource Location, 1.21.2+ `item_model` tag, JSON model `layer0` reference, `/give` command), asset technical specifications (dimensions, file size), and cross-reference dependency integrity checks.
- **Studio Asset Picker Modal**: An asset selector dialog in Item Studio and Block Studio enabling authors to browse and select workspace textures and models with automatic Resource Location insertion.

## Capabilities

### New Capabilities
- `asset-workspace`: Comprehensive workspace pack file manager, adaptive content viewer/editor, dynamic Minecraft Resource Location resolver, and metadata inspector.

### Modified Capabilities
- `resource-pack-pipeline`: Merge the local workspace pack directory (`data/packs/workspace/`) as a high-priority layer in the build and pre-flight validation pipeline.
- `item-studio`: Integrate the workspace asset picker modal into item model and texture configuration fields.

## Impact

- **Backend**:
  - `backend/app/api/packs.py`: Add workspace file tree, file content, upload, folder create, and metadata endpoints; update compilation logic to include `data/packs/workspace/`.
  - `backend/app/domain/pack_merger.py` / `pack_validator.py`: Support workspace pack layer in pre-flight checks and semantic merges.
- **Frontend**:
  - New feature directory `frontend/src/features/assets/` containing `AssetWorkspaceView.tsx`, `ResourceExplorer.tsx`, `ContentViewer.tsx`, `MetadataViewer.tsx`, and `AssetPickerModal.tsx`.
  - `frontend/src/App.tsx`: Add navigation tab for "Assets / Workspace Explorer".
  - `frontend/src/features/items/ItemEditor.tsx`: Add asset picker launch button for `item_model` and model fields.
- **Dependencies**: No external npm or pip dependencies required (uses native Canvas/img pixelated rendering, HTML5 Audio, standard React and FastAPI primitives).
