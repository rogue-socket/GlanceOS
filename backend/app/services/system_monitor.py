import psutil
import platform
import sys
from datetime import datetime


def _disk_path() -> str:
    return "C:\\" if sys.platform == "win32" else "/"


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
            "platform": platform.machine(),
            "hostname": platform.node(),
        },
    }
