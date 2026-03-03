# 🎬 Pipeline.py — Resumen

Realiza **reencuadre automático de video** simulando el comportamiento de un camarógrafo humano.

---

## 🎯 Objetivos

- Reducir videos pesados o con formatos raros  
- Seguir al sujeto principal (si existe)  
- Evitar movimientos bruscos, glitches o saltos rápidos  
- Aplicar reglas de dirección de cámara real  
- Mantener rendimiento alto (sin I/O innecesario)  

---

## 🧱 Etapas del Pipeline

### 1️⃣ Normalización (si hace falta)

Solo se convierte el video si:

- El códec no es H264  
- El FPS es muy distinto al target  
- La resolución es demasiado grande  
- El pixel format no es yuv420p  

Si ya está OK → solo se recorta el segmento (sin reencode).

---

### 2️⃣ Procesamiento por Stream

Se usa FFmpeg como:

- **Decoder** → envía frames crudos a Python  
- **Encoder** → recibe frames procesados  

🚫 No se guardan imágenes intermedias.

---

### 3️⃣ Detección de sujeto

Se intenta estimar el centro de atención usando:

- Detección de rostros  
- Actividad de voz (cuando hay audio útil)  
- Centro de escena como fallback  

Esta capa decide **a quién mirar**, no cómo mover la cámara.

---

### 4️⃣ Dirección de cámara (núcleo del sistema)

Implementado en `CameraDirector`.

Simula reglas humanas:

| Comportamiento humano | Regla computable |
|------------------------|------------------|
| Si cambio de plano, me quedo | Tiempo mínimo en plano (HOLD) |
| No voy y vuelvo | Histéresis |
| Los movimientos duran | Transiciones con duración |
| Puede haber cortes | Hard cuts |
| Ignorar errores de detección | Consenso temporal |
| El que habla importa | Fusión audio + visión |

Esto evita:

❌ Saltos nerviosos  
❌ Correcciones constantes  
❌ Cambios por ruido de detección  

---

### 5️⃣ Reencuadre

Se recorta el frame a formato vertical (9:16) siguiendo la posición de cámara calculada.

---

### 6️⃣ Audio

El audio no se procesa durante los frames.  
Se vuelve a unir al final para evitar problemas de sincronización.

---

## 🎥 Casos que el sistema contempla

- No hay rostros → modo escena  
- No hay voz → solo visión  
- Solo paisaje → cámara estable  
- Múltiples sujetos → decisión por consenso  
- Mucho ruido visual → cámara quieta  

---