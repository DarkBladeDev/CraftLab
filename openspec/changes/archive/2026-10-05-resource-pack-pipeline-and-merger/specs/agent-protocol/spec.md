# Spec Delta: Agent Protocol

## ADDED Requirements

### Requirement: Resource Pack Source Synchronization Message
The protocol SHALL define typed message payloads enabling a connected agent to notify the control plane of local plugin resource pack snapshots and stream their contents to the server.

#### Scenario: Agent announces local plugin pack update
- **WHEN** the agent detects changes in a local plugin pack directory like `plugins/Oraxen/pack/`
- **THEN** the agent sends a `resource_pack.source_sync` message containing plugin identifier, archive hash, and payload data to the control plane

### Requirement: Resource Pack Ready Notification Message
The protocol SHALL define a `resource_pack.ready` notification message dispatched from the control plane to registered agents containing the compiled download URL, SHA-1 checksum, required enforcement flag, and display prompt.

#### Scenario: Control plane notifies agent of new compiled pack
- **WHEN** a resource pack compilation completes for a target server
- **THEN** the control plane sends a `resource_pack.ready` envelope containing `{ "url": "...", "sha1": "...", "required": false, "prompt": "..." }` to the target's active session
