#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件管理模块 — 波函数文件的选择、信息预览与最近文件管理

功能：
  - 文件选择：支持 .fch/.fchk/.wfn/.wfx/.mwfn/.molden/.pdb 等格式
  - 显示文件基本信息：文件路径、大小、修改时间
  - 波函数信息预览：原子数、电子数、基函数数、轨道数（通过菜单 6-1 获取）
  - 最近打开文件列表（保存到 config）
  - 文件格式说明 tooltip

布局：
  - 顶部：文件选择按钮 + 文件路径显示 + 打开按钮
  - 中间左侧：文件信息面板
  - 中间右侧：波函数信息面板
  - 底部：状态标签

信号：file_selected(str) — 当文件成功加载后发射
深色主题适配
"""

import os
import time
from datetime import datetime

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox,
    QFileDialog, QMessageBox, QComboBox, QFormLayout, QTextEdit,
    QProgressBar, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont

from ..core.config_manager import ConfigManager
from ..core.multiwfn_service import MultiwfnService
from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.output_parser import OutputParser


# ============================================================================
# 深色主题颜色常量
# ============================================================================
_DARK_BG = "#161d27"
_DARK_FG = "#e2e8f0"
_DARK_GRID = "#334155"
_DARK_PANEL = "#1e293b"
_DARK_ACCENT = "#e74c3c"
_DARK_SUCCESS = "#34d399"
_DARK_WARN = "#fbbf24"
_DARK_ERROR = "#ef4444"

# ============================================================================
# 支持的文件格式说明
# ============================================================================
FILE_FORMAT_TIPS = {
    ".fch": (
        "Gaussian Formatted Checkpoint 文件 (.fch)\n\n"
        "由 Gaussian 计算产生的格式化检查点文件，包含分子轨道系数、"
        "基函数信息和能量等。是最常用的 Multiwfn 输入格式之一。\n"
        "可用 formchk 工具从 .chk 文件转换得到。"
    ),
    ".fchk": (
        "Gaussian Formatted Checkpoint 文件 (.fchk)\n\n"
        "与 .fch 相同格式，仅扩展名不同。包含完整的波函数信息。"
    ),
    ".wfn": (
        "Gaussian 波函数文件 (.wfn)\n\n"
        "较早的 Gaussian 波函数输出格式，包含分子轨道系数和基函数信息。"
        "不包含后 HF 方法的密度矩阵信息，功能不如 .fch 完整。"
    ),
    ".wfx": (
        "Gaussian 扩展波函数文件 (.wfx)\n\n"
        "Gaussian 09 引入的新格式，是 .wfn 的扩展版本，"
        "支持更多功能如频率计算等。包含比 .wfn 更完整的信息。"
    ),
    ".mwfn": (
        "Multiwfn 原生波函数文件 (.mwfn)\n\n"
        "Multiwfn 自有的波函数格式，保留最完整的波函数信息，"
        "包括自然轨道、密度矩阵等。适合在 Multiwfn 内部分析时使用。"
    ),
    ".molden": (
        "Molden 格式文件 (.molden)\n\n"
        "由 Molden 程序定义的通用波函数格式，多种量子化学程序可输出此格式，"
        "如 ORCA、PSI4、deMon2K 等。兼容性较好。"
    ),
    ".pdb": (
        "蛋白质数据库文件 (.pdb)\n\n"
        "标准分子结构文件，仅包含原子坐标和连接信息，不含波函数。"
        "可用于几何分析、静电势计算等不需要轨道信息的任务。"
    ),
    ".xyz": (
        "XYZ 坐标文件 (.xyz)\n\n"
        "最简单的分子坐标格式，仅含元素和笛卡尔坐标。"
        "不含电子结构信息，仅用于几何相关的分析。"
    ),
    ".mol2": (
        "Tripos Mol2 文件 (.mol2)\n\n"
        "包含原子坐标、键连和部分电荷信息的格式，常用于分子对接。"
    ),
    ".cub": (
        "Gaussian Cube 文件 (.cub/.cube)\n\n"
        "三维网格数据文件，包含实空间函数的数值。"
        "可直接用于绘制等值面或进行进一步数据处理。"
    ),
    ".gjf": (
        "Gaussian 输入文件 (.gjf)\n\n"
        "Gaussian 计算任务的输入文件，包含分子坐标和计算参数。"
        "可用于几何相关的分析。"
    ),
}

# 波函数信息字段中文映射
WFN_FIELD_NAMES = {
    "total_energy": "总能量 (a.u.)",
    "num_electrons": "总电子数",
    "alpha_electrons": "Alpha 电子数",
    "beta_electrons": "Beta 电子数",
    "num_orbitals": "基函数数",
    "num_gtf": "原始GTF数",
    "num_atoms": "原子数",
    "net_charge": "净电荷",
    "multiplicity": "多重度",
    "dipole_moment": "偶极矩 (a.u.)",
    "virial_ratio": "维里比",
    "homo_energy": "HOMO 能量 (a.u.)",
    "lumo_energy": "LUMO 能量 (a.u.)",
    "homo_lumo_gap": "HOMO-LUMO 间隙 (a.u.)",
    "molecular_weight": "分子量 (amu)",
    "point_group": "点群",
    "title": "文件标题",
    "wavefunction_type": "波函数类型",
    "occ_orbital_start": "占据轨道起始序号",
    "occ_orbital_end": "占据轨道终止序号",
    "num_occ_orbitals": "占据轨道数",
}


def _format_file_size(size_bytes):
    """将字节数格式化为易读的文件大小字符串。"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


