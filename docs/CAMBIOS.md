# Changelog del fork — mejora de flujo de análisis

**Fecha:** 2026-08-11  
**Base:** `atamez6/qa_analytics_adr`  
**Repo (mirror):** https://github.com/JesusAlberca3/qa_analytics_adr  
**Nota:** El fork nativo vía API (`gh repo fork`) devolvió *Forbidden*; se publicó un **mirror limpio** (sin historial con secretos en `.dvc/config`) bajo la cuenta `JesusAlberca3`.  
**Motivación:** Evaluar el trade-off del pipeline actual (parse → 60s → WEF → Z-score → Top-N → Apriori) y endurecer la capa estadística sin perder interpretabilidad QA.

---

## Resumen

Se documenta un **flujo oficial en capas**, se extrae el triage a **scripts CLI** (aptos para batch/paralelo), y se sustituye el núcleo débil (umbral fijo + Apriori) por:

1. **Filtro de ruido** de tags de plataforma  
2. **Detección de picos con MAD** (robusta vs Z-score global)  
3. **Co-ocurrencia PMI** de tags en minutos pico (reemplazo práctico de Apriori)  
4. **Batch paralelo** para N logs  

Isolation Forest permanece como Phase 2 (requiere histórico).

---

## Archivos nuevos

| Archivo | Descripción |
|---------|-------------|
| `docs/FLUJO_OFICIAL.md` | Contrato input/output y capas del análisis |
| `docs/CAMBIOS.md` | Este documento |
| `config/analysis_config.yaml` | Umbrales, ruido, MAD, PMI |
| `scripts/log_parser.py` | Parse compartido (formatos A/B logcat) |
| `scripts/analyze_log.py` | Triage de un log → JSON + consola |
| `scripts/batch_analyze.py` | Loop + paralelo sobre carpeta de logs |

---

## Cambios conceptuales vs notebooks actuales

| Antes | Ahora (oficial) | Trade-off |
|-------|-----------------|-----------|
| Umbral fijo `error_rate > 0.06` | Rates **clean** + MAD relativo al log | Menos falsos positivos multi-vendor; necesita lista de ruido |
| Z-score global de errors/min | **MAD** (median absolute deviation) | Más robusto si el log nace saturado |
| Apriori (Market Basket) como núcleo | **PMI** en minutos pico | Menos reglas obvias; no da “confianza” tipo Apriori |
| Un log por ejecución de notebook | CLI + `ProcessPoolExecutor` | Escala a X logs; menos PDF automático |
| Notebooks como única vía | Notebooks = exploración/PDF; scripts = ops | Dos superficies a mantener alineadas |

---

## Lo que NO cambia (a propósito)

- Parse regex logcat A/B  
- Ventana de **60 segundos**  
- Contadores **WEF** y Top-N (siguen siendo el explicador QA)  
- Diccionario `android_components_dict.py`  
- Notebooks `top_detector`, `eda_logs`, `crash_event_finder` (siguen usables)

---

## Cómo usar el fork

```bash
# Un log
python scripts/analyze_log.py /ruta/log.txt --output-dir data/processed_logs

# Carpeta de logs en paralelo
python scripts/batch_analyze.py /ruta/LogsADR --workers 4 --output-dir data/processed_logs
```

Salidas: `*_report.json` por log y `batch_summary.csv` con veredictos.

---

## Roadmap corto

1. ✅ Documentar flujo + scripts triage  
2. 🔜 Alinear celdas de config de notebooks a `analysis_config.yaml`  
3. 🔜 Baseline por vendor/firmware (percentiles históricos)  
4. 🔜 Isolation Forest sobre features clean (Phase 2)

---

## Decisión de diseño (recordatorio)

> El esqueleto parse → 60s → WEF → Top-N es correcto para QA STB.  
> El cuello de botella era ruido + umbrales fijos + Apriori débil, no “falta de deep learning”.
