# Flujo oficial de análisis — Logs STB/STV ADR

## Objetivo

Triage rápido de logs de tickets QA: **¿hay crash/ANR/fatal?**, **¿cuándo se degradó?**, **¿qué componente domina?**

## Capas (orden de ejecución)

```text
Log .txt
  → 1. Parse regex (logcat A/B)
  → 2. Filtro de ruido (tags plataforma)
  → 3. Ventanas 60s + WEF (All vs Claro)
  → 4. Picos robustos (MAD / Z rolling)
  → 5. Top-N tags + diccionario componentes
  → 6. Co-ocurrencia (PMI) en minutos pico   [reemplaza Apriori como núcleo]
  → 7. Isolation Forest (opcional, Phase 2)  [requiere histórico]
```

| Capa | Técnica | Qué responde |
|------|---------|--------------|
| 1–2 | Parse + ruido | Señal limpia |
| 3 | WEF / rates | Salud del log |
| 4 | MAD | ¿Cuándo? |
| 5 | Top-N + dict | ¿Qué? |
| 6 | PMI | ¿Qué va junto? |
| 7 | IF | Anomalía multivariada |

## Input

| Campo | Descripción |
|-------|-------------|
| Archivo | `.txt` logcat Android (STB/STV) |
| Formato A | `MM-DD HH:MM:SS.mmm PID TID L Tag: msg` |
| Formato B | `MM-DD HH:MM:SS.mmm L/Tag(PID): msg` |

**CLI (recomendado para 1 o N logs):**

```bash
# Un log
python scripts/analyze_log.py /ruta/al/log.txt --output-dir data/processed_logs

# Varios en paralelo
python scripts/batch_analyze.py /ruta/a/carpeta_logs --workers 4 --output-dir data/processed_logs
```

**Notebooks (exploración / PDF):**

| Notebook | Cuándo usarlo | Variable de input |
|----------|---------------|-------------------|
| `crash_event_finder.ipynb` | Triage crash/ANR | `LOG_FILE` |
| `top_detector.ipynb` | Picos + Top-N + PDF | `log_file` |
| `eda_logs.ipynb` | Features + EDA profundo | `log_file` |
| `ml_feature_extractor.ipynb` | Features para ML | `LOG_FILE` |
| `anomaly_detection.ipynb` | Phase 2 (vacío) | features CSV |

## Output

| Artefacto | Ubicación | Contenido |
|-----------|-----------|-----------|
| Reporte JSON | `data/processed_logs/<stem>_report.json` | Veredicto, WEF, picos, tops |
| Resumen batch | `data/processed_logs/batch_summary.csv` | Una fila por log |
| CSV por minuto | opcional vía scripts | errors/warnings/fatals/rate |
| PDF | `data/pdfs/` (solo top_detector) | Reporte compartible QA |
| Plots | `data/plots/` (notebooks) | PNG EDA |

### Campos clave del JSON

- `verdict`: `NORMAL` | `DEGRADADO` | `CRITICO`
- `totals`: E / W / F
- `rates`: error rate global y pico por minuto
- `spikes_mad`: minutos anómalos (MAD)
- `top_error_tags` / `top_error_tags_clean`: con y sin ruido
- `critical_events_sample`: crash / ANR / fatal / restart
- `cooccurrence_pmi`: pares de tags que co-ocurren en picos

## Umbrales y configuración

Definidos en `config/analysis_config.yaml` (y overrides CLI):

| Parámetro | Default | Notas |
|-----------|---------|-------|
| Ventana | 60 s | Misma que notebooks |
| `degradation_error_rate` | 0.06 | Fallback; preferir baseline relativo |
| `mad_z_threshold` | 3.5 | Pico robusto (≈ Z≈3) |
| `min_errors_absolute` | 20 | Evita picos en minutos vacíos |
| `noise_tags` | lista vendor | Filtrar antes de rates “clean” |

## Veredicto (heurística)

1. **CRITICO** — hay fatal (level F) o crash/ANR con pico fuerte
2. **DEGRADADO** — crash de sistema, muchos minutos MAD, o error rate alto post-filtro
3. **NORMAL** — resto

Los umbrales fijos **no generalizan** entre Sony / Hisense / ZTE: usar tasas **clean** (sin ruido) y MAD relativo al propio log.

## Qué no hacer en el núcleo

- No usar Apriori como detector principal (reglas débiles/obvias).
- No usar Z-score global si el log nace saturado.
- No entrenar Isolation Forest sin histórico de logs “normales” por familia de device.

## Relación con notebooks legacy

Los notebooks siguen válidos para exploración y PDF. El **flujo oficial operativo** es `scripts/analyze_log.py` + `scripts/batch_analyze.py`, alineado a las capas de este documento.
