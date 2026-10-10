---
title: Package craftlab_security
description: Contrato canónico de eventos de seguridad, sanitización universal y sumidero SQLite en modo WAL.
sidebar:
  order: 2
  label: craftlab_security
---

# Package craftlab_security

`craftlab_security` es la biblioteca transversal de seguridad y auditoría del monorepo CraftLab, encargada de:
1. Proveer un **contrato canónico de eventos de auditoría y seguridad** compartido entre el backend FastAPI, el WebSocket Gateway y el demonio supervisor `craftctld`.
2. Proporcionar un **sanitizador universal de datos** previo a la persistencia para evitar fugas de secretos y mitigar vectores de inyección o sobrecarga de búfer.
3. Proporcionar un **sumidero SQLite aislado (`security-audit.sqlite3`)** en modo WAL con doble ruta de escritura (síncrona fail-closed para eventos críticos y en cola asíncrona por lotes para telemetría de alto volumen).
4. Proveer un **validador de arranque fail-fast** que bloquea la inicialización de la plataforma en entornos de producción ante configuraciones inseguras, autenticación desactivada o tokens por defecto.

---

## Especificaciones Técnicas

- **Ubicación:** [`packages/craftlab_security`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages/craftlab_security)
- **Versión:** `0.1.0`
- **Tipo:** Biblioteca interna compartida (Python 3.11+)
- **Dependencias:** `pydantic >= 2.0.0`

---

## Subsistemas y Arquitectura

### 1. Esquema Canónico de Eventos (`models.py`)

Define los modelos de datos en Pydantic v2 para eventos estructurados.

#### Enumeraciones Estables
- `Component`: `backend`, `websocket_gateway`, `daemon`
- `EventType`:
  - `HTTP_REQUEST`: `http.request`
  - `AUTH_FAILURE`: `auth.failure`
  - `AUTHZ_DENIED`: `authz.denied`
  - `API_ENUMERATION_DETECTED`: `api.enumeration.detected`
  - `WEBSOCKET_AUTH_FAILURE`: `websocket.auth.failure`
  - `WEBSOCKET_LIMIT_EXCEEDED`: `websocket.limit.exceeded`
  - `WEBSOCKET_CONNECTED`: `websocket.connected`
  - `WEBSOCKET_DISCONNECTED`: `websocket.disconnected`
  - `ADMIN_ACTION`: `admin.action`
  - `DAEMON_OPERATION_FAILED`: `daemon.operation.failed`
  - `SECURITY_ALERT`: `security.alert`
- `Severity`: `INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`
- `Outcome`: `SUCCESS`, `DENIED`, `FAILED`, `UNKNOWN`
- `ActorType`: `ANONYMOUS`, `USER`, `AGENT`, `SYSTEM`, `UNKNOWN`
- `TransportType`: `HTTP`, `WS`, `IPC`, `INTERNAL`, `UNKNOWN`

#### Modelo de Evento: `SecurityEvent`
Campos normalizados:
- `schema_version`: Versión entera del contrato (`1`).
- `event_id`: UUIDv4 generado en el punto de emisión.
- `occurred_at`: Marca temporal UTC en formato ISO 8601.
- `component`: Subsistema emisor (`Component`).
- `event_type`: Clasificación semántica normalizada (`EventType`).
- `severity`: Nivel de severidad (`Severity`).
- `outcome`: Resultado (`Outcome`).
- `actor`: Contexto del actor verificado (`ActorContext(type, id, roles)`).
- `source`: Metadatos de origen de transporte (`SourceContext(ip, transport, user_agent)`).
- `request`: Contexto de la petición HTTP (`RequestContext(request_id, method, route, status_code)`).
- `target`: Entidad afectada (`TargetContext(type, id)`).
- `reason_code`: Código alfanumérico estable (`invalid_credentials`, `target_secret_mismatch`).
- `duration_ms`: Duración opcional de ejecución en milisegundos.
- `attributes`: Diccionario extensible con metadatos contextuales sanitizados.

---

### 2. Sanitizador Universal de Datos (`sanitizer.py`)

Garantiza que secretos, credenciales y cargas sobredimensionadas sean eliminados antes de persistir o registrar eventos.

#### Políticas de Sanitización:
1. **Redacción por Denylist:**
   - Detecta claves sensibles: `password`, `token`, `secret`, `authorization`, `cookie`, `session`, `credential`, `key`, `access_token`, `refresh_token`, `api_key`, `private_key`.
   - Reemplaza sus valores por `[REDACTED]`.
2. **Truncamiento Seguro de Cadenas:**
   - Cadenas de atributos que excedan 512 caracteres son truncadas con el sufijo `...[TRUNCATED]`.
3. **Poda de Profundidad:**
   - Estructuras JSON anidadas a más de 3 niveles son recortadas (`[NESTING_TRUNCATED]`) para prevenir agotamiento de memoria o recursión abusiva.
4. **Limpieza de Query Strings:**
   - Rutas HTTP normalizan y limpian query strings (ej. `/api/v1/ws/logs?token=xyz` se transforma en `/api/v1/ws/logs`).

