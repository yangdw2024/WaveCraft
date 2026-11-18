#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import traceback
from typing import Dict, List, Tuple
from datetime import datetime

class StartupChecker:
    def __init__(self):
        self._checks: List[Tuple[str, callable]] = []
        self._results: Dict[str, Dict] = {}
        
        self._register_default_checks()
    
    def _register_default_checks(self):
        self._checks = [
            ("python_version", self._check_python_version),
            ("module_imports", self._check_module_imports),
            ("config_file", self._check_config_file),
            ("multiwfn_path", self._check_multiwfn_path),
            ("resource_availability", self._check_resource_availability),
            ("directory_structure", self._check_directory_structure),
            ("permissions", self._check_permissions),
        ]
    
    def _check_python_version(self) -> Tuple[bool, str]:
        required = (3, 8)
        current = sys.version_info[:2]
        if current >= required:
            return True, f"Python {current[0]}.{current[1]} ✓"
        return False, f"Python {current[0]}.{current[1]} < 需要 3.8+"
    
    def _check_module_imports(self) -> Tuple[bool, str]:
        required_modules = [
            "PyQt5.QtWidgets",
            "PyQt5.QtCore",
            "PyQt5.QtGui",
            "psutil",
            "json",
            "threading",
            "subprocess",
            "re",
        ]
        
        missing = []
        for mod in required_modules:
            try:
                __import__(mod)
            except ImportError:
                missing.append(mod)
        
        if missing:
            return False, f"缺少模块: {', '.join(missing)}"
        return True, f"所有 {len(required_modules)} 个模块 ✓"
    
    def _check_config_file(self) -> Tuple[bool, str]:
        try:
            from .config_manager import ConfigManager
            config = ConfigManager()
            if config.config_file.exists():
                return True, f"配置文件: {config.config_file} ✓"
            return True, "配置文件将自动创建 ✓"
        except Exception as e:
            return False, f"配置管理器错误: {str(e)}"
    
    def _check_multiwfn_path(self) -> Tuple[bool, str]:
        try:
            from .multiwfn_service import MultiwfnService
            service = MultiwfnService()
            mwfn_path = service.find_multiwfn()
            if mwfn_path:
                if os.path.exists(mwfn_path):
                    return True, f"Multiwfn: {mwfn_path} ✓"
                return False, f"Multiwfn路径无效: {mwfn_path}"
            return False, "未找到Multiwfn（可在启动后配置）"
        except Exception as e:
            return False, f"Multiwfn服务错误: {str(e)}"
    
    def _check_resource_availability(self) -> Tuple[bool, str]:
        try:
            import psutil
            mem = psutil.virtual_memory()
            if mem.available > 1024 * 1024 * 1024:
                return True, f"可用内存: {mem.available // (1024**2)} MB ✓"
            return False, f"可用内存不足: {mem.available // (1024**2)} MB < 1GB"
        except Exception as e:
            return False, f"资源检查错误: {str(e)}"
    
    def _check_directory_structure(self) -> Tuple[bool, str]:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        required_dirs = [
            os.path.join(root_dir, "config"),
            os.path.join(root_dir, "logs"),
            os.path.join(root_dir, "output"),
        ]
        
        missing = []
        for d in required_dirs:
            if not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
                missing.append(d)
        
        if missing:
            return True, f"创建目录: {', '.join(missing)} ✓"
        return True, "目录结构完整 ✓"
    
    def _check_permissions(self) -> Tuple[bool, str]:
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        test_dir = os.path.join(root_dir, "logs")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "permissions_test.tmp")
        
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            return True, "文件读写权限 ✓"
        except PermissionError:
            return False, f"权限不足: {test_dir}"
        except Exception as e:
            return False, f"权限检查错误: {str(e)}"
    
    def run_all_checks(self) -> Dict[str, Dict]:
        self._results = {}
        all_passed = True
        
        for name, check_func in self._checks:
            start = datetime.now()
            try:
                passed, message = check_func()
                duration = (datetime.now() - start).total_seconds() * 1000
                self._results[name] = {
                    "passed": passed,
                    "message": message,
                    "duration_ms": round(duration, 2),
                    "timestamp": datetime.now().isoformat(),
                }
                if not passed:
                    all_passed = False
            except Exception as e:
                duration = (datetime.now() - start).total_seconds() * 1000
                self._results[name] = {
                    "passed": False,
                    "message": f"检查异常: {str(e)}",
                    "duration_ms": round(duration, 2),
                    "timestamp": datetime.now().isoformat(),
                    "exception": traceback.format_exc(),
                }
                all_passed = False
        
        self._results["summary"] = {
            "total_checks": len(self._checks),
            "passed": sum(1 for r in self._results.values() if r.get("passed")),
            "failed": len(self._checks) - sum(1 for r in self._results.values() if r.get("passed")),
            "all_passed": all_passed,
        }
        
        return self._results
    
    def get_failed_checks(self) -> List[Dict]:
        return [v for v in self._results.values() if isinstance(v, dict) and not v.get("passed")]
    
    def print_report(self):
        print("=" * 60)
        print("启动自检报告")
        print("=" * 60)
        
        for name, result in self._results.items():
            if name == "summary":
                continue
            
            status = "✓" if result["passed"] else "✗"
            print(f"\n[{status}] {name}:")
            print(f"    {result['message']}")
            print(f"    耗时: {result['duration_ms']:.2f} ms")
        
        summary = self._results.get("summary", {})
        print("\n" + "=" * 60)
        print(f"自检结果: {summary.get('passed', 0)}/{summary.get('total_checks', 0)} 通过")
        if summary.get("all_passed"):
            print("状态: 全部通过 ✓")
        else:
            print("状态: 部分失败，请检查")
        print("=" * 60)

class RuntimeMonitor:
    def __init__(self):
        self._watchlist: Dict[str, callable] = {}
        self._thresholds: Dict[str, float] = {}
        self._alerts: List[Dict] = []
    
    def add_watch(self, name: str, watch_func: callable, threshold: float = None):
        self._watchlist[name] = watch_func
        if threshold is not None:
            self._thresholds[name] = threshold
    
    def check_all(self) -> Dict[str, Dict]:
        results = {}
        
        for name, watch_func in self._watchlist.items():
            try:
                value = watch_func()
                threshold = self._thresholds.get(name)
                alert = False
                
                if threshold is not None:
                    if isinstance(value, (int, float)) and value > threshold:
                        alert = True
                        self._record_alert(name, value, threshold)
                
                results[name] = {
                    "value": value,
                    "threshold": threshold,
                    "alert": alert,
                    "timestamp": datetime.now().isoformat(),
                }
            except Exception as e:
                results[name] = {
                    "value": None,
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                }
        
        return results
    
    def _record_alert(self, name: str, value, threshold):
        alert = {
            "timestamp": datetime.now().isoformat(),
            "name": name,
            "value": value,
            "threshold": threshold,
            "message": f"{name} 超过阈值: {value} > {threshold}",
        }
        self._alerts.append(alert)
        if len(self._alerts) > 100:
            self._alerts = self._alerts[-50:]
    
    def get_alerts(self, limit: int = 20) -> List[Dict]:
        return self._alerts[-limit:]
    
    def clear_alerts(self):
        self._alerts = []