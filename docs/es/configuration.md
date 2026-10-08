---
title: Referencia de Configuración
description: Guía de referencia de variables de entorno, craftlab.toml y configuración del plugin Paper.
sidebar:
  order: 7
---

# Referencia de Configuración

Esta sección reúne todas las opciones de configuración disponibles en la plataforma CraftLab, abarcando variables de entorno (`.env`), el archivo de supervisión (`config/craftlab.toml`) y los ajustes del plugin en el juego (`config.yml`).

---

## 1. Variables de Entorno (`.env`)

Utilizadas primordialmente por `CraftLab-backend` y los scripts de automatización:

| Variable | Valor por Defecto | Descripción |
| :--- | :--- | :--- |
| `CRAFTLAB_HOST` | `127.0.0.1` | Dirección IP de escucha del backend FastAPI y del gateway WebSocket. |
| `CRAFTLAB_PORT` | `8000` | Puerto del API REST y del gateway WebSocket. |
| `CRAFTLAB_SECRET_KEY` | *(Aleatorio)* | Clave secreta empleada para firmar y verificar tokens de autenticación JWT. |
| `CRAFTLAB_GATEWAY_SECRET` | `dev-secret` | Contraseña compartida requerida por los servidores Paper para conectarse a `/ws/agent`. |
| `CRAFTLAB_DB_PATH` | `data/mcp.db` | Ruta relativa o absoluta al archivo de base de datos SQLite principal. |
| `CRAFTLAB_PACKS_DIR` | `data/packs` | Directorio donde residen los recursos crudos, workspaces y los archivos `.zip` compilados. |
| `MCP_PAPER_SERVER_DIR` | *(Ninguno)* | Ruta opcional a un servidor Paper local para auto-despliegue del JAR mediante `dev.ps1`. |
| `MCP_PAPER_START_SCRIPT` | *(Auto-detectado)* | Nombre opcional del script de arranque (ej. `run.bat` o `start.ps1`) para iniciar el servidor Paper. |
| `MCP_PAPER_SERVER_JAR` | *(Auto-detectado)* | Nombre opcional del archivo JAR del servidor Paper (ej. `paper-1.21.1-118.jar`). |

---

## 2. Configuración del Supervisor (`config/craftlab.toml`)

Utilizado por la utilidad `craftctl` y el demonio supervisor `craftctld`:

```toml
[platform]
name = "craftlab"
home_dir = "/opt/craftlab"
current_symlink = "current"

[server]
host = "0.0.0.0"
port = 8443
enable_tls = false

[services.backend]
enabled = true
command = "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
cwd = "backend"
health_endpoint = "http://127.0.0.1:8000/health"

[services.frontend]
enabled = true
serve_static = true
dist_dir = "frontend_dist"

[updates]
github_repo = "DarkBladeDev/CraftLab"
wheel_cache_dir = "cache/wheels"
releases_dir = "releases"
auto_rollback_on_failure = true
```

---

## 3. Configuración del Plugin Paper (`plugins/McpAgent/config.yml`)

Ubicado dentro del directorio `plugins/` en tu servidor Minecraft Paper:

```yaml
gateway:
  # Dirección WebSocket del backend de CraftLab
  url: "ws://127.0.0.1:8000/ws/agent"

  # Identificador único de este servidor dentro de la flota
  targetId: "local-paper-server"

  # Secreto idéntico al valor CRAFTLAB_GATEWAY_SECRET del backend
  secret: "dev-secret"

  # Intervalo de espera para reintentos de reconexión (en segundos)
  reconnect_delay_seconds: 5

props:
  # Habilitar el renderizado de props mediante display entities con PacketEvents
  enable_packetevents: true

  # Permitir a los jugadores sentarse en muebles al hacer clic derecho
  enable_sit_mechanic: true

packs:
  # Solicitar automáticamente la descarga del pack a los jugadores al entrar
  prompt_on_join: true

  # Expulsar a los jugadores si rechazan un resource pack obligatorio
  force_pack: false
```
