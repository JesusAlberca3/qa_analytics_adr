# Manual de Interpretación - Notebook 1

## Resumen WEF

```
ALL:
Logs: 44,943 | Errors: 4,798 | Warnings: 8,764 | Fatals: 155

Promedios (23 minutos):
Errors/min: 208.6 | Warnings/min: 381.0 | Fatals/min: 6.7
```

**Cómo leer:**
- **Errors/min > 200:** Log problemático, revisar diagnóstico
- **Errors/min < 50:** Log normal
- **Fatals > 0:** Crashes detectados, revisar sección de crashes

---

## Detección de Picos

```
Pico detectado: 14:27
Severidad: 2,217 errors (Z-score: 3.3)
```

**Cómo leer:**
- **Z-score > 3.0:** Pico severo, problema crítico en ese timestamp
- **Z-score 2.0-3.0:** Pico moderado, revisar componentes
- **Sin picos:** Log estable

**Qué hacer:**
1. Ver timestamp del pico (14:27 en este caso)
2. Correlacionar con acciones del usuario (¿qué estaba haciendo?)
3. Revisar componente más afectado

---

## Componentes

```
Componente más afectado: AppSearchManagerService (486 errors)
Categoría: APP
Severidad típica: ALTA
```

**Categorías:**
- **SYSTEM:** Ruido de Android, generalmente ignorable
- **APP:** Código de la app, crítico para revisar
- **MEDIA:** Video/audio pipeline, crítico para playback
- **DRM:** Licencias Widevine/PlayReady, crítico para contenido protegido
- **CUSTOM:** Componentes vendor (Sony/MediaTek), propietarios

**Qué hacer:**
- Si es SYSTEM: Ignorar, ver siguiente componente
- Si es APP/MEDIA/DRM: Revisar errores comunes y acción recomendada

---

## Crashes

```
Crash detectado: SIGSEGV
Thread: RenderThread
Timestamp: 14:27
Causa probable: Null pointer dereference
```

**Qué significa:**
- **SIGSEGV:** La app intentó acceder a memoria inválida (null pointer)
- **Thread:** Qué hilo crasheó (RenderThread = rendering, main = UI thread)

**Qué hacer:**
1. Ver timestamp (correlacionar con acciones del usuario)
2. Buscar en código el thread que crasheó
3. Revisar si hay OOM antes del crash (causa raíz común)

---

## OOM (Out of Memory)

```
Memory allocation failure detectado:
Intentó allocar: 8.3 MB
Thread: RenderThread
Mensaje: returning null pointer (OOM)
```

**Qué significa:**
- Sistema se quedó sin RAM
- Thread intentó allocar memoria y falló
- Si hay crash después, el OOM es la causa raíz

**Qué hacer:**
1. Revisar memory leaks en la app
2. Optimizar uso de memoria (bitmaps, buffers)
3. Verificar que se liberen recursos correctamente

---

## Rendering Pipeline

```
Rendering pipeline afectado:
  PqLink: 1,404 errors (CRÍTICO)
    Componente: Sony Picture Quality Engine
    Posibles causas (Android docs):
      - Consumer no procesa buffers a tiempo
      - Producer genera frames más rápido que consumer
```

**Severidad:**
- **CRÍTICO (>500 errors):** Rendering completamente saturado
- **ALTO (100-500):** Sobrecarga moderada
- **MEDIO (50-100):** Carga elevada pero manejable

**Qué hacer:**
- Revisar frame rate (¿está reproduciendo 4K/60fps?)
- Verificar si hay OOM asociado (causa común)
- Reducir complejidad de rendering si es posible

---

## Top 10 Errors (Claro)

```
1. PqLink: 1,404
2. AppSearchManagerService: 486
3. ActivityManager: 273
```

**Cómo leer:**
- Solo muestra componentes de la app Claro (ignora ruido del sistema)
- Ordenado por cantidad de errors
- Usar para priorizar qué revisar primero

---

## PDF Generado

El PDF contiene exactamente lo mismo que la consola pero en formato presentable para:
- Compartir con el equipo
- Adjuntar a tickets de Jira
- Presentar a management
- Guardar evidencia de análisis

---

## Escenarios Comunes

### Escenario 1: Crash por OOM
```
OOM: 8.3 MB | RenderThread | 14:27:19
Crash: SIGSEGV | RenderThread | 14:27:19 (1ms después)
```
**Causa:** Sistema sin RAM → thread intenta usar null pointer → crash
**Fix:** Optimizar memoria, liberar buffers

### Escenario 2: Rendering saturado
```
PqLink: 1,404 errors (CRÍTICO)
BufferQueueProducer: 99 errors (MEDIO)
```
**Causa:** GPU/buffers saturados, no puede procesar frames
**Fix:** Reducir frame rate, optimizar composición

### Escenario 3: Multi-user corruption
```
AppSearchManagerService: 486 errors
Error: UserHandle{10} is locked or not running
```
**Causa:** Sistema de multi-usuario corrupto
**Fix:** Verificar multi-user state antes de operaciones




#Esta Guia se genero con ayuda de un copilot
#Resume como interpretar/usar el notebook 1 TOp_detector
AT