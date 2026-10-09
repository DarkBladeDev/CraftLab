# Proposal

## Why

CraftLab currently exhibits several quality-of-life frictions, UI edge-case bugs, and missing CRUD controls across the Asset Explorer, Resource Pack Manager, Block Studio, and Item Catalog. Resolving these issues streamlines asset management, ensures pixel-perfect texture previews, eliminates model confusion for placed props, and provides a dynamic, comprehensive vanilla catalog.

## What Changes

- **Asset Explorer Operations**: Add filesystem rename support for directories and files (`POST /v1/packs/workspace/rename`) and enhance directory deletion UX in the Resource Explorer tree.
- **Content Viewer Fix**: Fix texture display offsets by aligning the checkerboard background container directly with the scaled image layout dimensions, removing arbitrary margin hacks.
- **Workspace Pack Configuration**: Expose base attributes of the main workspace pack (`pack.mcmeta` description, format versions, layer priority) through backend endpoints and UI controls.
- **Imported Pack Layer Management**: Allow modifying imported pack sources (rename, change layer priority, toggle active state, delete) via `PATCH /v1/packs/sources/{source_id}`.
- **Prop Model Identification**: Rename placed 3D display model attribute to `Block Model Identifier` (`block_model`) and introduce an optional `Item Model Identifier` (`item_model`) for the held/inventory item representation.
- **Solid Barrier Mechanics**: In Block Studio, disable or hide block hardness and optimal tool controls when Hitbox Type is `Solid Barrier`, reflecting vanilla unbreakable barrier semantics.
- **Lie Down Prop Interaction**: Add `Lie Down (Lay back in the block on right-click)` (`lay`) interaction behavior to Block Studio and the Paper runtime agent (via PacketEvents `SLEEPING` pose metadata).
- **Block-Only Snapshot Revisions**: Allow creating revision snapshots when the project contains blocks/props even if 0 items are defined.
- **Collapsible Multi-Source Asset Browser**: Provide a toggle collapse/expand button in Item Studio for the Asset Browser to recover screen space.
- **Vanilla Catalog Polish**: Rename category tab from `Vanilla 1.21 (X)` to `Vanilla (X)` and replace the static dictionary with a complete, dynamic repertoire of vanilla items with texture URLs.

## Capabilities

### New Capabilities
*(None)*

### Modified Capabilities
- `asset-workspace`: Add directory/file rename endpoint and UI actions, and guarantee pixel-perfect aligned image scaling in Content Viewer.
- `resource-pack-pipeline`: Support reading/updating workspace pack manifest attributes and updating imported pack layer priorities, names, and deletion.
- `block-studio`: Support distinct `block_model` and `item_model` fields, conditional barrier break controls, "Lie Down" interaction mechanics, and block-only snapshot revisions.
- `catalog-management`: Support dynamic loading of a comprehensive vanilla Minecraft catalog with official textures, and collapsible UI with simplified category labeling.

## Impact

- **Backend (`CraftLab-backend`)**:
  - `app/api/packs.py`: New endpoints for workspace rename, workspace config, and source editing.
  - `app/api/items.py`: Relax revision creation constraint to allow revisions with 0 items if blocks exist.
  - `app/models/block.py` & `app/domain/blocks.py`: Include `block_model` and `lay` interaction type.
  - `app/domain/catalogs.py`: Load dynamic vanilla catalog from a tracked resource file.
- **Frontend (`CraftLab-frontend`)**:
  - `api/client.ts`: New client methods for rename, source update, and workspace config.
  - `features/assets/ResourceExplorer.tsx`: Rename/delete directory actions.
  - `features/assets/ContentViewer.tsx`: Fix scaled image alignment and checkerboard container.
  - `features/packs/ResourcePackManagerView.tsx`: Edit modal/card for workspace and source layers.
  - `features/blocks/BlockStudio.tsx`: "Block Model" vs "Item Model", barrier hitbox condition, "Lie Down" interaction.
  - `features/items/AssetBrowser.tsx`: Collapsible header toggle, "Vanilla (X)" tab title.
- **Plugin (`CraftLab-plugin`)**:
  - `PropDefinition.java`, `PropManager.java`, `PropPlaceBreakListener.java`: Use `block_model` for world ItemDisplay and `item_model` for item drops/holding.
  - `PropInteractionListener.java`: Handle "Lie Down" interaction pose.
