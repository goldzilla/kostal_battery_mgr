from pathlib import Path
from datetime import datetime, time
from zoneinfo import ZoneInfo
import tempfile, os

# Konstanten: Reihenfolge bleibt erhalten (Python 3.7+)
CONSTS = {
    "STATE_BLOCKED": 0,
    "STATE_CHARGING": 1,
    "STATE_NORMAL": 2,
    "STATE_FORCED_DISCHARGE": 3,
    "STATE_UNDEFINED": 255,
}

def parse_time(hhmm: str) -> time:
    """'HH:MM' -> datetime.time"""
    hh, mm = hhmm.split(":")
    return time(int(hh), int(mm))

def parse_interval(interval_str: str) -> tuple[time, time]:
    """'HH:MM-HH:MM' -> (start_time, end_time)"""
    start_s, end_s = interval_str.split("-")
    return parse_time(start_s), parse_time(end_s)

def time_in_interval(t: time, iv: tuple[time, time]) -> bool:
    """Unterstützt Intervalle über Mitternacht (z.B. 22:00-06:00)."""
    start, end = iv
    if start <= end:
        return start <= t < end
    return t >= start or t < end

def any_interval_matches(t: time, intervals: list[tuple[time, time]]) -> bool:
    return any(time_in_interval(t, iv) for iv in intervals)

def build_file_content(active_state_name: str, write_numeric: bool = False) -> str:
    """Erzeugt den Text für die Datei, inkl. STATE_SET-Zeile."""
    lines = [f"{k} = {v}" for k, v in CONSTS.items()]
    if write_numeric:
        lines.append(f"STATE_SET = {CONSTS[active_state_name]}")
    else:
        lines.append(f"STATE_SET = {active_state_name}")
    lines.append("")  # newline am Ende
    return "\n".join(lines)

def write_atomic(path: Path, content: str) -> None:
    """Atomisches Schreiben (erst temp, dann replace)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, dir=str(path.parent)) as tmp:
        tmp.write(content)
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)

def set_kostal_state(
    file_path: str | Path = "kostal_battery_state",
    intervals: list[str] = None,
    tz: str = "Europe/Berlin",
    state_in_window: str = "STATE_CHARGING",
    state_default: str = "STATE_NORMAL",
    write_numeric: bool = False,
    return_content: bool = False,
):
    """
    Schreibt die Datei 'kostal_battery_state' mit Konstanten und STATE_SET.
    
    Args:
        file_path: Zielpfad/Dateiname.
        intervals: Liste von Strings wie ["06:30-08:00", "12:00-13:30"].
                   Intervalle können über Mitternacht gehen, z.B. "22:00-06:00".
        tz: IANA-TZ (Standard: Europe/Berlin).
        state_in_window: State-Name innerhalb der Intervalle, z.B. 'STATE_CHARGING'.
        state_default: State-Name außerhalb der Intervalle, z.B. 'STATE_NORMAL'.
        write_numeric: Wenn True, wird STATE_SET als Zahl geschrieben (z.B. '1').
        return_content: Wenn True, gibt die Funktion den Dateitext zurück.
    """
    if intervals is None or len(intervals) == 0:
        raise ValueError("Bitte mindestens ein Intervall angeben, z.B. ['06:30-08:00'].")

    if state_in_window not in CONSTS or state_default not in CONSTS:
        valid = ", ".join(CONSTS.keys())
        raise ValueError(f"Ungültiger State-Name. Erlaubt: {valid}")

    # Zeiten vorbereiten
    parsed = [parse_interval(iv) for iv in intervals]

    now = datetime.now(ZoneInfo(tz))
    current_t = now.time()

    in_window = any_interval_matches(current_t, parsed)
    active_state = state_in_window if in_window else state_default

    content = build_file_content(active_state, write_numeric=write_numeric)
    write_atomic(Path(file_path), content)

    info = {
        "now": now.isoformat(),
        "in_window": in_window,
        "active_state": active_state,
        "file": str(file_path),
        "write_numeric": write_numeric,
    }
    if return_content:
        return info, content
    return info
