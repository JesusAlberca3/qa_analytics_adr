# STB / STV — QA Analytics de logs ADR

Análisis de logs logcat de Set-Top Boxes / Android TV (ClaroVideo): triage de salud (WEF), picos, componentes y patrones para tickets de QA.

**Esta versión (mirror):** [JesusAlberca3/qa_analytics_adr](https://github.com/JesusAlberca3/qa_analytics_adr)  
**Upstream original:** [atamez6/qa_analytics_adr](https://github.com/atamez6/qa_analytics_adr)

Detalle de cambios: [`docs/CAMBIOS.md`](docs/CAMBIOS.md) · Flujo oficial: [`docs/FLUJO_OFICIAL.md`](docs/FLUJO_OFICIAL.md)

---

## Diferencia vs Atamez6 (`atamez6/qa_analytics_adr`)

| | **Atamez6 (upstream)** | **Esta versión** |
|---|---|---|
| Vía principal | Notebooks Jupyter (`eda_logs`, `top_detector`, …) | **CLI** `scripts/analyze_log.py` + batch paralelo |
| Detección de picos | Z-score global + umbral fijo (`error_rate > 0.06`) | **MAD** relativo al log + rates **clean** (sin ruido) |
| Patrones | Market Basket (**Apriori**) | **PMI** de tags en minutos pico |
| Escala | Un log por Run All | **N logs** con `batch_analyze.py` (`--workers`) |
| Config | Variables hardcodeadas en celdas | `config/analysis_config.yaml` |
| Notebooks | Núcleo del flujo | Siguen vivos para **EDA / PDF**; ops = scripts |
| Docs | README orientado a Phase 1 notebook | Flujo en capas + changelog del mirror |

**Qué se mantiene igual (a propósito):** parse regex logcat A/B, ventana 60 s, contadores WEF, Top-N, diccionario `android_components_dict.py`, notebooks de exploración.

---

## Qué hace este repo

1. Parsear logs `.txt` (logcat Android STB/STV)
2. Filtrar ruido de plataforma (`WifiVendorHal`, `adbd`, …)
3. Agregar por minuto (WEF All vs clean)
4. Detectar picos con MAD
5. Top-N de tags/mensajes + eventos críticos (crash/ANR/fatal)
6. Co-ocurrencia PMI en picos
7. (Opcional / Phase 2) Isolation Forest sobre features clean

---

## Estructura

```text
qa_analytics_adr/
├── config/
│   ├── analysis_config.yaml   # Umbrales, ruido, MAD, PMI (esta versión)
│   ├── stb_config.yaml
│   ├── stv_config.yaml
│   └── shared_config.yaml
├── scripts/                   # Flujo oficial operativo
│   ├── log_parser.py
│   ├── analyze_log.py         # 1 log → consola + JSON
│   └── batch_analyze.py       # N logs en paralelo
├── notebooks/stb/             # Exploración / PDF (upstream + esta versión)
│   ├── crash_event_finder.ipynb
│   ├── eda_logs.ipynb
│   ├── top_detector.ipynb
│   ├── ml_feature_extractor.ipynb
│   ├── anomaly_detection.ipynb
│   └── android_components_dict.py
├── docs/
│   ├── FLUJO_OFICIAL.md
│   ├── CAMBIOS.md
│   ├── ARQUITECTURE.md
│   └── manual_top_detector.md
├── data/
│   ├── processed_logs/        # JSON/CSV de salida CLI
│   ├── plots/
│   └── pdfs/
├── models/
└── requirements.txt
```

---

## Uso rápido (recomendado)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Un log
python scripts/analyze_log.py /ruta/al/log.txt --output-dir data/processed_logs

# Varios logs en paralelo
python scripts/batch_analyze.py /ruta/a/carpeta_logs --workers 4 --output-dir data/processed_logs
```

**Input:** archivo `.txt` logcat  
`MM-DD HH:MM:SS.mmm PID TID L Tag: mensaje`

**Output CLI:**
- `data/processed_logs/<stem>_report.json` — veredicto, WEF, picos MAD, tops, PMI
- `data/processed_logs/batch_summary.csv` — una fila por log (batch)

Veredicto: `NORMAL` | `DEGRADADO` | `CRITICO`

---

## Notebooks (exploración / PDF)

Igual que en Atamez6: edita `log_file` / `LOG_FILE` y Run All.

| Notebook | Uso |
|----------|-----|
| `crash_event_finder.ipynb` | Triage rápido crash/ANR/fatal |
| `top_detector.ipynb` | Top-N + picos + PDF QA |
| `eda_logs.ipynb` | EDA + features + Apriori (legado) |
| `ml_feature_extractor.ipynb` | Features para ML |
| `anomaly_detection.ipynb` | Phase 2 (pendiente) |

---

## Flujo de datos (esta versión)

```text
Raw log (.txt)
    → parse (logcat A/B)
    → filtro ruido
    → ventana 60s + WEF (all / clean)
    → picos MAD
    → Top-N + eventos críticos
    → PMI en minutos pico
    → JSON / batch_summary.csv
         ↘ notebooks: plots / PDF (opcional)
```

Upstream (Atamez6) termina en features CSV + Apriori + plots desde el notebook, sin CLI batch ni MAD/PMI como núcleo.

---

## Stack

- Python 3.10+
- `pandas`, `numpy`, `pyyaml`
- `matplotlib`, `seaborn`, `reportlab` (notebooks / PDF)
- `scikit-learn` (Phase 2), `mlxtend` (Apriori en notebooks legado)

---

## Roadmap

1. ✅ Phase 1 notebooks (upstream)
2. ✅ CLI oficial: ruido + MAD + PMI + batch (esta versión)
3. 🔜 Alinear notebooks a `analysis_config.yaml`
4. 🔜 Baseline por vendor/firmware
5. 🔜 Isolation Forest sobre features clean

---

## License

MIT — ver [LICENSE](LICENSE).

Upstream / autor original: Alberto (Atamez6) — QA & ML Automation, Claro México.  
Mirror y flujo CLI: JesusAlberca3 — Agosto 2026.
