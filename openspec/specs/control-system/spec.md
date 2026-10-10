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

### Requirement: Release Packaging and Artifact Verification
The control system SHALL support discovering, downloading, and validating release archives (`craftlab-v<version>.tar.gz` and `.sha256`) from GitHub Releases or local file paths, verifying SHA256 cryptographic integrity and manifest compatibility before extraction.

#### Scenario: Verifying release checksum and manifest
- **WHEN** `craftctl update prepare` is executed with a version identifier
- **THEN** it downloads the archive and checksum from GitHub Releases, verifies SHA256 integrity, extracts the release into `releases/<version>/`, and validates `manifest.json` compatibility against current runtime requirements

#### Scenario: Checksum mismatch rejection
- **WHEN** a downloaded archive does not match the published SHA256 checksum
- **THEN** preparation is aborted immediately, extracted temporary files are purged, and an error is reported

### Requirement: Isolated Release Environments with Shared Wheel Caching
The control system SHALL provision an isolated virtual environment (`.venv`) for each extracted release in `releases/<version>/` using a shared wheel cache directory located at `<CRAFTLAB_HOME>/cache/wheels` to accelerate dependency installation without external network access.

#### Scenario: Preparing release virtual environment from cache
- **WHEN** a release is extracted during `update prepare`
- **THEN** `craftctld` creates `releases/<version>/.venv` and installs dependencies using wheels located in `cache/wheels`, downloading missing wheels into the cache as needed

### Requirement: Two-Phase Atomic Application Updates
The control system SHALL execute application updates in two distinct phases (`prepare` and `apply`), where `prepare` executes without service disruption while the application continues serving traffic, and `apply` performs an atomic pointer swap to the new release with automated rollback if readiness probes fail.

#### Scenario: Successful application update
- **WHEN** `craftctl update apply` is invoked for a prepared release
- **THEN** the supervisor enables maintenance mode, gracefully terminates the running backend, applies database migrations, repoints `current` to `releases/<version>/`, launches the updated backend, verifies `/ready`, and disables maintenance mode

#### Scenario: Automatic rollback on startup failure
- **WHEN** the updated backend fails to start or fails the `/ready` probe within the configured timeout
- **THEN** `craftctld` reverts the `current` pointer to the prior release, restarts the prior version, disengages maintenance mode, and logs the failure to `state/audit.jsonl`

### Requirement: Release Version Listing, Rollback, and Retention
The control system SHALL maintain a list of installed releases, support explicit manual rollback to a previous release version, and automatically retain the most recent 3 releases while pruning older releases to conserve disk space.

#### Scenario: Explicit version rollback
- **WHEN** `craftctl rollback` is executed with a target prior release version
- **THEN** the supervisor swaps the active pointer, restarts the target version, and validates service readiness

#### Scenario: Pruning outdated releases
- **WHEN** an update is successfully applied and more than 3 releases exist in `releases/`
- **THEN** older release directories and their virtual environments are removed

### Requirement: Application Update and Release Lifecycle CLI Commands
The `craftctl` CLI tool SHALL expose dedicated subcommands and commands for application update lifecycle management, including checking GitHub releases, preparing and provisioning release environments, applying updates atomically, rolling back to previous versions, listing installed releases, and inspecting or toggling maintenance mode.

#### Scenario: Checking for updates via CLI
- **WHEN** `craftctl update check` is invoked
- **THEN** the CLI queries GitHub releases, compares the latest tag against current version, and prints release availability and release notes

#### Scenario: Staging a release via CLI
- **WHEN** `craftctl update prepare <version>` is invoked
- **THEN** the CLI downloads the release archive and checksum, verifies cryptographic integrity, extracts files into `releases/v<version>`, provisions the release virtual environment from cached wheels, and reports staged status

#### Scenario: Applying a release atomically via CLI
- **WHEN** `craftctl update apply <version>` is invoked for a staged release
- **THEN** the CLI commands `craftctld` to activate maintenance mode, stop the running application, switch the active release pointer, launch the updated application, poll readiness, and deactivate maintenance mode upon success

#### Scenario: Shorthand update execution via CLI
- **WHEN** `craftctl update <version>` is invoked
- **THEN** the CLI executes the prepare phase followed immediately by the apply phase in sequence with operator confirmation

#### Scenario: Rolling back release via CLI
- **WHEN** `craftctl rollback` is invoked with an optional target version
- **THEN** the CLI switches the active pointer to the specified or most recent prior release, restarts the service, and verifies operational readiness

#### Scenario: Listing installed releases via CLI
- **WHEN** `craftctl releases` is invoked
- **THEN** the CLI outputs all installed release directories, highlights the currently active release pointer, and displays maintenance mode status

#### Scenario: Managing maintenance mode via CLI
- **WHEN** `craftctl maintenance enable --message "<reason>"` or `craftctl maintenance disable` is invoked
- **THEN** the CLI toggles maintenance mode and records the status and reason

### Requirement: Remote Update and Release Management Endpoints
The `craftctld` HTTP gateway SHALL expose authenticated REST endpoints under `/api/v1/update/` for querying releases, preparing release artifacts, applying updates with automated rollback, executing rollbacks, and managing maintenance mode with RBAC role authorization and operation locking.

#### Scenario: Querying update status and releases via HTTP
- **WHEN** an authenticated user sends `GET /api/v1/update/releases` or `GET /api/v1/update/check`
- **THEN** the server returns the installed releases, active release pointer, maintenance state, and GitHub release metadata

