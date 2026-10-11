# Spec Delta: resource-pack-pipeline

## ADDED Requirements

### Requirement: Equipment Models and Armor Trims Packaging
The compiler and merger engine MUST discover and package Minecraft 1.21.2+ equipment model descriptors located at `models/equipment/<id>.json`, SHALL stage them within modern client overlay targets (`overlay_v1_21_2`) and root assets, SHALL verify that referenced texture paths under `textures/entity/equipment/<layer_type>/` exist during pre-flight conflict analysis, and SHALL synthesize required texture slots into `assets/minecraft/atlases/armor_trims.json`.

#### Scenario: Packaging equipment models during pack compilation
- **WHEN** resource pack compilation is triggered with custom equipment models defined in the workspace
- **THEN** compiler stages `models/equipment/<id>.json` in the compiled archive and verifies that all referenced layer textures exist in the asset tree

### Requirement: Semantic Font Provider, Sounds, and Particle Merging
The compiler and merger engine MUST perform semantic deduplication and merging across multi-source layers for font provider definitions (`font/*.json`), concatenating bitmap and space providers while verifying that no identical PUA codepoint conflicts exist across layers, MUST merge `sounds.json` audio event structures combining sound sample lists, and MUST package particle definition files (`particles/*.json`) and their associated texture atlas references into the compiled archive.

#### Scenario: Merging multi-source font providers
- **WHEN** compiler merges workspace font providers with external layer font configurations
- **THEN** compiler produces a unified `assets/<namespace>/font/default.json` containing all distinct bitmap providers and reports warnings if duplicate character codepoints are encountered
