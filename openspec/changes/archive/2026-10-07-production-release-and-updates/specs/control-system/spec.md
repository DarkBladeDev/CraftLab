# Spec Delta

## ADDED Requirements

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
