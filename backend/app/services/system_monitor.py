import psutil
import platform
import sys
import subprocess
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
    zone_paths = [
        "/sys/class/thermal/thermal_zone0/temp",
        "/sys/class/hwmon/hwmon0/temp1_input",
    ]

    for path in zone_paths:
        try:
            with open(path, "r", encoding="utf-8") as f:
                raw = f.read().strip()
            value = float(raw)
            celsius = value / 1000.0 if value > 1000 else value
            if -20 <= celsius <= 150:
                return celsius, "sysfs"
        except Exception:
            continue

    return None, None


def _read_temp_from_vcgencmd() -> tuple[float | None, str | None]:
    try:
        result = subprocess.run(
            ["vcgencmd", "measure_temp"],
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
        return None, None

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
