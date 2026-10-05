# Minecraft Content Platform

A modern web-based content authoring, versioning, and release-management engine for Paper Minecraft servers.

## Monorepo Layout

```
MinecraftResourceManager/
├── backend/                       # FastAPI Control Plane & WebSocket Gateway
│   ├── app/                       # Domain models, database, protocol, API
│   ├── tests/                     # 13 automated unit & E2E integration tests
│   └── mock_agent.py              # Lightweight simulated Paper 1.21 agent
├── frontend/                      # React 18 + Vite + Tailwind CSS Web Client
│   └── src/                       # Fleet monitor, Item editor, Deployment modal
├── paper-agent/                   # Native Java 21 Paper plugin (Gradle)
│   ├── src/main/java/             # WebSocket client, Paper 1.21 item adapter, /mcp command
│   └── build/libs/                # Compiled paper-agent-1.0.0-SNAPSHOT.jar
├── dev.ps1                        # All-in-one local dev deploy & runtime launcher
├── openspec/                      # OpenSpec specs and changes
└── minecraft-content-platform-spec-v1/ # Reference architecture documents
```

---

## Quickstart (Local Dev Deployment)

To build and start all systems locally in one command:

```powershell
.\dev.ps1
```

This will automatically:
1. Verify / build the Paper plugin JAR (`paper-agent/build/libs/paper-agent-1.0.0-SNAPSHOT.jar`).
2. Start the **FastAPI Backend & WebSocket Gateway** on `http://127.0.0.1:8000`.
3. Start the **React Web UI** on `http://localhost:3000`.
4. Start the **Paper 1.21 Mock Agent** connected as `local-paper-server`.
5. Open your browser at `http://localhost:3000`.

### Other Execution Modes

- **Backend & Frontend only** (for connecting to a real Minecraft server):
  ```powershell
  .\dev.ps1 -Mode server
  ```
- **Deploy JAR directly to a Paper server `plugins/` directory**:
  ```powershell
  .\dev.ps1 -PaperPluginsDir "C:\path\to\paper-server\plugins"
  ```
- **Stop all dev processes**:
  ```powershell
  .\dev.ps1 -Mode stop
  ```

---

## Testing the End-to-End Flow

1. Open **[http://localhost:3000](http://localhost:3000)**.
2. Observe that `local-paper-server` appears as **ONLINE** (green indicator receiving heartbeats).
3. Fill out the **Item Definition Editor**:
   - Identifier: `ruby_sword`
   - Material: `DIAMOND_SWORD`
   - Display Name: `<red><bold>Ruby Sword</bold></red>`
   - Lore: `<gray>Forged in ancient magma chambers.</gray>`
   - Custom Model Data: `10001`
4. Click **Save Definition**, then click **Create Revision**.
5. Click **Publish & Deploy** in the top navbar:
   - Click **Generate Deployment Plan**.
   - Review operations and click **Approve Plan**.
   - Click **Deploy to Live Server**.
6. The agent executes the allowlisted operation over WebSocket, compiles the Paper 1.21 item, saves it to `items.json`, and returns success!
7. In-game verification command:
   ```text
   /mcp give <player> ruby_sword
   ```

---

## Running Automated Tests

* **Backend tests** (13 tests including full WebSocket integration):
  ```powershell
  cd backend
  .\.venv\Scripts\pytest
  ```
* **Paper agent build & tests**:
  ```powershell
  cd paper-agent
  .\gradlew test
  ```
* **Frontend production build**:
  ```powershell
  cd frontend
  npm run build
  ```
