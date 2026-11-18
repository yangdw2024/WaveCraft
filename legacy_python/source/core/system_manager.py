#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any

class SystemManager:
    _instance = None
    _lock = threading.Lock()

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
        
        self._health_checks: Dict[str, Callable] = {}
        self._error_history: List[Dict] = []
        self._performance_records: List[Dict] = []
        self._recovery_actions: Dict[str, Callable] = {}
        self._experience_base: Dict[str, List[Dict]] = {}
        self._validation_results: Dict[str, Dict] = {}
        
        self._start_time = datetime.now()
        self._last_report_time = datetime.now()
        self._monitor_interval = 5
        
        self._initialized = True

    def register_health_check(self, name: str, check_func: Callable):
        self._health_checks[name] = check_func

    def run_health_checks(self) -> Dict[str, bool]:
        results = {}
        for name, check_func in self._health_checks.items():
            try:
                results[name] = check_func()
            except Exception as e:
                results[name] = False
                self.record_error("health_check", name, str(e))
        return results

    def record_error(self, error_type: str, component: str, message: str, details: str = ""):
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "component": component,
            "message": message,
            "details": details,
            "stack_trace": traceback.format_exc() if details else "",
        }
        self._error_history.append(error_record)
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-500:]

    def get_error_history(self, limit: int = 50) -> List[Dict]:
        return self._error_history[-limit:]

    def record_performance(self, operation: str, duration_ms: float, success: bool, data_size: int = 0):
        record = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "duration_ms": duration_ms,
            "success": success,
            "data_size": data_size,
        }
        self._performance_records.append(record)
        if len(self._performance_records) > 5000:
            self._performance_records = self._performance_records[-2000:]

    def get_performance_summary(self, hours: int = 24) -> Dict:
        cutoff = datetime.now() - timedelta(hours=hours)
        recent = [r for r in self._performance_records if datetime.fromisoformat(r["timestamp"]) > cutoff]
        
        if not recent:
            return {"total_operations": 0, "avg_duration_ms": 0, "success_rate": 0}
        
        success_count = sum(1 for r in recent if r["success"])
        avg_duration = sum(r["duration_ms"] for r in recent) / len(recent)
        
        return {
            "total_operations": len(recent),
            "avg_duration_ms": round(avg_duration, 2),
            "success_rate": round(success_count / len(recent) * 100, 2),
            "operations_by_type": self._group_by_operation(recent),
        }

    def _group_by_operation(self, records: List[Dict]) -> Dict[str, Dict]:
        result = {}
        for r in records:
            op = r["operation"]
            if op not in result:
                result[op] = {"count": 0, "total_duration_ms": 0, "success": 0}
            result[op]["count"] += 1
            result[op]["total_duration_ms"] += r["duration_ms"]
            if r["success"]:
                result[op]["success"] += 1
        return result

    def register_recovery_action(self, error_type: str, action: Callable):
        self._recovery_actions[error_type] = action

    def execute_recovery(self, error_type: str, **kwargs) -> bool:
        if error_type in self._recovery_actions:
            try:
                self._recovery_actions[error_type](**kwargs)
                return True
            except Exception as e:
                self.record_error("recovery", error_type, str(e))
                return False
        return False

    def add_experience(self, category: str, experience: Dict):
        if category not in self._experience_base:
            self._experience_base[category] = []
        experience["added_at"] = datetime.now().isoformat()
        self._experience_base[category].append(experience)

    def get_experiences(self, category: str = None) -> List[Dict]:
        if category:
            return self._experience_base.get(category, [])
        return [item for cat in self._experience_base.values() for item in cat]

    def record_validation(self, test_name: str, passed: bool, message: str = "", duration_ms: float = 0):
        self._validation_results[test_name] = {
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "message": message,
            "duration_ms": duration_ms,
        }

    def get_validation_summary(self) -> Dict:
        passed = sum(1 for r in self._validation_results.values() if r["passed"])
        total = len(self._validation_results)
        return {
            "total_tests": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": round(passed / total * 100, 2) if total > 0 else 0,
            "results": self._validation_results,
        }

    def generate_report(self) -> Dict:
        uptime = datetime.now() - self._start_time
        health = self.run_health_checks()
        perf = self.get_performance_summary()
        validation = self.get_validation_summary()
        errors = self.get_error_history(10)
        
        report = {
            "report_time": datetime.now().isoformat(),
            "uptime": str(uptime),
            "health_status": health,
            "performance": perf,
            "validation": validation,
            "recent_errors": errors,
            "system_info": self._get_system_info(),
        }
        
        self._last_report_time = datetime.now()
        return report

    def _get_system_info(self) -> Dict:
        try:
            import psutil
            return {
                "cpu_count": psutil.cpu_count(),
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage("/").percent,
                "python_version": sys.version,
                "platform": sys.platform,
            }
        except ImportError:
            return {
                "python_version": sys.version,
                "platform": sys.platform,
            }

    def save_report(self, filepath: str = None):
        report = self.generate_report()
        if filepath is None:
            # 参考 VS Code / JetBrains 做法：打包后的报告放在用户数据目录
            if getattr(sys, "frozen", False):
                base_dir = Path(os.path.expandvars(r"%APPDATA%")) / "WaveCraft"
            else:
                base_dir = Path(__file__).parent.parent.parent
            filepath = base_dir / "logs" / "system_report.json"
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def start_monitoring(self):
        def monitor_loop():
            while True:
                try:
                    self.run_health_checks()
                    self.save_report()
                except Exception:
                    pass
                time.sleep(self._monitor_interval)
        
        self._monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitor_thread.start()

system_manager = SystemManager()