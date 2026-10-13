# Spec Delta

## MODIFIED Requirements

### Requirement: Semantic Font Provider, Sounds, and Particle Merging
The compiler and merger engine MUST perform semantic deduplication and merging across multi-source layers for font provider definitions (`font/*.json`), concatenating bitmap and space providers while verifying that no identical PUA codepoint conflicts exist across layers, SHALL project custom namespace bitmap providers from `assets/<namespace>/font/default.json` into the root `assets/minecraft/font/default.json` so raw PUA characters render without explicit font tags, SHALL include the compiled glyph catalog in the pack `build_summary` and `resource_pack:ready` agent notifications, MUST merge `sounds.json` audio event structures combining sound sample lists, and MUST package particle definition files (`particles/*.json`) and their associated texture atlas references into the compiled archive.

#### Scenario: Merging multi-source font providers
- **WHEN** compiler merges workspace font providers with external layer font configurations
- **THEN** compiler produces a unified `assets/<namespace>/font/default.json` containing all distinct bitmap providers and reports warnings if duplicate character codepoints are encountered

#### Scenario: Projecting custom namespace glyphs into root default font
- **WHEN** compiler builds a resource pack containing custom bitmap providers in `assets/<namespace>/font/default.json`
- **THEN** compiler also merges those PUA bitmap providers into `assets/minecraft/font/default.json` so that raw PUA Unicode characters render in standard Minecraft UI contexts without requiring explicit `<font:...>` tags

#### Scenario: Publishing compiled glyph catalog on pack build
- **WHEN** resource pack compilation completes for a target server
- **THEN** compiler records the compiled glyph definitions in `build_summary.glyphs` and includes the `glyphs` array in the `resource_pack:ready` WebSocket event payload sent to the target agent
