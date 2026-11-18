#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import time
import uuid
import threading
from pathlib import Path
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from .logger import Logger
from .error_handler import ErrorHandler


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(Enum):
    PREPROCESS = "preprocess"
    ANALYSIS = "analysis"
    VISUALIZATION = "visualization"
    EXPORT = "export"


class Task:
    def __init__(self, id: str, name: str, task_type: TaskType,
                 commands: List[str], input_file: str, work_dir: str):
        self.id = id
        self.name = name
        self.type = task_type
        self.status = TaskStatus.PENDING
        self.commands = commands
        self.input_file = input_file
        self.work_dir = work_dir
        self.created_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self.started_at = None
        self.completed_at = None
        self.error_message = None
        self.progress = 0.0
        self.output = ""
        self.metadata = {}

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type.value,
            "status": self.status.value,
            "commands": self.commands,
            "input_file": self.input_file,
            "work_dir": self.work_dir,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "error_message": self.error_message,
            "progress": self.progress,
            "output": self.output,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "Task":
        task = cls(
            id=data["id"],
            name=data["name"],
            task_type=TaskType(data["type"]),
            commands=data["commands"],
            input_file=data["input_file"],
            work_dir=data["work_dir"],
        )
        task.status = TaskStatus(data["status"])
        task.started_at = data.get("started_at")
        task.completed_at = data.get("completed_at")
        task.error_message = data.get("error_message")
        task.progress = data.get("progress", 0.0)
        task.output = data.get("output", "")
        task.metadata = data.get("metadata", {})
        return task


class WorkflowEngine:
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

        self._tasks: Dict[str, Task] = {}
        self._task_order: List[str] = []
        self._current_task: Optional[str] = None
        self._listeners: List[Callable] = []
        self._lock = threading.Lock()
        self._logger = Logger()
        self._error_handler = ErrorHandler()
        self._running = False

        base_dir = Path(__file__).parent.parent.parent
        self._state_file = base_dir / "config" / "workflow_state.json"
        self._state_file.parent.mkdir(parents=True, exist_ok=True)

        self._initialized = True

    def add_task(self, name: str, task_type: TaskType, commands: List[str],
                 input_file: str, work_dir: str, metadata: Dict = None) -> str:
        task_id = str(uuid.uuid4())[:8]
        task = Task(
            id=task_id,
            name=name,
            task_type=task_type,
            commands=commands,
            input_file=input_file,
            work_dir=work_dir,
        )
        if metadata:
            task.metadata = metadata

        with self._lock:
            self._tasks[task_id] = task
            self._task_order.append(task_id)

        self._notify_listeners("task_added", {"task_id": task_id, "task": task.to_dict()})
        self._save_state()

        return task_id

    def get_task(self, task_id: str) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_all_tasks(self) -> List[Task]:
        return [self._tasks[id] for id in self._task_order]

    def remove_task(self, task_id: str):
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                self._task_order.remove(task_id)

        self._notify_listeners("task_removed", {"task_id": task_id})
        self._save_state()

    def clear_all_tasks(self):
        with self._lock:
            self._tasks.clear()
            self._task_order.clear()
            self._current_task = None

        self._notify_listeners("tasks_cleared", {})
        self._save_state()

    def start_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return

        thread = threading.Thread(target=self._execute_task, args=(task_id,))
        thread.daemon = True
        thread.start()

    def start_all(self):
        pending_tasks = [id for id in self._task_order if self._tasks[id].status == TaskStatus.PENDING]
        for task_id in pending_tasks:
            self.start_task(task_id)

    def _execute_task(self, task_id: str):
        task = self._tasks.get(task_id)
        if not task:
            return

        task.status = TaskStatus.RUNNING
        task.started_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self._current_task = task_id

        self._notify_listeners("task_started", {"task_id": task_id, "task": task.to_dict()})

        try:
            from .multiwfn_service import MultiwfnService
            mwfn = MultiwfnService()
            result = mwfn.run_command(task.input_file, task.commands, task.work_dir)

            task.output = result.get("output", "")
            task.progress = 100.0

            if result.get("success", True):
                task.status = TaskStatus.COMPLETED
                self._logger.info(f"Task completed: {task.name}")
            else:
                task.status = TaskStatus.FAILED
                err = result.get("error")
                if isinstance(err, dict):
                    task.error_message = err.get("message", "Unknown error")
                elif isinstance(err, str) and err.strip():
                    task.error_message = err.strip()
                else:
                    task.error_message = "Unknown error"
                self._logger.error(f"Task failed: {task.name} - {task.error_message}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error_message = str(e)
            self._logger.error(f"Task exception: {task.name} - {e}")

        task.completed_at = time.strftime("%Y-%m-%d %H:%M:%S")
        self._current_task = None

        self._notify_listeners("task_completed", {"task_id": task_id, "task": task.to_dict()})
        self._save_state()

    def add_listener(self, callback: Callable):
        with self._lock:
            if callback not in self._listeners:
                self._listeners.append(callback)

    def remove_listener(self, callback: Callable):
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def _notify_listeners(self, event_type: str, data: Dict):
        for listener in self._listeners:
            try:
                listener(event_type, data)
            except Exception:
                pass

    def _save_state(self):
        try:
            state = {
                "tasks": {tid: task.to_dict() for tid, task in self._tasks.items()},
                "task_order": self._task_order,
                "current_task": self._current_task,
            }
            with open(self._state_file, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def _load_state(self):
        if self._state_file.exists():
            try:
                with open(self._state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)
                for tid, data in state.get("tasks", {}).items():
                    self._tasks[tid] = Task.from_dict(data)
                self._task_order = state.get("task_order", [])
                self._current_task = state.get("current_task")
            except Exception:
                pass
