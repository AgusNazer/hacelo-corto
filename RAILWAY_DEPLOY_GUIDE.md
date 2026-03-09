# 🚀 Guía de Deploy en Railway

## Descripción General

Este proyecto contiene:
- **Backend**: FastAPI con uvicorn (Puerto 8000)
- **Frontend**: Next.js (Puerto 3000)
- **Servicios**: PostgreSQL, Redis, MinIO

## Configuración para Railway

### 1. Preparar el Repositorio

```bash
# Asegúrate de estar en la rama main/master
git checkout main

# Pushea todos los cambios
git push origin main
```

### 2. Backend (FastAPI)

#### En Railway Console:

1. **Crear nuevo proyecto**
   - Click en "New Project"
   - Conectar tu repositorio GitHub

2. **Configurar servicio API**
   - Seleccionar el repositorio
   - En "Root Directory" poner: `backend/api`
   - Railway auto-detectará el Dockerfile

3. **Variables de Entorno**

```env
# Base de datos (Railway crea automáticamente)
DATABASE_URL=postgresql://[usuario]:[contraseña]@[host]:[puerto]/[db]

# Redis (agregar servicio)
REDIS_HOST=[host-redis-railway]
REDIS_PORT=6379

# MinIO / S3
MINIO_ENDPOINT=[tu-bucket-s3-endpoint]
MINIO_PUBLIC_ENDPOINT=[endpoint-publico]
MINIO_ACCESS_KEY=[tu-access-key]
MINIO_SECRET_KEY=[tu-secret-key]

# Configuración
DEBUG=False
LOG_FORMAT=json
ENVIRONMENT=production
```

#### Agregar dependencias como servicios:

**PostgreSQL:**
- Click en "+" → "Add Service" → "PostgreSQL"
- Railway inyectará `DATABASE_URL` automáticamente

**Redis:**
- Click en "+" → "Add Service" → "Redis"
- Railway inyectará las variables de conexión

**Para MinIO/S3:**
- Puedes usar AWS S3 directamente o un servicio compatible
- O deployar MinIO como servicio adicional si es necesario

### 3. Frontend (Next.js)

#### En Railway Console:

1. **Crear nuevo servicio**
   - Click en "+" → "New Service"
   - Seleccionar el repositorio
   - En "Root Directory" poner: `frontend`

2. **Configurar Build**
   - Railway auto-detectará el Dockerfile
   - Build command: (déjalo vacío, usa el Dockerfile)
   - Start command: (déjalo vacío, usa el Dockerfile)

3. **Variables de Entorno**

```env
# Si tu backend está en Railway
NEXT_PUBLIC_API_URL=https://[tu-api-domain].railway.app

# O si usas un dominio personalizado
NEXT_PUBLIC_API_URL=https://api.tudominio.com

# Puedes agregar otras variables según necesites
NODE_ENV=production
```

### 4. Conectar Servicios

En Railway, los servicios se comunican automáticamente por nombre:
- Backend accede a `db` como `postgresql://...`
- Backend accede a `redis` como `redis:6379`

### 5. Dominios Personalizados

#### Para el Backend:
1. En el servicio API → "Deployments"
2. Click en el dominio temporal (*.railway.app)
3. "Add Domain" → Usar tu dominio personalizado

#### Para el Frontend:
1. Mismo proceso en el servicio Frontend
2. Este será tu dominio principal

### 6. Health Checks

Los Dockerfiles incluyen health checks que Railway monitoreará:
- **Backend**: GET `/api/v1/health`
- **Frontend**: Verifica conexión a puerto 3000

### 7. Configuración de Recursos

#### Backend (FastAPI):
- **Memoria**: 512 MB recomendado
- **CPU**: 0.5 compartido
- **Réplicas**: 1 (aumentar si el tráfico lo requiere)

#### Frontend (Next.js):
- **Memoria**: 256-512 MB
- **CPU**: 0.5 compartido
- **Réplicas**: 1

#### Bases de datos:
- Usa el plan mínimo de Railway para desarrollo/pequeños proyectos
- Aumenta según necesidad

### 8. Variables de Entorno Sensibles

Usa Railway's secret management:
1. En la sección "Variables"
2. Marca como "Reference secret" para valores sensibles
3. Railway las inyectará en tiempo de deploy

**Importantes:**
```
MINIO_ACCESS_KEY=***
MINIO_SECRET_KEY=***
DATABASE_URL=*** (auto configurado)
```

### 9. Logs y Monitoreo

Railway proporciona:
- Logs en tiempo real por servicio
- Métricas de CPU, memoria, networking
- Webhooks para alertas
- Integración con Sentry para errores

### 10. Database Migrations

Para ejecutar migraciones de Alembic:

```bash
# En el servicio API, ejecuta:
railway run alembic upgrade head
```

O agrega como pre-deployment script en Railway.

### 11. Worker (Opcional)

Si deseas deployar el worker:
1. Crear nuevo servicio con `Root Directory`: `backend`
2. En "Dockerfile", selecciona `worker/Dockerfile`
3. Mismo acceso a PostgreSQL y Redis

---

## Desarrollo Local con Docker

Para probar localmente antes de deployar:

```bash
cd backend

# Crear archivo .env con las variables
cp .env.example .env

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## Troubleshooting

### El backend no se conecta a la BD
- Verifica que `DATABASE_URL` esté configurada correctamente
- Espera a que la BD esté lista (health checks)

### Frontend no puede conectar al backend
- Verifica `NEXT_PUBLIC_API_URL` apunta al dominio correcto de Railway
- Verifica CORS en el backend

### MinIO/S3 no funciona
- Verifica credenciales de acceso
- Asegúrate que los buckets existen

---

**Última actualización**: Marzo 2026
