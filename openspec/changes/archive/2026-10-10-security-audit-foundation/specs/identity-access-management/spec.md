# Spec Delta

## MODIFIED Requirements

### Requirement: Dual Web Session and API Token Authentication
The system SHALL support web browser authentication via secure HTTP cookies and programmatic automation via Bearer API tokens, while enforcing transport security and disallowing query parameter credentials.

#### Scenario: Web browser login and SSO session cookie
- **WHEN** a user logs in through the web interface with valid credentials
- **THEN** the system issues an `HttpOnly`, `SameSite=Lax`, cryptographically signed session cookie with the `Secure` flag enabled in production environments

#### Scenario: Programmatic Bearer token authentication
- **WHEN** a client submits a request with an `Authorization: Bearer <token>` header containing a valid API token
- **THEN** the system authenticates the request and assigns the associated user identity and role context

#### Scenario: WebSocket authentication via session cookie
- **WHEN** an authenticated web browser initiates a WebSocket connection
- **THEN** the server authenticates the connection using the forwarded session cookie or Bearer authorization header, and rejects connections attempting to authenticate via query string parameters

### Requirement: Break-Glass Emergency Administrative Access
The system SHALL provide a fail-safe bootstrap root credential configurable via environment variables or configuration files that allows administrative recovery when the identity database is inaccessible or uninitialized, while prohibiting insecure default credentials in production.

#### Scenario: Emergency authentication when database unavailable
- **WHEN** `data/auth.db` is corrupt, locked, or absent and a client provides the configured break-glass root credential
- **THEN** the system grants emergency administrative access to execute recovery and diagnostic operations

#### Scenario: Rejection of placeholder credentials in production
- **WHEN** the system boots in production mode with unconfigured or placeholder root credentials
- **THEN** the startup sequence halts with a fatal configuration error

## ADDED Requirements

### Requirement: Strict Cross-Origin Resource Sharing Controls
The system SHALL enforce explicit origin allowlists on HTTP endpoints and forbid wildcard origins combined with credentialed requests.

#### Scenario: Rejection of wildcard origin with credentials
- **WHEN** CORS configuration is initialized
- **THEN** the system disallows wildcard origins when credentials are enabled and only permits explicitly configured trusted origins

#### Scenario: Preflight CORS request validation
- **WHEN** a browser makes an OPTIONS preflight request from an origin not in the trusted allowlist
- **THEN** the server rejects the preflight request without returning credential authorization headers
