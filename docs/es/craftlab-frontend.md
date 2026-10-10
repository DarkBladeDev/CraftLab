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
- **Soporte de CustomModelData**: Define IDs numéricos para retrocompatibilidad con resource packs clásicos.
- **Editor Visual de Atributos**: Modifica nombres en pantalla, descripciones formateadas (MiniMessage y códigos de color clásicos), rarezas y encantamientos.
- **Despliegue Inmediato**: Aplica cambios en los servidores Paper conectados con un solo clic.

### 2. Block Studio (Props Virtuales y Máquinas de Estados)
Diseña mobiliario, bloques decorativos y props 3D sin registrar tile entities ni provocar sobrecarga de ticks en el servidor:
- **Previsualizaciones PacketEvents**: Configuración de escalas, traslaciones y rotaciones para display entities.
- **Máquinas de Estados y Variantes**: Pestaña dedicada para crear múltiples estados (`default_state`, `states`), modelos alternativos, niveles de luz (0–15), sonidos de entrada y presets rápidos (Lámparas, Puertas/Rejas).
- **Hitboxes Dinámicas**: Alterna entre hitboxes sólidas (`solid`) y transitables (`passable`) por estado, asegurando eyección física de jugadores para evitar asfixia.
- **Anclaje de Colisiones Físicas**: Vinculación automática con bloques de barrera o structure void en coordenadas relativas.
- **Mecánicas Interactivas para Sentarse y Recostarse**: Asigna puntos de asiento a muebles permitiendo que los jugadores se sienten o recuesten al hacer clic derecho.
- **Ciclo de Vida de Destrucción**: Asigna drops específicos y efectos de sonido al romper los props.

### 3. Gestor de Packs (Pack Manager)
Panel integral para organizar y compilar recursos visuales:
- **Explorador Jerárquico**: Inspecciona carpetas de texturas, modelos de bloques, definiciones de ítems y cadenas de traducción.
- **Configuración de Manifiesto**: Define `pack_format`, descripción y el ícono personalizado del paquete.
- **Compilación en un Clic**: Dispara el empaquetado en el backend, revisa el digest SHA-1 y valida los enlaces de descarga.

### 4. Gestión de Servidores Objetivo (Targets)
Consola centralizada para supervisar los servidores Paper vinculados:
- **Estado en Tiempo Real**: Visualiza la conexión WebSocket activa, latencia y versiones de plugin.
- **Acciones Rápidas**: Ordena recargas de resource packs, refresco de catálogos o pruebas de entrega a usuarios.
