---
title: CraftLab-ctl (Sistema de Control y Demonio)
description: Demonio supervisor, CLI craftctl, pipeline de actualizaciones atómicas y panel web de control.
sidebar:
  order: 3
---

# CraftLab-ctl

**CraftLab-ctl** es el plano de control y supervisión de CraftLab. Está compuesto por el demonio en segundo plano `craftctld`, la herramienta CLI `craftctl`, un motor de actualizaciones atómicas y un panel web de control embebido.

---

## Arquitectura General

```
+---------------------------------------------------------------------------------+
|                                 CRAFTLAB-CTL                                    |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   CLI (craftctl) <-----------> Socket / REST de Control <------> Panel Web (:8443)
|                                      |                                          |
|                                      v                                          |
|                       Demonio Supervisor (craftctld)                            |
|                                      |                                          |
|         +----------------------------+----------------------------+             |
|         |                            |                            |             |
|         v                            v                            v             |
|  [LifecyclePlugin]             [CorePlugin]                 [UpdatePlugin]      |
|  * Supervisor de servicios     * Salud y Doctor             * API de Releases   |
|  * Monitor de procesos         * Resolución de rutas        * Caché de wheels   |
|  * Ejecutores Uvicorn / Vite   * Carga de configuración     * Gestor de rollback|
+---------------------------------------------------------------------------------+
```

---

## Interfaz de Línea de Comandos (`craftctl`)

El ejecutable `craftctl` proporciona acceso administrativo a las operaciones de la plataforma:

### Ciclo de Vida de los Servicios

| Comando | Descripción |
| :--- | :--- |
| `craftctl status` | Muestra el estado operativo del backend, frontend y demonio supervisor. |
| `craftctl start` | Arranca los servicios administrados (API backend y endpoints de control). |
| `craftctl stop` | Detiene de forma ordenada los procesos de la plataforma. |
| `craftctl restart` | Realiza un reinicio limpio de los servicios administrados. |

### Diagnóstico de la Plataforma

```bash
craftctl doctor
```
Verifica de manera proactiva:
- Integridad del entorno virtual Python y paquetes instalados.
- Presencia de bundles web estáticos (`frontend_dist/index.html` y `ctl_web_dist/index.html`).
- Permisos de escritura y conectividad con la base de datos SQLite.
- Disponibilidad de puertos de red (`CRAFTLAB_PORT`, puerto de control `8443`).

---

## Motor de Actualizaciones Atómicas

CraftLab implementa un sistema de actualización con cero tiempo de inactividad y capacidad de restauración ante fallos mediante `UpdatePlugin`:

```
               [GitHub Releases: DarkBladeDev/CraftLab]
                                  │
                          (craftctl update check)
                                  │
                                  ▼
                     Descarga de craftlab-v*.tar.gz
                                  │
                                  ▼
             Creación de venv aislado por versión (/releases/vX.Y.Z)
             Instalación rápida desde caché de wheels (/cache/wheels)
                                  │
                                  ▼
                Conmutación atómica de enlace simbólico (/current)
                Reinicio controlado de servicios
```

### Comandos de Actualización

- **Buscar actualizaciones disponibles**:
  ```bash
  craftctl update check
  ```
- **Preparar release** (descarga, descomprime y valida checksums sin aplicar):
  ```bash
  craftctl update prepare --version 0.3.3
  ```
- **Aplicar release** (conmuta la versión activa y reinicia servicios):
  ```bash
  craftctl update apply --version 0.3.3
  ```
- **Reversión instantánea (Rollback)** (restaura la versión anterior si surgen incidencias):
  ```bash
  craftctl update rollback
  ```

---

## Panel Web de Control

`craftctld` expone un dashboard web moderno y modular en el puerto `8443` construido con React y Tailwind CSS:

- **Páginas Categorizadas (Categorized Pages)**: Barra superior de pestañas horizontales (`Overview`, `System & Host`, `Lifecycle & Ops`, `Releases & Updates`, `Security & Audit`, `Doctor & Health`, `Terminal & Logs`) que organiza los dominios operativos preservando el 100% del ancho de pantalla para la cuadrícula de paneles.
- **Contenedores de Datos Paginados Modulares (Paginated Data Containers)**: Motor modular (`ContainerEngine`) basado en un schema declarativo tipado en TypeScript (`PaginatedContainerPreset`) con arquitectura de paginación híbrida:
  - **Modo Sub-vistas (`subviews`)**: Alterna modos de pantalla internos (resumen de métricas $\rightarrow$ desglose granular $\rightarrow$ formulario de acciones) dentro de un mismo slot de tarjeta compacto.
  - **Modo Colección de Registros (`records`)**: Pagina colecciones y listas de datos (releases instaladas, auditorías, agentes) con controles de avance/retroceso sin desbordar la tarjeta.
  - **Modo Simple (`none`)**: Visualización directa para flujos anchos continuos como el terminal de logs en tiempo real.
