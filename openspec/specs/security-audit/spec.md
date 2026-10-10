# security-audit Specification

## Purpose

The security-audit capability provides canonical security event ingestion, universal pre-persistence sanitization, and isolated dual-path SQLite storage for system activity and threat detection.

## Requirements

### Requirement: Canonical Security Event Contract
The system SHALL ingest and serialize security events conforming to a versioned canonical schema containing event identifiers, UTC timestamps, emitting component, event classification, severity, outcome, verified actor, and sanitized transport context.

#### Scenario: Valid security event emission
- **WHEN** any system component emits a security event conforming to the canonical schema
- **THEN** the event is validated, assigned a unique UUID, stamped with a UTC ISO 8601 timestamp, and dispatched to the persistence sink

#### Scenario: Rejection of malformed security events
- **WHEN** an event is submitted missing mandatory fields or containing invalid severity or outcome enumerations
- **THEN** the sink rejects the event without raising unhandled exceptions or disrupting caller execution

### Requirement: Universal Sensitive Data Sanitization
The system SHALL sanitize all security events before persistence or transmission, irreversibly redacting authentication tokens, passwords, session cookies, and private secrets.

#### Scenario: Redaction of credential keys in attributes
- **WHEN** a security event contains dictionary keys matching passwords, tokens, API keys, or session identifiers
- **THEN** the values are replaced with `[REDACTED]` prior to persistence

#### Scenario: Truncation of oversized attribute fields
- **WHEN** a security event contains string fields exceeding 512 characters or nested depth exceeding 3 levels
- **THEN** the strings are truncated with a truncation marker and excess nesting is pruned

### Requirement: Dedicated Isolated SQLite Audit Persistence
The system SHALL persist security events into an isolated SQLite database file `data/security-audit.sqlite3` operating in WAL mode, independent of application and identity databases.

#### Scenario: Database initialization in WAL mode
- **WHEN** the security audit system boots and `data/security-audit.sqlite3` is accessed
- **THEN** it ensures the database operates with WAL journal mode and indexed query tables for rapid time-series filtering

#### Scenario: Dual-path write strategy for critical and telemetric events
- **WHEN** a critical administrative action event is emitted
- **THEN** it is persisted synchronously with fail-closed semantics; when a telemetric network event is emitted, it is queued asynchronously for batch persistence

#### Scenario: Audit retention window enforcement
- **WHEN** the audit retention purge job executes
- **THEN** all events with timestamps older than the configured retention threshold are deleted without locking the database indefinitely
