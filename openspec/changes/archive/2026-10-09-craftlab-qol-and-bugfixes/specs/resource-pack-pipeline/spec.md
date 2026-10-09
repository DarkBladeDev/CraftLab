# Spec Delta

## MODIFIED Requirements

### Requirement: Pack Source Storage and Ingestion
The system SHALL maintain a repository of pack sources comprising Studio project assets, uploaded third-party zip archives, and automated plugin pack snapshots synchronized from connected server agents, structured with an explicit layer priority hierarchy, and SHALL support updating layer metadata (name, priority, active state) and deleting registered pack sources.

#### Scenario: Ingest external zip archive
- **WHEN** an operator uploads a valid resource pack `.zip` file via the web management interface
- **THEN** the system extracts and registers the pack source with metadata, layer precedence, and namespaces in the pack repository

#### Scenario: Ingest agent synchronized pack
- **WHEN** an agent uploads an extracted plugin pack snapshot from its local filesystem
- **THEN** the system registers or updates the corresponding agent pack source and records its synchronization timestamp

#### Scenario: Updating pack source attributes
- **WHEN** an operator modifies the display name, layer priority, or active status of a registered pack source
- **THEN** the system persists the updated layer attributes and reflects the new evaluation priority in pre-flight and compilation workflows

#### Scenario: Deleting a registered pack source
- **WHEN** an operator deletes an imported pack source
- **THEN** the system removes the source record and associated storage files from disk

### Requirement: Workspace Pack Layer Integration in Build Pipeline
The resource pack compiler and merger engine MUST incorporate the local workspace pack directory (`data/packs/workspace/`) into the compilation and pre-flight validation workflow as an authoring layer with priority above external imported sources and beneath dynamic studio database projections, and SHALL provide endpoints and UI controls to inspect and update the base workspace pack manifest attributes.

#### Scenario: Compiling pack with workspace assets
- **WHEN** an operator or deployment triggers `build_resource_pack`
- **THEN** the compiler merges assets from `data/packs/workspace/` into the staging directory before synthesizing the final `.zip` archive

#### Scenario: Pre-flight validation includes workspace assets
- **WHEN** the system executes pre-flight conflict validation
- **THEN** models, textures, and definitions in `data/packs/workspace/` are scanned alongside studio items and imported sources for identifier or collision errors

#### Scenario: Configuring workspace pack manifest attributes
- **WHEN** an operator updates the workspace pack description or supported format bounds in the management interface
- **THEN** the system updates `pack.mcmeta` in the workspace directory and uses the updated metadata on subsequent builds
