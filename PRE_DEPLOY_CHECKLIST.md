# ✅ Pre-Deploy Checklist para Railway

Antes de deployar en Railway, asegúrate de completar todos estos pasos.

## 🔧 Configuración Local

- [ ] He revisado que los Dockerfiles están actualizados
  - [ ] `backend/api/Dockerfile` - Multi-stage build
  - [ ] `frontend/Dockerfile` - Multi-stage build
  
- [ ] He probado localmente con Docker Compose
  ```bash
  cd backend
  docker-compose up -d
  # Verifica que todo funciona
  docker-compose down
  ```

- [ ] He creado/actualizado los archivos de configuración
  - [ ] `backend/.env.example`
  - [ ] `frontend/.env.example`
  - [ ] `RAILWAY_DEPLOY_GUIDE.md`

## 📝 Código y Git

- [ ] Todos los cambios están commiteados
  ```bash
  git status  # debe estar limpio
  ```

- [ ] He pusheado los cambios a GitHub
  ```bash
  git push origin main
  ```

- [ ] La rama está protegida y solo tengo acceso
  - [ ] README.md está actualizado
  - [ ] Documentación está al día

## 🔐 Secretos y Variables

- [ ] He identificado todas las variables sensibles:
  - [ ] `DATABASE_URL`
  - [ ] `MINIO_ACCESS_KEY`
  - [ ] `MINIO_SECRET_KEY`
  - [ ] Google OAuth credentials (si aplica)
  - [ ] Stripe/Sendgrid API keys (si aplica)

- [ ] He creado un documento privado con valores de producción
  - [ ] No está en Git
  - [ ] Está guardado en un lugar seguro

## 🏗️ Arquitectura Railway

- [ ] He planeado los servicios a usar:
  - [ ] Backend API (FastAPI)
  - [ ] Frontend (Next.js)
  - [ ] PostgreSQL Database
  - [ ] Redis Cache
  - [ ] S3/MinIO (si lo necesito)

- [ ] He definido los dominios:
  - [ ] API: `api.tudominio.com` o `[proyecto]-api.railway.app`
  - [ ] Frontend: `tudominio.com` o `[proyecto].railway.app`

## 💾 Base de Datos

- [ ] Las migraciones de Alembic están actualizadas
  ```bash
  cd backend/api
  alembic upgrade head  # Verifica que funciona
  ```

- [ ] He testeado la restauración de backups (si hay datos importantes)

- [ ] He documentado el schema de la BD

## 🚀 Deployment en Railway

### Crear Proyecto

- [ ] Me he registrado en https://railway.app
- [ ] He conectado mi cuenta de GitHub
- [ ] He creado un nuevo proyecto llamado "Hacelo Corto"

### Configurar Servicios

#### Backend API
- [ ] Root Directory: `backend/api`
- [ ] Build method: Dockerfile
- [ ] Port: 8000
- [ ] Health check: `/api/v1/health`

#### Frontend
- [ ] Root Directory: `frontend`
- [ ] Build method: Dockerfile
- [ ] Port: 3000
- [ ] Health check: `/`

#### Base de Datos
- [ ] He agregado PostgreSQL
- [ ] He agregado Redis
- [ ] He verificado que Railway inyecta `DATABASE_URL` automáticamente

### Variables de Entorno

#### Backend
```
DEBUG=False
LOG_FORMAT=json
ENVIRONMENT=production
REDIS_HOST=[railway-redis-host]
REDIS_PORT=6379
MINIO_ENDPOINT=[your-s3-bucket]
MINIO_PUBLIC_ENDPOINT=[public-s3-url]
MINIO_ACCESS_KEY=***
MINIO_SECRET_KEY=***
```

#### Frontend
```
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=https://[api-domain].railway.app
NEXT_PUBLIC_DEFAULT_LOCALE=es
```

- [ ] He configurado DATABASE_URL en Railway
- [ ] He configurado todos los secrets sensibles

## ✨ Optimizaciones

- [ ] Los Dockerfiles usan multi-stage build
- [ ] Las imágenes están basadas en Alpine (más pequeñas)
- [ ] He definido resource limits apropiados
- [ ] He habilitado health checks
- [ ] He configurado restart policies

## 🔍 Testing Pre-Producción

- [ ] He verificado que el Dockerfile funciona localmente
  ```bash
  docker build -t hacelo-api:latest backend/api
  docker run -p 8000:8000 hacelo-api:latest
  ```

- [ ] El frontend se construye correctamente
  ```bash
  docker build -t hacelo-frontend:latest frontend
  docker run -p 3000:3000 hacelo-frontend:latest
  ```

- [ ] Las variables de entorno están configuradas correctamente

## 🌐 Dominios y DNS

- [ ] He registrado/configurado mis dominios (si los tengo)
- [ ] He actualizado DNS pointing a Railway
- [ ] He configurado SSL/TLS certificates
- [ ] He testeado HTTPS

## 📊 Monitoreo y Logging

- [ ] He habilitado logs en Railway Console
- [ ] He configurado alertas para fallos de deploy
- [ ] He documentado los logs importantes
- [ ] He habilitado métricas de uso

## 📚 Documentación

- [ ] He actualizado el README con instrucciones de deploy
- [ ] He documentado cómo manejar migraciones en producción
- [ ] He documentado cómo hacer rollback si es necesario
- [ ] He crear runbook para incidents comunes

## 🚨 Seguridad

- [ ] Las credenciales no están en el código
- [ ] Los Dockerfiles no exponen información sensible
- [ ] He habilitado autenticación en MinIO/S3
- [ ] He configurado CORS correctamente en el backend
- [ ] He habilitado HTTPS en todos los endpoints

## 🎯 Go/No-Go Decision

**¿Listo para deployar?**

- [ ] Sí, todos los checks están completos
- [ ] No, necesito revisar:
  - [ ] ...

---

## 📞 Proceso de Deploy

1. **Crear proyecto en Railway**
   ```bash
   # O usa el website
   ```

2. **Conectar repositorio**
   - Selecciona tu repo de GitHub
   - Autoriza Railway

3. **Agregar servicios**
   - Backend (root: backend/api)
   - Frontend (root: frontend)
   - PostgreSQL
   - Redis

4. **Configurar variables**
   - Copia las variables del checklist anterior
   - Marca sensibles como "Reference secret"

5. **Deploy**
   - Railway auto-deploya cuando pusheas a main
   - Verifica logs en Railway Console

6. **Verifica salud**
   ```bash
   curl https://[tu-api].railway.app/api/v1/health
   curl https://[tu-frontend].railway.app
   ```

## 📞 Soporte

Si algo falla:
1. Revisa logs en Railway Console
2. Verifica variables de entorno
3. Revisa `RAILWAY_DEPLOY_GUIDE.md`
4. Revisa `DOCKER_CONFIG_SUMMARY.md`

---

**Fecha de review**: Marzo 2026
