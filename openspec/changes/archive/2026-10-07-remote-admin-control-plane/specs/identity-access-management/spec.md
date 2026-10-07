# Spec Delta

## Purpose

Provides a secure multi-user identity and access management system with dedicated SQLite persistence, Argon2id hashing, unified Single Sign-On (SSO) session cookies, API tokens, and hierarchical role-based access control (RBAC).

## ADDED Requirements

### Requirement: Dedicated Persistent Identity Storage
The identity system SHALL persist user accounts, credentials, and role assignments in a dedicated SQLite database located at `data/auth.db`, completely independent of the application content database `data/mcp.db`.

#### Scenario: User database initialization
- **WHEN** the system boots and `data/auth.db` does not exist
- **THEN** it automatically initializes the identity schema with user tables, role mappings, and audit timestamps

#### Scenario: Isolation from content database restore
- **WHEN** an operator restores a backup of the content database `data/mcp.db`
- **THEN** user accounts, passwords, and active session records in `data/auth.db` remain unaltered

### Requirement: Secure Password Hashing and Verification
The system SHALL hash all user passwords using the Argon2id algorithm with cryptographic salt, and SHALL verify passwords using constant-time comparison.

#### Scenario: Password hashing on creation or update
- **WHEN** a user account is created or its password changed
- **THEN** the password is saved exclusively as an Argon2id hash with random per-user salt and never stored in plain text

#### Scenario: Constant-time password verification
- **WHEN** a user submits authentication credentials
- **THEN** the system verifies the provided password against the stored Argon2id hash using constant-time comparison to prevent timing attacks

### Requirement: Dual Web Session and API Token Authentication
The system SHALL support web browser authentication via secure HTTP cookies and programmatic automation via Bearer API tokens.

#### Scenario: Web browser login and SSO session cookie
- **WHEN** a user logs in through the web interface with valid credentials
- **THEN** the system issues an `HttpOnly`, `SameSite=Lax`, cryptographically signed session cookie valid for Single Sign-On across both CraftLab App and the supervisor daemon

#### Scenario: Programmatic Bearer token authentication
- **WHEN** a client submits a request with an `Authorization: Bearer <token>` header containing a valid API token
- **THEN** the system authenticates the request and assigns the associated user identity and role context

#### Scenario: WebSocket authentication via session cookie
- **WHEN** an authenticated web browser initiates a WebSocket connection
- **THEN** the server authenticates the connection using the automatically forwarded session cookie without requiring query parameter tokens

### Requirement: Hierarchical Role-Based Access Control
The system SHALL enforce role-based access control with predefined roles (`admin`, `operator`, `creator`, `viewer`) across all supervisor and application endpoints.

#### Scenario: Admin role access
- **WHEN** an authenticated user with `admin` role requests any supervisor, lifecycle, backup, or application operation
- **THEN** the system authorizes the request

#### Scenario: Operator role restricted access
- **WHEN** an authenticated user with `operator` role requests status, metrics, diagnostics, or process restart
- **THEN** the system authorizes the operation, but rejects destructive operations such as database deletion or user privilege modification

#### Scenario: Creator role forbidden on supervisor
- **WHEN** an authenticated user with `creator` role attempts to access `craftctld` supervisor control endpoints
- **THEN** the request is rejected with a 403 Forbidden error

### Requirement: Break-Glass Emergency Administrative Access
The system SHALL provide a fail-safe bootstrap root credential configurable via environment variables or `craftctl.toml` that allows administrative recovery when the identity database is inaccessible or uninitialized.

#### Scenario: Emergency authentication when database unavailable
- **WHEN** `data/auth.db` is corrupt, locked, or absent and a client provides the configured break-glass root credential
- **THEN** the system grants emergency administrative access to execute recovery and diagnostic operations
