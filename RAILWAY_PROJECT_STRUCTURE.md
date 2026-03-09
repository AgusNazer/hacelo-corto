# 🏗️ Estructura del Proyecto para Railway

Este documento explica la estructura del proyecto y cómo Railway lo encuentra.

## 📂 Estructura del Repositorio

```
hacelo-corto/
├── backend/
│   ├── api/
│   │   ├── Dockerfile           ⭐ Backend API (FastAPI)
│   │   ├── requirements.txt
│   │   ├── app/
│   │   │   ├── main.py          Punto de entrada de la app
│   │   │   ├── models/          Modelos de BD
│   │   │   ├── schemas/         Schemas Pydantic
│   │   │   ├── api/             Rutas de la API
│   │   │   ├── services/        Lógica de negocio
│   │   │   └── ...
│   │   └── alembic/             Migraciones de BD
│   │
│   ├── worker/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── worker.py        Worker para procesar jobs
│   │       └── pipeline.py
│   │
│   ├── docker-compose.yml       Para desarrollo local
│   ├── .env.example
│   └── README.md
│
├── frontend/
│   ├── Dockerfile               ⭐ Frontend (Next.js)
│   ├── package.json
│   ├── src/
│   │   ├── app/
│   │   │   ├── page.tsx         Página principal
│   │   │   ├── layout.tsx
│   │   │   ├── app/             App directory
│   │   │   ├── auth/            Auth pages
│   │   │   └── ...
│   │   ├── components/          Componentes React
│   │   ├── services/            API clients
│   │   ├── store/               Zustand stores
│   │   └── ...
│   ├── .env.example
│   └── README.md
│
├── docs/                        Documentación general
├── RAILWAY_DEPLOY_GUIDE.md      📖 Guía de deploy
├── DOCKER_CONFIG_SUMMARY.md     📖 Resumen de Docker
├── PRE_DEPLOY_CHECKLIST.md      ✅ Checklist
├── deploy-railway.sh            🚀 Script de deployment
├── railway.json                 ⚙️ Config de railway
└── README.md                    Documentación principal
```

## 🎯 Cómo Railway Encuentra Tus Servicios

### Para el Backend

Railway buscará `Dockerfile` en:
1. `backend/api/Dockerfile` ← ✅ **Aquí lo encontrará**
2. `backend/Dockerfile` (si existe)
3. `Dockerfile` (en la raíz del repo)

**Configuración en Railway:**
- Root Directory: `backend/api`
- Build: Automático (detecta Dockerfile)

### Para el Frontend

Railway buscará `Dockerfile` en:
1. `frontend/Dockerfile` ← ✅ **Aquí lo encontrará**
2. Detecta `package.json` como app Node.js

**Configuración en Railway:**
- Root Directory: `frontend`
- Build: Automático (detecta Dockerfile)

## 🔄 Flujo de Build

### Backend

```
Git Push → Railway Webhook
         ↓
   Detecta cambios en backend/api
         ↓
   Build contexto: backend/api/
   Dockerfile: backend/api/Dockerfile
         ↓
   Instala dependencias (requirements.txt)
         ↓
   Copia código
         ↓
   Build completo
         ↓
   Start: uvicorn app.main:app ...
```

### Frontend

```
Git Push → Railway Webhook
         ↓
   Detecta cambios en frontend
         ↓
   Build contexto: frontend/
   Dockerfile: frontend/Dockerfile
         ↓
   npm ci (instala dependencias)
         ↓
   npm run build (construye Next.js)
         ↓
   Build completo
         ↓
   Start: next start -p 3000
```

## 📦 Dependencias

### Backend (Python)
Se instalan desde `backend/api/requirements.txt`:
- FastAPI + Uvicorn
- SQLAlchemy + Psycopg2 (PostgreSQL)
- Redis client
- Pydantic
- OAuth (Google, etc)
- Y más...

### Frontend (Node.js)
Se instalan desde `frontend/package.json`:
- Next.js 16.1.6
- React 19
- next-intl (internacionalización)
- Zustand (state management)
- Y más...

## 🔐 Variables de Entorno

Las variables se inyectan en tiempo de run:

### Backend
Desde Railway Console se configura:
```
DEBUG=False
REDIS_HOST=redis-railway-url
DATABASE_URL=postgresql://...  (auto-inyectado)
```

### Frontend
```
NEXT_PUBLIC_API_BASE_URL=https://tu-api.railway.app
NODE_ENV=production
```

## 🏥 Health Checks

Railway monitoreará:

### Backend
- **Endpoint**: GET `/api/v1/health`
- **Intervalo**: 30 segundos
- **Espera inicial**: 40 segundos
- **Reintentos**: 3

### Frontend
- **Endpoint**: GET `/`
- **Intervalo**: 30 segundos
- **Espera inicial**: 10 segundos
- **Reintentos**: 3

Si falla un health check, Railway lo reinicia automáticamente.

## 📊 Recursos

### Por Servicio

| Servicio | Memoria | CPU | Almacenamiento |
|----------|---------|-----|---|
| Backend API | 512 MB | 0.5 | - |
| Frontend | 256 MB | 0.5 | - |
| PostgreSQL | 1 GB | 1 | 10 GB |
| Redis | 256 MB | 0.5 | - |

Puedes aumentar estos recursos en Railway Console si lo necesitas.

## 🚀 Deployment Process

1. **Push a GitHub**
   ```bash
   git push origin main
   ```

2. **Webhook a Railway**
   Railway recibe notificación de nuevo commit

3. **Trigger Build**
   - Detecta Dockerfiles
   - Inicia buildprocess

4. **Ejecuta Dockerfile**
   ```dockerfile
   # backend/api/Dockerfile
   FROM python:3.11-slim
   ...
   ```

5. **Start Container**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

6. **Verify Health**
   Railway espera health check OK

7. **Rolling Deploy**
   Si hay réplicas, actualiza uno a la vez

## 🔗 Comunicación Entre Servicios

En Railway, los servicios se comunican por:
- **Nombre del servicio** como hostname
- **Puerto interno** del servicio

Ejemplos:
```
Backend → PostgreSQL: postgresql://user:pass@postgres-railway-url:5432/db
Backend → Redis: redis://redis-railway-url:6379
Frontend → Backend: NEXT_PUBLIC_API_BASE_URL=https://api.railway.app
```

## 📝 Notas Importantes

1. **Multi-stage Builds**: Reduce tamaño de imagen en ~60%
2. **Alpine Linux**: Imágenes más pequeñas para PostgreSQL y Redis
3. **Non-root User**: Mejor seguridad
4. **Health Checks**: Railway puede detectar y recuperar automáticamente
5. **Logs**: Disponibles en Railway Console en tiempo real

## 🆘 Si Algo No Funciona

1. **Verifica estructura de carpetas**
   - Backend debe estar en `backend/api/`
   - Frontend debe estar en `frontend/`

2. **Verifica Dockerfiles**
   - Existen los archivos
   - Tienen sintaxis correcta

3. **Revisa logs en Railway**
   - Console → Deployments → Logs
   - Busca error messages

4. **Verifica variables de entorno**
   - ¿DATABASE_URL está configurado?
   - ¿API_URL apunta al dominio correcto?

---

**Más detalles**: Ver [RAILWAY_DEPLOY_GUIDE.md](./RAILWAY_DEPLOY_GUIDE.md)
