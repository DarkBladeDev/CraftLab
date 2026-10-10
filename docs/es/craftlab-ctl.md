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

- **Páginas Categorizadas (Categorized Pages)**: Barra superior de pestañas horizontales (`Overview`, `System & Host`, `Lifecycle & Ops`, `Releases & Updates`, `Doctor & Health`, `Terminal & Logs`) que organiza los dominios operativos preservando el 100% del ancho de pantalla para la cuadrícula de paneles.
- **Contenedores de Datos Paginados Modulares (Paginated Data Containers)**: Motor modular (`ContainerEngine`) basado en un schema declarativo tipado en TypeScript (`PaginatedContainerPreset`) con arquitectura de paginación híbrida:
  - **Modo Sub-vistas (`subviews`)**: Alterna modos de pantalla internos (resumen de métricas $\rightarrow$ desglose granular $\rightarrow$ formulario de acciones) dentro de un mismo slot de tarjeta compacto.
  - **Modo Colección de Registros (`records`)**: Pagina colecciones y listas de datos (releases instaladas, auditorías, agentes) con controles de avance/retroceso sin desbordar la tarjeta.
  - **Modo Simple (`none`)**: Visualización directa para flujos anchos continuos como el terminal de logs en tiempo real.
- **Cuadrícula Reorganizable y Redimensionable (`DraggableGrid`)**: Arrastre nativo por tirador (`[::]`), ajuste dinámico del ancho de columnas (`- / + Cols`), persistencia automática del diseño personalizado en el `localStorage` del navegador y botón para restablecer valores por defecto.
- **Control de Acceso en Controles (RBAC)**: Validación automática de roles (`admin`, `operator`, `viewer`, `is_break_glass`) en botones y campos de entrada, deshabilitando acciones no autorizadas.

