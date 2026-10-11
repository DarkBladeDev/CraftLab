---
title: CraftLab-backend (API REST y Gateway)
description: Arquitectura del servicio backend, endpoints FastAPI, gateway WebSocket para agentes y pipeline de packs.
sidebar:
  order: 4
---

# CraftLab-backend

**CraftLab-backend** es el servidor de aplicaciones central de la plataforma CraftLab. Desarrollado con **FastAPI** y **SQLAlchemy**, gestiona las solicitudes REST del Web Studio, enruta instrucciones en tiempo real mediante un WebSocket Gateway hacia los servidores Paper conectados y compila resource packs optimizados para Minecraft.

---

## Capas Arquitectónicas

```
+---------------------------------------------------------------------------------+
|                                CRAFTLAB-BACKEND                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   [ Endpoints API REST ]                    [ Gateway WebSocket ]               |
|   * /api/v1/auth                            * /ws/agent                         |
|   * /api/v1/items                           * Enrutador de mensajes en vivo     |
|   * /api/v1/props                           * Autenticación de servidores Paper |
|   * /api/v1/packs                           * Sincronización de catálogos       |
|   * /api/v1/targets                                                             |
|                          \                         /                            |
|                           v                       v                             |
|                    +-------------------------------------+                      |
|                    |     Servicios de Dominio            |                      |
|                    |     * PackCompiler & PackMerger     |                      |
|                    |     * AssetWorkspaceService         |                      |
|                    |     * RBAC y Seguridad (Argon2)     |                      |
|                    +------------------+------------------+                      |
|                                       |                                         |
|                                       v                                         |
|                    +-------------------------------------+                      |
|                    |    Almacenamiento de Datos SQLite   |                      |
|                    |     (data/mcp.db vía SQLAlchemy)    |                      |
|                    +-------------------------------------+                      |
+---------------------------------------------------------------------------------+
```

---

## Subsistemas Principales

### 1. WebSocket Agent Gateway (`/ws/agent`)
El gateway establece una conexión bidireccional continua con los servidores Minecraft que ejecutan `CraftLab-plugin`:
- **Verificación de Servidores**: Comprueba el identificador `targetId` y el secreto compartido durante el apretón de manos inicial.
- **Despacho Dinámico de Acciones**: Emite paquetes de despliegue (`item:deploy`, `prop:deploy`, `resource_pack_ready`) de inmediato ante cambios realizados en el Web Studio.
- **Latidos y Monitorización de Estado**: Rastrea el estado de conexión del servidor, la versión de Paper y los packs cargados.

### 2. Pipeline de Resource Packs (`PackCompiler`, `PackMerger` y `PreflightValidator`)
Automatiza el ensamblado de paquetes de recursos multi-versión para Minecraft con cero duplicación de assets:
- **Overlays Acumulativos Multi-Versión**: Genera paquetes compatibles desde 1.21.0 hasta 1.21.4+ mediante la raíz (formatos 34..41), `overlay_v1_21_2` (formatos 42..max) para Item Definition V2 y `overlay_v1_21_4` (formatos 46..max) para shaders modernos de 1.21.4+.
- **Motor de Enrutamiento de Shaders (`ShaderRouter`)**: Clasifica automáticamente programas de shaders (`.vsh`, `.fsh`, `.json`), aislando formatos de vértices modernos de 1.21.4+ en `overlay_v1_21_4` y preservando shaders legacy en la raíz para clientes antiguos.
- **Auto-Síntesis de Atlas de Texturas (`AtlasSynthesizer`)**: Escanea namespaces personalizados y sprites de interfaz, inyectando entradas `directory` agrupadas en `assets/minecraft/atlases/blocks.json` y `gui.json` para evitar errores de renderizado.
- **Proyección Dual de Modelos**: Genera en paralelo overrides de predicados para 1.21.0 - 1.21.1 (`models/item/*.json`) y definiciones modernas para 1.21.2+ (`items/*.json`).
- **Auditor Pre-Flight de Conflictos**: Detecta colisiones de CustomModelData, referencias a texturas inexistentes en disco, colisiones de shaders entre capas con precedencia, validación de dimensiones potencia de dos (mipmaps) y detección de animaciones sin `.png.mcmeta`.
- **Empaquetado ZIP Hermético y Determinista**: Compila archivos ZIP idénticos bit a bit con timestamps normalizados y checksum SHA-1 para distribución inmediata mediante WebSocket.

