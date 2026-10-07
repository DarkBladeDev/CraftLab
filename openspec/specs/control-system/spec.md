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
