# Factus MCP Server 🇨🇴

**Servidor MCP (Model Context Protocol) para facturación electrónica colombiana integrada con Factus (DIAN).**

Permite que agentes de IA (Claude, OpenCode, etc.) creen, consulten y gestionen facturas electrónicas, notas crédito, documentos soporte y notas de ajuste a través de la API de Factus, usando el protocolo estándar MCP.

---

## ✨ Funcionalidades

| Tipo | Operaciones |
|------|------------|
| **Facturas** | Crear (raw y con numbering), consultar por referencia/número, listar, descargar PDF/XML |
| **Notas Crédito** | Crear, consultar, listar, descargar PDF/XML |
| **Documentos Soporte** | Crear, consultar, listar, descargar PDF/XML |
| **Notas de Ajuste** | Crear, consultar, listar, descargar PDF/XML |
| **Clientes** | CRUD completo + búsqueda por identificación/nombre/email |
| **Productos** | CRUD completo + búsqueda por código/nombre |
| **Establecimientos** | CRUD completo |
| **Rangos de Numeración** | Sincronizar desde Factus, consultar activos, obtener default |
| **Consultas** | Información de empresa, códigos DIAN |
| **Descargas** | PDF y XML de cada tipo de documento |

---

## 🏗️ Arquitectura

```
src/
├── core/                 # Configuración (pydantic-settings), constantes DIAN
├── schemas/              # Modelos SQLModel (7 tablas) + DTOs
├── infrastructure/       # DB asíncrona, FactusClient (OAuth2), Repositories
├── services/             # Lógica de negocio (mappers, validadores, servicios)
├── mcp_server/           # Capa MCP (tools, resources, prompts)
└── main.py               # Entry point
```

### Stack Tecnológico

| Tecnología | Versión | Rol |
|-----------|---------|-----|
| Python | ≥3.14 | Runtime |
| uv | — | Package manager |
| SQLModel | 0.0.38+ | ORM + modelos Pydantic |
| aiosqlite | 0.22+ | Driver SQLite asíncrono |
| httpx | 0.28+ | Cliente HTTP asíncrono (con OAuth2 transparente) |
| MCP SDK | 1.27+ | Protocolo MCP (transporte SSE) |
| uvicorn | 0.47+ | Servidor ASGI |
| pydantic-settings | 2.14+ | Configuración por entorno |

---

## 🚀 Quick Start (Local)

### Prerrequisitos

