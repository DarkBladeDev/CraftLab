# Spec Delta

## MODIFIED Requirements

### Requirement: Outbound Authenticated Session Lifecycle
Agents MUST initiate outbound TLS WebSocket connections, establish authenticated sessions using validated cryptographic credentials, and maintain connectivity using periodic heartbeats.

#### Scenario: Session establishment via Hello handshake
- **WHEN** an agent establishes a connection and sends an `agent.hello` payload with target ID, target secret, and runtime metadata
- **THEN** the gateway validates the target secret against stored target credentials, and responds with `agent.session.accept` containing negotiated protocol parameters upon successful verification

#### Scenario: Rejection of unauthenticated agent handshake
- **WHEN** an agent connection sends an `agent.hello` payload with an invalid, missing, or mismatched target secret
- **THEN** the gateway rejects the session with a policy violation code, closes the WebSocket immediately, and records an authentication failure event

#### Scenario: Heartbeat and connection staleness tracking
- **WHEN** an agent is connected
- **THEN** it periodically sends an `agent.heartbeat` and the gateway updates the target's last-seen timestamp, marking it offline if heartbeats cease beyond the configured threshold
