# Multi-stage build para optimizar tamaño de imagen
FROM python:3.11-slim as builder

WORKDIR /build

# Instalar dependencias del sistema necesarias para compilación
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .

# Crear directorio para wheels
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels torch==2.1.0+cpu torchaudio==2.1.0+cpu --index-url https://download.pytorch.org/whl/cpu \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels openai-whisper==20250625 \
    && pip wheel --no-cache-dir --no-deps --wheel-dir /build/wheels -r requirements.txt

# Stage final
FROM python:3.11-slim

WORKDIR /app

# Instalar solo dependencias de runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Copiar wheels del builder
COPY --from=builder /build/wheels /wheels

# Instalar dependencias desde wheels
RUN pip install --no-cache /wheels/*

# Copiar código de la aplicación
COPY . .

# Crear usuario non-root para seguridad
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Exponer puerto
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')" || exit 1

# Comando de inicio - SIN --reload para producción
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