- Python ≥3.14
- [uv](https://docs.astral.sh/uv/)

### Instalación

```bash
# Clonar
git clone https://github.com/pedropira/factus-mcp-server-challenge-.git
cd factus-mcp-server

# Crear entorno y sincronizar dependencias
uv sync

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales de Factus
```

### Ejecutar

```bash
# Modo desarrollo (con MCP Inspector)
uv run mcp dev main.py

# Modo producción (SSE — para Railway u otros hosting)
uv run mcp run main.py --transport sse --port 8000

# Modo stdio (para integración local con MCP clients)
uv run mcp run main.py
```

### Tests

```bash
# Tests unitarios
uv run pytest

# Tests de integración (requieren credenciales Factus en .env)
uv run pytest -m integration
```

---

## 🌐 Despliegue en Railway

### 1. Preparar el proyecto

El repositorio ya incluye:
- ✅ `Dockerfile` — Multi-stage build con Python 3.14 slim + uv
- ✅ `.dockerignore` — Excluye archivos innecesarios del build
- ✅ `pyproject.toml` — Dependencias completas

### 2. Conectar con Railway

**Opción A: Desde GitHub (recomendado)**

1. Ve a [Railway.app](https://railway.app) y haz login con GitHub
2. Click en **New Project** → **Deploy from GitHub repo**
3. Seleccioná `pedropira/factus-mcp-server-challenge-`
4. Railway detecta automáticamente el `Dockerfile`

**Opción B: Desde CLI**

```bash
# Instalar Railway CLI
npm i -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

### 3. Configurar variables de entorno

En el dashboard de Railway, agregá estas variables en **Variables**:

| Variable | Descripción | Ejemplo |
|----------|-------------|---------|
| `FACTUS_EMAIL` | Email de tu cuenta Factus | `tu-email@ejemplo.com` |
| `FACTUS_PASSWORD` | Contraseña de Factus | `tu-contraseña` |
| `FACTUS_API_KEY` | API Key de Factus | `tu-api-key` |
| `FACTUS_ENV` | Entorno (`sandbox` o `production`) | `sandbox` |
| `DATABASE_URL` | URL de base de datos | `sqlite+aiosqlite:///factus.db` |

> **Importante**: No incluyas el `.env` en el repo — Railway usa su propio sistema de variables.

### 4. Obtener la URL

Railway asigna una URL tipo `https://factus-mcp-server-challenge.up.railway.app`.

Para conectar un cliente MCP (OpenCode, Claude, etc.):

```json
{
  "factus": {
    "type": "remote",
    "url": "https://factus-mcp-server-challenge.up.railway.app/sse",
    "enabled": true
  }
}
```

### 5. Verificar salud

```bash
curl https://tu-app.up.railway.app/health
```

---

## 🔧 Variables de Entorno

| Variable | Requerida | Default | Descripción |
|----------|-----------|---------|-------------|
| `FACTUS_EMAIL` | ✅ | — | Email de la cuenta Factus |
| `FACTUS_PASSWORD` | ✅ | — | Contraseña de Factus |
| `FACTUS_API_KEY` | ✅ | — | API Key (opcional en sandbox) |
| `FACTUS_ENV` | ❌ | `sandbox` | `sandbox` o `production` |
| `DATABASE_URL` | ❌ | `sqlite+aiosqlite:///factus.db` | URL de conexión a DB |

---

## 🧪 Resultados de Auditoría (26/05/2026)

Herramientas probadas contra la API sandbox de Factus en vivo:

| Fase | Operaciones | Resultado |
|------|------------|-----------|
| Setup | Crear cliente, producto, establecimiento, rango | ✅ 4/4 |
| Consultas | Get, search, list, company info | ✅ 10/10 |
| Facturas | Raw + with numbering, get, list | ✅ 5/5 |
| Documentos | DS, NC, NA — crear, get, list | ✅ 9/9 |
| Descargas | PDF + XML (4 tipos de documento) | ✅ 8/8 |
| Updates | Customer, product, establishment | ✅ 3/3 |
| Deletes locales | Customer, product, establishment | ✅ 3/3 |
| **Total CREAR/LEER** | **27 endpoints** | **✅ 100%** |

> ⚠️ **Nota**: La API de Factus no expone endpoints DELETE para documentos (invoices, support documents, credit notes devuelven 405). Solo los deletes de entidades locales funcionan.

---

## 📋 Herramientas MCP Disponibles

### Entidades Locales
- `create_customer`, `get_customer`, `update_customer`, `delete_customer`, `search_customers`
- `create_product`, `get_product`, `get_product_by_code`, `update_product`, `delete_product`, `search_products`
- `create_establishment`, `get_establishment`, `update_establishment`, `delete_establishment`, `list_establishments`
- `create_numbering_range`, `get_active_numbering_ranges`, `get_default_numbering_range`, `fetch_numbering_ranges_from_factus`

### Documentos Electrónicos
- `create_invoice`, `create_invoice_with_numbering`, `get_invoice_by_reference`, `get_invoice_by_number`, `list_invoices`
- `create_support_document`, `get_support_document`, `list_support_documents`
- `create_credit_note`, `get_credit_note`, `list_credit_notes`
- `create_adjustment_note`, `get_adjustment_note`, `list_adjustment_notes`

### Descargas
- `download_invoice_pdf`, `download_invoice_xml`
- `download_support_document_pdf`, `download_support_document_xml`
- `download_credit_note_pdf`, `download_credit_note_xml`
- `download_adjustment_note_pdf`, `download_adjustment_note_xml`

### Utilidades
- `get_company_info`

---

## 📄 Licencia

MIT
