# Target Management

## Purpose
The Target Management capability manages the registration, secure enrollment, environment inventory, and capability discovery of Paper servers connected to the control plane.

## Requirements

### Requirement: Secure Target Enrollment Lifecycle
The system MUST provide a secure enrollment flow using short-lived, single-use tokens to authenticate new Paper server targets and issue revocable credentials.

#### Scenario: Successful target enrollment
- **WHEN** an administrator creates an enrollment token and a new Paper agent presents that token over TLS
- **THEN** the platform binds the target to the organization, issues a persistent revocable credential, and permanently invalidates the enrollment token

#### Scenario: Expired or reused token rejection
- **WHEN** an agent attempts enrollment with an expired or already-used token
- **THEN** enrollment is rejected and no target credentials are issued

### Requirement: Capability Discovery and Environment Inventory
Connected agents MUST report their host environment details and dynamically advertise the capabilities of installed adapters.

#### Scenario: Registering capability manifest
- **WHEN** an agent completes handshake or reports capabilities
- **THEN** the platform records the agent version, Minecraft version, Paper build, active adapters, and their supported resource kinds and operations

#### Scenario: Pre-deployment capability validation
- **WHEN** a deployment plan requires an operation or field not present in the target's active capability manifest
- **THEN** the system flags the incompatibility and blocks the deployment before dispatching commands

### Requirement: Target Observed-State Snapshots
The system MUST record snapshots of observed resources on connected targets along with observation metadata and content hashes.

#### Scenario: Capturing observed state
- **WHEN** an inspection is performed on a target
- **THEN** the platform records an observed-state snapshot containing target ID, timestamp, adapter ID/version, resource representations, and checksum

### Requirement: Target Live Session Tracking
The target management capability SHALL maintain active WebSocket session state and heartbeats for registered Paper targets.

#### Scenario: Real-time target connection state
- **WHEN** a target agent connects and completes the hello handshake
- **THEN** the target's status transitions to `online` and exposes its Paper 1.21 environment metadata to the platform

#### Scenario: Stale session timeout
- **WHEN** heartbeats from a target are not received within the configured timeout threshold
- **THEN** the target's status transitions to `offline` and active deployment dispatching to that target is suspended
