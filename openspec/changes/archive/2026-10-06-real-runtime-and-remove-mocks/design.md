# Technical Design: Real Runtime Execution and Mock Elimination

## Context

See `proposal.md` for motivation. Currently, `dev.ps1` launches `mock_agent.py` which simulates an agent connection and saves data to `mock_server_storage/items.json`. The real Java agent plugin (`paper-agent`) is already implemented and capable of handling item persistence, PacketEvents virtual props, and resource pack join distribution. The missing link is orchestrating execution against a live Paper 1.21 server via environment variables and eliminating mock artifacts.

## Goals / Non-Goals

**Goals:**
- Provide a seamless developer experience in `dev.ps1` targeting an existing Paper 1.21 server via `MCP_PAPER_SERVER_DIR`.
- Support multiple server boot strategies: custom script (`MCP_PAPER_START_SCRIPT`), designated JAR (`MCP_PAPER_SERVER_JAR`), or auto-detection of `paper*.jar`/`server*.jar`.
- Build and copy `paper-agent-1.0.0-SNAPSHOT.jar` to the target server's `plugins/` directory prior to boot.
- Verify pre-flight runtime dependencies (such as PacketEvents in `plugins/`).
- Offer a clean-slate reset switch (`-CleanData`) to ensure all test data is authored in live runtime.
- Remove `mock_agent.py` and `mock_server_storage/`.

**Non-Goals:**
- Downloading or bundling binary Minecraft server JARs into version control.
- Altering the Java agent protocol or core adapter logic (which already adheres to durable specs).

## Architecture & Workflow

```
+-----------------------------------------------------------------------------------------+
|                                    DEV.PS1 ORCHESTRATION                                |
+-----------------------------------------------------------------------------------------+
                                             |
             +-------------------------------+-------------------------------+
             |                               |                               |
             v                               v                               v
    [ 1. Preflight & Deploy ]       [ 2. Optional Reset ]          [ 3. Service Launch ]
    - Read $MCP_PAPER_SERVER_DIR    - If -CleanData:              - Console 1: FastAPI (:8000)
    - gradlew build (paper-agent)     * Remove backend/mcp.db     - Console 2: Vite UI (:3000)
    - Copy JAR to plugins/            * Empty data/packs/dist/    - Console 3: Paper 1.21 Server
    - Check PacketEvents.jar          * Empty data/packs/tmp/       (Script or java -jar)
    - Ensure McpAgent/config.yml
```

## Decisions

### 1. Dedicated Interactive Window for the Paper Server
- **Choice**: Launch the Paper server using `Start-Process powershell -ArgumentList "-NoExit", "-Command", ...` with title `MCP - Paper 1.21 Server`.
- **Rationale**: Paper console requires interactive stdin/stdout for server administration (e.g., executing `op <player>`, `stop`, viewing Paper startup logs, and reviewing PacketEvents initialization).
- **Alternative Considered**: Running headless in the background without a window. Rejected because administrators cannot input console commands or monitor startup crashes.

### 2. Multi-Tier Server Boot Resolution
- **Choice**: Hierarchical resolution:
  1. `MCP_PAPER_START_SCRIPT` (or `-StartScript` param): If defined, executes the script in the server directory (e.g. `run.bat`, `start.bat`).
  2. `MCP_PAPER_SERVER_JAR` (or `-ServerJar` param): If defined, executes `java -jar <jar> --nogui`.
  3. Auto-detection: Scans `$MCP_PAPER_SERVER_DIR` for `paper*.jar` or `server*.jar`. If found, executes `java -jar <found> --nogui`.
  4. If none resolved, logs actionable instructions and halts before starting services.
- **Rationale**: Respects developers who use customized startup scripts (with specific JVM flags/Aikar's flags) while allowing zero-config startup for standard setups.

### 3. Pre-flight Dependency Inspection (PacketEvents)
- **Choice**: Inspect `$MCP_PAPER_SERVER_DIR\plugins` for files matching `*packetevents*.jar`.
- **Rationale**: The props engine depends on PacketEvents at runtime. If missing, Spigot will fail to resolve PacketEvents classes when handling virtual displays. A clear colored warning in `dev.ps1` alerts the developer before server launch.

### 4. Mock Elimination and Clean-Slate Option
- **Choice**: Delete `backend/mock_agent.py` and `backend/mock_server_storage/`. Implement `dev.ps1 -CleanData` to wipe `backend/mcp.db`, `data/packs/dist/*`, and `data/packs/tmp/*`.
- **Rationale**: Removes confusing duplicate execution paths and guarantees that all test items, blocks, and revisions are generated and verified live.

## Risks / Trade-offs

- **[Risk]** Paper server port 25565 or Gateway port 8000 already in use.
  - *Mitigation*: `dev.ps1 -Mode stop` cleans up orphan processes; clear logging when ports are occupied.
- **[Risk]** Target server directory does not exist or environment variable not set.
  - *Mitigation*: `dev.ps1` checks path validity and displays step-by-step guidance on how to set `$env:MCP_PAPER_SERVER_DIR`.
