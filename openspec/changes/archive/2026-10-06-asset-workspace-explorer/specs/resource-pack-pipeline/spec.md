# Spec Delta: Resource Pack Pipeline

## ADDED Requirements

### Requirement: Workspace Pack Layer Integration in Build Pipeline
The resource pack compiler and merger engine MUST incorporate the local workspace pack directory (`data/packs/workspace/`) into the compilation and pre-flight validation workflow as an authoring layer with priority above external imported sources and beneath dynamic studio database projections.

#### Scenario: Compiling pack with workspace assets
- **WHEN** an operator or deployment triggers `build_resource_pack`
- **THEN** the compiler merges assets from `data/packs/workspace/` into the staging directory before synthesizing the final `.zip` archive

#### Scenario: Pre-flight validation includes workspace assets
- **WHEN** the system executes pre-flight conflict validation
- **THEN** models, textures, and definitions in `data/packs/workspace/` are scanned alongside studio items and imported sources for identifier or collision errors
