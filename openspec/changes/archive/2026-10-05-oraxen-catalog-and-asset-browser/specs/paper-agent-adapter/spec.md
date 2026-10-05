# Spec Delta: Paper Agent Adapter

## ADDED Requirements

### Requirement: Oraxen Runtime Inspection and Discovery
The Paper agent SHALL provide a soft-dependency adapter hook for Oraxen that inspects registered Oraxen items at runtime and serializes them into protocol catalog manifests.

#### Scenario: Discovering registered Oraxen items
- **WHEN** Oraxen is present and enabled on the Paper server and a catalog scan is triggered
- **THEN** the Oraxen adapter queries registered items, extracting identifier, base material, display name, lore, custom model data, and configuration attributes

#### Scenario: Graceful degradation when Oraxen is absent
- **WHEN** the agent runs on a server without Oraxen installed
- **THEN** the agent initializes without error and reports zero Oraxen items without throwing class loading exceptions

### Requirement: Bidirectional Oraxen Export and Hot-Reload
The Paper agent adapter SHALL support writing platform-deployed item definitions into Oraxen YAML configuration files and triggering an Oraxen reload.

#### Scenario: Exporting deployed item to Oraxen configuration
- **WHEN** the agent receives an item deployment payload with export target `oraxen`
- **THEN** it generates or updates the item definition in `plugins/Oraxen/items/platform_items.yml` and executes Oraxen's reload routine to register the changes
