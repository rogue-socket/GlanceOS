import psutil
import platform
import sys
import subprocess
from pathlib import Path
from datetime import datetime


def _disk_path() -> str:
    return "C:\\" if sys.platform == "win32" else "/"


def _read_temp_from_psutil() -> tuple[float | None, str | None]:
    try:
        sensors = psutil.sensors_temperatures(fahrenheit=False)
    except Exception:
        return None, None

    if not sensors:
        return None, None

    preferred_keys = [
        "cpu_thermal",
        "coretemp",
        "k10temp",
        "soc_thermal",
        "acpitz",
    ]

    for key in preferred_keys:
        entries = sensors.get(key)
        if not entries:
            continue
        for entry in entries:
            current = getattr(entry, "current", None)
            if isinstance(current, (int, float)) and -20 <= current <= 150:
                return float(current), key

    for key, entries in sensors.items():
        for entry in entries:
            current = getattr(entry, "current", None)
            if isinstance(current, (int, float)) and -20 <= current <= 150:
                return float(current), key

    return None, None


def _read_temp_from_sysfs() -> tuple[float | None, str | None]:
    candidates: list[tuple[float, str, bool]] = []

    for zone_temp in Path("/sys/class/thermal").glob("thermal_zone*/temp"):
        try:
            raw = zone_temp.read_text(encoding="utf-8").strip()
            value = float(raw)
            celsius = value / 1000.0 if value > 1000 else value
            if not (-20 <= celsius <= 150):
                continue

            zone_type_file = zone_temp.parent / "type"
            zone_type = ""
            if zone_type_file.exists():
                zone_type = zone_type_file.read_text(encoding="utf-8").strip().lower()

            preferred = any(
                token in zone_type for token in ("cpu", "soc", "package", "thermal")
            )
            source = f"sysfs:{zone_type or zone_temp.parent.name}"
            candidates.append((celsius, source, preferred))
        except Exception:
            continue

    for hwmon_temp in Path("/sys/class/hwmon").glob("hwmon*/temp*_input"):
        try:
            raw = hwmon_temp.read_text(encoding="utf-8").strip()
            value = float(raw)
            celsius = value / 1000.0 if value > 1000 else value
            if -20 <= celsius <= 150:
                candidates.append((celsius, f"sysfs:{hwmon_temp.parent.name}", False))
        except Exception:
            continue

    if candidates:
        preferred = [entry for entry in candidates if entry[2]]
        if preferred:
            best = max(preferred, key=lambda entry: entry[0])
            return best[0], best[1]
        best = max(candidates, key=lambda entry: entry[0])
        return best[0], best[1]

    return None, None


def _read_temp_from_vcgencmd() -> tuple[float | None, str | None]:
    commands = ["vcgencmd", "/usr/bin/vcgencmd", "/opt/vc/bin/vcgencmd"]

    for cmd in commands:
        try:
            result = subprocess.run(
                [cmd, "measure_temp"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1,
            )
            out = result.stdout.strip()
            # format: temp=48.6'C
            if out.startswith("temp="):
                value_str = out.split("=", 1)[1].split("'", 1)[0]
                celsius = float(value_str)
                if -20 <= celsius <= 150:
                    return celsius, "vcgencmd"
        except Exception:
            continue

    return None, None


def _read_cpu_temperature() -> dict:
    celsius, source = _read_temp_from_psutil()
    if celsius is None:
        celsius, source = _read_temp_from_sysfs()
    if celsius is None:
        celsius, source = _read_temp_from_vcgencmd()

    if celsius is None:
        return {"cpu_c": None, "cpu_f": None, "source": "unavailable"}

    fahrenheit = (celsius * 9 / 5) + 32
    return {
        "cpu_c": round(celsius, 1),
        "cpu_f": round(fahrenheit, 1),
        "source": source or "sensor",
    }


def get_system_stats() -> dict:
    cpu_percent = psutil.cpu_percent(interval=0.5)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage(_disk_path())

    net = psutil.net_io_counters()

    return {
        "type": "system",
        "timestamp": datetime.utcnow().isoformat(),
        "data": {
            "cpu": {
                "percent": cpu_percent,
                "cores": psutil.cpu_count(logical=True),
            },
            "memory": {
                "total": memory.total,
                "used": memory.used,
                "percent": memory.percent,
            },
            "disk": {
                "total": disk.total,
                "used": disk.used,
                "percent": disk.percent,
            },
            "network": {
                "bytes_sent": net.bytes_sent,
                "bytes_recv": net.bytes_recv,
            },
            "temperature": _read_cpu_temperature(),
            "platform": platform.machine(),
            "hostname": platform.node(),
        },
    }
