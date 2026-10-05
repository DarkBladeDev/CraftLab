# Spec Delta: Agent Protocol

## ADDED Requirements

### Requirement: Detected Plugin Reporting in Session Handshake
The agent protocol SHALL support reporting detected server plugins and adapter capabilities in the initial `hello` handshake envelope.

#### Scenario: Agent reports detected plugins during handshake
- **WHEN** an agent establishes a connection and transmits an `agent.hello` envelope
- **THEN** the payload includes a `detectedPlugins` list (including plugin ID and version) and summary counts for discovered items

### Requirement: Catalog Synchronization Operations
The agent protocol SHALL support on-demand and event-driven catalog discovery operations using typed message envelopes.

#### Scenario: Requesting on-demand catalog refresh
- **WHEN** the control plane sends a `catalog.refresh` request envelope with a correlation ID
- **THEN** the target agent scans external plugin registries and responds with a `catalog.manifest` envelope containing the discovered item definitions

#### Scenario: Streaming catalog manifest updates
- **WHEN** an agent completes an initial or on-demand scan of external plugin items
- **THEN** it sends a `catalog.manifest` envelope containing the target ID, source identifier, item count, and full item metadata
