# 🏗️ Arquitectura Técnica - STB Predictive QA Analytics

## Visión General

Pipeline de triage QA para logs STB/STV Android (ClaroVideo).  
El **flujo oficial operativo** está en `docs/FLUJO_OFICIAL.md` y se ejecuta vía `scripts/`.

```text
Raw log (.txt)
    │
    ▼
scripts/log_parser.py          ← regex logcat A/B
    │
    ▼
scripts/analyze_log.py         ← ruido → WEF → MAD → Top-N → PMI
    │
    ├─ JSON report (1 log)
    └─ batch_analyze.py        ← N logs en paralelo → batch_summary.csv
```

Los notebooks (`top_detector`, `eda_logs`, …) siguen siendo la capa de **exploración / PDF**.  
Apriori e Isolation Forest no son el núcleo del triage (ver `docs/CAMBIOS.md`).