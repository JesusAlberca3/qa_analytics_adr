#!/usr/bin/env python3
"""
Análisis rápido de un log STB (.txt) — flujo oficial (capa 1–6).

Incluye: parse, filtro ruido, WEF, picos MAD, Top-N, co-ocurrencia PMI.
No genera gráficas (rápido, apto para batch/paralelo).

Uso:
  python scripts/analyze_log.py /ruta/al/log.txt
  python scripts/analyze_log.py /ruta/al/log.txt --output-dir data/processed_logs
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter
from pathlib import Path

import pandas as pd
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
from log_parser import CRITICAL_PATTERNS, get_claro_pids, read_log_file

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG = ROOT / "config" / "analysis_config.yaml"


def load_config(path: Path | None = None) -> dict:
    cfg_path = path or DEFAULT_CONFIG
    if cfg_path.exists():
        with open(cfg_path, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def mad_z_scores(series: pd.Series) -> pd.Series:
    """Z-score basado en MAD (robusto a outliers / logs saturados)."""
    median = series.median()
    mad = (series - median).abs().median()
    if mad == 0 or pd.isna(mad):
        return pd.Series(0.0, index=series.index)
    return 0.6745 * (series - median) / mad


def detect_spikes_mad(
    by_minute: pd.DataFrame,
    *,
    mad_z_threshold: float,
    min_errors: int,
) -> pd.DataFrame:
    df = by_minute.copy()
    df["mad_z"] = mad_z_scores(df["errors"].astype(float))
    spikes = df[(df["mad_z"] >= mad_z_threshold) & (df["errors"] >= min_errors)].copy()
    return spikes.sort_values("mad_z", ascending=False)


def pmi_tag_pairs(
    df: pd.DataFrame,
    spike_minutes: list[str],
    *,
    top_n: int = 10,
    min_pmi: float = 0.5,
) -> list[dict]:
    """
    PMI entre tags de error que co-ocurren en los mismos minutos pico.
    Sustituto práctico de Apriori para triage QA.
    """
    if not spike_minutes:
        return []

    err = df[df["is_error"] & df["time"].isin(spike_minutes)]
    if err.empty:
        return []

    # Tags presentes por minuto
    tags_by_min: dict[str, set[str]] = {}
    for minute, group in err.groupby("time"):
        tags_by_min[str(minute)] = set(group["tag"].unique())

    n_minutes = len(tags_by_min)
    if n_minutes == 0:
        return []

    tag_count: Counter[str] = Counter()
    pair_count: Counter[tuple[str, str]] = Counter()

    for tags in tags_by_min.values():
        for t in tags:
            tag_count[t] += 1
        ordered = sorted(tags)
        for i, a in enumerate(ordered):
            for b in ordered[i + 1 :]:
                pair_count[(a, b)] += 1

    results = []
    for (a, b), c_ab in pair_count.items():
        p_ab = c_ab / n_minutes
        p_a = tag_count[a] / n_minutes
        p_b = tag_count[b] / n_minutes
        if p_a <= 0 or p_b <= 0:
            continue
        pmi = math.log2(p_ab / (p_a * p_b))
        if pmi >= min_pmi:
            results.append(
                {
                    "tag_a": a,
                    "tag_b": b,
                    "co_minutes": int(c_ab),
                    "pmi": round(pmi, 3),
                }
            )

    results.sort(key=lambda x: (-x["pmi"], -x["co_minutes"]))
    return results[:top_n]


def analyze_log(
    log_path: str | Path,
    *,
    config: dict | None = None,
    degradation_error_rate: float | None = None,
    degradation_fatal: int | None = None,
) -> dict:
    """Analiza un log y retorna métricas + eventos (flujo oficial)."""
    cfg = config if config is not None else load_config()
    deg = cfg.get("degradation", {})
    spikes_cfg = cfg.get("spikes", {})
    co_cfg = cfg.get("cooccurrence", {})
    noise_tags = set(cfg.get("noise_tags", []))

    degradation_error_rate = (
        degradation_error_rate
        if degradation_error_rate is not None
        else float(deg.get("error_rate", 0.06))
    )
    degradation_fatal = (
        degradation_fatal
        if degradation_fatal is not None
        else int(deg.get("fatal_count", 1))
    )
    mad_z_threshold = float(spikes_cfg.get("mad_z_threshold", 3.5))
    min_errors = int(spikes_cfg.get("min_errors_absolute", 20))
    min_pmi = float(co_cfg.get("min_pmi", 0.5))
    top_pairs = int(co_cfg.get("top_pairs", 10))

    log_path = Path(log_path)
    if not log_path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {log_path}")

    parsed, unparsed = read_log_file(str(log_path))
    if not parsed:
        return {
            "file": log_path.name,
            "path": str(log_path.resolve()),
            "status": "empty",
            "verdict": "SIN_DATOS",
            "parsed_lines": 0,
            "unparsed_lines": unparsed,
        }

    df = pd.DataFrame(parsed)
    df["is_error"] = df["level"] == "E"
    df["is_warning"] = df["level"] == "W"
    df["is_fatal"] = df["level"] == "F"
    df["is_noise"] = df["tag"].isin(noise_tags)

    claro_pids = get_claro_pids(parsed)
    df["is_claro"] = df["pid"].isin(claro_pids)

    df_clean = df[~df["is_noise"]].copy()

    def _by_minute(frame: pd.DataFrame) -> pd.DataFrame:
        if frame.empty:
            return pd.DataFrame(
                columns=["time", "total", "errors", "warnings", "fatals", "error_rate", "is_degraded"]
            )
        out = (
            frame.groupby("time")
            .agg(
                total=("level", "count"),
                errors=("is_error", "sum"),
                warnings=("is_warning", "sum"),
                fatals=("is_fatal", "sum"),
            )
            .reset_index()
        )
        out["error_rate"] = out["errors"] / out["total"].replace(0, 1)
        out["is_degraded"] = (out["error_rate"] > degradation_error_rate) | (
            out["fatals"] >= degradation_fatal
        )
        return out

    by_minute = _by_minute(df)
    by_minute_clean = _by_minute(df_clean)

    spikes = detect_spikes_mad(
        by_minute_clean if not by_minute_clean.empty else by_minute,
        mad_z_threshold=mad_z_threshold,
        min_errors=min_errors,
    )
    spike_minutes = spikes["time"].astype(str).tolist() if len(spikes) else []

    # Aviso: errores altos desde el inicio (Z global engaña)
    high_from_start = False
    if len(by_minute) > 1:
        first = by_minute.iloc[0]
        mean_err = by_minute["errors"].mean()
        if first["errors"] > mean_err * 0.8 and mean_err > 0:
            high_from_start = True

    events: list[dict] = []
    for event_type, pattern in CRITICAL_PATTERNS.items():
        matches = df[df["message"].str.contains(pattern.pattern, case=False, regex=True, na=False)]
        for _, row in matches.iterrows():
            events.append(
                {
                    "type": event_type,
                    "time": row["time"],
                    "level": row["level"],
                    "tag": row["tag"],
                    "message": row["message"][:200],
                }
            )

    levels = df["level"].value_counts().to_dict()
    avg_error_rate = float(df["is_error"].sum() / len(df))
    avg_error_rate_clean = (
        float(df_clean["is_error"].sum() / len(df_clean)) if len(df_clean) else 0.0
    )
    max_error_rate = float(by_minute["error_rate"].max()) if len(by_minute) else 0.0
    max_error_rate_clean = (
        float(by_minute_clean["error_rate"].max()) if len(by_minute_clean) else 0.0
    )
    degraded_minutes = int(by_minute["is_degraded"].sum()) if len(by_minute) else 0
    degraded_minutes_clean = (
        int(by_minute_clean["is_degraded"].sum()) if len(by_minute_clean) else 0
    )

    has_fatal = int(df["is_fatal"].sum()) > 0
    has_crash = any(e["type"] in ("crash", "anr", "fatal_msg") for e in events)
    n_spikes = len(spikes)

    # Veredicto: prioriza métricas clean + MAD
    if has_fatal or (has_crash and max_error_rate_clean > 0.3):
        verdict = "CRITICO"
    elif has_crash or n_spikes >= 2 or degraded_minutes_clean > 5 or avg_error_rate_clean > 0.05:
        verdict = "DEGRADADO"
    elif degraded_minutes > 5 or avg_error_rate > 0.05:
        verdict = "DEGRADADO"
    else:
        verdict = "NORMAL"

    top_error_tags = df.loc[df["is_error"], "tag"].value_counts().head(10).to_dict()
    top_error_tags_clean = (
        df_clean.loc[df_clean["is_error"], "tag"].value_counts().head(10).to_dict()
        if len(df_clean)
        else {}
    )
    top_error_messages = df.loc[df["is_error"], "message"].value_counts().head(5).to_dict()
    worst_minutes = (
        by_minute.sort_values("errors", ascending=False)
        .head(5)[["time", "errors", "total", "error_rate"]]
        .to_dict("records")
    )

    cooccurrence = pmi_tag_pairs(
        df_clean if len(df_clean) else df,
        spike_minutes,
        top_n=top_pairs,
        min_pmi=min_pmi,
    )

    spikes_records = (
        spikes.head(10)[["time", "errors", "total", "error_rate", "mad_z"]]
        .to_dict("records")
        if len(spikes)
        else []
    )

    return {
        "file": log_path.name,
        "path": str(log_path.resolve()),
        "status": "ok",
        "verdict": verdict,
        "pipeline": "official_v1_mad_noise_pmi",
        "time_range": {
            "start": f"{df['date'].iloc[0]} {df['time_raw'].iloc[0]}",
            "end": f"{df['date'].iloc[-1]} {df['time_raw'].iloc[-1]}",
            "minutes": int(df["time"].nunique()),
        },
        "parsed_lines": len(df),
        "unparsed_lines": unparsed,
        "noise_filtered_lines": int(df["is_noise"].sum()),
        "levels": {k: int(v) for k, v in levels.items()},
        "totals": {
            "errors": int(df["is_error"].sum()),
            "warnings": int(df["is_warning"].sum()),
            "fatals": int(df["is_fatal"].sum()),
            "errors_clean": int(df_clean["is_error"].sum()) if len(df_clean) else 0,
        },
        "rates": {
            "avg_error_rate_pct": round(avg_error_rate * 100, 2),
            "avg_error_rate_clean_pct": round(avg_error_rate_clean * 100, 2),
            "max_minute_error_rate_pct": round(max_error_rate * 100, 2),
            "max_minute_error_rate_clean_pct": round(max_error_rate_clean * 100, 2),
        },
        "degraded_minutes": degraded_minutes,
        "degraded_minutes_clean": degraded_minutes_clean,
        "spikes_mad": spikes_records,
        "spikes_mad_count": n_spikes,
        "high_errors_from_start": high_from_start,
        "claro_pids": len(claro_pids),
        "critical_events_count": len(events),
        "critical_events_sample": events[:15],
        "top_error_tags": top_error_tags,
        "top_error_tags_clean": top_error_tags_clean,
        "top_error_messages": {k[:100]: v for k, v in top_error_messages.items()},
        "worst_minutes": worst_minutes,
        "cooccurrence_pmi": cooccurrence,
    }


def print_report(result: dict) -> None:
    print("=" * 72)
    print(f"LOG: {result.get('file', '?')}")
    print("=" * 72)

    if result.get("status") == "empty":
        print("Sin líneas parseables.")
        return

    tr = result["time_range"]
    t = result["totals"]
    r = result["rates"]

    print(f"Rango: {tr['start']} → {tr['end']} ({tr['minutes']} min)")
    print(
        f"Parseadas: {result['parsed_lines']:,} | "
        f"No parseadas: {result['unparsed_lines']:,} | "
        f"Ruido filtrado: {result.get('noise_filtered_lines', 0):,}"
    )
    print(
        f"E/W/F: {t['errors']:,} / {t['warnings']:,} / {t['fatals']:,} "
        f"(errors clean: {t.get('errors_clean', 0):,})"
    )
    print(
        f"Error rate: {r['avg_error_rate_pct']}% "
        f"(clean: {r['avg_error_rate_clean_pct']}%) | "
        f"pico min clean: {r['max_minute_error_rate_clean_pct']}%"
    )
    print(
        f"Minutos degradados: {result['degraded_minutes']} "
        f"(clean: {result.get('degraded_minutes_clean', 0)}) | "
        f"Picos MAD: {result.get('spikes_mad_count', 0)} | "
        f"PIDs Claro: {result['claro_pids']}"
    )
    if result.get("high_errors_from_start"):
        print("⚠ Errores altos desde el inicio — no confiar en Z-score global solo.")

    print(f"Eventos críticos: {result['critical_events_count']}")
    if result["critical_events_sample"]:
        print("\n--- Eventos críticos (muestra) ---")
        for e in result["critical_events_sample"][:8]:
            print(f"  [{e['time']}] {e['type']} | {e['level']} {e['tag']}: {e['message'][:90]}")

    print("\n--- Top tags con errores (raw) ---")
    for tag, cnt in result["top_error_tags"].items():
        print(f"  {tag}: {cnt}")

    if result.get("top_error_tags_clean"):
        print("\n--- Top tags con errores (sin ruido) ---")
        for tag, cnt in result["top_error_tags_clean"].items():
            print(f"  {tag}: {cnt}")

    if result.get("spikes_mad"):
        print("\n--- Picos MAD ---")
        for s in result["spikes_mad"][:5]:
            print(
                f"  {s['time']}: {int(s['errors'])} err / {int(s['total'])} "
                f"(rate={s['error_rate']*100:.1f}%, mad_z={s['mad_z']:.1f})"
            )

    if result.get("cooccurrence_pmi"):
        print("\n--- Co-ocurrencia PMI (tags en picos) ---")
        for p in result["cooccurrence_pmi"][:5]:
            print(
                f"  {p['tag_a']} + {p['tag_b']}: "
                f"PMI={p['pmi']} ({p['co_minutes']} min)"
            )

    print("\n--- Peores minutos ---")
    for m in result["worst_minutes"]:
        print(
            f"  {m['time']}: {int(m['errors'])} errores / {int(m['total'])} logs "
            f"({m['error_rate']*100:.1f}%)"
        )

    icon = {"CRITICO": "🔴", "DEGRADADO": "🟡", "NORMAL": "🟢"}.get(result["verdict"], "")
    print(f"\nVEREDICTO: {icon} {result['verdict']}")
    print("=" * 72)


def main() -> int:
    parser = argparse.ArgumentParser(description="Analiza un log STB Android (.txt)")
    parser.add_argument("log_file", help="Ruta al archivo .txt")
    parser.add_argument("--output-dir", help="Guarda JSON en este directorio")
    parser.add_argument("--config", help="Ruta a analysis_config.yaml")
    parser.add_argument("--json-only", action="store_true", help="Solo imprime JSON")
    args = parser.parse_args()

    cfg = load_config(Path(args.config) if args.config else None)
    result = analyze_log(args.log_file, config=cfg)

    if args.json_only:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print_report(result)

    if args.output_dir:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        stem = Path(args.log_file).stem
        json_path = out / f"{stem}_report.json"
        json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\nJSON: {json_path}")

    return 0 if result.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
