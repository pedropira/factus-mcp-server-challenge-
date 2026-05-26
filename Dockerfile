FROM python:3.14-slim AS builder

# ── Build tools (necesarios si alguna dependencia compila C, ej: asyncpg sin wheel) ──
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# ── Instalar uv ─────────────────────────────────────────────────────────────
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# ── Cache de dependencias (capa independiente del código) ───────────────────
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-editable

# ── Imagen final ────────────────────────────────────────────────────────────
FROM python:3.14-slim

# Variables de entorno para producción
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENV=production

WORKDIR /app

# Copiar solo lo necesario desde builder
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copiar el código fuente
COPY . .

# Puerto que Railway asigna (se sobrescribe con $PORT)
EXPOSE 8080

# Railway provee el puerto via $PORT; main.py lee esa variable
CMD python main.py
