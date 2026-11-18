#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import traceback
from PyQt5.QtCore import QThread, pyqtSignal

from .logger import Logger


class CalculationWorker(QThread):
    """统一的异步 Multiwfn 计算工作线程。"""

    finished_ok = pyqtSignal(dict)
    failed = pyqtSignal(str)
    progress = pyqtSignal(int, str)

    def __init__(self, fchk_path, commands, work_dir=None, task_name="计算", template=None):
        super().__init__()
        self.fchk_path = fchk_path
        self.input_file = fchk_path
        self.commands = commands
        self.work_dir = work_dir or (os.path.dirname(fchk_path) if fchk_path else None)
        self.task_name = task_name
        self.template = template
        self._logger = Logger()
        self._cancel = False

    def run(self):
        try:
            from .multiwfn_service import MultiwfnService

            self.progress.emit(10, f"初始化{self.task_name}...")
            service = MultiwfnService()

            validation = service.validate_input_file(self.fchk_path)
            if not validation["valid"]:
                self.failed.emit(validation["message"])
                return

            if self._cancel:
                self.failed.emit("任务已取消")
                return

            self.progress.emit(30, "正在调用Multiwfn...")
            self._logger.info(
                f"Running {self.task_name} on {os.path.basename(self.fchk_path)}"
            )

            result = service.run_command(self.fchk_path, self.commands, self.work_dir)
            if self._cancel:
                self.failed.emit("任务已取消")
                return

            self.progress.emit(90, "解析结果...")
            if isinstance(result, dict):
                result.setdefault("success", True)
                result["template"] = self.template or {}

            self._logger.info(f"{self.task_name} completed successfully")
            self.finished_ok.emit(result)
        except Exception as e:
            error_msg = f"{self.task_name}失败: {str(e)}\n\n{traceback.format_exc()}"
            self._logger.error(f"{self.task_name} exception: {error_msg}")
            self.failed.emit(error_msg)

    def cancel(self):
        self._cancel = True
