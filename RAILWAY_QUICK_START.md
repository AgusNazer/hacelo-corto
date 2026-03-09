# 🚀 Quick Start - Deploy en Railway

**Tiempo estimado: 15 minutos**

## 1️⃣ Preparativos (5 min)

### A. Verifica que todo está ready

```bash
# Estás en la raíz del proyecto
pwd
# /home/agusdev/projectos/HaceloCorto/hacelo-corto

# Verifica Dockerfiles existen
test -f backend/api/Dockerfile && echo "✅ Backend Dockerfile OK"
test -f frontend/Dockerfile && echo "✅ Frontend Dockerfile OK"

# Verifica git está limpio
git status
# ✅ Should say "working tree clean"
```

### B. Crea una cuenta en Railway (si no la tienes)

- Ve a https://railway.app
- Sign up con GitHub
- Autoriza Railway

---

## 2️⃣ Crear Proyecto en Railway (3 min)

### Paso 1: New Project

1. https://railway.app → "New Project"
2. "Deploy from GitHub repo"
3. Selecciona tu repo `hacelo-corto`
4. Selecciona rama `main`

### Paso 2: Rail-way Auto-detecta

Railway detectará automáticamente:
- ✅ Dockerfile de Backend en `backend/api/`
- ✅ Dockerfile de Frontend en `frontend/`

Si no los ve, verifica:
- Los archivos existen
- Git está actualizado (`git push origin main`)

---

## 3️⃣ Configurar Servicios (5 min)

### Agregar Base de Datos

```
Railway Console → New Service → PostgreSQL
└─ Auto-inyecta DATABASE_URL ✅
```

### Agregar Redis

```
Railway Console → New Service → Redis
```

### Configurar Backend

```
Root Directory: backend/api
Build: Automático ✅ (detecta Dockerfile)
Port: 8000
```

**Variables:**
```
DEBUG=False
LOG_FORMAT=json
MINIO_ENDPOINT=[tu-s3-bucket o servicio minio]
MINIO_ACCESS_KEY=***
MINIO_SECRET_KEY=***
REDIS_HOST=redis       (Railway lo resuelve)
```

### Configurar Frontend

```
Root Directory: frontend
Build: Automático ✅ (detecta Dockerfile)
Port: 3000
```

**Variables:**
```
NODE_ENV=production
NEXT_PUBLIC_API_BASE_URL=https://[api-domain].railway.app
NEXT_PUBLIC_DEFAULT_LOCALE=es
```

**Para obtener [api-domain]:**
1. Backend service → Deployments
2. Clickea el dominio temporal railway.app
3. Cópialo
4. Ústalo en NEXT_PUBLIC_API_BASE_URL

---

## 4️⃣ Deploy (Auto-automático)

```bash
# Push tus cambios
git push origin main

# Railway hace todo automáticamente ✅
# 1. Detecta cambios
# 2. Build de imágenes
# 3. Deploy de servicios
# 4. Health checks
```

**Monitorea en Railway Console:**
```
[Proyecto] → Deployments → Logs
```

---

## 5️⃣ Verify (2 min)

### Test Backend

```bash
# Reemplaza con tu dominio
curl https://[tu-api].railway.app/api/v1/health

# Esperado:
# 200 OK + JSON response
```

### Test Frontend

```bash
# Abre en navegador
https://[tu-frontend].railway.app

# Debe cargar tu página
```

---

## ✅ ¡Listo!

Tu app está corriendo en Railway.

**URLs:**
- API: `https://[api-domain].railway.app`
- Frontend: `https://[frontend-domain].railway.app`

---

## 📝 Próximos Pasos (Opcionales)

### Agregar Dominio Personalizado

```
Backend service → Deployments → Domain
└─ "Add Domain" → tudominio.com/api

Frontend service → Deployments → Domain
└─ "Add Domain" → tudominio.com
```

### Ejecutar Migraciones

```bash
# Si aún no lo has hecho
cd backend/api
alembic upgrade head
```

### Monitore & Alertas

```
Railway Console → [Proyecto] → Settings → Alerts
└─ Configura Slack/Discord para errores
```

---

## 🆘 Algo No Funciona?

### Check 1: Revisar Logs

```
Railway Console → [Servicio] → Logs
```

### Check 2: Verificar Variables

```
Railway Console → [Servicio] → Variables
└─ Asegúrate que DATABASE_URL existe
└─ Asegúrate que REDIS_HOST=redis
└─ Asegúrate que NEXT_PUBLIC_API_BASE_URL es correcto
```

### Check 3: Verifica Health Check

```
Railway Console → [Servicio] → Health
└─ Si falla, significa que la app no está lista
```

### Check 4: Leer Guíasdetalladas

- [RAILWAY_DEPLOY_GUIDE.md](./RAILWAY_DEPLOY_GUIDE.md) - Guía completa
- [RAILWAY_TROUBLESHOOTING.md](./RAILWAY_TROUBLESHOOTING.md) - Problemas comunes

---

## 💰 Costos Estimados

| Servicio | Precio/mes |
|----------|-----------|
| Backend API | ~$7 |
| Frontend | ~$5 |
| PostgreSQL | ~$20 |
| Redis | ~$5 |
| **Total** | **~$37** |

*(Precios aproximados, pueden variar)*

Para reducir costos:
- Usa plan gratuito para desarrollo
- Scale up solo en producción

---

## 🎓 Documentación Completa

- 📖 [RAILWAY_DEPLOY_GUIDE.md](./RAILWAY_DEPLOY_GUIDE.md)
- 📖 [DOCKER_CONFIG_SUMMARY.md](./DOCKER_CONFIG_SUMMARY.md)
- ✅ [PRE_DEPLOY_CHECKLIST.md](./PRE_DEPLOY_CHECKLIST.md)
- 🏗️ [RAILWAY_PROJECT_STRUCTURE.md](./RAILWAY_PROJECT_STRUCTURE.md)
- 🆘 [RAILWAY_TROUBLESHOOTING.md](./RAILWAY_TROUBLESHOOTING.md)

---

**¿Necesitas ayuda?** Revisa las guías o contacta soporte de Railway.

**Good luck! 🚀**
