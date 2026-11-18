#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
导出对话框 - 提供结果导出格式选择、路径配置、进度显示
"""
import os
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QGroupBox, QProgressBar,
    QFileDialog, QMessageBox, QRadioButton, QButtonGroup,
    QWidget, QCheckBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal

from ..utils.export_manager import ExportManager


class ExportWorker(QThread):
    """后台导出工作线程"""
    progress = pyqtSignal(int, str)
    finished = pyqtSignal(dict)

    def __init__(self, export_manager, export_items, output_dir):
        super().__init__()
        self.export_manager = export_manager
        self.export_items = export_items
        self.output_dir = output_dir

    def run(self):
        self.progress.emit(10, "准备导出...")
        result = self.export_manager.batch_export(self.export_items, self.output_dir)
        self.progress.emit(100, "导出完成")
        self.finished.emit(result)


class ExportDialog(QDialog):
    """结果导出对话框"""

    def __init__(self, charges=None, raw_output=None, metadata=None, parent=None):
        super().__init__(parent)
        self.charges = charges or []
        self.raw_output = raw_output or ""
        self.metadata = metadata or {}
        self.export_manager = ExportManager()
        self.setWindowTitle("导出计算结果")
        self.setMinimumSize(500, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 导出内容选择
        content_group = QGroupBox("导出内容")
        content_layout = QVBoxLayout()

        self.charge_check = QCheckBox(f"原子电荷数据 ({len(self.charges)} 个原子)")
        self.charge_check.setChecked(len(self.charges) > 0)
        self.charge_check.setEnabled(len(self.charges) > 0)
        content_layout.addWidget(self.charge_check)

        self.raw_check = QCheckBox("原始 Multiwfn 输出文本")
        self.raw_check.setChecked(bool(self.raw_output))
        self.raw_check.setEnabled(bool(self.raw_output))
        content_layout.addWidget(self.raw_check)

        content_group.setLayout(content_layout)
        layout.addWidget(content_group)

        # 格式选择
        format_group = QGroupBox("导出格式")
        format_layout = QVBoxLayout()

        self.format_combo = QComboBox()
        for fmt, desc in self.export_manager.get_supported_formats().items():
            self.format_combo.addItem(desc, fmt)
        self.format_combo.setMinimumHeight(28)
        format_layout.addWidget(self.format_combo)

        format_group.setLayout(format_layout)
        layout.addWidget(format_group)

        # 输出路径
        path_group = QGroupBox("输出路径")
        path_layout = QVBoxLayout()

        path_h = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择导出文件或目录...")
        self.path_edit.setMinimumHeight(28)
        self.browse_btn = QPushButton("浏览...")
        self.browse_btn.setMinimumWidth(80)
        self.browse_btn.clicked.connect(self.browse_path)
        path_h.addWidget(self.path_edit)
        path_h.addWidget(self.browse_btn)
        path_layout.addLayout(path_h)

        self.path_status = QLabel("")
        self.path_status.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        path_layout.addWidget(self.path_status)

        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #555; font-size: 12px;")
        layout.addWidget(self.status_label)

        layout.addStretch()

        # 按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.export_btn = QPushButton("导出")
        self.export_btn.setMinimumWidth(90)
        self.export_btn.clicked.connect(self.do_export)
        btn_layout.addWidget(self.export_btn)

        self.close_btn = QPushButton("关闭")
        self.close_btn.setMinimumWidth(90)
        self.close_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.close_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

        # 设置默认路径
        self._set_default_path()

    def _set_default_path(self):
        """设置默认导出路径"""
        default_dir = os.path.join(os.getcwd(), "output")
        os.makedirs(default_dir, exist_ok=True)
        self.path_edit.setText(default_dir)

    def browse_path(self):
        """浏览选择导出路径"""
        fmt = self.format_combo.currentData()
        if fmt == "xlsx":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存导出文件", self.path_edit.text(),
                "Excel (*.xlsx);;CSV (*.csv);;文本 (*.txt)"
            )
        elif fmt == "csv":
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存导出文件", self.path_edit.text(),
                "CSV (*.csv);;文本 (*.txt)"
            )
        else:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存导出文件", self.path_edit.text(),
                "文本 (*.txt);;CSV (*.csv)"
            )

        if file_path:
            self.path_edit.setText(file_path)

    def do_export(self):
        """执行导出"""
        if not self.charge_check.isChecked() and not self.raw_check.isChecked():
            QMessageBox.warning(self, "导出内容为空", "请至少选择一项导出内容")
            return

        path = self.path_edit.text().strip()
        if not path:
            QMessageBox.warning(self, "路径为空", "请选择导出路径")
            return

        fmt = self.format_combo.currentData()
        export_items = []

        if self.charge_check.isChecked():
            filename = f"charges.{fmt}"
            export_items.append({
                "type": "charges",
                "data": self.charges,
                "filename": filename,
                "metadata": self.metadata,
            })

        if self.raw_check.isChecked():
            export_items.append({
                "type": "raw",
                "data": self.raw_output,
                "filename": "multiwfn_output.txt",
            })

        self.export_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在导出...")

        self.worker = ExportWorker(self.export_manager, export_items, path)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def on_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.status_label.setText(message)

    def on_finished(self, result):
        self.export_btn.setEnabled(True)
        self.progress_bar.setVisible(False)

        if result["success"]:
            self.status_label.setText(f"✓ 导出成功: {result['success_count']}/{result['total']} 文件")
            self.status_label.setStyleSheet("color: #27ae60; font-size: 12px;")
            QMessageBox.information(
                self, "导出成功",
                f"已成功导出 {result['success_count']} 个文件到:\n{self.path_edit.text()}"
            )
        else:
            self.status_label.setText(f"✗ 导出失败: {result['details']}")
            self.status_label.setStyleSheet("color: #e74c3c; font-size: 12px;")
            QMessageBox.warning(self, "导出失败", "部分文件导出失败，请检查路径权限")
