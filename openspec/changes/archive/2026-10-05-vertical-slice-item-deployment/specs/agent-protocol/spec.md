# Spec Delta

## ADDED Requirements

### Requirement: Item Deployment Operation Payload
The agent protocol SHALL support typed `create_or_update_item` operation payloads inside `operation.execute` requests.

#### Scenario: Dispatching item deployment request
- **WHEN** the gateway dispatches an `operation.execute` message with action `create_or_update_item` and the item definition payload
- **THEN** the message includes operationId, correlationId, targetId, and timestamp conforming to the protocol envelope schema

#### Scenario: Agent reports item operation completion
- **WHEN** the agent finishes executing a `create_or_update_item` operation
- **THEN** it sends an `agent.operation.result` envelope containing the matching correlationId, success boolean, and verification hash
