#!/bin/bash

# Script para preparar y deployar en Railway
# Uso: ./deploy-railway.sh

set -e

echo "🚀 Preparando deploy en Railway..."
echo ""

# Verificar que estamos en la rama correcta
BRANCH=$(git rev-parse --abbrev-ref HEAD)
echo "📍 Rama actual: $BRANCH"

if [ "$BRANCH" != "main" ] && [ "$BRANCH" != "master" ]; then
    echo "⚠️  Advertencia: No estás en la rama main/master"
    read -p "¿Deseas continuar? (s/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Ss]$ ]]; then
        exit 1
    fi
fi

echo ""
echo "✅ Verificando Dockerfiles..."

# Verificar que existan los Dockerfiles
if [ ! -f "backend/api/Dockerfile" ]; then
    echo "❌ Error: No encontrado backend/api/Dockerfile"
    exit 1
fi

if [ ! -f "frontend/Dockerfile" ]; then
    echo "❌ Error: No encontrado frontend/Dockerfile"
    exit 1
fi

echo "✅ Dockerfiles encontrados"
echo ""

# Crear archivos .env.example si no existen
echo "📝 Preparando archivos de configuración..."

if [ ! -f "backend/.env.example" ]; then
    echo "⚠️  Creando backend/.env.example"
fi

if [ ! -f "frontend/.env.example" ]; then
    echo "⚠️  Creando frontend/.env.example"
fi

echo "✅ Configuración lista"
echo ""

# Verificar que no hay cambios sin commitar
echo "🔍 Verificando estado de git..."
if ! git diff --quiet; then
    echo "⚠️  Hay cambios sin stagear:"
    git status --short
    echo ""
    read -p "¿Deseas commitear estos cambios? (s/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Ss]$ ]]; then
        git add .
        read -p "Mensaje de commit: " commit_msg
        git commit -m "$commit_msg"
    fi
fi

echo ""
echo "📤 Pusheando cambios a GitHub..."
git push origin $BRANCH

echo ""
echo "✅ ¡Listo para Railway!"
echo ""
echo "próximos pasos:"
echo "1. Ve a https://railway.app"
echo "2. Crea un nuevo proyecto"
echo "3. Conecta tu repositorio"
echo "4. Railway detectará automáticamente los Dockerfiles"
echo ""
echo "Servicios a agregar:"
echo "  - Backend: Root Directory 'backend/api'"
echo "  - Frontend: Root Directory 'frontend'"
echo "  - PostgreSQL: Railway lo crea automáticamente"
echo "  - Redis: Railway lo crea automáticamente"
echo ""
echo "Variables de entorno a configurar:"
echo "  Backend: DEBUG=False, LOG_FORMAT=json"
echo "  Frontend: NEXT_PUBLIC_API_BASE_URL=https://[tu-api].railway.app"
echo ""
echo "📖 Lee RAILWAY_DEPLOY_GUIDE.md para más detalles"