class FileManagerTab(QWidget):
    """文件管理标签页：文件选择、信息预览与最近文件管理。"""

    # 当文件成功加载后发射，携带文件绝对路径
    file_selected = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.config = ConfigManager()
        self.mwfn_service = MultiwfnService()
        self._worker = None
        self._last_wfn_info = {}
        self._current_file = ""
        self._init_ui()
        self._load_recent_files()

    # ====================================================================
    # 界面构建
    # ====================================================================
    def _init_ui(self):
        """构建完整界面。"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # ---- 顶部：文件选择栏 ----
        top_group = QGroupBox("文件选择")
        top_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        top_layout = QVBoxLayout()

        # 第一行：文件路径 + 浏览 + 打开
        file_row = QHBoxLayout()
        self.file_path_edit = QLineEdit()
        self.file_path_edit.setPlaceholderText("选择或输入波函数文件路径...")
        self.file_path_edit.setStyleSheet(
            f"QLineEdit {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 8px; }}"
        )
        self.file_path_edit.setToolTip(
            "波函数文件路径\n\n"
            "在此输入或通过「浏览」按钮选择波函数文件。\n"
            "支持格式：.fch .fchk .wfn .wfx .mwfn .molden .pdb .xyz .mol2 .cub .gjf"
        )

        self.browse_btn = QPushButton("浏览")
        self.browse_btn.setStyleSheet(
            f"QPushButton {{ background-color: #2563eb; color: white; "
            f"border: none; border-radius: 4px; padding: 6px 16px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: #1d4ed8; }}"
            f"QPushButton:pressed {{ background-color: #1e40af; }}"
        )
        self.browse_btn.setToolTip(
            "浏览文件\n\n"
            "打开文件选择对话框，选择波函数文件。\n"
            "可在下方格式筛选中选择特定格式。"
        )
        self.browse_btn.clicked.connect(self._browse_file)

        self.open_btn = QPushButton("打开")
        self.open_btn.setStyleSheet(
            f"QPushButton {{ background-color: {_DARK_SUCCESS}; color: #161d27; "
            f"border: none; border-radius: 4px; padding: 6px 16px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: #2dd4bf; }}"
            f"QPushButton:pressed {{ background-color: #14b8a6; }}"
        )
        self.open_btn.setToolTip(
            "打开文件\n\n"
            "加载指定路径的波函数文件，并自动获取波函数基本信息。\n"
            "加载成功后会发射 file_selected 信号，供其他标签页使用。"
        )
        self.open_btn.clicked.connect(self._open_file)

        file_row.addWidget(self.file_path_edit, stretch=1)
        file_row.addWidget(self.browse_btn)
        file_row.addWidget(self.open_btn)
        top_layout.addLayout(file_row)

        # 第二行：格式筛选
        format_row = QHBoxLayout()
        format_label = QLabel("格式筛选:")
        format_label.setStyleSheet(f"color: {_DARK_FG};")
        format_label.setToolTip("按文件格式筛选浏览对话框中显示的文件类型")

        self.format_combo = QComboBox()
        self.format_combo.setStyleSheet(
            f"QComboBox {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 8px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox QAbstractItemView {{ background-color: {_DARK_PANEL}; "
            f"color: {_DARK_FG}; selection-background-color: #2563eb; }}"
        )
        self.format_combo.setToolTip(
            "文件格式筛选\n\n"
            "选择后在浏览对话框中只显示对应格式的文件，\n"
            "选择「全部」可显示所有支持的格式。"
        )
        # 添加格式选项
        self.format_combo.addItem("全部 Multiwfn 支持文件", "all")
        for fmt in self.mwfn_service.get_supported_file_types():
            ext = fmt["ext"]
            name = fmt["name"]
            tip = FILE_FORMAT_TIPS.get(ext, f"{name}格式文件")
            self.format_combo.addItem(f"{name} (*{ext})", ext)
            # 设置每个项目的 tooltip
            idx = self.format_combo.count() - 1
            self.format_combo.setItemData(idx, tip, Qt.ToolTipRole)

        format_row.addWidget(format_label)
        format_row.addWidget(self.format_combo)
        format_row.addStretch()
        top_layout.addLayout(format_row)

        top_group.setLayout(top_layout)
        main_layout.addWidget(top_group)

        # ---- 中间：文件信息 + 波函数信息（左右分栏）----
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：文件信息面板
        file_info_group = QGroupBox("文件信息")
        file_info_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        file_info_layout = QFormLayout()
        file_info_layout.setSpacing(8)
        file_info_layout.setLabelAlignment(Qt.AlignRight)

        # 文件路径
        self.info_path_label = QLabel("未选择文件")
        self.info_path_label.setWordWrap(True)
        self.info_path_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.info_path_label.setStyleSheet(f"color: {_DARK_FG};")
        self.info_path_label.setToolTip("当前加载的文件完整路径")
        file_info_layout.addRow(self._make_form_label("文件路径:"), self.info_path_label)

        # 文件名
        self.info_name_label = QLabel("—")
        self.info_name_label.setStyleSheet(f"color: {_DARK_FG};")
        self.info_name_label.setToolTip("文件名（含扩展名）")
        file_info_layout.addRow(self._make_form_label("文件名:"), self.info_name_label)

        # 文件格式
        self.info_ext_label = QLabel("—")
        self.info_ext_label.setStyleSheet(f"color: {_DARK_FG};")
        self.info_ext_label.setToolTip("文件扩展名及格式说明")
        file_info_layout.addRow(self._make_form_label("文件格式:"), self.info_ext_label)

        # 文件大小
        self.info_size_label = QLabel("—")
        self.info_size_label.setStyleSheet(f"color: {_DARK_FG};")
        self.info_size_label.setToolTip("文件大小（字节/KB/MB）")
        file_info_layout.addRow(self._make_form_label("文件大小:"), self.info_size_label)

        # 修改时间
        self.info_mtime_label = QLabel("—")
        self.info_mtime_label.setStyleSheet(f"color: {_DARK_FG};")
        self.info_mtime_label.setToolTip("文件最后修改时间")
        file_info_layout.addRow(self._make_form_label("修改时间:"), self.info_mtime_label)

        # 格式说明
        self.info_format_tip_label = QLabel("—")
        self.info_format_tip_label.setWordWrap(True)
        self.info_format_tip_label.setStyleSheet(f"color: {_DARK_WARN}; font-size: 12px;")
        self.info_format_tip_label.setToolTip("当前文件格式的详细说明")
        file_info_layout.addRow(self._make_form_label("格式说明:"), self.info_format_tip_label)

        file_info_group.setLayout(file_info_layout)
        splitter.addWidget(file_info_group)

        # 右侧：波函数信息面板
        wfn_info_group = QGroupBox("波函数信息")
        wfn_info_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        wfn_info_layout = QVBoxLayout()

        self.wfn_info_text = QTextEdit()
        self.wfn_info_text.setReadOnly(True)
        self.wfn_info_text.setStyleSheet(
            f"QTextEdit {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"font-family: 'Consolas', 'Microsoft YaHei', monospace; font-size: 13px; }}"
        )
        self.wfn_info_text.setToolTip(
            "波函数基本信息\n\n"
            "通过 Multiwfn 菜单 6-1 获取，包括：\n"
            "  • 总能量、偶极矩、维里比\n"
            "  • 原子数、电子数、基函数数、轨道数\n"
            "  • HOMO/LUMO 能量及间隙\n"
            "  • 波函数类型、点群等"
        )
        self.wfn_info_text.setPlaceholderText("加载文件后将显示波函数信息...")

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(300)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"background-color: {_DARK_PANEL}; text-align: center; color: {_DARK_FG}; }}"
            f"QProgressBar::chunk {{ background-color: #2563eb; border-radius: 3px; }}"
        )
        self.progress_bar.setToolTip("波函数信息加载进度，setRange(0,0) 表示忙碌状态")

        wfn_info_layout.addWidget(self.wfn_info_text, stretch=1)
        wfn_info_layout.addWidget(self.progress_bar)

        wfn_info_group.setLayout(wfn_info_layout)
        splitter.addWidget(wfn_info_group)

        # 设置分栏初始比例
        splitter.setSizes([300, 500])
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background-color: {_DARK_GRID}; }}"
        )

        main_layout.addWidget(splitter, stretch=1)

        # ---- 最近打开文件列表 ----
        recent_group = QGroupBox("最近打开文件")
        recent_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        recent_layout = QHBoxLayout()

        self.recent_list = QListWidget()
        self.recent_list.setMaximumHeight(100)
        self.recent_list.setStyleSheet(
            f"QListWidget {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; }}"
            f"QListWidget::item {{ padding: 4px 8px; }}"
            f"QListWidget::item:selected {{ background-color: #2563eb; color: white; }}"
            f"QListWidget::item:hover {{ background-color: #1e3a5f; }}"
        )
        self.recent_list.setToolTip(
            "最近打开的波函数文件列表\n\n"
            "双击列表项可直接加载对应文件。\n"
            "最多保存 10 条记录，可在设置中修改。"
        )
        self.recent_list.itemDoubleClicked.connect(self._load_recent_file)

        clear_recent_btn = QPushButton("清空列表")
        clear_recent_btn.setStyleSheet(
            f"QPushButton {{ background-color: transparent; color: {_DARK_WARN}; "
            f"border: 1px solid {_DARK_WARN}; border-radius: 4px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background-color: {_DARK_WARN}; color: #161d27; }}"
        )
        clear_recent_btn.setToolTip("清空最近打开文件列表")
        clear_recent_btn.clicked.connect(self._clear_recent_files)

        recent_layout.addWidget(self.recent_list, stretch=1)
        recent_layout.addWidget(clear_recent_btn)
        recent_group.setLayout(recent_layout)
        main_layout.addWidget(recent_group)

        # ---- 底部：状态标签 ----
        self.status_label = QLabel("就绪 — 请选择波函数文件")
        self.status_label.setStyleSheet(
            f"color: #94a3b8; font-size: 12px; padding: 4px 8px; "
            f"background-color: {_DARK_PANEL}; border-radius: 4px;"
        )
        self.status_label.setToolTip("当前操作状态")
        main_layout.addWidget(self.status_label)

        self.setLayout(main_layout)

    def _make_form_label(self, text):
        """创建表单标签，统一深色主题样式。"""
        label = QLabel(text)
        label.setStyleSheet(
            f"color: #94a3b8; font-weight: bold; font-size: 12px;"
        )
        return label

    # ====================================================================
    # 文件选择与加载
    # ====================================================================
    def _browse_file(self):
        """打开文件选择对话框。"""
        selected_format = self.format_combo.currentData()

        if selected_format == "all":
            all_types = ";;".join([
                f"{fmt['name']} (*{fmt['ext']})"
                for fmt in self.mwfn_service.get_supported_file_types()
            ])
            all_extensions = " ".join([f"*{fmt['ext']}" for fmt in self.mwfn_service.get_supported_file_types()])
            file_types = f"全部 Multiwfn 支持文件 ({all_extensions});;{all_types}"
        else:
            # 查找格式名称
            fmt_name = selected_format
            for fmt in self.mwfn_service.get_supported_file_types():
                if fmt["ext"] == selected_format:
                    fmt_name = fmt["name"]
                    break
            file_types = f"{fmt_name} (*{selected_format})"

        start_dir = self.config.get("multiwfn.work_dir") or os.getcwd()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择波函数文件", start_dir, file_types
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def _open_file(self):
        """加载指定路径的波函数文件，获取文件信息和波函数信息。"""
        file_path = self.file_path_edit.text().strip()
        if not file_path:
            QMessageBox.warning(self, "警告", "请输入或选择文件路径")
            return

        # 验证文件
        validation = self.mwfn_service.validate_input_file(file_path)
        if not validation["valid"]:
            QMessageBox.critical(self, "错误", validation["message"])
            return

        # 更新文件基本信息
        self._update_file_info(file_path)

        # 更新最近文件列表
        self._update_recent_files(file_path)

        # 保存工作目录
        work_dir = os.path.dirname(file_path)
        self.mwfn_service.set_work_dir(work_dir)
        self.config.set("multiwfn.work_dir", work_dir)

        self._current_file = file_path

        # 获取波函数信息（通过 CalculationWorker 执行菜单 6-1）
        self._fetch_wfn_info(file_path)

        # 发射信号
        self.file_selected.emit(file_path)

        self.status_label.setText(f"已加载: {os.path.basename(file_path)}")
        self.status_label.setStyleSheet(
            f"color: {_DARK_SUCCESS}; font-size: 12px; padding: 4px 8px; "
            f"background-color: {_DARK_PANEL}; border-radius: 4px;"
        )

    def _update_file_info(self, file_path):
        """更新文件基本信息面板。"""
        self.info_path_label.setText(file_path)
        self.info_name_label.setText(os.path.basename(file_path))

        # 文件格式
        ext = os.path.splitext(file_path)[1].lower()
        self.info_ext_label.setText(ext)

        # 格式说明
        tip = FILE_FORMAT_TIPS.get(ext, "未知格式")
        self.info_format_tip_label.setText(tip.split("\n")[0] if tip else "—")

        try:
            stat = os.stat(file_path)
            self.info_size_label.setText(_format_file_size(stat.st_size))
            mtime_dt = datetime.fromtimestamp(stat.st_mtime)
            self.info_mtime_label.setText(mtime_dt.strftime("%Y-%m-%d %H:%M:%S"))
        except OSError:
            self.info_size_label.setText("—")
            self.info_mtime_label.setText("—")

    def _fetch_wfn_info(self, file_path):
        """使用 CalculationWorker 执行菜单 6-1 获取波函数基本信息。"""
        if self._worker and self._worker.isRunning():
            self.status_label.setText("正在加载，请稍候...")
            return

        commands = InputGenerator.generate_wfn_check_commands()
        work_dir = os.path.dirname(file_path)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 忙碌状态
        self.wfn_info_text.setText("正在获取波函数信息...")
        self.status_label.setText("正在获取波函数信息...")

        self._worker = CalculationWorker(
            file_path, commands, work_dir,
            task_name="波函数信息获取"
        )
        self._worker.finished_ok.connect(self._on_wfn_info_loaded)
        self._worker.failed.connect(self._on_wfn_info_failed)
        self._worker.start()

    def _on_wfn_info_loaded(self, result):
        """波函数信息获取成功的回调。"""
        try:
            output = result.get("output", "")
            wfn_info = OutputParser.parse_wfn_info(output)
            self._last_wfn_info = wfn_info
            self._display_wfn_info(wfn_info)
        except Exception as e:
            self.wfn_info_text.setText(f"波函数信息解析失败: {e}")
            self._last_wfn_info = {}
        finally:
            self.progress_bar.setVisible(False)
            self._worker = None

    def _on_wfn_info_failed(self, error_msg):
        """波函数信息获取失败的回调。"""
        self.wfn_info_text.setText(f"获取波函数信息失败:\n{error_msg}")
        self.progress_bar.setVisible(False)
        self._worker = None
        self.status_label.setText("波函数信息获取失败")
        self.status_label.setStyleSheet(
            f"color: {_DARK_ERROR}; font-size: 12px; padding: 4px 8px; "
            f"background-color: {_DARK_PANEL}; border-radius: 4px;"
        )

    def _display_wfn_info(self, info):
        """将波函数信息字典格式化显示到文本框。"""
        if not info:
            self.wfn_info_text.setText("未解析到波函数信息。\n请确认文件格式正确且 Multiwfn 可正常读取。")
            return

        lines = []
        lines.append("=" * 50)
        lines.append("波函数基本信息")
        lines.append("=" * 50)

        # 按优先级排列显示
        display_order = [
            "wavefunction_type", "title", "num_atoms", "num_electrons",
            "alpha_electrons", "beta_electrons", "num_orbitals", "num_gtf",
            "net_charge", "multiplicity",
            "total_energy", "dipole_moment", "virial_ratio",
            "homo_energy", "lumo_energy", "homo_lumo_gap",
            "occ_orbital_start", "occ_orbital_end", "num_occ_orbitals",
            "molecular_weight", "point_group",
        ]

        for key in display_order:
            if key in info:
                cn_name = WFN_FIELD_NAMES.get(key, key)
                value = info[key]
                if isinstance(value, float):
                    lines.append(f"  {cn_name:<20s}  {value:.6f}")
                else:
                    lines.append(f"  {cn_name:<20s}  {value}")

        # 显示不在 display_order 中的其他字段
        for key, value in info.items():
            if key not in display_order and key != "status":
                cn_name = WFN_FIELD_NAMES.get(key, key)
                if isinstance(value, float):
                    lines.append(f"  {cn_name:<20s}  {value:.6f}")
                else:
                    lines.append(f"  {cn_name:<20s}  {value}")

        lines.append("=" * 50)
        self.wfn_info_text.setText("\n".join(lines))

    # ====================================================================
    # 最近文件管理
    # ====================================================================
    def _load_recent_files(self):
        """从配置加载最近文件列表。"""
        recent_files = self.config.get("history.recent_files", [])
        self.recent_list.clear()
        for file_path in recent_files:
            if os.path.exists(file_path):
                item = QListWidgetItem(os.path.basename(file_path))
                item.setData(Qt.UserRole, file_path)
                # tooltip 显示完整路径
                item.setToolTip(
                    f"文件: {file_path}\n\n双击可直接加载此文件"
                )
                self.recent_list.addItem(item)

    def _update_recent_files(self, file_path):
        """更新最近文件列表（移到最前，去重，限制数量）。"""
        recent_files = self.config.get("history.recent_files", [])
        if file_path in recent_files:
            recent_files.remove(file_path)
        recent_files.insert(0, file_path)
        max_recent = self.config.get("history.max_recent", 10)
        recent_files = recent_files[:max_recent]
        self.config.set("history.recent_files", recent_files)
        self._load_recent_files()

    def _load_recent_file(self, item):
        """双击最近文件列表项加载文件。"""
        file_path = item.data(Qt.UserRole)
        if file_path and os.path.exists(file_path):
            self.file_path_edit.setText(file_path)
            self._open_file()
        else:
            QMessageBox.warning(self, "文件不存在", f"文件已不存在:\n{file_path}")
            # 从列表中移除
            self.recent_list.takeItem(self.recent_list.row(item))

    def _clear_recent_files(self):
        """清空最近文件列表。"""
        self.config.set("history.recent_files", [])
        self.recent_list.clear()

    # ====================================================================
    # 外部接口
    # ====================================================================
    def set_input_file(self, file_path):
        """外部设置文件路径（供主窗口调用）。"""
        self.file_path_edit.setText(file_path)
        if file_path and os.path.exists(file_path):
            self._open_file()

    def set_current_file(self, file_path):
        """外部设置当前文件（兼容旧接口）。"""
        self.set_input_file(file_path)

    def get_current_file(self):
        """返回当前加载的文件路径。"""
        return self._current_file

    @property
    def current_file(self):
        """兼容属性访问（供主窗口检查文件状态）。"""
        return self._current_file
