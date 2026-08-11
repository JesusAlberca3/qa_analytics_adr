"""Utilidades compartidas para parsear logs Android STB/STV (logcat)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any

# Formato A: MM-DD HH:MM:SS.mmm PID TID LEVEL Tag: mensaje
PATTERN_A = re.compile(
    r"^(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}\.\d{3})\s+(\d+)\s+(\d+)\s+"
    r"([VDIWEF])\s+([^:]+):\s+(.+)$"
)
# Formato B: MM-DD HH:MM:SS.mmm LEVEL/Tag(PID): mensaje
PATTERN_B = re.compile(
    r"^(\d{2}-\d{2})\s+(\d{2}:\d{2}:\d{2}\.\d{3})\s+"
    r"([VDIWEF])/([^(]+)\(\s*(\d+)\):\s+(.+)$"
)

CLARO_PID_PATTERN = re.compile(r"(?i)(claro|amx\.?|clarotv|launcher|com\.amx)")

CRITICAL_PATTERNS = {
    "crash": re.compile(r"crash|CRASH|crashed", re.I),
    "anr": re.compile(r"ANR|not responding|Input dispatching timed out", re.I),
    "fatal_msg": re.compile(r"fatal|FATAL", re.I),
    "restart": re.compile(r"restart.*crashed|Scheduling restart", re.I),
    "force_close": re.compile(r"Force.*close|Force.*stop", re.I),
}


def parse_line(line: str) -> dict[str, Any] | None:
    """Parsea una línea de logcat. Retorna None si no coincide con formatos conocidos."""
    if not line or line.startswith("-----"):
        return None

    match = PATTERN_A.match(line)
    if match:
        return {
            "date": match.group(1),
            "time_raw": match.group(2),
            "pid": match.group(3),
            "tid": match.group(4),
            "level": match.group(5),
            "tag": match.group(6).strip(),
            "message": match.group(7),
        }

    match = PATTERN_B.match(line)
    if match:
        pid = match.group(5).strip()
        return {
            "date": match.group(1),
            "time_raw": match.group(2),
            "level": match.group(3),
            "tag": match.group(4).strip(),
            "pid": pid,
            "tid": pid,
            "message": match.group(6),
        }

    return None


def time_to_minute(time_raw: str) -> str:
    """Redondea HH:MM:SS.mmm a HH:MM (ventana de 60 s usada en los notebooks)."""
    dt = datetime.strptime(time_raw, "%H:%M:%S.%f")
    return dt.replace(second=0, microsecond=0).strftime("%H:%M")


def read_log_file(filepath: str) -> tuple[list[dict[str, Any]], int]:
    """
    Lee un archivo .txt y retorna (lista parseada, líneas no parseadas).

    encoding=utf-8 con errors='ignore' — igual que en los notebooks.
    """
    parsed: list[dict[str, Any]] = []
    unparsed = 0

    with open(filepath, "r", encoding="utf-8", errors="ignore") as handle:
        for raw in handle:
            line = raw.strip()
            if not line:
                unparsed += 1
                continue
            entry = parse_line(line)
            if entry is None:
                unparsed += 1
                continue
            entry["time"] = time_to_minute(entry["time_raw"])
            parsed.append(entry)

    return parsed, unparsed


def get_claro_pids(parsed_logs: list[dict[str, Any]]) -> set[str]:
    """PIDs asociados a procesos Claro/AMX según el mensaje del log."""
    pids: set[str] = set()
    for log in parsed_logs:
        if CLARO_PID_PATTERN.search(log["message"]):
            pids.add(log["pid"])
    return pids