### 3. Servicios de Dominio Creative Assets Lab
CraftLab proporciona servicios especializados para la creación y gestión de assets visuales y de audio para el cliente:
- **Asignador de Glifos y Fuentes PUA (`GlyphService`)**: Administra puntos de código en el área de uso privado (`\uE000`–`\uF8FF`), escanea fuentes del workspace en busca de espacios libres, valida anulaciones hexadecimales manuales contra colisiones activas y sintetiza proveedores bitmap en `font/*.json`.
- **Modelos de Equipamiento 1.21.2+ (`EquipmentService`)**: Valida jerarquías de capas (`humanoid`, `humanoid_leggings`, `wings`, `horse`, etc.), gestiona máscaras de tinte teñibles (`dyeable`) y sintetiza `models/equipment/<id>.json` en la raíz y en `overlay_v1_21_2`.
- **Eventos de Sonido y Downmixing Mono Espacial (`SoundEventService`)**: Administra el catálogo `sounds.json`, analiza encabezados binarios Vorbis para verificar la topología de canales (Mono vs. Estéreo) y proporciona downmixing automático `(L+R)/2` a Mono `.ogg` para atenuación posicional 3D en Minecraft.
- **Motor de Partículas VFX (`ParticleService`)**: Valida rutas de texturas de sprites, genera descriptores `particles/<id>.json` y sintetiza comandos ejecutables `/particle` para el juego.

### 4. Control de Acceso Basado en Roles (RBAC)
- **Hasheo Seguro de Contraseñas**: Utiliza algoritmos de derivación de claves Argon2id.
- **Roles Granulares**: Soporta niveles de permiso `admin`, `operator` y `viewer`.
- **Tokens de Sesión**: Genera tokens JWT firmados con expiración configurable.

---

## Resumen de Endpoints REST

| Ruta | Método | Descripción |
| :--- | :--- | :--- |
| `/api/v1/auth/login` | POST | Autentica al usuario y entrega un token JWT de acceso. |
| `/api/v1/items` | GET / POST | Lista y crea definiciones de ítems personalizados. |
| `/api/v1/items/{id}` | GET / PUT / DELETE | Consulta, actualiza o elimina una definición de ítem. |
| `/api/v1/props` | GET / POST | Lista y crea definiciones de bloques/props virtuales con soporte para máquinas de estados. |
| `/api/v1/assets/creative/glyphs` | GET / POST / DELETE | Gestiona el registro de glifos PUA y asignación de fuentes. |
| `/api/v1/assets/creative/equipment` | GET / POST / DELETE | Gestiona descriptores de modelos de equipamiento 1.21.2+ y capas. |
| `/api/v1/assets/creative/sounds` | GET / POST / DELETE | Gestiona eventos de sounds.json y diagnósticos de audio. |
| `/api/v1/assets/creative/sounds/convert-mono` | POST | Convierte pistas de audio estéreo a un canal mono simétrico `.ogg`. |
| `/api/v1/assets/creative/particles` | GET / POST / DELETE | Gestiona definiciones de partículas y comandos `/particle`. |
| `/api/v1/packs/build` | POST | Dispara la compilación del resource pack y genera el ZIP final. |
| `/api/v1/packs/download` | GET | Descarga el archivo comprimido del resource pack activo. |
| `/api/v1/targets` | GET / POST | Administra los servidores Paper registrados en la flota. |

