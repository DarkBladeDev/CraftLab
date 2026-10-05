# Design

## Context
See `proposal.md` for high-level motivation. The repository currently contains architectural specifications in `minecraft-content-platform-spec-v1/` and formalized OpenSpec baseline capability specifications. No production code exists yet. This design details the concrete technical architecture to implement the first end-to-end vertical slice.

## Goals / Non-Goals

**Goals:**
- Provide a working monorepo setup (`backend/`, `frontend/`, `paper-agent/`).
- Build an async control plane in FastAPI with SQLite storage and native WebSockets.
- Implement an outbound-connecting Java 21 Paper plugin with native 1.21 item data components.
- Enable end-to-end authoring, immutable revisioning, deployment planning, and live application of a custom item.
- Provide `/mcp give <player> <item_id>` for in-game verification.

**Non-Goals:**
- External plugin adapters (Oraxen, ItemsAdder, MythicMobs).
- Complex 3-way visual merge UI (conflict warnings are sufficient for MVP).
- Full multi-tenant RBAC (use baseline admin/editor permissions).
- Production TLS certificate infrastructure (local dev uses self-signed or insecure WS flag).

## Decisions

### Decision 1: FastAPI Modular Monolith with Native WebSockets
- **Choice**: FastAPI + Pydantic v2 + SQLAlchemy (async SQLite) running via Uvicorn.
- **Rationale**: Provides native async WebSockets without requiring external message brokers (Redis), Celery, or Daphne. Pydantic models cleanly express JSON schemas for protocol envelopes and item definitions with static type safety.
- **Alternatives Considered**: Django + Django Channels (heavyweight operational footprint with Redis requirement for local dev) or Node.js/NestJS (less suited for Python-oriented team data models).

### Decision 2: Paper 1.21.x Target with Extensible Adapter Interface
- **Choice**: Target Paper 1.21.x (Java 21) using an `ItemAdapter` interface implemented by `Paper121ItemAdapter`.
- **Rationale**: Uses native 1.21 Data Components (replacing legacy NBT/ItemMeta manipulation). The decoupled adapter interface guarantees backward compatibility (e.g. `PaperLegacyItemAdapter` for 1.20.4) can be introduced later without changing core agent networking or command logic.
- **Alternatives Considered**: Multi-version NMS reflection layer (fragile, high maintenance overhead for MVP).

### Decision 3: Local Agent Storage for Applied Items
- **Choice**: Paper agent persists deployed items in `plugins/MinecraftContentPlatform/items.json`.
- **Rationale**: Guarantees that items remain accessible on server restarts even if the control plane gateway is offline or disconnected during boot.
- **Alternatives Considered**: Pure in-memory registry (items vanish on restart) or remote fetch on server boot (fails if control plane is down).

### Decision 4: Clean Monorepo Structure
- **Choice**:
  - `backend/`: FastAPI application, gateway, and domain logic.
  - `frontend/`: React + Vite + Tailwind CSS client.
  - `paper-agent/`: Java 21 Paper plugin buildable via Gradle.
- **Rationale**: Maximizes project intuitiveness and allows atomic planning and verification across all three tiers.

## Risks / Trade-offs

- **[Network drops during deployment]** → Mitigated by protocol message correlation IDs, idempotency tokens, and timeout handling. If an agent disconnects during deployment, the plan transitions to `failed` rather than hanging indefinitely.
- **[Paper 1.21 Data Components API differences across minor builds]** → Mitigated by compiling against stable Paper API 1.21.1 and using standard high-level Bukkit/Paper item component APIs rather than internal Mojang NMS mappings.
- **[Concurrent modification by multiple users]** → Mitigated by immutable revision hashing (SHA-256) where each deployment plan explicitly targets a frozen revision snapshot.

## Open Questions

- *Build tool for paper-agent*: Standard Gradle (Kotlin DSL) recommended for modern Paper plugins; Maven is acceptable as fallback. Gradle 8.x with Java 21 toolchain is the default choice.
