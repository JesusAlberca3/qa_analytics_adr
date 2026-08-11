# Notebook 1: Análisis de Logs STB

## Qué hace

Analiza logs de Android TV (STB) para detectar picos de errors usando Z-score y genera diagnóstico automático.

## Entrada

Log en formato logcat de Android:
```
04-07 14:27:19.576 14204 14247 W libc : calloc(8294400, 1) failed
04-07 14:27:19.577 14204 14247 F libc : Fatal signal 11 (SIGSEGV)
```

## Salida

1. **Consola:**
   - Resumen WEF (Errors/Warnings/Fatals + promedios)
   - Top 10s (componentes más afectados)
   - Detección de picos (Z-score)
   - Diagnóstico (componente culpable + crashes + OOM + rendering)

2. **Gráficas PNG:**
   - `/data/plots/01_eda_overview.png` - Overview general
   - `/data/plots/02_picos_detectados.png` - Picos detectados con Z-score

3. **PDF:**
   - `/data/pdfs/nombre_log.pdf`
   - Contiene: Resumen WEF + Top 10 + Gráfica + Diagnóstico completo

## Cómo usar

```python
# 1. Configurar path del log
log_file = "/ruta/a/tu/log.txt"

# 2. Ejecutar todas las celdas del notebook

# 3. Revisar outputs:
#    - Consola: diagnóstico inmediato
#    - PDF: reporte completo para compartir
```

## Configuración

```python
# En el notebook:
ZSCORE_THRESHOLD = 2.0  # Detecta picos con Z >= 2.0
PLOTS_DIR = "../../data/plots"
PDFS_DIR = "../../data/pdfs"
```

## Qué detecta

- **Picos de errors:** Usa Z-score estadístico
- **Crashes:** SIGSEGV (Segmentation Fault)
- **OOM:** Memory allocation failures (calloc/malloc failed)
- **Rendering:** Saturación de GPU/buffers (PqLink, gralloc4, BufferQueue)
- **Componentes:** Clasifica en SYSTEM/APP/MEDIA/DRM según diccionario Android

## Dependencias

```bash
pip install pandas numpy matplotlib seaborn scipy
pip install reportlab  # Para PDFs
```

## Archivos

- `top_detector.ipynb` - Notebook principal
- `android_components_dict.py` - Diccionario de 27+ componentes Android


## Limitaciones

- Solo detecta picos con Z >= 2.0 (configurable)
- Diagnóstico basado en componentes documentados en diccionario, el diccionario se puede agregar nuevos elementos


