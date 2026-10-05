# Proposal: Oraxen Catalog and Asset Browser

## Why

Currently, content authors in the web client must manually type vanilla material names, guess `custom_model_data` numbers, and write item definitions blindly without visibility into what materials exist in Minecraft 1.21 or what custom items are already registered in server plugins like Oraxen. This leads to configuration errors, CustomModelData collisions with existing resource packs, and a disconnected authoring workflow.

By introducing a categorized multi-source catalog browser (Vanilla, Platform drafts, and live Oraxen discovered items) along with a hybrid schema-driven/raw YAML editor and bidirectional Oraxen export via `paper-agent`, authors can visually explore existing assets, fork them as templates, avoid collision risks, and deploy directly into Oraxen configurations.

## What Changes

- **Target-Linked Discovered Catalog**: Persist external items discovered on Paper servers (e.g., Oraxen) into a target-indexed database table (`discovered_catalog_items`) so they remain queryable even when targets are offline.
- **Agent Protocol Discovery Extensions**: Extend the WebSocket protocol to report detected plugins (`detectedPlugins`) during handshake `hello`, and support bidirectional catalog sync messages (`catalog:refresh` request and `catalog:manifest` event/response).
- **Paper Agent Oraxen Adapter & Exporter**: Implement an Oraxen hook in `paper-agent` using soft-dependency reflection/Bukkit API to inspect `OraxenItems`, stream manifests, and write deployed items into Oraxen YAML (`plugins/Oraxen/items/platform_*.yml`) with hot-reload invocation.
- **Config Schemas & Mappings Engine**: Introduce a declarative schema registry (`oraxen-item-v1`) that powers a reactive modular form for Oraxen-specific properties (Pack models, Mechanics, Durability) with instant fallback and bi-directional synchronization to a raw YAML/JSON editor.
- **Unified Web Asset Browser**: Add an interactive multi-tab Asset Browser in the frontend (`Vanilla 1.21`, `Platform Drafts`, `Oraxen (Target)`) with search, CMD filtering, and a 1-click **Fork / Use as Base** action that pre-populates the Item Editor.

## Capabilities

### New Capabilities
- `catalog-management`: Manages multi-source asset catalogs (Vanilla 1.21 taxonomy, target-linked discovered items from Oraxen/Nexo, and configuration schema registries for plugin mappings).

### Modified Capabilities
- `agent-protocol`: Extends the handshake `hello` payload with detected plugin capabilities, and adds typed `catalog:refresh` request and `catalog:manifest` response/event envelopes.
- `paper-agent-adapter`: Adds Oraxen soft-dependency discovery hooks, manifest serialization, and bidirectional YAML file export with reload execution.
- `content-model`: Extends the canonical item definition model to include export targets (`native`, `oraxen`), schema-mapped plugin configurations, and raw YAML extension blocks.

## Impact

- **Backend**:
  - New entity `DiscoveredCatalogItemModel` and database migration/schema update.
  - New endpoints in `app/api/catalogs.py` (`/api/catalogs/vanilla`, `/api/catalogs/targets/{id}/items`, `/api/catalogs/targets/{id}/sync`, `/api/schemas/plugins/{id}`).
  - Gateway message handler updates in `app/gateway/manager.py` for `catalog:manifest` and `catalog:refresh`.
- **Frontend**:
  - New `AssetBrowser` component with tabbed views, search, and "Fork as Base".
  - Enhanced `ItemEditor` with Exporter target selection, Modular Reactive Form, and synchronized Raw YAML editor.
- **Paper Agent**:
  - Updated `paper-plugin.yml` with `softdepend: [Oraxen]`.
  - `OraxenCatalogProvider` and `OraxenItemExporter` classes under `com.minecraft.agent.adapter.oraxen`.
- **Protocol**:
  - Backward-compatible additions to protocol envelope payloads.
