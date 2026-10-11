---
title: CraftLab-frontend (Estudio Web Visual)
description: Entorno de autoría web, Item Studio, Block Studio y gestor de Resource Packs.
sidebar:
  order: 5
---

# CraftLab-frontend

**CraftLab-frontend** es el entorno de creación visual para constructores, desarrolladores y administradores de servidores Minecraft. Desarrollado con **React 18**, **Vite** y **Tailwind CSS**, permite diseñar ítems personalizados, previsualizar props decorativos en 3D y gestionar paquetes de texturas sin editar archivos YAML o JSON de forma manual.

---

## Espacios de Trabajo

```
+---------------------------------------------------------------------------------+
|                               CRAFTLAB-FRONTEND                                 |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   +-----------------------+  +-----------------------+  +--------------------+  |
|   |      ITEM STUDIO      |  |     BLOCK STUDIO      |  |   GESTOR DE PACKS  |  |
|   | Modelos de ítems      |  | Props display entity  |  | Texturas y modelos |  |
|   | Data Components 1.21  |  | Colisiones barrera    |  | Manifiesto sonidos |  |
|   | CustomModelData       |  | Interacción sentarse  |  | Compilación a ZIP  |  |
|   +-----------------------+  +-----------------------+  +--------------------+  |
|                                                                                 |
|   +-------------------------------------------------------------------------+   |
|   |                      GESTIÓN DE SERVIDORES OBJETIVO                     |   |
|   | Monitor de conexión de la flota, latencia y comandos de sincronización  |   |
|   +-------------------------------------------------------------------------+   |
+---------------------------------------------------------------------------------+
```

---

## Espacios en Detalle

### 1. Item Studio
Crea y modifica ítems personalizados con compatibilidad completa para versiones modernas de Minecraft:
- **Data Components de Minecraft 1.21**: Configura identificadores `item_model` nativos vinculados a tus modelos personalizados.
- **Componentes de Equipamiento (1.21.2+)**: Vincula modelos de armaduras y equipamiento (`minecraft:equippable`) con autocompletado cargado directamente desde el Creative Assets Lab.
- **Soporte de CustomModelData**: Define IDs numéricos para retrocompatibilidad con resource packs clásicos.
- **Editor Visual de Atributos**: Modifica nombres en pantalla, descripciones formateadas (MiniMessage y códigos de color clásicos), rarezas y encantamientos.
- **Despliegue Inmediato**: Aplica cambios en los servidores Paper conectados con un solo clic.

### 2. Block Studio (Props Virtuales y Máquinas de Estados)
Diseña mobiliario, bloques decorativos y props 3D sin registrar tile entities ni provocar sobrecarga de ticks en el servidor:
- **Previsualizaciones PacketEvents**: Configuración de escalas, traslaciones y rotaciones para display entities.
- **Máquinas de Estados y Variantes**: Pestaña dedicada para crear múltiples estados (`default_state`, `states`), modelos alternativos, niveles de luz (0–15), sonidos de entrada, disparadores de partículas VFX y presets rápidos (Lámparas, Puertas/Rejas).
- **Triggers de Audio y VFX**: Vincula eventos de sonido y partículas personalizadas con calibración de offsets tridimensionales a las transiciones de estado.
- **Hitboxes Dinámicas**: Alterna entre hitboxes sólidas (`solid`) y transitables (`passable`) por estado, asegurando eyección física de jugadores para evitar asfixia.
- **Anclaje de Colisiones Físicas**: Vinculación automática con bloques de barrera o structure void en coordenadas relativas.
- **Mecánicas Interactivas para Sentarse y Recostarse**: Asigna puntos de asiento a muebles permitiendo que los jugadores se sienten o recuesten al hacer clic derecho.
- **Ciclo de Vida de Destrucción**: Asigna drops específicos y efectos de sonido al romper los props.

### 3. Creative Assets Lab
Espacio creativo unificado para diseñar y gestionar assets de audio, fuentes, equipamiento y partículas:
- **Arquitectura Dinámica Multi-Namespace**: Soporte nativo para múltiples namespaces en todas las pestañas con selectores explícitos, sugerencias por datalist del workspace, descomposición automática de dos puntos (`namespace:id`) y badges delimitados en la lista lateral.
- **Glifos y Fuentes**: Asignador automático de códigos PUA (`\uE000`–`\uF8FF`), anulación hexadecimal manual con detección de colisiones en tiempo real, etiquetas MiniMessage y simuladores de Chat y Tablist en vivo.
- **Equipamiento y Armaduras (1.21.2+)**: Constructor multicapa compatible con `humanoid`, `humanoid_leggings` y `wings`, máscaras teñibles (`dyeable`), previsualizador 2D/3D tipo paper doll en modelos Steve y Alex, y generador de componentes `minecraft:equippable`.
- **Eventos de Sonido (SFX)**: Editor visual de `sounds.json` con variaciones multipista, análisis de canales Vorbis (Mono vs. Estéreo) y downmix en un clic `(L+R)/2` a Mono `.ogg` para atenuación posicional 3D.
- **Partículas y Efectos VFX**: Editor de `particles/<id>.json` con validador de texturas de sprites, simulador de emisor en canvas HTML5 a 60 FPS y generador de comandos `/particle`.
- **Drawer de Esquema y JSON Raw**: Editor de código colapsable con sincronización bidireccional y validación contra esquemas oficiales de Minecraft 1.21.2+.

### 4. Gestor de Packs (Pack Manager)
Panel integral para organizar y compilar recursos visuales:
- **Matriz Multi-Versión Universal**: Visualización en tiempo real de la arquitectura de 4 capas: Capa Base (1.21.0 - 1.21.1, formatos 34..41), Items V2 (1.21.2+, formatos 42..max), Shaders Modernos (1.21.4+, formatos 46..max) y atlas de texturas auto-sintetizados.
- **Gestión de Precedencia de Capas**: Ajusta la prioridad de capas entre assets de Studio, workspace y paquetes de terceros importados.
- **Auditor de Conflictos Pre-Flight**: Modal de diagnóstico interactivo que alerta sobre colisiones de CustomModelData, texturas faltantes en disco, solapamiento de shaders con resolución de precedencia y advertencias de seguridad para mipmaps y animaciones.
- **Configuración de Manifiesto**: Define el formato base, límites máximos configurables por el operador (`max_inclusive`) y descripción.
- **Compilación en un Clic**: Dispara el empaquetado en el backend, revisa el digest SHA-1 determinista y valida los enlaces de descarga.

### 5. Gestión de Servidores Objetivo (Targets)
Consola centralizada para supervisar los servidores Paper vinculados:
- **Estado en Tiempo Real**: Visualiza la conexión WebSocket activa, latencia y versiones de plugin.
- **Acciones Rápidas**: Ordena recargas de resource packs, refresco de catálogos o pruebas de entrega a usuarios.

