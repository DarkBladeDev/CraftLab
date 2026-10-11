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

### 2. Resource Pack Pipeline (`PackCompiler`, `PackMerger` & `PreflightValidator`)
CraftLab automates the assembly of multi-version Minecraft resource packs with zero asset bloat:
- **Cumulative Multi-Version Overlays**: Produces packs compatible across Minecraft 1.21.0 to 1.21.4+ via root assets (formats 34..41), `overlay_v1_21_2` (formats 42..max) for Item Definition V2, and `overlay_v1_21_4` (formats 46..max) for modern core shader pipelines.
- **Shader Routing Engine (`ShaderRouter`)**: Automatically classifies core shader programs (`.vsh`, `.fsh`, `.json`), isolating 1.21.4+ vertex formats in `overlay_v1_21_4` while preserving legacy shaders in root assets for older clients.
- **Texture Atlas Auto-Synthesis (`AtlasSynthesizer`)**: Scans custom namespaces and GUI sprites, automatically generating minimal, grouped `directory` entries in `assets/minecraft/atlases/blocks.json` and `gui.json` to eliminate missing sprite checkerboards.
- **Dual-Projection Synthesis**: Simultaneously synthesizes legacy `models/item/*.json` predicate overrides and modern `items/*.json` select definitions from unified mappings.
- **Pre-Flight Conflict Auditor**: Validates CustomModelData collisions, missing physical texture references, core shader overlaps across layers, power-of-two mipmap dimensions, and animated vertical spritesheets missing `.png.mcmeta`.
- **Hermetic ZIP Packaging & Determinism**: Builds bit-identical ZIP archives with normalized timestamps and SHA-1 checksums for client verification and hot distribution via WebSocket notifications.

### 3. Creative Assets Lab Domain Services
CraftLab provides dedicated backend domain services for custom client visual and audio assets:
- **PUA Font & Glyph Allocator (`GlyphService`)**: Manages Private Use Area codepoints (`\uE000`–`\uF8FF`), scans workspace fonts for free slots, validates manual hex overrides against active collisions, and synthesizes `font/*.json` bitmap providers.
- **Equipment Models 1.21.2+ (`EquipmentService`)**: Validates layer hierarchies (`humanoid`, `humanoid_leggings`, `wings`, `horse`, etc.), manages dyeable overlay tint masks, and synthesizes `models/equipment/<id>.json` across root and `overlay_v1_21_2`.
- **Sound Events & Spatial Mono Downmixer (`SoundEventService`)**: Manages `sounds.json` audio event catalogs, probes Vorbis binary headers to verify channel topology (Mono vs. Stereo), and provides automated `(L+R)/2` downmixing to single-channel Mono `.ogg` for 3D positional distance attenuation in Minecraft.
- **Particle VFX Engine (`ParticleService`)**: Validates sprite texture paths, synthesizes `particles/<id>.json` descriptors, and generates executable in-game `/particle` commands.

### 4. Role-Based Access Control (RBAC)
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
| `/api/v1/props` | GET / POST | Lists and creates custom virtual block/prop definitions with multi-state machine support. |
| `/api/v1/assets/creative/glyphs` | GET / POST / DELETE | Manages PUA unicode glyph registrations and font allocations. |
| `/api/v1/assets/creative/equipment` | GET / POST / DELETE | Manages 1.21.2+ equipment model descriptors and layer stacks. |
| `/api/v1/assets/creative/sounds` | GET / POST / DELETE | Manages sounds.json events and audio probe inspections. |
| `/api/v1/assets/creative/sounds/convert-mono` | POST | Downmixes stereo audio samples into single-channel Mono `.ogg`. |
| `/api/v1/assets/creative/particles` | GET / POST / DELETE | Manages custom particle definitions and command generation. |
| `/api/v1/packs/build` | POST | Triggers resource pack compilation and generates distribution ZIP. |
| `/api/v1/packs/download` | GET | Serves the active compiled resource pack archive. |
| `/api/v1/targets` | GET / POST | Manages registered Paper game servers in the fleet. |

