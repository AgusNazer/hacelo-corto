# 🧪 Guía de Testing: Integración con YouTube

## ⚡ Quick Start para Testers

**¿Primera vez testeando? Sigue estos 3 pasos:**

1. **Preparar ambiente**: [Ver instrucciones](#preparar-ambiente)
2. **Testing con PowerShell**: [Script completo](#testing-con-powershell-recomendado) ⭐ **RECOMENDADO**
3. **Verificar en BD** (opcional): [Ver queries](#verificación-en-base-de-datos)

⚠️ **NOTA IMPORTANTE**: Swagger UI no funciona bien para este flujo OAuth. **Usa PowerShell** (ver sección Testing con PowerShell).

---

## 📋 Índice
1. [Requisitos Previos](#requisitos-previos)
2. [Preparar Ambiente](#preparar-ambiente)
3. [Testing con Swagger UI](#testing-con-swagger-ui)
4. [Testing con PowerShell](#testing-con-powershell)
5. [Verificación en Base de Datos](#verificación-en-base-de-datos)
6. [Troubleshooting](#troubleshooting)

---

## 🔧 Requisitos Previos

### 1. Google Cloud Console
- ✅ Proyecto creado: "NoCountry Video Processor"
- ✅ YouTube Data API v3 habilitada
- ✅ Credenciales OAuth 2.0 creadas:
  - Client ID: `<TU_CLIENT_ID>.apps.googleusercontent.com`
  - Client Secret: `<TU_CLIENT_SECRET>`
  - Redirect URI: `http://localhost:3000/auth/callback`
- ✅ App en modo **Testing** (no Production)
- ✅ Tu email agregado como Test User

### 2. Variables de Entorno
Verificar en `backend/api/.env`:
```bash
GOOGLE_CLIENT_ID=<TU_CLIENT_ID>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=<TU_CLIENT_SECRET>
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback
```

### 3. Docker Desktop
- Docker Desktop corriendo
- Al menos 4GB RAM disponible

---

## 🐳 Preparar Ambiente

### Paso 1: Limpiar ambiente anterior (IMPORTANTE)
```powershell
cd C:\Users\Daniela\Desktop\S02-26-Equipo-04-Web-App-Development\backend

# Detener y eliminar contenedores + volúmenes (limpieza completa)
docker compose down -v
```

⚠️ **NOTA**: `-v` elimina los volúmenes, incluyendo la base de datos. Esto garantiza un test limpio.

### Paso 2: Construir sin caché
```powershell
# Construcción limpia de todas las imágenes
docker compose build --no-cache
```
⏱️ **Tiempo estimado**: 3-5 minutos

### Paso 3: Iniciar servicios
```powershell
# Primero las dependencias (DB, Redis, MinIO)
docker compose up -d db redis minio

# Esperar 10 segundos para que DB esté lista
Start-Sleep -Seconds 10

# Aplicar migraciones
docker compose run --rm api alembic upgrade head

# Iniciar API
docker compose up -d api

# Verificar que todo esté corriendo
docker compose ps
```

✅ **Resultado esperado**:
```
NAME        IMAGE           STATUS
postgres    postgres:16     Up
redis       redis:7         Up
minio       minio/minio     Up
fastapi     api:latest      Up
```

### Paso 4: Verificar logs
```powershell
# Ver logs del API
docker compose logs api --tail 50

# Verificar que no haya errores
```

✅ **Buscar en logs**:
- `"Application startup complete"`
- `"Uvicorn running on http://0.0.0.0:8000"`

---

## 🎯 Testing con Swagger UI

### 🌐 Abrir Swagger
1. Navegar a: **http://localhost:8000/docs**
2. Deberías ver la interfaz de Swagger UI con todas las rutas

---

### ✅ Paso 1: Health Check

**Endpoint**: `GET /health`

1. Expandir el endpoint **GET /health**
2. Click en **"Try it out"**
3. Click en **"Execute"**

**✅ Respuesta esperada (200 OK)**:
```json
{
  "status": "healthy"
}
```

---

### 🔑 Paso 2: Obtener URL de Autorización

**Endpoint**: `GET /api/v1/auth/google/authorize`

1. Expandir el endpoint **GET /api/v1/auth/google/authorize**
2. Click en **"Try it out"**
3. Click en **"Execute"**

**✅ Respuesta esperada (200 OK)**:
```json
{
  "url": "https://accounts.google.com/o/oauth2/v2/auth?response_type=code&client_id=<TU_CLIENT_ID>.apps.googleusercontent.com&redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fauth%2Fcallback&scope=openid+...",
  "state": "algun_token_aleatorio_de_seguridad"
}
```

4. **COPIAR la URL completa** (desde `https://` hasta el final)
5. **COPIAR el valor de `state`** (lo necesitarás en el siguiente paso)

---

### 🌐 Paso 3: Autorizar con Google (En el navegador)

1. **Abrir la URL copiada** en tu navegador
2. **Iniciar sesión** con tu cuenta de Google (la que agregaste como Test User)
3. Verás una pantalla que dice:
   ```
   NoCountry Video Processor wants to access your Google Account
   
   This will allow NoCountry Video Processor to:
   ✅ See your primary Google Account email address
   ✅ See your personal info, including any personal info you've made publicly available
   ✅ Manage your YouTube videos
   ✅ View your YouTube account
   ```
4. **Click en "Continuar"** o **"Allow"**
5. Serás redirigido a:
   ```
   http://localhost:3000/auth/callback?code=4/0AfrIepA...&scope=openid+email+...&state=...
   ```
6. **COPIAR el valor del parámetro `code`** (todo lo que está entre `code=` y `&scope`)
   - Ejemplo: `4/0AfrIepAuDLF-rBTFXkS_vx7CdF-xZ2-sBthHEvupV_14QIshZCZxD_ScI5NpxcfHLvemAQ`

⚠️ **IMPORTANTE**: El `code` expira en **10 minutos**. Si tarda mucho, repite desde el Paso 2.

---

### 🔐 Paso 4: Intercambiar Code por JWT Token

**Endpoint**: `POST /api/v1/auth/google/callback`

1. Regresar a **Swagger UI (http://localhost:8000/docs)**
2. Expandir **POST /api/v1/auth/google/callback**
3. Click en **"Try it out"**
4. En el cuadro **Request body**, reemplazar con:
   ```json
   {
     "code": "PEGAR_AQUI_EL_CODE_DEL_PASO_3",
     "state": "PEGAR_AQUI_EL_STATE_DEL_PASO_2"
   }
   ```
5. Click en **"Execute"**

**✅ Respuesta esperada (200 OK)**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3NzI3Mjc...",
  "token_type": "bearer",
  "expires_in": 604800
}
```

6. **COPIAR el valor de `access_token`** (lo necesitarás para los siguientes pasos)

📌 **Este token dura 7 días** (604800 segundos)

---

### 🔓 Paso 5: Usar el Token JWT en Swagger

⚠️ **IMPORTANTE**: El botón "Authorize" de Swagger muestra **OAuth2PasswordBearer** (username/password), pero los endpoints de YouTube necesitan el **JWT token de Google OAuth**.

**SOLUCIÓN**: Agregar el token **manualmente en cada endpoint**:

#### NO uses el botón "Authorize" principal
- ❌ El "Authorize" de arriba es para login tradicional (username/password)
- ✅ Debes agregar el header manualmente en cada endpoint de YouTube

#### Cómo agregar el JWT token manualmente:

Cuando vayas a probar **cualquier endpoint protegido** (YouTube status, YouTube publish, etc.):

1. Expandir el endpoint (ejemplo: **GET /api/v1/youtube/status**)
2. Click en **"Try it out"**
3. **ANTES de hacer "Execute"**, busca la sección de **"Parameters"** o **"Headers"**
4. Si no hay forma de agregar headers manualmente, sigue estos pasos:
   - En la parte derecha del endpoint, verás un **candado** 🔒
   - Click en ese candado pequeño (del endpoint específico, no el de arriba)
   - Debería abrir un modal de autorización
   - Si no aparece un campo para Bearer token, **usa la alternativa de PowerShell** (ver Paso 5B)

#### 🔄 Paso 5B: ALTERNATIVA - Testing con PowerShell (RECOMENDADO)

Como Swagger UI no está bien configurado para Bearer tokens JWT, **usa PowerShell** directamente:

Salta al final de esta guía: [Testing con PowerShell](#testing-con-powershell-alternativa)

✅ **Con PowerShell es más directo y funciona al 100%**

---

### 📺 Paso 6: Verificar Conexión con YouTube (con PowerShell)

⚠️ **NOTA**: Como Swagger no acepta bien el Bearer token JWT, **usa PowerShell**:

```powershell
# Asegúrate de tener el $jwt guardado del paso anterior
# Si no lo tienes, vuelve a ejecutar el Paso 4

$headers = @{
    Authorization = "Bearer $jwt"
}

$statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/youtube/status" -Method Get -Headers $headers
$statusResponse | ConvertTo-Json -Depth 10
```

**✅ Respuesta esperada (200 OK)**:
```json
{
  "connected": true,
  "provider_username": null,
  "provider_user_id": "113822179860751389711",
  "token_expires_at": "2026-02-26T17:15:42.301753",
  "is_expired": false
}
```

✅ **Validaciones**:
- `connected` debe ser `true`
- `provider_user_id` debe tener tu Google User ID
- `token_expires_at` debe ser una fecha futura (~1 hora desde ahora)
- `is_expired` debe ser `false`

---

### 🎬 Paso 7: Publicar Video en YouTube (con PowerShell - Próximamente)

⚠️ **NOTA**: Este endpoint aún no sube videos reales (es un placeholder).

```powershell
# Usar el mismo $jwt y $headers del paso anterior
$videoId = "550e8400-e29b-41d4-a716-446655440000"  # UUID de ejemplo

$publishBody = @{
    title = "Test Video desde API"
    description = "Video de prueba generado con NoCountry Video Processor"
    privacy = "private"
} | ConvertTo-Json

$publishResponse = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/youtube/publish/$videoId" `
    -Method Post `
    -Headers $headers `
    -Body $publishBody `
    -ContentType "application/json"

$publishResponse | ConvertTo-Json -Depth 10
```

**⚠️ Respuesta actual (501 Not Implemented)**:
```json
{
  "detail": "Video upload not yet implemented"
}
```

📌 **Próximo paso de desarrollo**: Implementar la subida real usando `google-api-python-client`.

---

## 💻 Testing con PowerShell (RECOMENDADO)

⚠️ **IMPORTANTE**: Swagger UI no está bien configurado para Bearer tokens JWT. **Usa PowerShell** para testing completo.

### 🎯 Script Completo de Testing

Copia y pega estos comandos **uno por uno** en PowerShell:

#### 1️⃣ Obtener URL de Autorización
```powershell
$authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/google/authorize" -Method Get
$authUrl = $authResponse.url
$state = $authResponse.state

Write-Host ""
Write-Host "=== PASO 1: ABRIR ESTA URL EN TU NAVEGADOR ===" -ForegroundColor Green
Write-Host $authUrl -ForegroundColor Yellow
Write-Host ""
Write-Host "=== State guardado para el siguiente paso ===" -ForegroundColor Cyan
Write-Host $state
Write-Host ""
```

#### 2️⃣ Autorizar con Google (En el navegador)

1. **Abrir la URL** que aparece en la terminal
2. **Iniciar sesión** con tu cuenta de Google
3. **Aceptar permisos** de YouTube
4. Serás redirigido a: `http://localhost:3000/auth/callback?code=4/0AfrIepA...`
5. **COPIAR el valor del parámetro `code`** (todo entre `code=` y `&scope`)

#### 3️⃣ Intercambiar Code por JWT Token
```powershell
# IMPORTANTE: Reemplazar "TU_CODE_AQUI" con el code copiado del navegador
$code = "TU_CODE_AQUI"

$callbackBody = @{
    code = $code
    state = $state
} | ConvertTo-Json

$tokenResponse = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/auth/google/callback" `
    -Method Post `
    -Body $callbackBody `
    -ContentType "application/json"

$jwt = $tokenResponse.access_token

Write-Host ""
Write-Host "=== JWT TOKEN OBTENIDO ===" -ForegroundColor Green
Write-Host $jwt -ForegroundColor Yellow
Write-Host ""
Write-Host "Token expira en:" $tokenResponse.expires_in "segundos (7 días)" -ForegroundColor Cyan
Write-Host ""
```

✅ **Si ves el JWT token, ¡el OAuth flow funcionó!**

#### 4️⃣ Verificar Conexión con YouTube
```powershell
$headers = @{
    Authorization = "Bearer $jwt"
}

$statusResponse = Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/youtube/status" `
    -Method Get `
    -Headers $headers

Write-Host ""
Write-Host "=== ESTADO DE CONEXIÓN YOUTUBE ===" -ForegroundColor Green
$statusResponse | ConvertTo-Json -Depth 10
Write-Host ""
```

**✅ Respuesta esperada**:
```json
{
  "connected": true,
  "provider_user_id": "113822179860751389711",
  "token_expires_at": "2026-02-26T17:15:42.301753",
  "is_expired": false
}
```

✅ **Validaciones**:
- `connected` = `true` ✅
- `token_expires_at` = fecha futura ✅
- `is_expired` = `false` ✅

#### 5️⃣ (Opcional) Intentar Publicar Video
```powershell
$videoId = "550e8400-e29b-41d4-a716-446655440000"

$publishBody = @{
    title = "Test Video desde API"
    description = "Video de prueba generado con NoCountry Video Processor"
    privacy = "private"
} | ConvertTo-Json

try {
    $publishResponse = Invoke-RestMethod `
        -Uri "http://localhost:8000/api/v1/youtube/publish/$videoId" `
        -Method Post `
        -Headers $headers `
        -Body $publishBody `
        -ContentType "application/json"
    
    Write-Host "=== VIDEO PUBLICADO ===" -ForegroundColor Green
    $publishResponse | ConvertTo-Json -Depth 10
} catch {
    Write-Host "=== RESPUESTA (esperada: 501 Not Implemented) ===" -ForegroundColor Yellow
    $_.Exception.Response.StatusCode.value__
    $_.ErrorDetails.Message
}
```

⚠️ **Nota**: Este endpoint retorna **501 Not Implemented** porque aún no implementa la subida real.

---

## 💻 Testing con PowerShell (Alternativa Original)

Si prefieres usar PowerShell en vez de Swagger:

### Variables de sesión
```powershell
# 1. Obtener URL de autorización
$authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/google/authorize" -Method Get
$authUrl = $authResponse.url
$state = $authResponse.state

Write-Host "Abrir en navegador: $authUrl"
Write-Host "State guardado: $state"

# 2. Después de autorizar y copiar el code:
$code = "PEGAR_CODE_AQUI"

$callbackBody = @{
    code = $code
    state = $state
} | ConvertTo-Json

$tokenResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/google/callback" -Method Post -Body $callbackBody -ContentType "application/json"

$jwt = $tokenResponse.access_token
Write-Host "JWT obtenido: $jwt"

# 3. Verificar conexión con YouTube
$headers = @{
    Authorization = "Bearer $jwt"
}

$statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/youtube/status" -Method Get -Headers $headers
$statusResponse | ConvertTo-Json -Depth 10
```

---

## 🗄️ Verificación en Base de Datos

### Conectar a PostgreSQL
```powershell
docker compose exec db psql -U fastapi_user -d fastapi_db
```

### Verificar usuario creado
```sql
SELECT id, email, full_name, provider, provider_id, created_at 
FROM users 
ORDER BY created_at DESC 
LIMIT 1;
```

✅ **Deberías ver tu email de Google**

### Verificar tokens de YouTube
```sql
SELECT 
    id, 
    user_id, 
    provider, 
    token_type, 
    expires_at, 
    scope, 
    provider_user_id,
    created_at,
    updated_at
FROM oauth_tokens 
ORDER BY created_at DESC 
LIMIT 1;
```

✅ **Validaciones**:
- `provider` debe ser `'youtube'`
- `access_token` debe estar presente (campo no NULL)
- `refresh_token` debe estar presente
- `expires_at` debe ser una fecha futura
- `scope` debe contener `youtube.upload` y `youtube`
- `provider_user_id` debe ser tu Google User ID

### Salir de PostgreSQL
```sql
\q
```

---

## 🐛 Troubleshooting

### ❌ Error: "401 Unauthorized - No YouTube tokens found"

**Causa**: El usuario no ha completado el OAuth flow.

**Solución**: Repetir desde el Paso 2 (Obtener URL de Autorización).

---

### ❌ Error: "403 That's an error. You do not have access to this page"

**Causa**: La app está en modo Production o tu email no está como Test User.

**Solución**:
1. Ir a Google Cloud Console → OAuth consent screen
2. Cambiar **Publishing status** a **"Testing"**
3. Agregar tu email en **"Test users"**
4. Esperar 5 minutos y reintentar

---

### ❌ Error: "400 Bad Request - Invalid grant: code expired"

**Causa**: El authorization code expira en 10 minutos.

**Solución**: Obtener un nuevo code repitiendo desde el Paso 2.

---

### ❌ Error: "Invalid parameter value for prompt: consent""

**Causa**: La URL de autorización no está usando `urlencode()` correctamente.

**Solución**: Ya está corregido en el commit `eb3fa1a`. Si persiste:
```powershell
docker compose down
docker compose build --no-cache api
docker compose up -d
```

---

### ❌ Error: Docker containers no inician

**Solución**:
```powershell
# Ver logs detallados
docker compose logs db
docker compose logs api

# Reinicio completo
docker compose down -v
docker compose up -d
```

---

### ❌ Error: "Could not connect to database"

**Causa**: PostgreSQL no está listo cuando FastAPI inicia.

**Solución**:
```powershell
# Esperar más tiempo antes de iniciar API
docker compose up -d db redis minio
Start-Sleep -Seconds 20
docker compose up -d api
```

---

### ❌ Scopes de YouTube no aparecen en pantalla de autorización

**Causa**: Los scopes están comentados en `google_oauth_service.py`.

**Solución**: Ya está corregido en el commit `5287411`. Verificar:
```powershell
docker compose exec api cat /app/app/services/google_oauth_service.py | Select-String "youtube.upload"
```

Debe mostrar líneas **SIN** `#` al inicio.

---

## ✅ Checklist Final

Antes de marcar como completado, verificar:

- [ ] Docker Compose limpio (down -v, build --no-cache)
- [ ] Migraciones aplicadas (alembic upgrade head)
- [ ] Health check retorna 200 OK
- [ ] URL de autorización generada correctamente
- [ ] Scopes de YouTube aparecen en pantalla de Google
- [ ] Authorization code obtenido en redirect
- [ ] JWT token obtenido del callback
- [ ] YouTube status retorna `connected: true`
- [ ] Usuario en tabla `users`
- [ ] Tokens en tabla `oauth_tokens`
- [ ] `expires_at` es fecha futura
- [ ] `refresh_token` está almacenado

---

## 📚 Referencias

- [Documentación completa de integración](./YOUTUBE_INTEGRATION.md)
- [YouTube Data API v3 Docs](https://developers.google.com/youtube/v3)
- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)

---

**✨ ¡Listo para probar! ✨**

Si todo funciona, tu integración con YouTube está completa y lista para merge. 🎉
