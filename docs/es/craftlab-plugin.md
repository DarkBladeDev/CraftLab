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
  - `Oraxen` (Dependencia opcional para sincronización de catálogos existentes).
  - `PlaceholderAPI` (Dependencia opcional para placeholders `%craftlab_<dominio>_...%`).
- **Persistencia Local**: Base de datos SQLite embebida (`plugins/McpAgent/data/props.db`) para bloques/props colocados, `items.json` para definiciones de ítems y `glyphs.json` para glifos sincronizados del resource pack.

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

### 1. Adaptador de Ítems (`Paper121ItemAdapter`) y Pipeline Extensible de Data Components
- **Registro Extensible de Componentes (`ItemComponentRegistry`)**: Implementa un patrón Strategy extensible (`ItemComponentApplier`) que despacha dinámicamente todas las entradas del mapa `components` de un ítem durante la compilación y entrega con `/mcp give`.
- **Componente Equippable (`minecraft:equippable`)**:
  - Soporte integral para componentes `minecraft:equippable` de Minecraft 1.21.2 - 1.21.4+.
  - Soporta atributos principales: `slot` (`head`, `chest`, `legs`, `feet`, `body`, `mainhand`, `offhand`, `saddle`) y el identificador canónico `asset_id` (con fallback retrocompatible `model`).
  - Soporta todos los atributos opcionales: `camera_overlay` (overlay de textura en pantalla), `equip_sound` (sonidos Bukkit o identificadores de sonido personalizados), `allowed_entities` (filtrado por tipos de entidades) y banderas booleanas de comportamiento (`dispensable`, `swappable`, `damage_on_hurt`, `can_be_sheared`).
  - Emplea detección reflectiva de capacidades (`isSupported()`) que garantiza compatibilidad binaria segura entre Paper 1.21.0 y 1.21.4+ sin generar errores `NoClassDefFoundError`.
- **Modificadores de Atributos (`minecraft:attribute_modifiers`)**:
  - Compila listas y objetos de atributos a instancias nativas de Bukkit `AttributeModifier`.
  - Soporta la API moderna 1.21 de `NamespacedKey` y `EquipmentSlotGroup` con fallback seguro para UUIDs en servidores anteriores.
- **Encantamientos (`minecraft:enchantments`)**:
  - Aplica niveles de encantamiento sin restricción de topes (`ignoreLevelRestriction = true`), soportando armas y armaduras RPG avanzadas.
- **Modelos de Ítems y CustomModelData**:
  - Aplica reflectivamente `item_model` nativo en Paper 1.21.2+ manteniendo en paralelo `CustomModelData` para packs tradicionales.
- **Persistencia**: Persiste las definiciones de ítems localmente en `items.json` para que sigan funcionando incluso si se interrumpe la conexión con el backend.

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

### 5. Integración Extensible con PlaceholderAPI y Proveedor de Glifos (`PlaceholderRegistry`)
- **Arquitectura Enrutada por Dominios**: Implementa un enrutador desacoplado (`PlaceholderRegistry` + `PlaceholderProvider`) bajo la expansión persistente `craftlab` (`%craftlab_<dominio>_<params>%`), aislado mediante `PlaceholderApiHook` para que el plugin opere sin errores cuando PlaceholderAPI no está instalado.
- **Sincronización Vinculada a Publicación de Pack**: Sincroniza los glifos PUA compilados (`\uE000`–`\uF8FF`) hacia `plugins/McpAgent/glyphs.json` al compilar/publicar el resource pack (`resource_pack:ready`) o durante el handshake inicial (`hello`). Los proveedores bitmap de namespaces personalizados (`assets/<ns>/font/default.json`) se proyectan en `assets/minecraft/font/default.json` durante la compilación para que el carácter Unicode se renderice directamente en chat, TAB, scoreboards y hologramas sin requerir etiquetas `<font:...>`.
- **Placeholders de Glifos Soportados (dominio `glyph`)**:
  - `%craftlab_glyph_<id>%`: Devuelve el carácter PUA `\uXXXX` por ID (priorizando el namespace `craftlab`).
  - `%craftlab_glyph_<namespace>:<id>%`: Devuelve el carácter PUA para un namespace e identificador específicos.
  - `%craftlab_glyph_hex_<hex>%`: Devuelve el carácter PUA según su código hexadecimal de 4 dígitos (ej. `%craftlab_glyph_hex_E001%`).
  - `%craftlab_glyph_mm_<selector>%`: Devuelve la etiqueta formateada para MiniMessage `<font:<namespace>:<font>>\uXXXX</font>`.

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
