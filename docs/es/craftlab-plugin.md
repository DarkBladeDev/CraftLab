---
title: CraftLab-plugin (Plugin Paper para Minecraft)
description: Plugin agente para servidores Paper 1.21+, props virtuales con PacketEvents, sincronización Oraxen y comandos.
sidebar:
  order: 6
---

# CraftLab-plugin

**CraftLab-plugin** es el componente nativo instalado directamente en los servidores **Paper Minecraft 1.21.1 – 1.21.4+**. Conecta el servidor de juego con `CraftLab-backend` a través de un WebSocket seguro, procesa ítems y props virtuales desplegados, distribuye paquetes de recursos a los jugadores e interactúa con plugins como Oraxen.

---

## Especificaciones Técnicas

- **Plataforma Soportada**: Paper / Purpur 1.21.1+ (Java 21).
- **Protocolo de Red**: WebSocket seguro (`/ws/agent`) con reconexión automática y autenticación por token secreto.
- **Dependencias**:
  - `PacketEvents` (Spigot / Paper) versión 2.14.0+ (Obligatoria para la renderización de entidades virtuales de display).
  - `Oraxen` (Dependencia opcional suave para sincronización de catálogos existentes).
- **Persistencia Local**: Base de datos SQLite embebida (`plugins/McpAgent/data/props.db`) para bloques/props colocados, y `items.json` para definiciones de ítems.

---

## Capacidades Principales

```
+---------------------------------------------------------------------------------+
|                                 CRAFTLAB-PLUGIN                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                       Cliente WebSocket Gateway                         |   |
|   |  Handshake (targetId + secret) -> Despachador de Eventos -> Enrutador   |   |
|   +------------------------------------+------------------------------------+   |
|                                        |                                        |
|         +------------------------------+------------------------------+         |
|         |                              |                              |         |
|         v                              v                              v         |
|  [Adaptador de Ítems]         [Gestor de Props]           [Distribución Packs]  |
|  * Data Components 1.21       * Displays PacketEvents     * Solicitud en        |
|    (item_model)               * Cero lag en ticks           PlayerJoinEvent     |
|  * CustomModelData alternativo* Anclaje con barreras      * URL y hash SHA-1    |
|  * Sincronización items.json  * Mecánica de sentarse        del pack activo     |
+---------------------------------------------------------------------------------+
```

### 1. Adaptador de Ítems (`Paper121ItemAdapter`)
- Aplica Data Components modernos de Minecraft 1.21 (`item_model`) mediante reflexión al ejecutarse en Paper 1.21.2+.
- Mantiene compatibilidad aplicando simultáneamente `CustomModelData` para packs y configuraciones anteriores.
- Persiste las definiciones de ítems localmente en el servidor para que sigan funcionando incluso si se interrumpe la conexión con el backend.

### 2. Motor de Props y Displays Virtuales (`PropManager`)
- **Cero Lag de Ticks**: En lugar de sobrecargar el mundo con ArmorStands pesados o entidades de bloque, los props se renderizan a nivel de cliente mediante paquetes de display entities emitidos por PacketEvents.
- **Colisiones Sólidas**: Ubica automáticamente bloques de barrera invisibles en las coordenadas del prop para evitar que los jugadores lo atraviesen.
- **Mecánica Interactiva de Asiento**: Detecta clics derechos sobre sillas o sofás y monta al jugador en un marcador invisible.
- **Persistencia en SQLite**: Las coordenadas, rotaciones y estados de los props se almacenan de manera persistente en `plugins/McpAgent/data/props.db`.

### 3. Distribución de Resource Packs (`ResourcePackManager`)
- Escucha el evento `PlayerJoinEvent` e invita a los jugadores a descargar el resource pack del servidor.
- Proporciona la URL HTTP y el hash SHA-1 para asegurar que el cliente de Minecraft almacene el paquete en caché sin descargas redundantes.
- Permite forzar el reenvío del pack en caliente sin reiniciar el servidor ni desconectar jugadores.

### 4. Hook de Compatibilidad con Oraxen
- Detecta y lee ítems de Oraxen mediante reflexión sin generar excepciones por falta de dependencias.
- Facilita la sincronización bidireccional: exporta ítems de Oraxen al estudio de CraftLab y sincroniza las carpetas de recursos.

---

## Comandos para Operadores

CraftLab-plugin registra el espacio de comandos `/mcp` (requiere el permiso `mcp.admin`):

| Comando | Argumentos | Descripción |
| :--- | :--- | :--- |
| `/mcp give` | `<jugador> <itemId> [cantidad]` | Entrega el ítem o prop personalizado indicado al jugador. |
| `/mcp status` | Ninguno | Muestra el estado de la conexión WebSocket, targetId y props cargados. |
| `/mcp reloadpack` | `[jugador]` | Fuerza el reenvío del resource pack a todos los usuarios o al indicado. |
| `/mcp reload` | Ninguno | Recarga el archivo `config.yml` y restablece la conexión con el gateway. |

---

## Archivo de Configuración (`plugins/McpAgent/config.yml`)

```yaml
gateway:
  url: "ws://127.0.0.1:8000/ws/agent"
  targetId: "local-paper-server"
  secret: "tu-secreto-gateway"

props:
  enable_packetevents: true
  enable_sit_mechanic: true
```
