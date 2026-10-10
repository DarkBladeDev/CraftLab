# Spec Delta: content-model

## ADDED Requirements

### Requirement: Canonical Prop States Schema
The canonical block and prop model SHALL validate and store a `default_state` string and a typed mapping of `states`, where each state entry contains an optional display label `name`, an optional `block_model` identifier, an integer `light_level` bounded between 0 and 15, an optional `sound` specification (with `key`, `volume`, and `pitch`), an optional `hitbox_type` collision override (`solid` or `passable`), and an optional `next_state` identifier.

#### Scenario: Validating prop states structure
- **WHEN** a client submits a block definition containing a valid `default_state` and a populated `states` dictionary
- **THEN** the backend validates that `default_state` exists within `states`, all state models conform to valid Minecraft namespaced identifier format, and persists the definition

#### Scenario: Backward compatibility for single-state props
- **WHEN** a legacy block definition with no `states` or an empty states mapping is loaded or submitted
- **THEN** the system treats the definition as a single-state prop without raising validation errors, utilizing the top-level `block_model` and `hitbox_type`

#### Scenario: Rejecting invalid light level or dangling transition target
- **WHEN** a prop definition defines a state with `light_level: 20` or a `next_state` pointing to a non-existent state identifier
- **THEN** the backend rejects the submission with explicit field validation error messages
