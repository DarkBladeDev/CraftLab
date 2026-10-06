# Spec Delta

## ADDED Requirements

### Requirement: Canonical Block Definitions
The system MUST support a canonical, typed representation for Minecraft block and prop definitions that supports both virtual packet-based display props and note block mappings.

#### Scenario: Valid display prop definition authoring
- **WHEN** a user or client submits a block definition with a valid identifier, display name, mode `display_prop`, item model, transform vectors, and drop item id
- **THEN** the system validates the definition against the canonical block schema and persists it in the project draft

#### Scenario: Rejection of invalid block schema
- **WHEN** a block definition contains negative scale dimensions or invalid mode strings
- **THEN** the system rejects the definition with descriptive field-level validation errors

## MODIFIED Requirements

### Requirement: Immutable Project Revisions
Projects MUST create immutable revision snapshots representing the exact desired state of all project resources (items and blocks) at a point in time.

#### Scenario: Creating a revision snapshot
- **WHEN** a user creates a revision from current project draft definitions
- **THEN** the platform freezes both item and block resource states into an immutable revision, records author and timestamp, and prevents any subsequent modification of that revision

#### Scenario: Attempting to modify an existing revision
- **WHEN** any operation attempts to update or delete resources within an existing revision snapshot
- **THEN** the system rejects the operation, preserving the immutability of historical revisions

### Requirement: Deterministic Content Hashing
Every project revision MUST have a deterministic hash computed over its canonical resource definitions across items and blocks to enable tamper-evident verification and drift detection.

#### Scenario: Computing revision hash
- **WHEN** a revision is created
- **THEN** a SHA-256 content hash is computed over the canonical, canonically ordered JSON serialization of all contained items and blocks

#### Scenario: Identical contents produce identical hash
- **WHEN** two revisions contain identical resource definitions across all collections
- **THEN** their computed content hashes match
