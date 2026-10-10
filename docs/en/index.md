---
title: Welcome to CraftLab
description: Overview and architecture of CraftLab, the modern Minecraft Content Platform.
sidebar:
  order: 1
---

# CraftLab (Minecraft Content Platform)

**CraftLab** is an integrated content authoring, resource pack pipeline, and fleet release management system designed for **Paper Minecraft 1.21.1 – 1.21.4+** servers. It eliminates the friction of configuring custom items, custom entities/props, and distributing server resource packs by bridging a visual web studio directly with in-game servers.

---

## High-Level Architecture

CraftLab is structured as a coordinated monorepo of 4 primary components:

```text
+---------------------------------------------------------------------------------------+
|                                  CRAFTLAB PLATFORM                                    |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +-----------------------+                    +----------------------------------+   |
|   |   CraftLab-frontend   |                    |           CraftLab-ctl           |   |
|   | (React + Vite Studio) |                    |  (Supervisor Daemon & CLI Panel) |   |
|   +-----------+-----------+                    +-----------------+----------------+   |
|               |                                                  |                    |
|          HTTP | REST                                   HTTP / WS | Remote Admin       |
|               v                                                  v                    |
|   +-------------------------------------------------------------------------------+   |
|   |                               CraftLab-backend                                |   |
|   |              FastAPI + SQLite Engine + Resource Pack Pipeline                 |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                 WebSocket | Gateway (/ws/agent)                       |
|                                           v                                           |
|                       +---------------------------------------+                       |
|                       |            CraftLab-plugin            |                       |
|                       |   Paper 1.21+ Plugin (PacketEvents)   |                       |
|                       +---------------------------------------+                       |
+---------------------------------------------------------------------------------------+
```

---

## Core Modules

### 1. [CraftLab-backend](craftlab-backend.md)
The central intelligence engine:
- **FastAPI REST API**: Serves item schemas, block models, target server registrations, and role-based permissions.
- **WebSocket Gateway**: Persistent bi-directional channel (`/ws/agent`) communicating with active game servers in real time.
- **Resource Pack Pipeline**: Automated pack compiler and merger that collects textures, models, and sound manifests into production `.zip` distributions with automatic SHA-1 hashing.
- **Security & RBAC**: Password hashing via Argon2 and token-based authentication.

### 2. [CraftLab-frontend](craftlab-frontend.md)
The modern web-based authoring suite:
- **Item Studio**: Design custom items with Minecraft 1.21 Data Components (`item_model`) and fallback CustomModelData.
- **Block Studio / Virtual Props**: Configure custom block models using PacketEvents display entities with barrier collision anchors and interactive seats.
- **Pack Manager**: Visual asset workspace inspecting texture layers, sounds, and live pack status.
- **Fleet Targets**: Monitor connected Paper servers and deployment statuses.

### 3. [CraftLab-ctl](craftlab-ctl.md)
The operations supervisor and deployment manager:
- **`craftctl` CLI**: Intuitive command-line interface for starting, stopping, restarting, and checking system health.
- **`craftctld` Daemon**: Background supervisor executing periodic health checks and managing isolated release environments.
- **Atomic Updates**: Seamless updates downloaded directly from GitHub Releases (`DarkBladeDev/CraftLab`) with dedicated virtualenvs, a pre-cached wheel directory, and instant rollback support.
- **Control Web Dashboard**: Dedicated SPA dashboard served on port `8443`.

### 4. [CraftLab-plugin](craftlab-plugin.md)
The native in-game runtime for Paper servers:
- **Java 21 & Paper 1.21+**: Leverages modern Paper APIs and PacketEvents 2.14.0 for tick-free display entity rendering.
- **Bidirectional Handshake**: Connects to the backend gateway over WebSockets with authentication tokens.
- **Player Resource Pack Delivery**: Prompts joining players with the updated pack URL and SHA-1 hash upon login.
- **Oraxen Compatibility**: Scans and exports legacy Oraxen configurations without conflicts.
- **In-Game Commands**: Provides `/mcp give`, `/mcp status`, and `/mcp reloadpack` for server operators.

### 5. [Shared Packages](packages/index.md)
Modular libraries powering cross-cutting domain logic:
- **`craftlab_security`**: Canonical security event schema, pre-persistence sensitive data sanitization, WAL SQLite audit logging, and production fail-fast environment validation.

---

## Next Steps

- Check out the [Installation Guide](installation.md) to run CraftLab locally or deploy to a production server.
- Learn about configuring components in the [Configuration Reference](configuration.md).
