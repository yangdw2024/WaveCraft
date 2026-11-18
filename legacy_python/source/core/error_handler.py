#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import time
import json
import threading
import traceback
from datetime import datetime
from typing import Dict, List, Optional, Callable, Any
from enum import Enum


class ErrorCategory(Enum):
    CONFIG = "config"
    MULTIWFN = "multiwfn"
    CALCULATION = "calculation"
    UI = "ui"
    SYSTEM = "system"
    NETWORK = "network"


class ErrorSeverity(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MultiwfnError(Exception):
    def __init__(self, message: str, category: ErrorCategory = None, severity: ErrorSeverity = None):
        super().__init__(message)
        self.category = category or ErrorCategory.MULTIWFN
        self.severity = severity or ErrorSeverity.ERROR
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "message": str(self),
            "category": self.category.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
        }

class ErrorHandler:
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
        
        self._error_handlers: Dict[str, List[Callable]] = {}
        self._recovery_strategies: Dict[str, Callable] = {}
        self._error_history: List[Dict] = []
        self._error_counts: Dict[str, int] = {}
        self._max_retries = 3
        self._retry_delay = 1.0
        
        self._initialized = True

    def register_handler(self, error_type: str, handler: Callable):
        if error_type not in self._error_handlers:
            self._error_handlers[error_type] = []
        if handler not in self._error_handlers[error_type]:
            self._error_handlers[error_type].append(handler)

    def register_recovery(self, error_type: str, strategy: Callable):
        self._recovery_strategies[error_type] = strategy

    def handle_error(self, error_type: str, message: str, exc_info=None, **kwargs):
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "exc_info": traceback.format_exception(*exc_info) if exc_info else "",
            "kwargs": kwargs,
        }
        
        self._error_history.append(error_record)
        if len(self._error_history) > 500:
            self._error_history = self._error_history[-200:]
        
        self._error_counts[error_type] = self._error_counts.get(error_type, 0) + 1
        
        if error_type in self._error_handlers:
            for handler in self._error_handlers[error_type]:
                try:
                    handler(error_record)
                except Exception:
                    pass
        
        if error_type in self._recovery_strategies:
            try:
                self._recovery_strategies[error_type](error_record)
            except Exception as e:
                print(f"恢复策略执行失败: {e}")

    def run_with_retry(self, func: Callable, error_type: str, max_retries=None, **kwargs):
        retries = max_retries or self._max_retries
        delay = self._retry_delay
        
        for attempt in range(retries):
            try:
                return func(**kwargs)
            except Exception as e:
                if attempt < retries - 1:
                    self.handle_error(error_type, f"尝试 {attempt + 1}/{retries} 失败: {str(e)}")
                    time.sleep(delay * (2 ** attempt))
                else:
                    self.handle_error(error_type, f"所有 {retries} 次尝试均失败: {str(e)}", sys.exc_info())
                    raise

    def get_error_summary(self) -> Dict:
        total_errors = len(self._error_history)
        unique_types = len(self._error_counts)
        
        return {
            "total_errors": total_errors,
            "unique_types": unique_types,
            "error_counts": dict(sorted(self._error_counts.items(), key=lambda x: x[1], reverse=True)),
            "recent_errors": self._error_history[-10:],
        }

    def save_error_log(self, filepath: str = None):
        if filepath is None:
            filepath = os.path.join(os.path.dirname(__file__), "..", "logs", "error_log.json")
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(self._error_history, f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def clear_history(self):
        self._error_history = []
        self._error_counts = {}

class AutoRecovery:
    def __init__(self):
        self._strategies: Dict[str, Dict] = {}
        self._recovery_history: List[Dict] = []

    def add_strategy(self, error_type: str, strategy: Callable, description: str, priority: int = 1):
        self._strategies[error_type] = {
            "strategy": strategy,
            "description": description,
            "priority": priority,
        }

    def recover(self, error_type: str, **kwargs) -> bool:
        if error_type not in self._strategies:
            return False
        
        strategy_info = self._strategies[error_type]
        strategy = strategy_info["strategy"]
        
        try:
            result = strategy(**kwargs)
            
            recovery_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "strategy": strategy_info["description"],
                "success": result,
                "kwargs": kwargs,
            }
            
            self._recovery_history.append(recovery_record)
            if len(self._recovery_history) > 100:
                self._recovery_history = self._recovery_history[-50:]
            
            return result
        except Exception as e:
            recovery_record = {
                "timestamp": datetime.now().isoformat(),
                "error_type": error_type,
                "strategy": strategy_info["description"],
                "success": False,
                "error": str(e),
                "kwargs": kwargs,
            }
            self._recovery_history.append(recovery_record)
            return False

    def get_recovery_history(self, limit: int = 20) -> List[Dict]:
        return self._recovery_history[-limit:]

    def get_strategies(self) -> Dict[str, Dict]:
        return self._strategies

error_handler = ErrorHandler()
auto_recovery = AutoRecovery()