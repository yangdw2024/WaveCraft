#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框 - GB/T 8566  compliant configuration dialog
提供 Multiwfn 路径配置、工作目录设置、线程数调整等核心参数配置
"""
import os
import sys
from pathlib import Path

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QSpinBox, QGroupBox, QTabWidget, QWidget,
    QFileDialog, QMessageBox, QCheckBox, QFormLayout,
    QComboBox, QTextEdit
)
from PyQt5.QtCore import Qt


class SettingsDialog(QDialog):
    """系统设置对话框，支持 Multiwfn 路径配置、工作目录、线程数等参数"""

    def __init__(self, config, mwfn_service, parent=None):
        super().__init__(parent)
        self.config = config
        self.mwfn_service = mwfn_service
        self.setWindowTitle("WaveCraft 设置")
        self.setMinimumSize(600, 450)
        self.init_ui()
        self.load_settings()

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # 标签页
        self.tabs = QTabWidget()

        # === Multiwfn 配置页 ===
        mwfn_page = QWidget()
        mwfn_layout = QVBoxLayout()
        mwfn_layout.setSpacing(12)

        # Multiwfn 路径配置组
        path_group = QGroupBox("Multiwfn 可执行文件路径")
        path_layout = QVBoxLayout()

        path_h = QHBoxLayout()
        self.mwfn_path_edit = QLineEdit()
        self.mwfn_path_edit.setPlaceholderText("自动检测或手动选择 Multiwfn.exe 路径...")
        self.mwfn_path_edit.setMinimumHeight(28)
        self.browse_mwfn_btn = QPushButton("浏览...")
        self.browse_mwfn_btn.setMinimumWidth(80)
        self.browse_mwfn_btn.clicked.connect(self.browse_multiwfn)
        self.auto_detect_btn = QPushButton("自动检测")
        self.auto_detect_btn.setMinimumWidth(80)
        self.auto_detect_btn.clicked.connect(self.auto_detect_multiwfn)
        path_h.addWidget(self.mwfn_path_edit)
        path_h.addWidget(self.browse_mwfn_btn)
        path_h.addWidget(self.auto_detect_btn)
        path_layout.addLayout(path_h)

        # 路径状态提示
        self.path_status_label = QLabel("状态: 未检测")
        self.path_status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        path_layout.addWidget(self.path_status_label)

        # 路径合法性校验结果
        self.path_validation_label = QLabel("")
        self.path_validation_label.setStyleSheet("font-size: 11px;")
        path_layout.addWidget(self.path_validation_label)

        path_group.setLayout(path_layout)
        mwfn_layout.addWidget(path_group)

        # 工作目录配置组
        workdir_group = QGroupBox("工作目录")
        workdir_layout = QVBoxLayout()

        workdir_h = QHBoxLayout()
        self.workdir_edit = QLineEdit()
        self.workdir_edit.setPlaceholderText("选择计算结果输出目录...")
        self.workdir_edit.setMinimumHeight(28)
        self.browse_workdir_btn = QPushButton("浏览...")
        self.browse_workdir_btn.setMinimumWidth(80)
        self.browse_workdir_btn.clicked.connect(self.browse_work_dir)
        workdir_h.addWidget(self.workdir_edit)
        workdir_h.addWidget(self.browse_workdir_btn)
        workdir_layout.addLayout(workdir_h)

        self.workdir_status_label = QLabel("状态: 未设置")
        self.workdir_status_label.setStyleSheet("color: #7f8c8d; font-size: 11px;")
        workdir_layout.addWidget(self.workdir_status_label)

        workdir_group.setLayout(workdir_layout)
        mwfn_layout.addWidget(workdir_group)

        # 计算参数组
        calc_group = QGroupBox("计算参数")
        calc_form = QFormLayout()
        calc_form.setSpacing(10)

        self.nthreads_spin = QSpinBox()
        self.nthreads_spin.setRange(1, 64)
        self.nthreads_spin.setValue(8)
        self.nthreads_spin.setMinimumHeight(28)
        calc_form.addRow("并行线程数:", self.nthreads_spin)

        self.auto_detect_check = QCheckBox("启动时自动检测 Multiwfn 路径")
        self.auto_detect_check.setChecked(True)
        calc_form.addRow(self.auto_detect_check)

        calc_group.setLayout(calc_form)
        mwfn_layout.addWidget(calc_group)

        mwfn_layout.addStretch()
        mwfn_page.setLayout(mwfn_layout)
        self.tabs.addTab(mwfn_page, "Multiwfn 配置")

        # === 系统设置页 ===
        sys_page = QWidget()
        sys_layout = QVBoxLayout()
        sys_layout.setSpacing(12)

        theme_group = QGroupBox("界面主题")
        theme_form = QFormLayout()
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["浅色", "深色", "跟随系统"])
        self.theme_combo.setMinimumHeight(28)
        theme_form.addRow("主题:", self.theme_combo)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["简体中文", "English"])
        self.language_combo.setMinimumHeight(28)
        theme_form.addRow("语言:", self.language_combo)

        theme_group.setLayout(theme_form)
        sys_layout.addWidget(theme_group)

        log_group = QGroupBox("日志设置")
        log_form = QFormLayout()
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        self.log_level_combo.setMinimumHeight(28)
        log_form.addRow("日志级别:", self.log_level_combo)

        self.auto_save_check = QCheckBox("自动保存配置")
        self.auto_save_check.setChecked(True)
        log_form.addRow(self.auto_save_check)

        log_group.setLayout(log_form)
        sys_layout.addWidget(log_group)

        sys_layout.addStretch()
        sys_page.setLayout(sys_layout)
        self.tabs.addTab(sys_page, "系统设置")

        # === 关于页 ===
        about_page = QWidget()
        about_layout = QVBoxLayout()
        about_text = QTextEdit()
        about_text.setReadOnly(True)
        about_text.setHtml("""
        <h2 style='color: #2c3e50;'>WaveCraft</h2>
        <p style='color: #7f8c8d;'>Multiwfn 波函数分析图形界面 v1.0.0</p>
        <hr>
        <p><b>软件遵循标准:</b></p>
        <ul>
        <li>GB/T 8566-2022 信息技术 软件生存周期过程</li>
        <li>GB/T 8567-2006 计算机软件文档编制规范</li>
        <li>GB/T 13702-1992 计算机软件分类与代码</li>
        </ul>
        <p><b>支持的波函数格式:</b></p>
        <ul>
        <li>.fch / .fchk (Gaussian checkpoint)</li>
        <li>.wfn / .wfx (Gaussian WFN/WFX)</li>
        <li>.mwfn (Multiwfn 专属格式)</li>
        <li>.molden, .pdb, .xyz, .mol2, .cub, .gjf</li>
        </ul>
        <p style='color: #95a5a6; font-size: 11px;'>基于 PyQt5 构建</p>
        """)
        about_layout.addWidget(about_text)
        about_page.setLayout(about_layout)
        self.tabs.addTab(about_page, "关于")

        layout.addWidget(self.tabs)

        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.test_btn = QPushButton("测试连接")
        self.test_btn.setMinimumWidth(90)
        self.test_btn.clicked.connect(self.test_multiwfn_connection)
        btn_layout.addWidget(self.test_btn)

        self.save_btn = QPushButton("保存")
        self.save_btn.setMinimumWidth(90)
        self.save_btn.setDefault(True)
        self.save_btn.clicked.connect(self.save_settings)
        btn_layout.addWidget(self.save_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setMinimumWidth(90)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_settings(self):
        """从 ConfigManager 加载已有配置"""
        # Multiwfn 路径
        saved_path = self.config.get("multiwfn.exe_path", "")
        if saved_path and os.path.isfile(saved_path):
            self.mwfn_path_edit.setText(saved_path)
            self._validate_mwfn_path(saved_path)
        else:
            # 尝试自动检测
            detected = self.mwfn_service.find_multiwfn()
            if detected:
                self.mwfn_path_edit.setText(detected)
                self._validate_mwfn_path(detected)
            else:
                self.path_status_label.setText("状态: 未找到 Multiwfn，请手动指定路径")
                self.path_status_label.setStyleSheet("color: #e74c3c; font-size: 11px;")

        # 工作目录
        work_dir = self.config.get("multiwfn.work_dir", "")
        if work_dir and os.path.isdir(work_dir):
            self.workdir_edit.setText(work_dir)
            self.workdir_status_label.setText(f"状态: 已设置 ({work_dir})")
            self.workdir_status_label.setStyleSheet("color: #27ae60; font-size: 11px;")
        else:
            default_dir = os.getcwd()
            self.workdir_edit.setText(default_dir)
            self.workdir_status_label.setText(f"状态: 使用默认目录 ({default_dir})")

        # 线程数
        self.nthreads_spin.setValue(self.config.get("multiwfn.nthreads", 8))

        # 自动检测
        self.auto_detect_check.setChecked(self.config.get("multiwfn.auto_detect", True))

        # 系统设置
        theme_map = {"light": 0, "dark": 1, "system": 2}
        self.theme_combo.setCurrentIndex(theme_map.get(self.config.get("system.theme", "dark"), 1))
        self.log_level_combo.setCurrentText(self.config.get("system.log_level", "INFO"))
        self.auto_save_check.setChecked(self.config.get("system.auto_save_config", True))

    def browse_multiwfn(self):
        """手动浏览选择 Multiwfn.exe"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择 Multiwfn 可执行文件",
            os.path.dirname(self.mwfn_path_edit.text()) or os.getcwd(),
            "可执行文件 (*.exe);;所有文件 (*.*)"
        )
        if file_path:
            self.mwfn_path_edit.setText(file_path)
            self._validate_mwfn_path(file_path)

    def auto_detect_multiwfn(self):
        """自动检测 Multiwfn 安装路径"""
        self.path_status_label.setText("状态: 正在检测...")
        self.path_status_label.setStyleSheet("color: #3498db; font-size: 11px;")
        self.repaint()

        detected = self.mwfn_service.find_multiwfn()
        if detected:
            self.mwfn_path_edit.setText(detected)
            self._validate_mwfn_path(detected)
            QMessageBox.information(self, "检测成功", f"已找到 Multiwfn:\n{detected}")
        else:
            self.path_status_label.setText("状态: 自动检测失败，请手动指定路径")
            self.path_status_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            QMessageBox.warning(self, "检测失败", "未找到 Multiwfn 可执行文件。\n\n"
                               "请确认 Multiwfn 已正确安装，或手动指定路径。")

    def _validate_mwfn_path(self, path: str) -> bool:
        """路径合法性校验：文件存在性、可执行性"""
        if not path:
            self.path_status_label.setText("状态: 路径为空")
            self.path_status_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self.path_validation_label.setText("")
            return False

        if not os.path.exists(path):
            self.path_status_label.setText("状态: 路径不存在")
            self.path_status_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self.path_validation_label.setText("❌ 文件不存在")
            self.path_validation_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            return False

        if not os.path.isfile(path):
            self.path_status_label.setText("状态: 路径不是文件")
            self.path_status_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            self.path_validation_label.setText("❌ 路径指向的不是文件")
            self.path_validation_label.setStyleSheet("color: #e74c3c; font-size: 11px;")
            return False

        # 检查文件名
        basename = os.path.basename(path).lower()
        if "multiwfn" not in basename:
            self.path_status_label.setText(f"状态: 警告 - 文件名 '{basename}' 可能不是 Multiwfn")
            self.path_status_label.setStyleSheet("color: #f39c12; font-size: 11px;")
            self.path_validation_label.setText("⚠ 文件名不包含 'multiwfn'，请确认是否正确")
            self.path_validation_label.setStyleSheet("color: #f39c12; font-size: 11px;")
            return False

        self.path_status_label.setText(f"状态: 路径有效")
        self.path_status_label.setStyleSheet("color: #27ae60; font-size: 11px;")
        self.path_validation_label.setText(f"✓ 文件存在，大小: {os.path.getsize(path) / (1024*1024):.1f} MB")
        self.path_validation_label.setStyleSheet("color: #27ae60; font-size: 11px;")
        return True

    def browse_work_dir(self):
        """浏览选择工作目录"""
        dir_path = QFileDialog.getExistingDirectory(
            self, "选择工作目录",
            self.workdir_edit.text() or os.getcwd()
        )
        if dir_path:
            self.workdir_edit.setText(dir_path)
            self.workdir_status_label.setText(f"状态: 已设置 ({dir_path})")
            self.workdir_status_label.setStyleSheet("color: #27ae60; font-size: 11px;")

    def test_multiwfn_connection(self):
        """测试 Multiwfn 连接"""
        path = self.mwfn_path_edit.text().strip()
        if not self._validate_mwfn_path(path):
            QMessageBox.warning(self, "测试失败", "路径无效，无法进行测试")
            return

        self.mwfn_service.set_exe_path(path)
        info = self.mwfn_service.get_version_info()

        if info.get("valid"):
            QMessageBox.information(
                self, "连接成功",
                f"Multiwfn 连接测试通过!\n\n"
                f"路径: {info['path']}\n"
                f"版本: {info['version']}\n"
                f"线程数: {info['nthreads']}"
            )
        else:
            QMessageBox.warning(
                self, "连接失败",
                f"无法运行 Multiwfn，请检查路径是否正确:\n{path}\n\n"
                f"提示: 请确保选择的是 Multiwfn.exe 可执行文件"
            )

    def save_settings(self):
        """保存所有配置到 ConfigManager"""
        # 校验 Multiwfn 路径
        mwfn_path = self.mwfn_path_edit.text().strip()
        if mwfn_path and not self._validate_mwfn_path(mwfn_path):
            reply = QMessageBox.question(
                self, "路径无效",
                "Multiwfn 路径校验未通过，是否仍要保存?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return

        # 保存配置
        self.config.set("multiwfn.exe_path", mwfn_path)
        self.config.set("multiwfn.work_dir", self.workdir_edit.text().strip())
        self.config.set("multiwfn.nthreads", self.nthreads_spin.value())
        self.config.set("multiwfn.auto_detect", self.auto_detect_check.isChecked())

        theme_map = {0: "light", 1: "dark", 2: "system"}
        self.config.set("system.theme", theme_map.get(self.theme_combo.currentIndex(), "dark"))
        self.config.set("system.log_level", self.log_level_combo.currentText())
        self.config.set("system.auto_save_config", self.auto_save_check.isChecked())

        # 同步更新 MultiwfnService
        if mwfn_path:
            self.mwfn_service.set_exe_path(mwfn_path)
        self.mwfn_service.set_work_dir(self.workdir_edit.text().strip())
        self.mwfn_service.set_nthreads(self.nthreads_spin.value())

        QMessageBox.information(self, "保存成功", "配置已保存并生效")
        self.accept()
