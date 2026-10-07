# Spec Delta

## Purpose

Defines the contract between the CraftLab application and host environment, governing configuration loading, canonical directory layouts, health/readiness probing, and graceful process termination.

## ADDED Requirements

### Requirement: External Configuration Loading
The application SHALL load configuration from a `craftlab.toml` file located in the canonical configuration directory, overlaid by environment variables prefixed with `CRAFTLAB_`, falling back to safe local development defaults when no configuration is provided.

#### Scenario: Config file present
- **WHEN** the application starts and a valid `craftlab.toml` exists in the configuration directory
- **THEN** settings defined in `craftlab.toml` are loaded into the application settings

#### Scenario: Environment variable override
- **WHEN** an environment variable such as `CRAFTLAB_PORT=8080` or `CRAFTLAB_DATABASE_URL` is set
- **THEN** its value overrides any conflicting setting defined in `craftlab.toml` or default values

#### Scenario: Default configuration fallback
- **WHEN** neither configuration file nor environment variables are provided
- **THEN** the application initializes with default development settings without raising an error

### Requirement: Canonical Filesystem Layout Resolution
The application SHALL resolve runtime filesystem locations for configuration (`config/`), persistent state and database (`data/`), runtime sockets and PID files (`run/`), and logs (`logs/`) relative to an explicit `CRAFTLAB_HOME` directory, preventing database and pack storage paths from depending on the current working directory.

#### Scenario: Custom CRAFTLAB_HOME resolution
- **WHEN** `CRAFTLAB_HOME` is specified as `/opt/craftlab`
- **THEN** the application resolves its database path under `/opt/craftlab/data/` and logs under `/opt/craftlab/logs/`

#### Scenario: Local fallback resolution
- **WHEN** `CRAFTLAB_HOME` is not set
- **THEN** runtime paths are resolved relative to the detected repository or application root directory

### Requirement: Application Health and Liveness Probing
The application SHALL expose an unauthenticated `GET /health` endpoint that returns HTTP 200 and a JSON payload indicating service liveness and process runtime metadata without querying external dependencies.

#### Scenario: Liveness check succeeds
- **WHEN** an HTTP GET request is sent to `/health` while the application process is running
- **THEN** the server returns HTTP 200 OK with `{"status": "pass"}` and process uptime

### Requirement: Application Dependency Readiness Probing
The application SHALL expose an unauthenticated `GET /ready` endpoint that verifies connectivity to the configured database and access to required pack storage directories, returning HTTP 200 when ready, or HTTP 503 when dependencies fail.

#### Scenario: All dependencies healthy
- **WHEN** an HTTP GET request is sent to `/ready` and the database connection and storage directories are accessible
- **THEN** the server returns HTTP 200 OK with `{"status": "ready"}` and component breakdown

#### Scenario: Database connection failure
- **WHEN** an HTTP GET request is sent to `/ready` and the database connection fails or times out
- **THEN** the server returns HTTP 503 Service Unavailable with details on the failed database check

### Requirement: Graceful Shutdown Protocol
The application SHALL intercept operating system termination signals (`SIGTERM` on Linux/POSIX, `SIGINT` and `CTRL_BREAK_EVENT` on Windows) to execute a graceful shutdown sequence that stops accepting new connections, allows in-flight requests to complete within a configurable timeout, releases active WebSocket gateway connections, and closes database pools cleanly.

#### Scenario: Graceful termination on SIGTERM
- **WHEN** the application process receives a `SIGTERM` signal
- **THEN** it drains ongoing requests, closes active agent WebSocket sessions, shuts down the database engine, and exits with code 0
