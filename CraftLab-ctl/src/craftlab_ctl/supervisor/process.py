import os
import sys
import time
import signal
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, List
import psutil
from craftlab_ctl.core.paths import CtlPaths


class ProcessSupervisor:
    def __init__(self, paths: CtlPaths, service_name: str = "backend"):
        self.paths = paths
        self.service_name = service_name
        self.pid_file = self.paths.run_dir / f"{service_name}.pid"

    def get_pid(self) -> Optional[int]:
        if not self.pid_file.exists():
            return None
        try:
            pid_str = self.pid_file.read_text(encoding="utf-8").strip()
            return int(pid_str)
        except Exception:
            return None

    def is_running(self) -> bool:
        pid = self.get_pid()
        if not pid:
            return False
        try:
            proc = psutil.Process(pid)
            return proc.is_running() and proc.status() != psutil.STATUS_ZOMBIE
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            if self.pid_file.exists():
                try:
                    self.pid_file.unlink()
                except Exception:
                    pass
            return False

    def get_status(self) -> Dict[str, Any]:
        pid = self.get_pid()
        if not pid or not self.is_running():
            return {"status": "stopped", "service": self.service_name, "pid": None}

        try:
            proc = psutil.Process(pid)
            create_time = proc.create_time()
            uptime = time.time() - create_time
            mem_info = proc.memory_info()
            return {
                "status": "running",
                "service": self.service_name,
                "pid": pid,
                "uptime_seconds": round(uptime, 2),
                "memory_mb": round(mem_info.rss / (1024 * 1024), 2),
            }
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return {"status": "stopped", "service": self.service_name, "pid": None}

    def start_process(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        env: Optional[Dict[str, str]] = None,
        stdout_file: Optional[Path] = None,
        stderr_file: Optional[Path] = None,
    ) -> int:
        if self.is_running():
            raise RuntimeError(f"Service '{self.service_name}' is already running with PID {self.get_pid()}")

        self.paths.ensure_directories()
        out_f = None
        err_f = None
        if stdout_file:
            out_f = open(stdout_file, "a", encoding="utf-8")
        if stderr_file:
            err_f = open(stderr_file, "a", encoding="utf-8")

        proc_env = os.environ.copy()
        if env:
            proc_env.update(env)

        kwargs: Dict[str, Any] = {
            "cwd": str(cwd) if cwd else str(self.paths.home),
            "env": proc_env,
            "stdout": out_f,
            "stderr": err_f,
        }

        if sys.platform == "win32":
            detached = getattr(subprocess, "DETACHED_PROCESS", 0x00000008)
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP | detached
        else:
            kwargs["preexec_fn"] = os.setsid

        proc = subprocess.Popen(cmd, **kwargs)
        self.pid_file.write_text(str(proc.pid), encoding="utf-8")
        return proc.pid

    def stop_process(self, timeout: float = 10.0) -> bool:
        pid = self.get_pid()
        if not pid or not self.is_running():
            if self.pid_file.exists():
                try:
                    self.pid_file.unlink()
                except Exception:
                    pass
            return True

        try:
            parent = psutil.Process(pid)
            children = parent.children(recursive=True)
            procs = [parent] + children

            # Send graceful termination signal
            if sys.platform == "win32":
                for p in procs:
                    try:
                        p.terminate()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
            else:
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                except Exception:
                    for p in procs:
                        try:
                            p.terminate()
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            pass

            # Wait up to timeout
            gone, alive = psutil.wait_procs(procs, timeout=timeout)
            if alive:
                # Force kill escalation
                for p in alive:
                    try:
                        p.kill()
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        pass
                psutil.wait_procs(alive, timeout=3.0)

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        finally:
            if self.pid_file.exists():
                try:
                    self.pid_file.unlink()
                except Exception:
                    pass

        return not self.is_running()
