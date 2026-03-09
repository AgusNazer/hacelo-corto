# 🆘 Troubleshooting - Issues Comunes en Railway

Guía de resolución para los problemas más comunes al deployar en Railway.

## 🔴 Build Failures

### ❌ Error: "Dockerfile not found"

**Síntomas:**
```
Build failed: Dockerfile not found
```

**Causa:**
Railway no encontró el Dockerfile en la ruta especificada.

**Solución:**
1. Verifica que exista el archivo:
   - `backend/api/Dockerfile` para Backend
   - `frontend/Dockerfile` para Frontend

2. Verifica el "Root Directory" en Railway:
   - Backend: `backend/api`
   - Frontend: `frontend`

3. Verifica que no haya espacios en blanco en el nombre

### ❌ Error: "requirements.txt not found"

**Síntomas:**
```
ERROR: Could not open requirements file [ENOENT]: No such file or directory: 'requirements.txt'
```

**Causa:**
El Dockerfile lee `requirements.txt` desde el Root Directory.

**Solución:**
```dockerfile
# ❌ Incorrecto en backend/api/Dockerfile
COPY requirements.txt .

# ✅ Correcto
COPY requirements.txt .
# (requirements.txt debe estar en backend/api/)
```

Verifica que `backend/api/requirements.txt` existe.

### ❌ Error: "ModuleNotFoundError"

**Síntomas:**
```
ModuleNotFoundError: No module named 'app'
```

**Causa:**
El working directory o importes están mal configurados.

**Solución:**
```dockerfile
# En backend/api/Dockerfile
WORKDIR /app
COPY . .

# Luego levanta con:
CMD ["uvicorn", "app.main:app", ...]
```

Verifica que `app/main.py` existe y está en la carpeta correcta.

---

## 🟠 Runtime Errors

### ❌ Database Connection Failed

**Síntomas:**
```
ERROR: could not translate host name "db" to address
PostgreSQL connection failed
```

**Cause:**
`DATABASE_URL` no está configurado o is incorrect.

**Solución:**

1. **Verifica DATABASE_URL en Railway:**
   - Railway Console → [Servicio API] → Variables
   - Debe existir una variable `DATABASE_URL`

2. **Si usas PostgreSQL de Railway:**
   - Railway auto-inyecta `DATABASE_URL`
   - NO la copies manualmente

3. **Formato correcto (si lo fijas manualmente):**
   ```
   postgresql://user:password@host:5432/dbname
   ```
   - SIN espacios
   - SIN caracteres especiales no escapados

4. **Verifica que PostgreSQL esté corriendo:**
   ```bash
   # Desde Railway Console
   # Servicio PostgreSQL debe estar en estado "running"
   ```

### ❌ Redis Connection Failed

**Síntomas:**
```
ConnectionError: Error 111 connecting to redis:6379
```

**Solución:**

1. **Asegúrate que Redis está en Railway:**
   - [Proyecto] → Database/Redis
   - Si no existe, agrégalo

2. **Configura REDIS_HOST:**
   ```
   REDIS_HOST=redis (dentro de Railway)
   REDIS_HOST=[actual-host] (desde internet)
   REDIS_PORT=6379
   ```

3. **En Backend, asegúrate de usar variable correcta:**
   ```python
   REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
   redis_client = redis.Redis(host=REDIS_HOST, port=6379)
   ```

### ❌ MinIO/S3 Connection Failed

**Síntomas:**
```
botocore.exceptions.ConnectionError: Unable to connect to MinIO
```

**Solución:**

1. **Opción A: Usar AWS S3** (Recomendado)
   ```
   MINIO_ENDPOINT=s3.amazonaws.com
   MINIO_ACCESS_KEY=AKIAIOSFODNN7EXAMPLE
   MINIO_SECRET_KEY=...
   ```

2. **Opción B: Deployar MinIO en Railway**
   - Agregar como servicio
   - Usar endpoint de Railway

3. **Verifica credenciales:**
   - `MINIO_ACCESS_KEY` correcto
   - `MINIO_SECRET_KEY` correcto
   - Sin caracteres especiales sin escapar

---

## 🟡 Configuration Issues

### ❌ Variable NEXT_PUBLIC_API_BASE_URL Error

**Síntomas:**
```
Frontend no puede conectar al backend
Requests a undefined endpoint
```

**Causa:**
`NEXT_PUBLIC_API_BASE_URL` no está configurada o está incorrecta.

**Solución:**

1. **En Frontend .env:**
   ```bash
   # ❌ Incorrecto (no funciona en producción)
   NEXT_PUBLIC_API_BASE_URL=http://localhost:8000

   # ✅ Correcto (dominio de Railway)
   NEXT_PUBLIC_API_BASE_URL=https://tu-api.railway.app

   # ✅ O tu dominio personalizado
   NEXT_PUBLIC_API_BASE_URL=https://api.tudominio.com
   ```

2. **En Railway Console:**
   - Frontend service → Variables
   - `NEXT_PUBLIC_API_BASE_URL=https://[tu-api-domain]`

3. **Verifica que el dominio está correcto:**
   ```bash
   # Desde terminal local
   curl https://tu-api.railway.app/api/v1/health
   # Debe retornar 200 OK
   ```

4. **CORS en Backend:**
   - Asegúrate que el backend permite CORS del frontend
   ```python
   CORSMiddleware(
       allow_origins=[
           "https://tu-frontend.railway.app",
           "https://tudominio.com"
       ]
   )
   ```

