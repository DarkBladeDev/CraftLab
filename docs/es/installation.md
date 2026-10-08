---
title: Instalación y Primeros Pasos
description: Prerrequisitos, inicio rápido para desarrolladores y guía de despliegue en producción de CraftLab.
sidebar:
  order: 2
---

# Instalación y Primeros Pasos

Esta guía detalla los prerrequisitos del sistema, el flujo de trabajo de desarrollo local y el proceso de despliegue en producción para CraftLab.

---

## Prerrequisitos

Antes de configurar CraftLab, asegúrate de tener instalado el siguiente software en tu entorno:

| Componente | Versión Mínima | Notas |
| :--- | :--- | :--- |
| **Java Development Kit** | JDK 21 (Temurin u OpenJDK) | Requerido para compilar y ejecutar `CraftLab-plugin` |
| **Python** | 3.11+ | Requerido para `CraftLab-backend` y `CraftLab-ctl` |
| **Node.js** | 20.x LTS | Requerido para el Web Studio (`CraftLab-frontend`) y el panel web |
| **Servidor Minecraft Paper** | 1.21.1+ | Entorno de ejecución del servidor de juegos con Java 21 |
| **PacketEvents** | 2.14.0+ | Plugin de dependencia obligatoria instalado en el servidor Paper |

---

## Inicio Rápido en Entorno de Desarrollo

La forma más veloz de iniciar la plataforma completa en tu máquina de desarrollo es mediante el script de automatización PowerShell:

```powershell
.\scripts\dev.ps1
```

### Acciones automáticas ejecutadas por `dev.ps1`:
1. **Compila el Plugin de Paper**: Genera `CraftLab-plugin/build/libs/CraftLab-plugin-1.0.0-SNAPSHOT.jar` mediante Gradle.
2. **Inicializa el Backend**: Verifica el entorno virtual `CraftLab-backend\.venv` y migra las tablas de base de datos.
3. **Inicia Backend y Gateway WebSocket**: Arranca FastAPI en `http://127.0.0.1:8000`.
4. **Inicia el Web Studio Frontend**: Arranca el servidor de desarrollo Vite en `http://localhost:3000`.
5. **Abre el Navegador**: Lanza tu navegador predeterminado apuntando a `http://localhost:3000`.

### Modos de Ejecución en Desarrollo

- **Solo Servicios Web** (sin compilar ni desplegar el JAR del plugin):
  ```powershell
  .\scripts\dev.ps1 -Mode web-only
  ```

- **Auto-Despliegue a Servidor Paper Local**:
  ```powershell
  .\scripts\dev.ps1 -PaperServerDir "C:\minecraft\paper-server"
  ```
  *Copia automáticamente el JAR compilado a la carpeta `plugins/`, genera el archivo de configuración por defecto si no existe y arranca el servidor Paper en una consola interactiva.*

- **Limpieza y Reinicio de Datos** (elimina base de datos de prueba y caché de packs):
  ```powershell
  .\scripts\dev.ps1 -CleanData
  ```

- **Detener Procesos en Ejecución**:
  ```powershell
  .\scripts\dev.ps1 -Mode stop
  ```

---

## Despliegue en Servidores de Producción

En entornos de producción, CraftLab se despliega mediante paquetes oficiales de release (`craftlab-v<version>.tar.gz`) administrados por el supervisor `craftctl`.

### 1. Descarga y Descompresión

Descarga el release correspondiente desde [GitHub Releases](https://github.com/DarkBladeDev/CraftLab/releases):

```bash
mkdir -p /opt/craftlab
cd /opt/craftlab
tar -xzf craftlab-v0.3.3.tar.gz
```

### 2. Configurar Variables de Entorno

Copia la plantilla `.env.example` a `.env` y configura tus credenciales seguras:

```bash
cp .env.example .env
nano .env
```

Parámetros clave a personalizar:
- `CRAFTLAB_SECRET_KEY`: Cadena aleatoria robusta para firma de tokens JWT.
- `CRAFTLAB_GATEWAY_SECRET`: Contraseña compartida para la conexión WebSocket del plugin del servidor.
- `CRAFTLAB_HOST` / `CRAFTLAB_PORT`: Interfaz de red y puerto de enlace (por defecto `127.0.0.1:8000`).

### 3. Instalar y Controlar mediante `craftctl`

Instala el paquete Python complementario:

```bash
pip install craftlab_ctl-0.3.3-py3-none-any.whl
```

Ejecuta el diagnóstico del sistema:

```bash
craftctl doctor
```

Inicia los servicios en segundo plano:

```bash
craftctl start
```

Comprueba el estado de la plataforma:

```bash
craftctl status
```
