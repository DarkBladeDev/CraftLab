---
title: Arquitectura de Packages Compartidos
description: Visión general, arquitectura y registro de paquetes compartidos del monorepo CraftLab.
sidebar:
  order: 1
  label: Visión General de Packages
---

# Arquitectura de Packages Compartidos

El monorepo de CraftLab incluye bibliotecas modulares e independientes ubicadas en [`packages/`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages). Estos paquetes proporcionan contratos de dominio y servicios reutilizables para los diferentes componentes de la plataforma (`CraftLab-backend`, `CraftLab-ctl`, herramientas de compilación y entornos de ejecución de agentes).

---

## Registro de Packages

| Package | Directorio | Versión | Estado | Descripción | Documentación |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`craftlab_security`** | [`packages/craftlab_security`](https://github.com/DarkBladeDev/CraftLab/tree/main/packages/craftlab_security) | `0.1.0` | **Activo** | Contrato canónico de eventos de seguridad, sanitización universal de datos y sumidero SQLite en modo WAL. | [craftlab_security](craftlab-security.md) |

---

## Directrices de Arquitectura en el Monorepo

Todos los paquetes desarrollados bajo `packages/` deben cumplir con los siguientes estándares:

### 1. Cero Dependencias Circulares y Mínimo Acoplamiento
- Los paquetes compartidos **nunca** deben importar módulos internos de aplicación de `CraftLab-backend`, `CraftLab-ctl` o `CraftLab-frontend`.
- Deben depender exclusivamente de la biblioteca estándar de Python o de dependencias ligeras aprobadas (ej. `pydantic >= 2.0.0`).

### 2. Estructura Estándar PEP 621
Cada directorio de paquete bajo `packages/<nombre_paquete>/` debe cumplir con los estándares PEP 621:

```text
packages/<nombre_paquete>/
├── pyproject.toml              # Configuración de compilación (PEP 621)
├── README.md                   # Resumen y guía de inicio rápido
├── src/
│   └── <nombre_paquete>/
│       ├── __init__.py         # Exportaciones de la API pública
│       ├── py.typed            # Marcador de tipado en línea PEP 561
│       └── ...                 # Módulos de implementación
└── tests/
    ├── __init__.py
    └── test_*.py               # Suite de pruebas unitarias hermética
```

### 3. Aprovisionamiento Multi-Entorno Virtual
Dado que CraftLab mantiene entornos virtuales dedicados (`CraftLab-backend/.venv` y entornos aislados de ejecución/release en `releases/v0.3.0/.venv` / `CraftLab-ctl`), los paquetes compartidos deben aprovisionarse en modo editable en todos los entornos objetivo:

```bash
pip install -e packages/<nombre_paquete>
```

### 4. Pruebas Unitarias Herméticas e Inmunidad Externa
Cada paquete debe incluir pruebas unitarias completas bajo `packages/<nombre_paquete>/tests/` que se ejecuten y pasen en total aislamiento, sin requerir demonios activos, sockets de red ni servicios en segundo plano.
