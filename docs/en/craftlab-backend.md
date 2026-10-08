---
title: CraftLab-backend (REST API & Gateway)
description: Backend service architecture, FastAPI endpoints, WebSocket agent gateway, and pack pipeline.
sidebar:
  order: 4
---

# CraftLab-backend

**CraftLab-backend** is the central application server for the CraftLab platform. Built with **FastAPI** and **SQLAlchemy**, it handles REST requests from the Web Studio, routes real-time commands through a WebSocket Gateway to connected Paper servers, and compiles optimized Minecraft resource packs.

---

## Architectural Layers

```
+---------------------------------------------------------------------------------+
|                                CRAFTLAB-BACKEND                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   [ REST API Endpoints ]                    [ WebSocket Gateway ]               |
|   * /api/v1/auth                            * /ws/agent                         |
|   * /api/v1/items                           * Bi-directional message router     |
|   * /api/v1/props                           * Target server authentication      |
|   * /api/v1/packs                           * Live catalog synchronization      |
|   * /api/v1/targets                                                             |
|                          \                         /                            |
|                           v                       v                             |
|                    +-------------------------------------+                      |
|                    |     Domain Services & Pipeline      |                      |
|                    |     * PackCompiler & PackMerger     |                      |
|                    |     * AssetWorkspaceService         |                      |
|                    |     * RBAC & Security (Argon2)      |                      |
|                    +------------------+------------------+                      |
|                                       |                                         |
|                                       v                                         |
|                    +-------------------------------------+                      |
|                    |         SQLite Data Storage         |                      |
|                    |    (data/mcp.db via SQLAlchemy)     |                      |
|                    +-------------------------------------+                      |
+---------------------------------------------------------------------------------+
```

---

## Key Subsystems

### 1. WebSocket Agent Gateway (`/ws/agent`)
The gateway establishes a persistent bi-directional link with in-game servers running `CraftLab-plugin`:
- **Target Verification**: Validates `targetId` and shared gateway secret upon connection handshake.
- **Dynamic Command Dispatch**: Sends deployment envelopes (`item:deploy`, `prop:deploy`, `resource_pack_ready`) immediately when assets change in Web Studio.
- **Heartbeats & State Tracking**: Monitors server connection state, Paper version, and loaded packs.

### 2. Resource Pack Pipeline (`PackCompiler` & `PackMerger`)
CraftLab automates the tedious assembly of Minecraft resource packs:
- **Asset Collection**: Gathers textures, custom model JSONs, sound definitions, and modern 1.21 item definitions.
- **Hermetic ZIP Packaging**: Compiles the pack into standard Minecraft pack formats (`pack.mcmeta` version 34+ for 1.21.1+).
- **Automated SHA-1 Calculation**: Generates the exact hexadecimal SHA-1 checksum required by Minecraft clients to verify pack integrity.
- **Hot Distribution**: Automatically dispatches a `resource_pack_ready` notification to connected servers to prompt online players.

### 3. Role-Based Access Control (RBAC)
- **Password Hashing**: Employs industry-standard Argon2id hashing algorithms.
- **Granular Roles**: Supports `admin`, `operator`, and `viewer` permissions.
- **Session Tokens**: Issues secure JWT authentication tokens with configurable expiration.

---

## REST API Overview

| Route | Method | Description |
| :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | Authenticates user and returns JWT access token. |
| `/api/v1/items` | GET / POST | Lists and creates custom item definitions. |
| `/api/v1/items/{id}` | GET / PUT / DELETE | Retrieves, updates, or deletes an item definition. |
| `/api/v1/props` | GET / POST | Lists and creates custom virtual block/prop definitions. |
| `/api/v1/packs/build` | POST | Triggers resource pack compilation and generates distribution ZIP. |
| `/api/v1/packs/download` | GET | Serves the active compiled resource pack archive. |
| `/api/v1/targets` | GET / POST | Manages registered Paper game servers in the fleet. |
