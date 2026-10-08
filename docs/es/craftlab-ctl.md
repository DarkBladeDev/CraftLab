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

`craftctld` expone un dashboard web en el puerto `8443`:
- **Métricas en tiempo real**: Monitorea consumo de memoria, CPU y tiempo en línea de los módulos.
- **Actualizaciones a un clic**: Ejecuta comprobaciones, preparaciones y conmutaciones con salida de terminal en vivo.
- **Historial de diagnósticos**: Revisa los resultados del chequeo `doctor` y los manifiestos de versión instalados.
