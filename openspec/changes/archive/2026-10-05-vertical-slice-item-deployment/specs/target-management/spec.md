# Spec Delta

## ADDED Requirements

### Requirement: Target Live Session Tracking
The target management capability SHALL maintain active WebSocket session state and heartbeats for registered Paper targets.

#### Scenario: Real-time target connection state
- **WHEN** a target agent connects and completes the hello handshake
- **THEN** the target's status transitions to `online` and exposes its Paper 1.21 environment metadata to the platform

#### Scenario: Stale session timeout
- **WHEN** heartbeats from a target are not received within the configured timeout threshold
- **THEN** the target's status transitions to `offline` and active deployment dispatching to that target is suspended
