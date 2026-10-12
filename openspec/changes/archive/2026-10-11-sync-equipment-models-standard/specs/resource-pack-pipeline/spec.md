# Spec Delta: Resource Pack Pipeline

## MODIFIED Requirements

### Requirement: Equipment Models and Armor Trims Packaging
The compiler and merger engine MUST discover and package Minecraft 1.21.4+ canonical equipment model descriptors located at `assets/<namespace>/equipment/<id>.json`, SHALL stage them within root assets and modern client overlay targets (`overlay_v1_21_4`), SHALL automatically generate backward-compatible mirror descriptors under `assets/<namespace>/models/equipment/<id>.json` within `overlay_v1_21_2` targets to maintain compatibility with 1.21.2-1.21.3 clients, SHALL verify that referenced texture paths under `textures/entity/equipment/<layer_type>/` exist during pre-flight conflict analysis, and SHALL synthesize required texture slots into `assets/minecraft/atlases/armor_trims.json`.

#### Scenario: Packaging equipment models during pack compilation
- **WHEN** resource pack compilation is triggered with custom equipment models defined in the workspace
- **THEN** compiler stages canonical descriptors under `assets/<namespace>/equipment/<id>.json` in the root archive and generates backward-compatible mirror files under `overlay_v1_21_2/assets/<namespace>/models/equipment/<id>.json`, while verifying that all referenced layer textures exist in the asset tree
