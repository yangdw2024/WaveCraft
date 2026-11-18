#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import sys
import threading
from pathlib import Path
from typing import Any, Dict, Optional, Callable, List


class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_file=None):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, config_file=None):
        if self._initialized:
            return

        if config_file is None:
            # 参考 VS Code / JetBrains 做法：打包后的配置文件放在用户数据目录
            if getattr(sys, "frozen", False):
                base_dir = Path(os.path.expandvars(r"%APPDATA%")) / "WaveCraft"
            else:
                base_dir = Path(__file__).parent.parent.parent
            config_file = base_dir / "config" / "app_config.json"

        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        self._data: Dict[str, Any] = {}
        self._defaults = self._build_defaults()
        self._listeners: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

        self._load()
        self._initialized = True

    def _build_defaults(self) -> Dict[str, Any]:
        return {
            "multiwfn": {
                "exe_path": "",
                "auto_detect": True,
                "nthreads": 8,
                "work_dir": "",
            },
            "visualization": {
                "vmd_path": "",
                "default_view": "ballstick",
                "isosurface_value": 0.02,
                "color_scheme": "default",
            },
            "system": {
                "theme": "dark",
                "language": "zh_CN",
                "log_level": "INFO",
                "auto_save_config": True,
                "output_dir": "./output",
            },
            "resources": {
                "max_memory_gb": 0,
                "max_cpu_cores": 0,
                "disk_warning_threshold_gb": 10.0,
            },
            "history": {
                "recent_files": [],
                "max_recent": 10,
                "command_history": [],
            },
            "analysis": {
                "charge_method": "ADCH",
                "bond_order_method": "Mayer",
                "grid_spacing": 0.1,
                "plot_resolution": 1000,
            },
        }

    def _load(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    self._data = loaded
            except Exception:
                self._data = {}
        else:
            self._data = {}

    def _save(self):
        if self._data.get("system", {}).get("auto_save_config", True):
            try:
                with open(self.config_file, "w", encoding="utf-8") as f:
                    json.dump(self._data, f, indent=2, ensure_ascii=False)
            except Exception:
                pass

    def get(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        data = self._data
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return self._get_default(key, default)
        return data

    def _get_default(self, key: str, default: Any = None) -> Any:
        parts = key.split(".")
        data = self._defaults
        for part in parts:
            if isinstance(data, dict) and part in data:
                data = data[part]
            else:
                return default
        return data

    def set(self, key: str, value: Any):
        with self._lock:
            parts = key.split(".")
            data = self._data
            for i, part in enumerate(parts[:-1]):
                if part not in data:
                    data[part] = {}
                data = data[part]
            old_value = data.get(parts[-1])
            data[parts[-1]] = value
            self._save()
            self._notify(key, old_value, value)

    def _notify(self, key: str, old_value: Any, new_value: Any):
        if key in self._listeners:
            for listener in self._listeners[key]:
                try:
                    listener(key, old_value, new_value)
                except Exception:
                    pass

    def add_listener(self, key: str, callback: Callable):
        with self._lock:
            if key not in self._listeners:
                self._listeners[key] = []
            if callback not in self._listeners[key]:
                self._listeners[key].append(callback)

    def remove_listener(self, key: str, callback: Callable):
        with self._lock:
            if key in self._listeners and callback in self._listeners[key]:
                self._listeners[key].remove(callback)

    def reset_to_defaults(self):
        with self._lock:
            self._data = {}
            self._save()

    def get_all(self) -> Dict[str, Any]:
        result = {}
        for key in self._defaults.keys():
            result[key] = self.get(key)
        return result