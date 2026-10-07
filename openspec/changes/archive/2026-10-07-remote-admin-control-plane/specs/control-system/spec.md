# Spec Delta

## ADDED Requirements

### Requirement: Remote HTTP and WebSocket Control Gateway
The `craftctld` supervisor daemon SHALL expose an independent asynchronous HTTP and WebSocket control server running on a dedicated port, capable of processing REST lifecycle commands and streaming real-time events while the supervised application is offline or restarting.

#### Scenario: Supervisor availability during application shutdown
- **WHEN** the supervised application process is stopped, starting, or crashed
- **THEN** the `craftctld` HTTP gateway remains responsive, answering health, status, and lifecycle requests

#### Scenario: Real-time application log streaming over WebSocket
- **WHEN** an authenticated client connects to `/api/v1/ws/logs`
- **THEN** the supervisor streams lines of stdout and stderr captured from the supervised process in real-time

#### Scenario: Long-running operation progress streaming
- **WHEN** an authenticated client initiates a long-running mutating operation via the HTTP gateway
- **THEN** `craftctld` emits real-time step events and custom plugin progress messages over `/api/v1/ws/events` until completion

### Requirement: Embedded Web Administration Dashboard Hosting
The `craftctld` daemon SHALL serve a precompiled single-page web administration dashboard from static assets at its root or configured path prefix, enabling browser-based server and application administration.

#### Scenario: Serving administration interface assets
- **WHEN** a user navigates to the supervisor web endpoint in a browser
- **THEN** the daemon serves the web administration HTML, CSS, and JavaScript assets with client-side routing support

#### Scenario: Dashboard authentication integration
- **WHEN** an unauthenticated browser user accesses the dashboard
- **THEN** the application displays a user-friendly login view and redirects to the dashboard view upon successful session creation

### Requirement: Live Host and Process Resource Telemetry
The control system SHALL collect and expose real-time host and managed child process resource metrics via an authenticated telemetry endpoint.

#### Scenario: Querying system resource metrics
- **WHEN** an authenticated client requests `/api/v1/metrics`
- **THEN** the daemon returns host CPU utilization percentage, total and free system memory, filesystem disk usage for data directories, and supervised process CPU and RSS memory usage

### Requirement: Remote CLI Execution
The `craftctl` CLI tool SHALL support connecting to and executing operations against a remote `craftctld` daemon instance over HTTPS when configured with server URL and API token parameters.

#### Scenario: Remote status check via CLI
- **WHEN** a user executes `craftctl --server https://vps.example.com:8443 --token <API_TOKEN> status`
- **THEN** the CLI queries the remote daemon HTTP endpoint and prints the formatted status response

#### Scenario: Remote command execution with streamed steps
- **WHEN** a user executes a remote mutating command via `craftctl` with `--server` and `--token`
- **THEN** the CLI connects to the remote daemon, receives streamed progress steps, and outputs execution results
