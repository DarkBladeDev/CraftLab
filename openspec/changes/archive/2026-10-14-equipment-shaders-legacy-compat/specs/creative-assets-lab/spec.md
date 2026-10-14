# Spec Delta: Creative Assets Lab

## ADDED Requirements

### Requirement: Legacy Shader Metadata and Multi-Version Equipment Diagnostics
The Creative Assets Lab Equipment Model editor SHALL provide a dedicated Multi-Version Compatibility Diagnostic panel within the equipment inspector. The system MUST compute and display the model's assigned legacy shader layer index, 24-bit integer ID, RGB hexadecimal color code (e.g. `#000001`), and vertical atlas offset percentage for clients on Minecraft 1.20.0 through 1.21.3, alongside the canonical Minecraft 1.21.4+ `assets/<namespace>/equipment/<id>.json` structure and 1.21.2-1.21.3 `models/equipment/<id>.json` mirror status.

#### Scenario: Inspecting multi-version equipment diagnostics
- **WHEN** user selects an active equipment model in Creative Assets Lab
- **THEN** inspector displays the canonical 1.21.4+ asset key (`namespace:id`), the calculated legacy shader index, the assigned 24-bit RGB hex tint, and the paper doll preview showing combined layers

#### Scenario: Alerting when textures are incompatible with vertical atlas
- **WHEN** user uploads layer textures with non-standard aspect ratios or differing dimensions across humanoid layers
- **THEN** diagnostic panel warns of potential atlas alignment distortion and provides a one-click action to normalize texture dimensions to canonical 64x32 or 64x64 dimensions
