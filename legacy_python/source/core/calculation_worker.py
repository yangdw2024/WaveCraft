#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""兼容旧引用的导出模块，实际实现统一位于 worker.py。"""

from .worker import CalculationWorker

__all__ = ["CalculationWorker"]