#### Scenario: Preparing a release via HTTP
- **WHEN** an authenticated administrator sends `POST /api/v1/update/prepare` with a target version
- **THEN** the server acquires the mutation lock, executes release extraction and venv provisioning, logs the audit event, and returns operation results

#### Scenario: Applying an update with automated rollback via HTTP
- **WHEN** an authenticated administrator sends `POST /api/v1/update/apply` with a target version
- **THEN** the server executes the atomic switch, enters maintenance mode, starts the new version, verifies `/ready`, automatically reverts to the previous version if startup fails, and logs the outcome to the audit log

#### Scenario: Toggling maintenance mode via HTTP
- **WHEN** an authenticated operator sends `POST /api/v1/update/maintenance` with desired state and message
- **THEN** the server sets maintenance mode and returns the updated state

### Requirement: Interactive Release and Update Dashboard Management
The embedded single-page web administration dashboard SHALL provide interactive controls for inspecting release status, checking for GitHub releases, staging release packages, applying atomic updates with real-time feedback, rolling back to installed releases, and toggling maintenance mode.

#### Scenario: Inspecting releases and maintenance state in dashboard
- **WHEN** an administrator or operator accesses the administration dashboard
- **THEN** the dashboard renders an Updates card displaying current active release, installed versions, maintenance status badge, and update availability

#### Scenario: Triggering an update from dashboard
- **WHEN** an authorized user triggers update preparation and apply from the dashboard
- **THEN** the dashboard initiates the operations, shows live progress feedback, and updates status upon completion

#### Scenario: Reverting to a prior release from dashboard
- **WHEN** an authorized user selects a previously installed release and clicks Rollback
- **THEN** the dashboard issues the rollback request, displays progress, and refreshes service telemetry upon completion

### Requirement: Categorized Pages Navigation in Web Administration Dashboard
The embedded single-page web administration dashboard SHALL provide a horizontal category tab navigation system that groups dashboard panels into distinct operational domains, preserving full viewport width for active domain panels.

#### Scenario: Switching operational categories
- **WHEN** an authenticated user selects a category tab (e.g., `System & Telemetry`, `Lifecycle & Supervisor`, `Releases & Updates`, or `Audit & Logs`)
- **THEN** the dashboard switches the active view and renders the registered data container panels assigned to that category without reloading the browser page

#### Scenario: Persistent category tab selection across refreshes
- **WHEN** a user switches to a category tab and reloads the browser
- **THEN** the dashboard restores the previously active category tab from the browser URL or session storage

### Requirement: Modular Paginated Data Container Engine
The web administration dashboard SHALL provide a modular data container engine capable of rendering panels defined as presets, supporting both sub-view switching and data collection pagination.

#### Scenario: Sub-views internal pagination mode
- **WHEN** a container preset configured with `paginationMode: "subviews"` is rendered
- **THEN** the container displays internal pagination controls (`◀` / `▶` and page indicators) that navigate across discrete sub-view pages (such as metric summary, granular telemetry, and action forms) within a constant panel footprint

#### Scenario: Records collection pagination mode
- **WHEN** a container preset configured with `paginationMode: "records"` is rendered with tabular or collection data
- **THEN** the container renders collection items divided by page size and displays page controls that navigate pages of items without changing the card structure

#### Scenario: Single non-paginated container mode
- **WHEN** a container preset configured with `paginationMode: "none"` is rendered
- **THEN** the container renders its contents directly without pagination navigation elements

### Requirement: Draggable and Resizable Dashboard Layout with Persistence
The web administration dashboard SHALL provide an interactive layout grid allowing operators to rearrange panel positions and resize column and row spans, persisting layout preferences locally.

#### Scenario: Reordering containers via drag and drop
- **WHEN** an operator drags a container by its handle and drops it in a new grid position
- **THEN** the dashboard reorders the panels in the grid and saves the new sequence to `localStorage`

#### Scenario: Resizing container dimensions
- **WHEN** an operator resizes a container using its resize handle
- **THEN** the dashboard updates the panel's column and row spans within configured min/max constraints and saves the updated geometry to `localStorage`

#### Scenario: Resetting layout to defaults
- **WHEN** an operator clicks the "Reset Layout" action for a category
- **THEN** the dashboard restores all container positions and sizes in that category to their preset default grid dimensions and clears customized overrides from `localStorage`

### Requirement: Declarative Container Preset Contract and Role-Based Input Control
The dashboard container engine SHALL evaluate typed declarative presets specifying output primitives, input action primitives, and role-based access restrictions.

#### Scenario: Rendering typed output primitives
- **WHEN** the container engine evaluates output declarations
- **THEN** it renders the declared primitives (`metric_stat`, `gauge`, `progress_bar`, `key_value`, `status_pill`, or `log_stream`) bound to live supervisor data

#### Scenario: Enforcing role-based access on input controls
- **WHEN** an input primitive specifies a required role (e.g. `admin` or `operator`) and the active session lacks that role or break-glass access
- **THEN** the container engine disables or hides the interactive input control and prevents action dispatch

#### Scenario: Executing authorized container action
- **WHEN** an authorized operator activates an input action control (e.g. lifecycle start, doctor probe, or release rollback)
- **THEN** the container engine dispatches the operation request to the supervisor API, shows real-time action feedback, and refreshes dependent container outputs


