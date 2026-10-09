# Spec Delta

## MODIFIED Requirements

### Requirement: Vanilla Minecraft Asset Taxonomy
The system SHALL provide a queryable, dynamically populated catalog of native Minecraft materials comprising comprehensive item identifiers, display names, categories, and official asset texture URLs, organized by standard gameplay categories with search and filtering capabilities, presented in a collapsible interface labeled without static version restrictions.

#### Scenario: Querying vanilla material catalog
- **WHEN** a client requests the vanilla catalog with an optional category or name query
- **THEN** the system returns matching vanilla items containing item identifier, display name, category, stack size, and texture URLs from the comprehensive repertoire

#### Scenario: Collapsing the multi-source asset browser
- **WHEN** a user triggers the collapse toggle in the Item Studio asset browser header
- **THEN** the interface collapses the asset browser into a compact summary view to maximize editor workspace space

#### Scenario: Simplified vanilla category labeling
- **WHEN** the asset browser renders category tabs
- **THEN** the vanilla catalog tab is labeled `Vanilla (X)` reflecting the dynamic count of loaded items without hardcoded minor version strings