---

### 3. Sumidero SQLite en Modo WAL (`sink.py`)

Almacena eventos de auditoría en una base de datos SQLite aislada (`data/security-audit.sqlite3`).

#### Aspectos Clave de Diseño:
- **Base de Datos Exclusiva:** Independiente de `mcp.db` (contenido) y `auth.db` (usuarios).
- **WAL Journaling:** `PRAGMA journal_mode = WAL` permite lecturas concurrentes sin bloquear escrituras.
- **Ingesta por Doble Ruta:**
  - `emit_critical(event)`: Ruta síncrona y fail-closed para fallos de autenticación, denegaciones y mutaciones administrativas.
  - `emit_telemetry(event)`: Cola en memoria con límite de 5,000 elementos, volcada en lotes de 50 o cada 2 segundos para telemetría de red de alta frecuencia.
- **Purga Periódica:** `purge_old_events(retention_days=90)` para mantener el tamaño bajo control.
- **Protección contra Bloqueos en Windows:** Conexiones cerradas explícitamente vía context manager `@contextmanager def _connection()` evitando errores `WinError 32`.
- **Consultas Filtradas:** `query_events(component, event_type, outcome, actor_id, limit, offset)` respaldado por índices compuestos.

---

### 4. Validación Fail-Fast en Arranque (`validation.py`)

Garantiza la seguridad en despliegues de producción.

Función: `validate_production_security_environment()`
- Inspecciona las variables `CRAFTLAB_ENV` o `ENV`.
- Si el valor es `production` o `prod`:
  1. **Autenticación Desactivada:** Lanza `SecurityConfigurationError` si `CRAFTLAB_AUTH_ENABLED == "false"`.
  2. **Tokens de Emergencia por Defecto:** Lanza `SecurityConfigurationError` si `CRAFTLAB_ROOT_TOKEN` contiene valores de ejemplo (`change_me_to_a_secure_root_token`, `root-token`, `admin`, etc.).
- En entornos de desarrollo o test genera advertencias informativas sin interrumpir la ejecución.

---

## Integración en el Monorepo

### 1. `CraftLab-backend`
- **Ciclo de Vida:** Invoca `validate_production_security_environment()` durante el inicio de FastAPI en `main.py`.
- **Auditoría de Endpoints:** Helper común `app.core.security.emit_audit_event()` emite eventos para intentos de inicio de sesión fallidos (`auth.failure`), operaciones administrativas (`admin.action`) y denegaciones (`authz.denied`).
- **WebSocket Gateway:** `app.gateway.manager.AgentSessionManager` valida criptográficamente el secreto del agente en el handshake `hello` mediante `secrets.compare_digest`, rechazando agentes no autorizados con código 1008 y registrando `websocket.auth.failure`.

### 2. `CraftLab-ctl`
- **Inicio de Supervisor:** Valida la configuración de producción en `DaemonService.start()` y `server/app.py`.
- **CORS Estricto:** Prohíbe comodines en orígenes cuando se permiten credenciales.
- **Cookies Seguras:** Exige `Secure=True` en cookies de sesión para entornos HTTPS.
- **Logs WebSocket:** Deshabilita autenticación por query string en `/api/v1/ws/logs`.
- **Identidad Confiable:** `DaemonService.handle_action` deriva la identidad del actor estrictamente del socket IPC autenticado (`ipc:{user}`).
- **Registro Dual:** `AuditLogger` escribe en paralelo a `audit.jsonl` (sanitizado) y al sumidero canónico `SecurityAuditSink`.

---

## Ejemplos de Código

### Emisión de un Evento Crítico
```python
from pathlib import Path
from craftlab_security import (
    SecurityAuditSink, SecurityEvent, Component, EventType,
    Severity, Outcome, ActorContext, ActorType, SourceContext, TransportType
)

sink = SecurityAuditSink(Path("data/security-audit.sqlite3"))

event = SecurityEvent(
    component=Component.BACKEND,
    event_type=EventType.AUTH_FAILURE,
    severity=Severity.HIGH,
    outcome=Outcome.DENIED,
    actor=ActorContext(type=ActorType.ANONYMOUS),
    source=SourceContext(ip="203.0.113.195", transport=TransportType.HTTP),
    reason_code="invalid_credentials",
    attributes={"attempted_username": "admin"},
)

sink.emit_critical(event)
```

### Sanitización Universal
```python
from craftlab_security import DataSanitizer

raw_attributes = {
    "username": "developer",
    "password": "SuperSecretPassword123!",
    "nested": {
        "api_key": "raw-secret-token",
        "description": "Acción estándar"
    }
}

clean_attributes = DataSanitizer.sanitize_dict(raw_attributes)
# clean_attributes["password"] == "[REDACTED]"
# clean_attributes["nested"]["api_key"] == "[REDACTED]"
```

---

## Pruebas Unitarias

Las pruebas unitarias del paquete se ubican en [`packages/craftlab_security/tests/`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages/craftlab_security/tests):

```bash
pytest packages/craftlab_security/tests -v
```
