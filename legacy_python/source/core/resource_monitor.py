#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import platform
from typing import Dict, Optional

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False


class ResourceMonitor:
    _instance = None
    _lock = __import__('threading').Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cpu_info_cached = None

    def get_cpu_info(self) -> Dict:
        if self._cpu_info_cached:
            return self._cpu_info_cached

        cpu_info = {
            "name": "CPU",
            "cores": os.cpu_count() or 4,
            "threads": os.cpu_count() or 4,
            "architecture": platform.machine(),
        }

        if PSUTIL_AVAILABLE:
            try:
                freq = psutil.cpu_freq()
                if freq:
                    cpu_info["frequency_mhz"] = freq.max or freq.current
                cpu_info["cores"] = psutil.cpu_count(logical=False) or cpu_info["cores"]
                cpu_info["threads"] = psutil.cpu_count(logical=True) or cpu_info["threads"]
            except Exception:
                pass

        self._cpu_info_cached = cpu_info
        return cpu_info

    def get_total_memory_gb(self) -> float:
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                return round(mem.total / (1024 ** 3), 1)
            except Exception:
                pass
        return 8.0

    def get_available_memory_gb(self) -> float:
        if PSUTIL_AVAILABLE:
            try:
                mem = psutil.virtual_memory()
                return round(mem.available / (1024 ** 3), 1)
            except Exception:
                pass
        return 2.0

    def get_cpu_usage(self) -> float:
        if PSUTIL_AVAILABLE:
            try:
                return psutil.cpu_percent(interval=0.1)
            except Exception:
                pass
        return 0.0

    def get_memory_usage_percent(self) -> float:
        if PSUTIL_AVAILABLE:
            try:
                return psutil.virtual_memory().percent
            except Exception:
                pass
        return 0.0

    def get_disk_space_gb(self, path: str = None) -> Dict:
        if path is None:
            path = os.path.expanduser("~")

        if PSUTIL_AVAILABLE:
            try:
                usage = psutil.disk_usage(path)
                return {
                    "total": round(usage.total / (1024 ** 3), 1),
                    "free": round(usage.free / (1024 ** 3), 1),
                    "used": round(usage.used / (1024 ** 3), 1),
                }
            except Exception:
                pass

        return {"total": 0.0, "free": 0.0, "used": 0.0}

    def get_gpu_info(self) -> Dict:
        gpu_info = {"available": False, "count": 0, "names": [], "memories": []}

        if PSUTIL_AVAILABLE:
            try:
                if hasattr(psutil, 'sensors_gpu'):
                    gpus = psutil.sensors_gpu()
                    if gpus:
                        gpu_info["count"] = len(gpus)
                        gpu_info["available"] = True
                        for gpu in gpus:
                            gpu_info["names"].append(getattr(gpu, 'label', 'GPU'))
            except Exception:
                pass

        return gpu_info

    def get_system_info(self) -> Dict:
        return {
            "os": f"{platform.system()} {platform.release()}",
            "python": platform.python_version(),
            "cpu": self.get_cpu_info(),
            "memory": {
                "total_gb": self.get_total_memory_gb(),
                "available_gb": self.get_available_memory_gb(),
            },
            "disk": self.get_disk_space_gb(),
            "gpu": self.get_gpu_info(),
        }

    def get_resource_info(self) -> Dict:
        return {
            "cpu_percent": self.get_cpu_usage(),
            "memory_percent": self.get_memory_usage_percent(),
        }