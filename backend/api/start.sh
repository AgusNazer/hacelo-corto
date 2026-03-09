#!/bin/bash
set -e  # Exit on error

echo "🔄 Running database migrations..."

# Esperar a que la base de datos esté disponible
echo "⏳ Waiting for database..."
max_retries=30
retry=0
until python -c "from app.core.config import settings; from sqlalchemy import create_engine; create_engine(settings.DATABASE_URL).connect()" 2>/dev/null || [ $retry -eq $max_retries ]; do
    retry=$((retry+1))
    echo "⏳ Waiting for database... ($retry/$max_retries)"
    sleep 2
done

if [ $retry -eq $max_retries ]; then
    echo "❌ Database connection timeout"
    exit 1
fi

echo "✅ Database is ready"

# Correr migraciones
alembic upgrade head

if [ $? -eq 0 ]; then
    echo "✅ Migrations completed successfully"
else
    echo "❌ Migrations failed"
    exit 1
fi

echo "🚀 Starting API server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WEB_CONCURRENCY:-2}
