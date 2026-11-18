#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
独立结果预览窗口 - GB/T 8566 compliant result preview component
支持悬浮预览、最大化、分栏查看、多格式导出
"""
import os
from datetime import datetime
from typing import Dict, List, Optional

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QTabWidget, QTextEdit,
    QSplitter, QFileDialog, QMessageBox, QGroupBox, QProgressBar,
    QWidget, QComboBox, QLineEdit, QCheckBox, QMenu, QAction
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QFontMetrics, QKeySequence

from ..utils.export_manager import ExportManager


class ResultPreviewWindow(QDialog):
    """
    独立结果预览窗口
    - 悬浮于主界面之上，不占用主界面空间
    - 支持最大化/恢复/关闭
    - 分栏查看：数据表格 + 原始输出 + 参数信息
    - 内置导出按钮，支持 txt/csv/xlsx/png
    """

    def __init__(self, title: str = "计算结果预览", data: Optional[Dict] = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(900, 650)
        self.resize(1100, 750)
        self.data = data or {}
        self.export_manager = ExportManager()
        self.init_ui()
        self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(12, 12, 12, 12)

        # 顶部操作栏
        toolbar = QHBoxLayout()

        self.title_label = QLabel(self.data.get("task_name", "计算结果"))
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #2c3e50;")
        toolbar.addWidget(self.title_label)

        toolbar.addStretch()

        # 导出格式选择
        self.format_combo = QComboBox()
        self.format_combo.addItem("导出 TXT", "txt")
        self.format_combo.addItem("导出 CSV", "csv")
        self.format_combo.addItem("导出 Excel", "xlsx")
        self.format_combo.setMinimumWidth(120)
        self.format_combo.setMinimumHeight(28)
        toolbar.addWidget(self.format_combo)

        self.export_btn = QPushButton("📥 导出")
        self.export_btn.setMinimumWidth(80)
        self.export_btn.clicked.connect(self.do_export)
        toolbar.addWidget(self.export_btn)

        self.close_btn = QPushButton("✕ 关闭")
        self.close_btn.setMinimumWidth(80)
        self.close_btn.clicked.connect(self.close)
        toolbar.addWidget(self.close_btn)

        layout.addLayout(toolbar)

        # 元数据信息栏
        meta_group = QGroupBox("计算信息")
        meta_layout = QHBoxLayout()
        self.meta_labels = {}
        for key in ["计算方法", "输入文件", "原子数量", "耗时"]:
            lbl = QLabel(f"{key}: --")
            lbl.setStyleSheet("color: #555; font-size: 12px;")
            meta_layout.addWidget(lbl)
            self.meta_labels[key] = lbl
        meta_layout.addStretch()
        meta_group.setLayout(meta_layout)
        layout.addWidget(meta_group)

        # 分栏内容区
        splitter = QSplitter(Qt.Vertical)

        # 数据表格页
        table_widget = QWidget()
        table_layout = QVBoxLayout()
        table_layout.setContentsMargins(0, 0, 0, 0)
        self.data_table = QTableWidget()
        self.data_table.setAlternatingRowColors(True)
        self.data_table.setSortingEnabled(True)
        self.data_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.data_table.customContextMenuRequested.connect(self.show_table_context_menu)
        table_layout.addWidget(self.data_table)
        table_widget.setLayout(table_layout)
        splitter.addWidget(table_widget)

        # 原始输出页
        output_widget = QWidget()
        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setFont(QFont("Consolas", 10))
        self.output_text.setLineWrapMode(QTextEdit.NoWrap)
        output_layout.addWidget(self.output_text)
        output_widget.setLayout(output_layout)
        splitter.addWidget(output_widget)

        splitter.setSizes([400, 250])
        layout.addWidget(splitter, 1)

        # 底部状态栏
        self.status_label = QLabel("就绪")
        self.status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

        # 窗口属性
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowMaximizeButtonHint |
            Qt.WindowCloseButtonHint
        )

    def load_data(self):
        """加载计算结果数据"""
        # 填充元数据
        metadata = self.data.get("metadata", {})
        for key, lbl in self.meta_labels.items():
            val = metadata.get(key, "--")
            lbl.setText(f"{key}: {val}")

        # 填充数据表格
        table_data = self.data.get("table_data", [])
        headers = self.data.get("table_headers", [])
        if table_data and headers:
            self.data_table.setColumnCount(len(headers))
            self.data_table.setHorizontalHeaderLabels(headers)
            self.data_table.setRowCount(len(table_data))
            for row_idx, row_data in enumerate(table_data):
                for col_idx, val in enumerate(row_data):
                    item = QTableWidgetItem(str(val))
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                    self.data_table.setItem(row_idx, col_idx, item)
            for col in range(len(headers)):
                self.data_table.resizeColumnToContents(col)
            self.data_table.horizontalHeader().setStretchLastSection(True)

        # 填充原始输出
        raw_output = self.data.get("raw_output", "")
        if raw_output:
            self.output_text.setText(raw_output)
        else:
            self.output_text.setText("暂无原始输出数据")

        self.status_label.setText(
            f"数据行数: {len(table_data)} | "
            f"原始输出: {len(raw_output)} 字符"
        )

    def show_table_context_menu(self, position):
        """表格右键菜单：复制选中单元格"""
        menu = QMenu()
        copy_action = QAction("复制", self)
        copy_action.triggered.connect(self.copy_selected_cells)
        menu.addAction(copy_action)
        copy_row_action = QAction("复制整行", self)
        copy_row_action.triggered.connect(self.copy_selected_rows)
        menu.addAction(copy_row_action)
        menu.exec_(self.data_table.viewport().mapToGlobal(position))

    def copy_selected_cells(self):
        """复制选中单元格"""
        items = self.data_table.selectedItems()
        text = "\t".join([item.text() for item in items])
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText(text)

    def copy_selected_rows(self):
        """复制选中整行"""
        rows = set()
        for item in self.data_table.selectedItems():
            rows.add(item.row())
        lines = []
        for row in sorted(rows):
            cols = []
            for col in range(self.data_table.columnCount()):
                item = self.data_table.item(row, col)
                cols.append(item.text() if item else "")
            lines.append("\t".join(cols))
        from PyQt5.QtWidgets import QApplication
        QApplication.clipboard().setText("\n".join(lines))

    def do_export(self):
        """执行导出"""
        fmt = self.format_combo.currentData()
        default_name = self._generate_filename(fmt)

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出结果",
            default_name,
            f"*.{fmt}"
        )
        if not file_path:
            return

        # 准备导出数据
        table_data = self.data.get("table_data", [])
        headers = self.data.get("table_headers", [])

        # 转换为 charges 格式（通用接口）
        charges = []
        for row in table_data:
            charge = {}
            for i, h in enumerate(headers):
                key_map = {
                    "原子序号": "index", "index": "index",
                    "元素符号": "symbol", "symbol": "symbol",
                    "电荷值": "charge", "charge": "charge",
                    "键级": "bond_order", "bond_order": "bond_order",
                    "原子1": "atom1", "atom2": "atom2",
                }
                key = key_map.get(h, h)
                val = row[i]
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    pass
                charge[key] = val
            charges.append(charge)

        result = self.export_manager.export_charges(
            charges, file_path, self.data.get("metadata")
        )

        if result["success"]:
            self.status_label.setText(f"✓ 已导出: {file_path}")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 11px;")
            QMessageBox.information(self, "导出成功", f"结果已保存到:\n{file_path}")
        else:
            self.status_label.setText(f"✗ 导出失败: {result.get('error', '')}")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            QMessageBox.critical(self, "导出失败", str(result.get("error", "未知错误")))

    def _generate_filename(self, fmt: str) -> str:
        """生成默认文件名: 任务名_分析类型_时间戳.扩展名"""
        task = self.data.get("task_name", "result")
        analysis = self.data.get("analysis_type", "analysis")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{task}_{analysis}_{timestamp}"
        # 清理非法字符
        safe_name = "".join(c for c in safe_name if c.isalnum() or c in "_-.")
        return f"{safe_name}.{fmt}"
