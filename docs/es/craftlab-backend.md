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

### 2. Pipeline de Resource Packs (`PackCompiler` y `PackMerger`)
Automatiza el complejo ensamblado de paquetes de texturas y modelos para Minecraft:
- **Recolección de Recursos**: Agrupa texturas, archivos JSON de modelos personalizados, metadatos de audio y definiciones de ítems modernas para 1.21.
- **Empaquetado ZIP Hermético**: Compila el archivo respetando la estructura oficial (`pack.mcmeta` versión 34+ para Paper 1.21.1+).
- **Cálculo Automático de Hash SHA-1**: Genera el checksum hexadecimal requerido por los clientes de Minecraft para validar la integridad del paquete.
- **Distribución en Caliente**: Emite el evento `resource_pack_ready` a los servidores vinculados para solicitar la descarga automática a los usuarios en línea.

### 3. Control de Acceso Basado en Roles (RBAC)
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
| `/api/v1/packs/build` | POST | Dispara la compilación del resource pack y genera el ZIP final. |
| `/api/v1/packs/download` | GET | Descarga el archivo comprimido del resource pack activo. |
| `/api/v1/targets` | GET / POST | Administra los servidores Paper registrados en la flota. |
