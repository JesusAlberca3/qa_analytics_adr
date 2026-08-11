#!/usr/bin/env python3
"""
Analiza X logs STB en ciclo (secuencial o paralelo).

Uso:
  python scripts/batch_analyze.py /ruta/a/carpeta_logs
  python scripts/batch_analyze.py /ruta/a/carpeta_logs --workers 4
  python scripts/batch_analyze.py /ruta/a/carpeta_logs --glob '*.txt' --output-dir data/processed_logs
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_log import analyze_log, load_config


def _analyze_one(args: tuple[str, dict | None]) -> dict:
    path, config = args
    try:
        return analyze_log(path, config=config or {})
    except Exception as exc:  # noqa: BLE001 — batch no debe morir por 1 log
        return {
            "file": Path(path).name,
            "path": path,
            "status": "error",
            "verdict": "ERROR",
            "error": str(exc),
            "traceback": traceback.format_exc()[-500:],
        }


def collect_logs(directory: Path, pattern: str) -> list[Path]:
    files = sorted(directory.glob(pattern))
    return [p for p in files if p.is_file()]


def summarize_row(result: dict) -> dict:
    totals = result.get("totals") or {}
    rates = result.get("rates") or {}
    return {
        "file": result.get("file"),
        "verdict": result.get("verdict"),
        "status": result.get("status"),
        "parsed_lines": result.get("parsed_lines", 0),
        "errors": totals.get("errors", 0),
        "warnings": totals.get("warnings", 0),
        "fatals": totals.get("fatals", 0),
        "errors_clean": totals.get("errors_clean", 0),
        "avg_error_rate_clean_pct": rates.get("avg_error_rate_clean_pct"),
        "spikes_mad_count": result.get("spikes_mad_count", 0),
        "critical_events_count": result.get("critical_events_count", 0),
        "degraded_minutes_clean": result.get("degraded_minutes_clean", 0),
        "error": result.get("error"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Batch análisis de logs STB")
    parser.add_argument("logs_dir", help="Carpeta con archivos .txt")
    parser.add_argument("--glob", default="*.txt", dest="glob_pattern", help="Glob de archivos")
    parser.add_argument("--workers", type=int, default=None, help="Procesos paralelos (1=secuencial)")
    parser.add_argument("--output-dir", default="data/processed_logs", help="Salida JSON + CSV")
    parser.add_argument("--config", help="analysis_config.yaml")
    args = parser.parse_args()

    logs_dir = Path(args.logs_dir)
    if not logs_dir.is_dir():
        print(f"No es un directorio: {logs_dir}", file=sys.stderr)
        return 1

    cfg = load_config(Path(args.config) if args.config else None)
    workers = args.workers
    if workers is None:
        workers = int(cfg.get("batch", {}).get("default_workers", 4))

    files = collect_logs(logs_dir, args.glob_pattern)
    if not files:
        print(f"No hay archivos con patrón {args.glob_pattern} en {logs_dir}")
        return 1

    out = Path(args.output_dir)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Logs a analizar: {len(files)} | workers={workers}")
    jobs = [(str(p), cfg) for p in files]
    results: list[dict] = []

    if workers <= 1:
        for job in jobs:
            r = _analyze_one(job)
            results.append(r)
            print(f"  [{r.get('verdict')}] {r.get('file')}")
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            futures = {pool.submit(_analyze_one, job): job[0] for job in jobs}
            for fut in as_completed(futures):
                r = fut.result()
                results.append(r)
                print(f"  [{r.get('verdict')}] {r.get('file')}")

    # Guardar JSON individual
    for r in results:
        if r.get("status") == "ok":
            stem = Path(r["file"]).stem
            (out / f"{stem}_report.json").write_text(
                json.dumps(r, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    summary = pd.DataFrame([summarize_row(r) for r in results])
    # Orden estable por nombre de archivo
    if "file" in summary.columns:
        summary = summary.sort_values("file").reset_index(drop=True)
    csv_path = out / "batch_summary.csv"
    summary.to_csv(csv_path, index=False)

    print("\n" + "=" * 72)
    print("RESUMEN BATCH")
    print("=" * 72)
    if "verdict" in summary.columns:
        print(summary["verdict"].value_counts().to_string())
    print(f"\nCSV: {csv_path}")
    print(f"JSONs: {out}/*_report.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