- **Cuadrícula Reorganizable y Redimensionable (`DraggableGrid`)**: Arrastre nativo por tirador (`[::]`), ajuste dinámico del ancho de columnas (`- / + Cols`), persistencia automática del diseño personalizado en el `localStorage` del navegador y botón para restablecer valores por defecto.
- **Control de Acceso en Controles (RBAC)**: Validación automática de roles (`admin`, `operator`, `viewer`, `is_break_glass`) en botones y campos de entrada, deshabilitando acciones no autorizadas.

---

## Plano de Seguridad y Auditoría (Security & Audit)

`CraftLab-ctl` integra supervisión de postura de amenazas, motor de detección heurística de anomalías proactivo, explorador de auditoría forense y mitigaciones de contención inmediata.

### Presets Modulares de Seguridad

La categoría dedicada **Security & Audit** aloja tres contenedores modulares especializados:

1. **Radar de Amenazas (`securityThreatRadarPreset`)**:
   - **Índice Compuesto de Amenazas (Threat Index)**: Medidor radial 0–100% evaluado en tiempo real por el motor de anomalías sobre una ventana deslizante de 15 minutos.
   - **Clasificación de Postura**: Insignia de estado (`NORMAL`, `ELEVATED`, `HIGH`, `CRITICAL` o `LOCKDOWN`).
   - **Telemetría en Vivo**: Conteo de fallos de autenticación en 15 min, eventos totales en 24h, IPs en cuarentena activas y anomalías detectadas.
   - **Acciones de Emergencia**: Palanca de bloqueo de emergencia (Emergency Lockdown, restringida a rol `admin`) y purga de retención de registros de auditoría.

2. **Monitor de Anomalías y Mitigaciones (`securityAnomalyMonitorPreset`)**:
   - **Motor de Detección Heurística**: Identifica ráfagas de fuerza bruta (>5 intentos fallidos en 60s desde la misma IP o usuario), uso de credenciales de emergencia break-glass, picos de denegación de privilegios y escaneos de rutas sospechosas.
   - **Sub-vistas Dobles**:
     - *Active Anomalies*: Tarjetas de incidente con severidad, descripción, actor o IP de origen y botones de mitigación inmediata (**Quarantine IP**, **Dismiss**).
     - *Active Containment*: Listado de IPs en cuarentena con tiempo restante (TTL), formulario para poner IPs en cuarentena manual, levantamiento de bloqueos y botón de emergencia **Revoke All Active Sessions**.

3. **Explorador de Auditoría Forense (`securityAuditExplorerPreset`)**:
   - **Persistencia Aislada SQLite en Modo WAL**: Consulta directa a `data/security-audit.sqlite3` con pre-sanitización estricta de credenciales y tokens antes de almacenar.
   - **Paginación y Filtros Multi-criterio**: Filtrado por severidad (`CRITICAL`, `HIGH`, `WARN`, `INFO`), componente emisor y resultado (`success`, `failure`, `blocked`).
   - **Panel Lateral de Atributos**: Despliega el contexto completo sanitizado (IP de origen, ruta consultada, código HTTP, razones de fallo) protegiendo secretos y contraseñas.

### Endpoints REST de Seguridad

Todos los endpoints requieren autenticación activa bajo `/api/v1/security/`:

| Endpoint | Método | Rol Requerido | Descripción |
| :--- | :--- | :--- | :--- |
| `/api/v1/security/posture` | `GET` | Autenticado | Devuelve índice de amenaza, estado de postura y métricas. |
| `/api/v1/security/anomalies` | `GET` | Autenticado | Lista las anomalías activas detectadas. |
| `/api/v1/security/anomalies/dismiss`| `POST` | Operador / Admin | Descarta una alerta de anomalía por su ID. |
| `/api/v1/security/events` | `GET` | Autenticado | Consulta paginada sobre los registros de auditoría canónicos. |
| `/api/v1/security/quarantines` | `GET` | Autenticado | Lista las direcciones IP en cuarentena y sus TTLs de expiración. |
| `/api/v1/security/quarantine` | `POST` | Admin | Aplica cuarentena inmediata a una IP con TTL configurable (minutos). |
| `/api/v1/security/unquarantine` | `POST` | Admin | Levanta la cuarentena de una dirección IP. |
| `/api/v1/security/revoke-sessions` | `POST` | Admin | Revoca sesiones para un usuario específico o todas las sesiones activas. |
| `/api/v1/security/toggle-lockdown` | `POST` | Admin | Conmuta el modo de confinamiento/bloqueo de emergencia (Emergency Lockdown). |
| `/api/v1/security/purge` | `POST` | Admin | Purga registros de auditoría con antigüedad superior a los días especificados. |

### Middleware de Contención Activa

- **Filtro de Cuarentena de IP**: El middleware del servidor intercepta las solicitudes entrantes contra el `IpQuarantineManager` en memoria y persistido en disco. Las IPs bloqueadas reciben de inmediato `403 Forbidden` y generan un evento de auditoría `authz.denied`.
- **Compuerta de Bloqueo de Emergencia**: En modo confinamiento (Lockdown), se rechaza cualquier inicio de sesión no administrativo y las acciones mutantes quedan restringidas exclusivamente a administradores.


