# Agent Protocol

## Purpose
The Agent Protocol capability defines the standardized, transport-independent bidirectional communication contract between the central control plane gateway and registered server agents over persistent, outbound authenticated TLS connections.

## Requirements

### Requirement: Standard Message Envelope
All protocol messages between the control plane and agents MUST adhere to a unified JSON message envelope containing metadata for protocol versioning, routing, tracing, and idempotency.

#### Scenario: Valid envelope transmission
- **WHEN** a message is sent across the gateway
- **THEN** it contains protocolVersion, messageType, messageId, correlationId, targetId, sentAt, expiresAt, and payload fields conforming to the envelope schema

#### Scenario: Rejection of malformed or outdated envelope
- **WHEN** an endpoint receives a message missing required envelope fields or with an unsupported protocolVersion
- **THEN** the message is rejected with a structured protocol error and not dispatched to handlers

### Requirement: Outbound Authenticated Session Lifecycle
Agents MUST initiate outbound TLS WebSocket connections, establish authenticated sessions, and maintain connectivity using periodic heartbeats.

#### Scenario: Session establishment via Hello handshake
- **WHEN** an authenticated agent establishes a connection and sends an `agent.hello` payload with target ID and runtime metadata
- **THEN** the gateway validates the credential target binding and responds with `agent.session.accept` containing negotiated protocol parameters

#### Scenario: Heartbeat and connection staleness tracking
- **WHEN** an agent is connected
- **THEN** it periodically sends an `agent.heartbeat` and the gateway updates the target's last-seen timestamp, marking it offline if heartbeats cease beyond the configured threshold

### Requirement: Typed Allowlisted Operations
The protocol MUST only permit predefined, typed operations and explicitly forbid arbitrary shell, remote code execution, or unrestricted Bukkit/Paper command execution.

#### Scenario: Execution of allowlisted operation
- **WHEN** the control plane sends an `operation.execute` request containing an allowlisted action type and schema-validated parameters
- **THEN** the agent executes the typed handler and returns an `agent.operation.result` correlated with the request

#### Scenario: Rejection of disallowed or arbitrary operation
- **WHEN** a message requests an unknown action, an unregistered adapter command, or arbitrary shell/script execution
- **THEN** the agent rejects the operation immediately with an `OPERATION_FORBIDDEN` error without executing any runtime instructions

### Requirement: Idempotent Retries and Correlation
All command requests MUST support correlation IDs and idempotency tokens so that duplicate messages or retries caused by network reconnections do not cause duplicate side effects.

#### Scenario: Duplicate message handling
- **WHEN** an agent receives a request with an operationId or messageId that has already been executed within the retention window
- **THEN** the agent returns the cached execution result without re-executing the operation side effects

### Requirement: Item Deployment Operation Payload
The agent protocol SHALL support typed `create_or_update_item` operation payloads inside `operation.execute` requests.

#### Scenario: Dispatching item deployment request
- **WHEN** the gateway dispatches an `operation.execute` message with action `create_or_update_item` and the item definition payload
- **THEN** the message includes operationId, correlationId, targetId, and timestamp conforming to the protocol envelope schema

#### Scenario: Agent reports item operation completion
- **WHEN** the agent finishes executing a `create_or_update_item` operation
- **THEN** it sends an `agent.operation.result` envelope containing the matching correlationId, success boolean, and verification hash

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
