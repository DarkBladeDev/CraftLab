# Control System

## Purpose
Provides an extensible Python-based control system with CLI, daemon process supervisor, plugin architecture, local IPC, and environmental diagnostics.

## Requirements

### Requirement: Extensible Plugin Architecture
The control system SHALL discover and load plugins via Python entry points in the `craftlab_ctl.plugins` group, allowing plugins to expose typed commands (`@command`), lifecycle hooks (`@hook`), and health checks (`@check`).

#### Scenario: Plugin discovery and registration
- **WHEN** `craftctld` initializes and encounters installed packages with entry points in `craftlab_ctl.plugins`
- **THEN** it loads each plugin, validates its SDK version compatibility, and registers its commands, hooks, and checks

#### Scenario: Incompatible plugin rejection
- **WHEN** a discovered plugin specifies an unsupported SDK version
- **THEN** `craftctld` rejects the plugin with a descriptive diagnostic message while continuing to load other valid plugins

### Requirement: Process Supervision and Lifecycle Management
The `craftctld` supervisor daemon SHALL supervise the CraftLab application as a managed child process, recording its PID, managing its process group, and providing `start`, `stop`, `restart`, and `status` lifecycle operations.

#### Scenario: Starting supervised application
- **WHEN** `craftctl start` is invoked and the application is stopped
- **THEN** `craftctld` launches the application process within a managed process group, writes its PID to `run/`, and reports successful startup once `/ready` passes

#### Scenario: Stopping supervised application
- **WHEN** `craftctl stop` is invoked and the application is running
- **THEN** `craftctld` sends a graceful termination signal, waits for the process to exit within a configurable timeout, and escalates to forced termination if the process does not terminate

#### Scenario: Inspecting application status
- **WHEN** `craftctl status` is invoked
- **THEN** `craftctld` queries the process status, uptime, PID, and health status, returning a structured summary

### Requirement: Local Inter-Process Communication Control Transport
The control system SHALL provide a secure local communication channel between the `craftctl` client and `craftctld` daemon, using Unix domain sockets with filesystem permission controls on Linux and local loopback transport with a generated authentication token on Windows.

#### Scenario: Client communication on Linux
- **WHEN** `craftctl` connects on Linux
- **THEN** it connects to `run/craftctld.sock` enforcing filesystem user and group permission boundaries

#### Scenario: Client communication on Windows
- **WHEN** `craftctl` connects on Windows
- **THEN** it authenticates to the local daemon endpoint using the secret token stored in `run/craftctld.token`

### Requirement: Dynamic Command Introspection and Execution
The `craftctl` CLI SHALL query registered commands and schemas from the daemon over the control transport, dynamically building CLI subcommands and validating parameters against generated schemas.

#### Scenario: Introspecting commands
- **WHEN** a user runs `craftctl --help`
- **THEN** the CLI displays all currently registered commands from active plugins with their arguments and descriptions

#### Scenario: Executing command with streamed progress
- **WHEN** a user executes a long-running command via `craftctl`
- **THEN** the CLI streams progress events and step completions from `craftctld` in real-time until operation completion

### Requirement: System Environment Diagnostic Probing
The control system SHALL provide a `craftctl doctor` diagnostic command that runs all registered plugin diagnostic checks (`@check`), evaluating environmental health, dependencies, and file permissions.

#### Scenario: Running diagnostic checks
- **WHEN** `craftctl doctor` is executed
- **THEN** it evaluates configuration validity, filesystem directory accessibility, database connectivity, and runtime daemon status, outputting a categorized pass/warn/fail report

### Requirement: Autonomous Operation Execution and Audit Logging
The `craftctld` daemon SHALL execute mutating commands under an operation lock preventing conflicting concurrent modifications, and SHALL append all executed mutations to a persistent audit log file.

#### Scenario: Concurrent mutation lock rejection
- **WHEN** a mutating operation is requested while another mutating operation is already in progress
- **THEN** the second request is rejected with a busy lock error

#### Scenario: Audit logging of executed operations
- **WHEN** any mutating command completes or fails
- **THEN** an audit event record containing timestamp, command name, parameters, execution outcome, and caller identifier is written to `state/audit.jsonl`

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
