# Design: Oraxen Catalog and Asset Browser

## Context

See [proposal.md](proposal.md) for motivation.

The current system supports basic item definition authoring and memory-based deployment to Paper 1.21 servers. However, authors lack visual catalog inspection tools, cannot view vanilla materials or existing custom items on their servers, and have no integration with established Minecraft item plugins like Oraxen.

## Goals / Non-Goals

**Goals:**
- Provide a target-linked catalog persistence layer (`discovered_catalog_items`) in the backend.
- Extend the WebSocket protocol to handle `catalog:refresh` and `catalog:manifest` messages, plus plugin detection in `hello`.
- Implement a decoupled, soft-dependency Oraxen discovery provider and YAML exporter in `paper-agent`.
- Build a declarative schema engine supporting `oraxen-item-v1` with dual-mode UI: Modular Reactive Form and syntax-highlighted Raw YAML.
- Build an interactive web `AssetBrowser` with Vanilla, Platform Drafts, and Oraxen tabs, featuring instant search and "Fork as Base".

**Non-Goals:**
- Implementing the Nexo exporter in this change (the schema engine and adapter interfaces support it, but Nexo runtime integration will be done in a subsequent change).
- In-browser 3D model rendering or texture editing.
- Parsing Oraxen YAML files directly in Python (inspection is performed inside the Paper server runtime by `paper-agent`).

## Decisions

### 1. Target-Linked Discovered Item Persistence
- **Choice**: Store discovered items in a dedicated `discovered_catalog_items` table in SQLite with `(target_id, source, item_id)` uniqueness.
- **Alternatives Considered**: In-memory caching on the gateway manager.
- **Rationale**: Persisting discovered items to the database allows content designers to browse the catalog, inspect CustomModelData allocations, and fork templates even when the target Paper server is offline.

### 2. Soft-Dependency Java Runtime Isolation
- **Choice**: Check plugin presence via `Bukkit.getPluginManager().isPluginEnabled("Oraxen")` and isolate Oraxen API calls within an `OraxenCatalogHook` class loaded only when present.
- **Alternatives Considered**: Shading Oraxen API as a required compile-time library or requiring Oraxen to be installed.
- **Rationale**: `paper-agent` must remain lightweight and run cleanly on vanilla Paper servers without throwing `ClassNotFoundException` or failing startup.

### 3. Declarative Schema Registry with Dual Reactive / Raw UI
- **Choice**: Define a JSON schema (`oraxen-item-v1.json`) outlining Oraxen item fields (Pack, Mechanics, Durability). The frontend dynamically renders interactive inputs when the schema matches, with a toggle to a synchronized Raw YAML editor.
- **Alternatives Considered**: Hardcoding Oraxen form components directly in React.
- **Rationale**: Schema-driven rendering ensures that when new plugins (e.g. Nexo) or new Oraxen mechanics are added, no core React UI rewrites are required.

### 4. File-Based Exporter Deployment & Reload
- **Choice**: When deploying with `export_format: "oraxen"`, `paper-agent` writes definitions to `plugins/Oraxen/items/platform_items.yml` and triggers Oraxen's reload command/API.
- **Alternatives Considered**: Injecting items purely into Oraxen's in-memory maps.
- **Rationale**: Oraxen relies on disk configurations to build resource packs and persist items across server restarts. Writing to a designated platform file ensures compatibility with Oraxen's resource pack pipeline.

## Architecture & Data Flow

```text
+-----------------------------------------------------------------------------+
|                         SYSTEM ARCHITECTURE & DATA FLOW                     |
+-----------------------------------------------------------------------------+

 1. DISCOVERY & SYNC
 
    [Paper 1.21] <--(Softdepend)--- [paper-agent: OraxenCatalogHook]
                                            |
                                            v (catalog:manifest)
    [FastAPI Gateway] <================ WebSocket
            |
            v
    [SQLite: discovered_catalog_items]
            |
            v (REST: /api/catalogs/targets/{id}/items)
    [Web Asset Browser] (Tabs: Vanilla | Platform | Oraxen)
            |
            v ("Fork as Base")
    [ItemEditor] <---> [Config Schemas Engine (Reactive Form <-> Raw YAML)]


 2. DEPLOYMENT & EXPORT
 
    [ItemEditor] -- (export_format: "oraxen") --> [FastAPI Backend]
                                                         |
    [paper-agent: OraxenItemExporter] <=========== WebSocket
            |
            +--> Writes 'plugins/Oraxen/items/platform_items.yml'
            +--> Executes Oraxen Reload
```

## Risks / Trade-offs

- **[Risk] Large catalog payload sizes over WebSocket**
  → *Mitigation*: Stream manifests in batched envelopes if item count exceeds 500 items, and store items with indexed database queries.
- **[Risk] Oraxen API differences across minor versions**
  → *Mitigation*: Use defensive reflection on `OraxenItems` API and log clear warnings if unexpected versions are encountered.
- **[Risk] State drift between Reactive Form and Raw YAML**
  → *Mitigation*: Use a single canonical JavaScript object as state, serializing to YAML when switching to Raw mode and parsing back when switching to Form mode with immediate error feedback.
