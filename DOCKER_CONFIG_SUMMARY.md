# Docker Configuration Summary

## 📦 Cambios Realizados

### Backend (FastAPI) - `backend/api/Dockerfile`
✅ **Multi-stage build** - Reduce tamaño de imagen en ~60%
✅ **Optimizado para producción** - Sin `--reload`, con 4 workers
✅ **Health checks** - Monitoreo automático de disponibilidad
✅ **Usuario non-root** - Mayor seguridad
✅ **Wheels pre-compilados** - Instalación más rápida

### Frontend (Next.js) - `frontend/Dockerfile`
✅ **Multi-stage build** - Separación de build y runtime
✅ **Node 20 Alpine** - Imagen ligera (~150MB)
✅ **dumb-init** - Manejo correcto de signals
✅ **Usuario non-root** - Mayor seguridad
✅ **Health checks** - Verificación de disponibilidad

### Docker Compose - `backend/docker-compose.yml`
✅ **Health checks** - Servicios esperan a que otros estén listos
✅ **Variables configurables** - `.env` support para desarrollo
✅ **Named volumes** - Persistencia de datos
✅ **Network aislada** - Mejor seguridad local
✅ **Alpine linux** - Imágenes más pequeñas (Redis, PostgreSQL, Node.js)

---

## 🚀 Quick Start - Desarrollo Local

```bash
# 1. Ir al backend
cd backend

# 2. Crear archivo .env (opcional, usa defaults si no existe)
cp .env.example .env

# 3. Iniciar servicios
docker-compose up -d

# 4. Ver logs
docker-compose logs -f api

# 5. Verificar salud
docker-compose ps

# 6. Detener todo
docker-compose down
```

**URLs locales:**
- API: http://localhost:8000
- MinIO Console: http://localhost:9001
- PostgreSQL: localhost:5432
- Redis: localhost:6379

---

## 🌐 Railway Deploy

### Paso 1: Push a GitHub
```bash
git push origin main
```

### Paso 2: Crear proyecto en Railway
1. https://railway.app → New Project
2. Conectar repositorio GitHub
3. Railway detectará automáticamente los Dockerfiles

### Paso 3: Agregar servicios
**Backend:**
- Root Directory: `backend/api`
- Puerto: 8000

**Frontend:**
- Root Directory: `frontend`
- Puerto: 3000

**Bases de datos:**
- PostgreSQL (Railway auto-inyecta DATABASE_URL)
- Redis

### Paso 4: Variables de entorno
```
# Backend
DATABASE_URL=postgresql://[auto]
REDIS_HOST=[redis-railway]
MINIO_ENDPOINT=[tu-s3-bucket]
DEBUG=False
```

```
# Frontend
NEXT_PUBLIC_API_BASE_URL=https://[tu-api].railway.app
NODE_ENV=production
```

### Paso 5: Deploy
```bash
git push origin main
# Railway auto-deploya cuando detecta cambios
```

---

## 🔍 Verificación Post-Deploy

```bash
# Verificar salud del backend
curl https://[tu-api].railway.app/api/v1/health

# Verificar frontend
curl https://[tu-frontend].railway.app

# Ver logs en tiempo real
# Desde Railway Console → Deployments → Logs
```

---

## 📊 Estimaciones de Recursos

| Servicio | Memoria | CPU | Costo aproximado |
|----------|---------|-----|-----------------|
| Backend | 512 MB | 0.5 | $7/mes |
| Frontend | 256 MB | 0.5 | $5/mes |
| PostgreSQL | 1 GB | 1 | $20/mes |
| Redis | 256 MB | 0.5 | $5/mes |
| **Total** | **2 GB** | **2.5** | **~$37/mes** |

*Precios pueden variar según Railway*

---

## ⚠️ Consideraciones Importantes

1. **Cold starts**: Primera solicitud tarda ~2-3s (normal en Railway)
2. **Migraciones**: Ejecutar `alembic upgrade head` antes del primer deploy
3. **Secretos**: Usar Railway's secret management para credenciales
4. **Backups**: Railway auto-backupea PostgreSQL, configura retención
5. **CORS**: Ajusta en backend según dominio del frontend

---

## 🆘 Troubleshooting

**El frontend no ve el backend:**
```
❌ NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 (incorrecto en producción)
✅ NEXT_PUBLIC_API_BASE_URL=https://tu-api.railway.app (correcto)
```

**Base de datos no conecta:**
```
Verifica DATABASE_URL está sin espacios y tiene el formato correcto:
postgresql://user:password@host:port/dbname
```

**Worker no procesa jobs:**
```
Revisa REDIS_HOST apunta a la instancia correcta en Railway
Verifica that workers pod tiene acceso a la base de datos
```

---

**Última actualización**: Marzo 2026
