# ⚡ Testing Rápido - YouTube OAuth

## 🎯 Para testers que quieren probar rápido

### Prerequisitos
- ✅ Docker Desktop corriendo
- ✅ Backend corriendo en `http://localhost:8000`

### 🚀 Script de Testing (Copy-Paste)

**Abre PowerShell** y ejecuta estos comandos **uno por uno**:

---

#### 1. Obtener URL de autorización
```powershell
$authResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/google/authorize" -Method Get
$authUrl = $authResponse.url
$state = $authResponse.state
Write-Host "Abrir en navegador:" -ForegroundColor Green
Write-Host $authUrl -ForegroundColor Yellow
```

📋 **Se abrirá una URL de Google**, cópiala y ábrela en tu navegador.

---

#### 2. Autorizar con Google
1. Pega la URL en tu navegador
2. Inicia sesión con tu cuenta de Google
3. Acepta los permisos de YouTube
4. Serás redirigido a: `http://localhost:3000/auth/callback?code=XXXX...`
5. **COPIA el valor del parámetro `code`** (el texto largo después de `code=` y antes de `&scope`)

---

#### 3. Obtener JWT Token
```powershell
# ⬇️ PEGA TU CODE AQUÍ (entre las comillas)
$code = "PEGA_TU_CODE_AQUI"

$callbackBody = @{ code = $code; state = $state } | ConvertTo-Json
$tokenResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/google/callback" -Method Post -Body $callbackBody -ContentType "application/json"
$jwt = $tokenResponse.access_token
Write-Host "JWT obtenido:" -ForegroundColor Green
Write-Host $jwt -ForegroundColor Yellow
```

✅ **Si ves un JWT token largo, ¡funcionó!**

---

#### 4. Verificar conexión YouTube
```powershell
$headers = @{ Authorization = "Bearer $jwt" }
$statusResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/youtube/status" -Method Get -Headers $headers
Write-Host "Estado YouTube:" -ForegroundColor Green
$statusResponse | ConvertTo-Json
```

**✅ Resultado esperado:**
```json
{
  "connected": true,
  "provider_user_id": "tu_google_id",
  "token_expires_at": "fecha_futura",
  "is_expired": false
}
```

---

## ✅ Test Exitoso = Viste esto:
1. ✅ URL de Google autorización generada
2. ✅ Pantalla de Google pidiendo permisos de YouTube
3. ✅ JWT token obtenido (string largo que empieza con `eyJ...`)
4. ✅ Status retorna `"connected": true`

---

## ❌ Troubleshooting Rápido

### Error: "400 Bad Request - code expired"
**Solución**: El code expira en 10 minutos. Vuelve al paso 1.

### Error: "403 You do not have access"
**Solución**: Pídele a Daniela que agregue tu email como Test User en Google Cloud Console.

### Error: "401 Unauthorized"
**Solución**: Verifica que copiaste bien el JWT token (debe empezar con `eyJ`).

---

## 📚 ¿Quieres más detalles?

Ver documentación completa: [YOUTUBE_TESTING_GUIDE.md](./YOUTUBE_TESTING_GUIDE.md)

---

**🎉 ¡Listo para probar!**