### ❌ Port Mismatch

**Síntomas:**
```
Connection refused
Service unavailable
```

**Causa:**
El puerto en Railway no coincide con el del Dockerfile.

**Solución:**

**Backend:**
```dockerfile
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend:**
```dockerfile
EXPOSE 3000
CMD ["dumb-init", "next", "start", "-p", "3000"]
```

Verifica en Railway Console que el puerto está correcto.

---

## 🔵 Performance Issues

### ⚠️ Build Takes Too Long

**Síntomas:**
```
Build timeout after 30 minutes
```

**Solución:**

1. **Optimiza Dockerfile:**
   ```dockerfile
   # ❌ Instala muchas dependencias globales
   RUN apt-get install -y ...

   # ✅ Solo instala lo necesario
   RUN apt-get install --no-install-recommends -y ...
   ```

2. **Cachea layers:**
   ```dockerfile
   # ❌ Invalida caché cada vez
   COPY . .
   COPY requirements.txt .

   # ✅ Cachea dependencias
   COPY requirements.txt .
   RUN pip install -r requirements.txt
   COPY . .
   ```

3. **Usa Alpine Linux:**
   ```dockerfile
   # más rápido que full debian/python
   FROM python:3.11-slim
   FROM node:20-alpine
   ```

### ⚠️ Container Crashes Soon After Start

**Síntomas:**
```
Container exited with code 1
Restart policy: always (keeps restarting)
```

**Causa:**
Health check falla, luego se reinicia infinitamente.

**Solución:**

1. **Revisa los logs:**
   - Railway Console → Logs
   - Busca el error inicial

2. **Aumenta wait time:**
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s --start-period=60s
   ```

3. **Verifica que la app realmente inicia:**
   ```bash
   # Test local
   docker run -p 8000:8000 tu-imagen
   # Espera y verifica que inicia
   ```

---

## 🟢 Deployment Issues

### ⚠️ Cold Start / Slow First Request

**Síntomas:**
```
Primera solicitud tarda 5-10 segundos
```

**Esperado:**
Normal en Railway. Es así.

**Mitigación:**
```python
# Backend: Precarga recursos costosos
@app.on_event("startup")
async def startup():
    # Cargar modelos de ML
    # Conectar a BD
    pass
```

### ⚠️ Rolling Deployment Fails

**Síntomas:**
```
New version falla a deployar
Old version sigue corriendo
```

**Solución:**

1. **Verifica health checks:**
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=10s
   ```

2. **Aumenta replicas:**
   - Si tienes 1 replica, agrega a 2
   - Railway actualiza una a la vez

3. **Revisa logs:**
   - La nueva versión falla en startup

---

## 🟣 Database Issues

### ❌ Migration Fails

**Síntomas:**
```
Alembic migration error
Foreign key constraint failure
```

**Solución:**

1. **Ejecuta migration antes del deploy:**
   ```bash
   # Localmente
   cd backend/api
   alembic upgrade head
   # Si todo OK, commitea y pushea
   ```

2. **Desde Railway (si es necesario):**
   ```bash
   # Railway CLI
   railway run alembic upgrade head
   ```

3. **Verifica estado de BD:**
   ```bash
   # Test local
   cd backend/api
   python view_db.py  # si tienes este script
   ```

### ⚠️ Database Bloat

**Síntomas:**
```
Conexiones lentas
Queries timeout
```

**Solución:**

1. **En Railway Console:**
   - PostgreSQL → Increase storage/resources

2. **Cleanup:**
   ```sql
   -- Ejecuta en la BD
   VACUUM FULL;
   ```

---

## 📊 Monitoring & Logs

### Cómo Ver Logs

**En Railway Console:**
1. Proyecto → [Servicio]
2. Pestaña "Logs"
3. Busca errores

**Real-time:**
```bash
# Con Railway CLI
railway logs --follow
```

### Configurar Alertas

1. Railway Console → [Proyecto]
2. "Settings" → "Alerts"
3. Configura webhook para Slack/Discord

---

## 🔧 Quick Debug Checklist

```bash
# 1. ¿Existe el Dockerfile?
ls backend/api/Dockerfile
ls frontend/Dockerfile

# 2. ¿Están los archivos en git?
git ls-files | grep Dockerfile

# 3. ¿Puedo buildear localmente?
docker build -t test-api backend/api
docker build -t test-frontend frontend

# 4. ¿Puedo correr localmente?
docker run -p 8000:8000 test-api
docker run -p 3000:3000 test-frontend

# 5. ¿Las variables de entorno están OK?
# Verifica en Railway Console

# 6. ¿Los health checks pasan?
curl http://localhost:8000/api/v1/health
curl http://localhost:3000

# 7. ¿La BD está lista?
# Verifica PostgreSQL en Railway Console
```

---

## 📞 Si Nada de Esto Funciona

1. **Revisa la documentación:**
   - [RAILWAY_DEPLOY_GUIDE.md](./RAILWAY_DEPLOY_GUIDE.md)
   - [DOCKER_CONFIG_SUMMARY.md](./DOCKER_CONFIG_SUMMARY.md)

2. **Verifica Railway Docs:**
   - https://docs.railway.app/

3. **Contacta soporte:**
   - Railway tiene soporte comunitario en Discord

4. **Rollback:**
   ```bash
   git revert [commit-problemático]
   git push origin main
   # Railway auto-deploya la versión anterior
   ```

---

**Última actualización**: Marzo 2026
