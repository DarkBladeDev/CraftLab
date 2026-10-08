---
title: Bienvenido a CraftLab
description: Visión general y arquitectura de CraftLab, la plataforma moderna de contenidos para Minecraft.
sidebar:
  order: 1
---

# CraftLab (Minecraft Content Platform)

**CraftLab** es una plataforma integral de autoría de contenido, compilación de resource packs y administración de versiones diseñada para servidores **Paper Minecraft 1.21.1 – 1.21.4+**. Elimina la fricción al configurar ítems personalizados, entidades/props de bloques decorativos y la distribución de paquetes de texturas mediante la conexión directa entre un estudio web visual y los servidores en juego.

---

## Arquitectura General

CraftLab está estructurado como un monorepositorio coordinado compuesto por 4 módulos principales:

```text
+---------------------------------------------------------------------------------------+
|                                  PLATAFORMA CRAFTLAB                                  |
+---------------------------------------------------------------------------------------+
|                                                                                       |
|   +-----------------------+                    +----------------------------------+   |
|   |   CraftLab-frontend   |                    |           CraftLab-ctl           |   |
|   |  (Estudio Web React)  |                    | (Demonio Supervisor y Panel CLI) |   |
|   +-----------+-----------+                    +-----------------+----------------+   |
|               |                                                  |                    |
|          HTTP | REST                                   HTTP / WS | Admin Remoto       |
|               v                                                  v                    |
|   +-------------------------------------------------------------------------------+   |
|   |                               CraftLab-backend                                |   |
|   |          FastAPI + Motor SQLite + Pipeline de Compilación de Packs            |   |
|   +---------------------------------------+---------------------------------------+   |
|                                           |                                           |
|                                 WebSocket | Gateway (/ws/agent)                       |
|                                           v                                           |
|                       +---------------------------------------+                       |
|                       |            CraftLab-plugin            |                       |
|                       |   Plugin Paper 1.21+ (PacketEvents)   |                       |
|                       +---------------------------------------+                       |
+---------------------------------------------------------------------------------------+
```

---

## Módulos Principales

### 1. [CraftLab-backend](craftlab-backend.md)
El núcleo central del sistema:
- **API REST FastAPI**: Gestiona esquemas de ítems, modelos de bloques, registros de servidores objetivo y control de acceso.
- **WebSocket Gateway**: Canal bidireccional persistente (`/ws/agent`) que comunica con los servidores de juego activos en tiempo real.
- **Pipeline de Resource Packs**: Compilador y unificador automático que empaqueta texturas, modelos y archivos de sonido en distribuciones `.zip` con cálculo automático de hash SHA-1.
- **Seguridad y RBAC**: Hasheo de credenciales con Argon2 y autenticación por tokens JWT.

### 2. [CraftLab-frontend](craftlab-frontend.md)
El entorno de autoría visual basado en React 18 + Vite + Tailwind:
- **Item Studio**: Diseña ítems personalizados con Data Components de Minecraft 1.21 (`item_model`) y compatibilidad con CustomModelData.
- **Block Studio / Props Virtuales**: Configura modelos de bloques decorativos mediante display entities de PacketEvents, con colisiones de barrera y mecánicas para sentarse.
- **Pack Manager**: Espacio de trabajo visual para inspeccionar capas de texturas, sonidos y estado de compilación.
- **Servidores Objetivo (Fleet)**: Monitorea el estado de conexión de los servidores Paper registrados.

### 3. [CraftLab-ctl](craftlab-ctl.md)
El supervisor de operaciones y gestor de ciclo de vida:
- **CLI `craftctl`**: Interfaz de comandos para iniciar, detener, reiniciar y diagnosticar la plataforma.
- **Demonio `craftctld`**: Servicio en segundo plano con comprobaciones de estado periódicas y gestión de versiones aisladas.
- **Actualizaciones Atómicas**: Descarga de releases directamente desde GitHub (`DarkBladeDev/CraftLab`), entornos virtuales aislados, caché compartida de dependencias y capacidad de rollback inmediato.
- **Panel Web de Control**: Dashboard SPA accesible en el puerto `8443`.

### 4. [CraftLab-plugin](craftlab-plugin.md)
El componente nativo en el servidor Paper:
- **Java 21 y Paper 1.21+**: Integración con APIs modernas de Paper y PacketEvents 2.14.0 para visualización de entidades sin impacto en los ticks del servidor.
- **Handshake Bidireccional**: Conexión al backend vía WebSocket validando token secreto y targetId.
- **Distribución de Resource Packs**: Notificación automática del enlace del pack y su hash SHA-1 a los jugadores al unirse (`PlayerJoinEvent`).
- **Compatibilidad con Oraxen**: Detección, exportación y sincronización bidireccional sin conflictos.
- **Comandos de Operador**: Acceso en el juego mediante `/mcp give`, `/mcp status` y `/mcp reloadpack`.

---

## Siguientes Pasos

- Consulta la [Guía de Instalación](installation.md) para ejecutar CraftLab en desarrollo o producción.
- Revisa las variables y opciones en la [Referencia de Configuración](configuration.md).
