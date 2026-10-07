import time
from pathlib import Path
from typing import Dict, Any, Optional
import psutil

from craftlab_ctl.core.paths import CtlPaths
from craftlab_ctl.supervisor import ProcessSupervisor


def collect_system_metrics(paths: CtlPaths, supervisor: Optional[ProcessSupervisor] = None) -> Dict[str, Any]:
    # Host Metrics
    vm = psutil.virtual_memory()
    disk = psutil.disk_usage(str(paths.data_dir if paths.data_dir.exists() else paths.home))
    host_cpu = psutil.cpu_percent(interval=None)

    host_data = {
        "cpu_percent": host_cpu,
        "memory": {
            "total_bytes": vm.total,
            "used_bytes": vm.used,
            "free_bytes": vm.available,
            "percent": vm.percent,
            "total_mb": round(vm.total / (1024 * 1024), 2),
            "used_mb": round(vm.used / (1024 * 1024), 2),
        },
        "disk": {
            "total_bytes": disk.total,
            "used_bytes": disk.used,
            "free_bytes": disk.free,
            "percent": disk.percent,
            "total_gb": round(disk.total / (1024 * 1024 * 1024), 2),
            "free_gb": round(disk.free / (1024 * 1024 * 1024), 2),
        },
    }

    # Process Metrics
    process_data: Dict[str, Any] = {
        "status": "stopped",
        "service": "backend",
        "pid": None,
        "cpu_percent": 0.0,
        "memory_mb": 0.0,
        "threads": 0,
        "uptime_seconds": 0.0,
    }

    if supervisor and supervisor.is_running():
        pid = supervisor.get_pid()
        if pid:
            try:
                proc = psutil.Process(pid)
                process_data = {
                    "status": "running",
                    "service": supervisor.service_name,
                    "pid": pid,
                    "cpu_percent": proc.cpu_percent(interval=None),
                    "memory_mb": round(proc.memory_info().rss / (1024 * 1024), 2),
                    "threads": proc.num_threads(),
                    "uptime_seconds": round(time.time() - proc.create_time(), 2),
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    return {
        "timestamp": time.time(),
        "host": host_data,
        "process": process_data,
    }
