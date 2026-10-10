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

### 2. Motor de Props, Máquina de Estados y Displays Virtuales (`PropManager`)
- **Cero Lag de Ticks**: En lugar de sobrecargar el mundo con ArmorStands pesados o entidades de bloque, los props se renderizan a nivel de cliente mediante paquetes de display entities emitidos por PacketEvents.
- **Máquina de Estados y Swapping Visual**: Permite múltiples estados por prop (`default_state` y `states`), alternando modelos visuales al instante vía `WrapperPlayServerEntityMetadata` (Data Component `item_model`) sin parpadeos ni despawn de entidades.
- **Iluminación Dinámica Nativa**: Administra bloques `Material.LIGHT` (niveles 0 a 15) en Paper 1.21; los coloca y remueve automáticamente al cambiar de estado o al destruir el prop.
- **Hitboxes Dinámicas y Eyección Segura**: Soporta transición entre estados sólidos (`BARRIER`) y transitables (`STRUCTURE_VOID`), aplicando un impulso de velocidad horizontal suave a los jugadores que ocupen el área antes de cerrar colisiones sólidas para evitar asfixia o atrapamiento.
- **Interacción y Efectos**: Control de cooldown anti-spam (250 ms) en clics derechos, reproducción de efectos de sonido configurados (Bukkit y nombres de pack personalizados) y soporte para mecánicas de asiento (`seat`) o recostado (`lay`).
- **Persistencia en SQLite**: Las coordenadas, rotaciones y el estado activo (`current_state`) de los props se almacenan de manera persistente en `plugins/McpAgent/data/props.db`.

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
