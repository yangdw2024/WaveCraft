#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结构与轨道可视化模块 — 对应 Multiwfn 主菜单 0

功能：
  - 分子结构信息显示（原子坐标表格）
  - HOMO/LUMO/指定轨道可视化（导出 cube 文件）
  - 电子密度等值面计算（导出 cube 文件）
  - 轨道信息列表
  - 每个功能有详细中文 tooltip

布局：
  - 控制栏：功能选择(QComboBox) + 参数设置
  - 结果区：文本输出 + 原子坐标表格 + 导出按钮

使用已有组件：CalculationWorker / InputGenerator / OutputParser / ExportButtonWidget
深色主题适配
"""

import os
import glob as glob_module

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QTableWidget, QTableWidgetItem, QGroupBox,
    QProgressBar, QMessageBox, QTextEdit, QSpinBox, QDoubleSpinBox,
    QFormLayout, QHeaderView, QSplitter
)
from PyQt5.QtCore import Qt

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.output_parser import OutputParser
from ..utils.export_utils import ExportButtonWidget


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
# 功能定义 — 带详细中文 tooltip
# ============================================================================
STRUCTURE_FUNCTIONS = {
    "structure_info": {
        "label": "分子结构信息",
        "tooltip": (
            "分子结构信息\n\n"
            "功能：加载波函数文件后自动获取并显示分子的原子坐标信息。\n\n"
            "显示内容：\n"
            "  • 各原子的序号、元素符号、笛卡尔坐标 (Å)\n"
            "  • 原子总数、分子量等基本信息\n\n"
            "对应 Multiwfn 路径：主菜单 0（自动加载）"
        ),
    },
    "orbital_view": {
        "label": "轨道可视化（导出cube）",
        "tooltip": (
            "分子轨道可视化\n\n"
            "功能：生成指定分子轨道(MO)的 cube 文件，\n"
            "可用 VMD / PyMOL / VESTA 等软件绘制等值面。\n\n"
            "参数说明：\n"
            "  • 轨道序号：从 1 开始，HOMO 轨道通常是占据轨道中序号最大的\n"
            "  • 等值面值：控制等值面的大小，通常取 0.02~0.05 a.u.\n\n"
            "HOMO 轨道：最高占据分子轨道，反映分子给出电子的能力\n"
            "LUMO 轨道：最低未占分子轨道，反映分子接受电子的能力\n\n"
            "对应 Multiwfn 路径：主菜单 0 → 4 → 输入轨道序号 → 1 导出 cube"
        ),
    },
    "density_cube": {
        "label": "电子密度等值面（导出cube）",
        "tooltip": (
            "电子密度等值面计算\n\n"
            "功能：计算电子密度 ρ(r) 的三维网格数据并导出为 cube 文件，\n"
            "可用 VMD / PyMOL 等软件绘制等值面图。\n\n"
            "参数说明：\n"
            "  • 网格质量：粗糙(快) / 中等(默认) / 精细(慢) / 超精细(很慢)\n"
            "    质量越高，等值面越平滑，但计算时间越长\n\n"
            "电子密度等值面可以清晰展示分子的形状和化学键区域，\n"
            "是最基本也是最常用的实空间可视化方式。\n\n"
            "对应 Multiwfn 路径：主菜单 5 → 1(电子密度) → 选择网格质量 → 2 导出 cube"
        ),
    },
}

# 网格质量选项
GRID_QUALITY_OPTIONS = ["粗糙 (快)", "中等", "精细 (慢)", "超精细 (很慢)"]


class StructureViewerTab(QWidget):
    """结构与轨道可视化标签页，对应 Multiwfn 主菜单 0。"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_atoms = []
        self._last_wfn_info = {}
        self._last_output = ""
        self._loading = False
        self._init_ui()

    # ====================================================================
    # 界面构建
    # ====================================================================
    def _init_ui(self):
        """构建完整界面：控制栏 + 结果区。"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # ---- 控制栏：功能选择 + 参数 ----
        control_group = QGroupBox("功能选择与参数设置")
        control_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        control_layout = QVBoxLayout()

        # 第一行：功能选择
        func_row = QHBoxLayout()
        func_label = QLabel("功能:")
        func_label.setStyleSheet(f"color: {_DARK_FG}; font-weight: bold;")
        func_label.setToolTip("选择要执行的分子结构与轨道分析功能")

        self.func_combo = QComboBox()
        self.func_combo.setStyleSheet(
            f"QComboBox {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 8px; "
            f"min-width: 250px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox QAbstractItemView {{ background-color: {_DARK_PANEL}; "
            f"color: {_DARK_FG}; selection-background-color: #2563eb;}}"
        )
        self.func_combo.setToolTip("选择要执行的分析功能")
        for key, func_def in STRUCTURE_FUNCTIONS.items():
            self.func_combo.addItem(func_def["label"], key)
        self.func_combo.currentIndexChanged.connect(self._on_function_changed)

        func_row.addWidget(func_label)
        func_row.addWidget(self.func_combo, stretch=1)
        func_row.addStretch()
        control_layout.addLayout(func_row)

        # 第二行：轨道可视化参数（轨道序号 + 等值面值）
        orbital_param_widget = QWidget()
        orbital_param_layout = QHBoxLayout(orbital_param_widget)
        orbital_param_layout.setContentsMargins(0, 0, 0, 0)

        orb_index_label = QLabel("轨道序号:")
        orb_index_label.setStyleSheet(f"color: {_DARK_FG}; font-weight: bold;")
        orb_index_label.setToolTip("要可视化的分子轨道序号（从1开始）")

        self.orbital_spin = QSpinBox()
        self.orbital_spin.setRange(1, 10000)
        self.orbital_spin.setValue(1)
        self.orbital_spin.setStyleSheet(
            f"QSpinBox {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 8px; }}"
        )
        self.orbital_spin.setToolTip(
            "分子轨道序号\n\n"
            "从 1 开始编号。HOMO 是最高占据轨道，LUMO 是最低未占轨道。\n"
            "加载文件后可在波函数信息中查看 HOMO/LUMO 的序号。\n"
            "对应 Multiwfn 主菜单 0 → 4 的轨道序号输入。"
        )

        orb_homo_btn = QPushButton("HOMO")
        orb_homo_btn.setStyleSheet(
            f"QPushButton {{ background-color: #2563eb; color: white; "
            f"border: none; border-radius: 4px; padding: 4px 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: #1d4ed8; }}"
        )
        orb_homo_btn.setToolTip(
            "快速设置轨道序号为 HOMO\n\n"
            "HOMO (Highest Occupied Molecular Orbital)：\n"
            "最高占据分子轨道，反映分子给出电子的能力。\n"
            "HOMO 能量越高，分子越容易给出电子，亲核性越强。"
        )
        orb_homo_btn.clicked.connect(self._set_homo)

        orb_lumo_btn = QPushButton("LUMO")
        orb_lumo_btn.setStyleSheet(
            f"QPushButton {{ background-color: #7c3aed; color: white; "
            f"border: none; border-radius: 4px; padding: 4px 10px; font-weight: bold; }}"
            f"QPushButton:hover {{ background-color: #6d28d9; }}"
        )
        orb_lumo_btn.setToolTip(
            "快速设置轨道序号为 LUMO\n\n"
            "LUMO (Lowest Unoccupied Molecular Orbital)：\n"
            "最低未占分子轨道，反映分子接受电子的能力。\n"
            "LUMO 能量越低，分子越容易接受电子，亲电性越强。"
        )
        orb_lumo_btn.clicked.connect(self._set_lumo)

        iso_label = QLabel("等值面值:")
        iso_label.setStyleSheet(f"color: {_DARK_FG}; font-weight: bold;")
        iso_label.setToolTip("轨道等值面的数值，通常取 0.02~0.05 a.u.")

        self.iso_spin = QDoubleSpinBox()
        self.iso_spin.setRange(0.0001, 10.0)
        self.iso_spin.setValue(0.02)
        self.iso_spin.setDecimals(5)
        self.iso_spin.setSingleStep(0.005)
        self.iso_spin.setStyleSheet(
            f"QDoubleSpinBox {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 8px; }}"
        )
        self.iso_spin.setToolTip(
            "轨道等值面数值\n\n"
            "控制等值面的大小。数值越大，等值面越小（只包含密度更高的区域）。\n"
            "推荐值：\n"
            "  • 轨道等值面：0.02 ~ 0.05 a.u.\n"
            "  • 电子密度等值面：0.02 ~ 0.2 a.u.\n\n"
            "正值和负值分别对应轨道波函数的不同相位。"
        )

        orbital_param_layout.addWidget(orb_index_label)
        orbital_param_layout.addWidget(self.orbital_spin)
        orbital_param_layout.addWidget(orb_homo_btn)
        orbital_param_layout.addWidget(orb_lumo_btn)
        orbital_param_layout.addSpacing(20)
        orbital_param_layout.addWidget(iso_label)
        orbital_param_layout.addWidget(self.iso_spin)
        orbital_param_layout.addStretch()

        self._orbital_param_widget = orbital_param_widget

        # 第三行：电子密度参数（网格质量）
        density_param_widget = QWidget()
        density_param_layout = QHBoxLayout(density_param_widget)
        density_param_layout.setContentsMargins(0, 0, 0, 0)

        grid_label = QLabel("网格质量:")
        grid_label.setStyleSheet(f"color: {_DARK_FG}; font-weight: bold;")
        grid_label.setToolTip("网格精度，影响计算时间和结果精细度")

        self.grid_combo = QComboBox()
        self.grid_combo.addItems(GRID_QUALITY_OPTIONS)
        self.grid_combo.setCurrentIndex(1)  # 默认"中等"
        self.grid_combo.setStyleSheet(
            f"QComboBox {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 8px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox QAbstractItemView {{ background-color: {_DARK_PANEL}; "
            f"color: {_DARK_FG}; selection-background-color: #2563eb;}}"
        )
        self.grid_combo.setToolTip(
            "网格质量选择\n\n"
            "  • 粗糙 (快)：约 75×75×75 格点，适合快速预览\n"
            "  • 中等：约 100×100×100 格点，兼顾速度和质量（默认）\n"
            "  • 精细 (慢)：约 150×150×150 格点，适合发表级图像\n"
            "  • 超精细 (很慢)：约 200×200×200 格点，最高精度\n\n"
            "格点数越多，等值面越平滑，但计算时间显著增加。"
        )

        density_param_layout.addWidget(grid_label)
        density_param_layout.addWidget(self.grid_combo)
        density_param_layout.addStretch()

        self._density_param_widget = density_param_widget

        # 将参数面板加入控制区域（初始隐藏密度参数）
        control_layout.addWidget(self._orbital_param_widget)
        control_layout.addWidget(self._density_param_widget)
        self._density_param_widget.setVisible(False)

        # 功能说明标签
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(
            f"color: {_DARK_WARN}; font-size: 12px; padding: 6px; "
            f"background-color: {_DARK_PANEL}; border-radius: 4px;"
        )
        self.desc_label.setToolTip("当前选择功能的简要说明")
        control_layout.addWidget(self.desc_label)

        # 执行按钮 + 进度条
        run_row = QHBoxLayout()
        self.run_btn = QPushButton("执行")
        self.run_btn.setStyleSheet(
            f"QPushButton {{ background-color: #e67e22; color: white; "
            f"border: none; border-radius: 4px; padding: 8px 24px; "
            f"font-weight: bold; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: #d35400; }}"
            f"QPushButton:pressed {{ background-color: #c0392b; }}"
            f"QPushButton:disabled {{ background-color: #4a5568; color: #718096; }}"
        )
        self.run_btn.setToolTip("执行当前选择的分析功能")
        self.run_btn.clicked.connect(self._execute)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(250)
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"background-color: {_DARK_PANEL}; text-align: center; color: {_DARK_FG}; }}"
            f"QProgressBar::chunk {{ background-color: #2563eb; border-radius: 3px; }}"
        )
        self.progress_bar.setToolTip("计算进度指示，setRange(0,0) 表示忙碌状态")

        run_row.addWidget(self.run_btn)
        run_row.addWidget(self.progress_bar)
        run_row.addStretch()
        control_layout.addLayout(run_row)

        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)

        # ---- 结果区：原子坐标表格 + 输出文本 ----
        splitter = QSplitter(Qt.Vertical)

        # 原子坐标表格
        atom_group = QGroupBox("原子坐标信息")
        atom_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        atom_layout = QVBoxLayout()

        self.atom_table = QTableWidget()
        self.atom_table.setColumnCount(5)
        self.atom_table.setHorizontalHeaderLabels(["序号", "元素", "X (Å)", "Y (Å)", "Z (Å)"])
        self.atom_table.horizontalHeader().setStretchLastSection(True)
        self.atom_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.atom_table.setAlternatingRowColors(True)
        self.atom_table.setStyleSheet(
            f"QTableWidget {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"gridline-color: {_DARK_GRID}; }}"
            f"QTableWidget::item {{ padding: 2px 6px; }}"
            f"QTableWidget::item:alternate {{ background-color: #1a2332; }}"
            f"QHeaderView::section {{ background-color: #0f172a; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; padding: 4px; font-weight: bold; }}"
        )
        self.atom_table.setToolTip(
            "原子坐标信息\n\n"
            "加载波函数文件后自动从 Multiwfn 输出中解析原子坐标。\n"
            "坐标单位为埃 (Å)。点击列标题可排序。"
        )
        atom_layout.addWidget(self.atom_table)

        # 原子坐标导出
        self.atom_export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_atom_export_data,
            default_filename="atom_coordinates"
        )
        self.atom_export_widget.setStyleSheet(
            f"QPushButton {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background-color: #2563eb; color: white; }}"
        )
        self.atom_export_widget.setToolTip("将原子坐标和波函数基本信息导出为 TXT/CSV/Excel 格式")
        atom_layout.addWidget(self.atom_export_widget)

        atom_group.setLayout(atom_layout)
        splitter.addWidget(atom_group)

        # 输出文本区
        output_group = QGroupBox("输出信息")
        output_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_FG}; font-weight: bold; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"margin-top: 8px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; }}"
        )
        output_layout = QVBoxLayout()

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setStyleSheet(
            f"QTextEdit {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; "
            f"font-family: 'Consolas', 'Microsoft YaHei', monospace; font-size: 13px; }}"
        )
        self.output_text.setToolTip(
            "分析输出信息\n\n"
            "显示 Multiwfn 的文本输出，包括：\n"
            "  • 分子结构信息\n"
            "  • 轨道计算结果\n"
            "  • cube 文件导出路径\n"
            "  • 错误和警告信息"
        )
        self.output_text.setPlaceholderText("执行分析后，输出信息将显示在这里...")

        # 输出文本导出
        self.output_export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_output_export_data,
            default_filename="structure_output"
        )
        self.output_export_widget.setStyleSheet(
            f"QPushButton {{ background-color: {_DARK_PANEL}; color: {_DARK_FG}; "
            f"border: 1px solid {_DARK_GRID}; border-radius: 4px; padding: 4px 12px; }}"
            f"QPushButton:hover {{ background-color: #2563eb; color: white; }}"
        )
        self.output_export_widget.setToolTip("将输出信息导出为 TXT/CSV/Excel 格式")
        output_layout.addWidget(self.output_text)
        output_layout.addWidget(self.output_export_widget)

        output_group.setLayout(output_layout)
        splitter.addWidget(output_group)

        # 设置分栏初始比例
        splitter.setSizes([250, 300])
        splitter.setStyleSheet(
            f"QSplitter::handle {{ background-color: {_DARK_GRID}; }}"
        )

        main_layout.addWidget(splitter, stretch=1)

        self.setLayout(main_layout)

        # 初始化功能说明标签
        self._on_function_changed(0)

    # ====================================================================
    # 功能切换
    # ====================================================================
    def _on_function_changed(self, index):
        """功能选择变更时，切换参数面板和更新说明。"""
        if not self.func_combo:
            return

        func_key = self.func_combo.currentData()
        if func_key is None:
            return

        func_def = STRUCTURE_FUNCTIONS.get(func_key, {})
        tooltip = func_def.get("tooltip", "")
        self.desc_label.setText(tooltip.split("\n\n")[0] if tooltip else "")

        # 切换参数面板可见性
        self._orbital_param_widget.setVisible(func_key == "orbital_view")
        self._density_param_widget.setVisible(func_key == "density_cube")

    # ====================================================================
    # HOMO / LUMO 快捷设置
    # ====================================================================
    def _set_homo(self):
        """将轨道序号设置为 HOMO（占据轨道的最后一个）。"""
        occ_end = self._last_wfn_info.get("occ_orbital_end")
        if occ_end is not None:
            self.orbital_spin.setValue(int(occ_end))
        else:
            # 从波函数信息尝试推断
            num_elec = self._last_wfn_info.get("num_electrons")
            alpha = self._last_wfn_info.get("alpha_electrons")
            if alpha is not None:
                self.orbital_spin.setValue(int(alpha))
            elif num_elec is not None:
                self.orbital_spin.setValue(int(num_elec) // 2)
            else:
                QMessageBox.information(
                    self, "提示",
                    "尚未获取波函数信息，无法确定 HOMO 序号。\n"
                    "请先加载文件后再使用此功能。"
                )

    def _set_lumo(self):
        """将轨道序号设置为 LUMO（HOMO 的下一个）。"""
        occ_end = self._last_wfn_info.get("occ_orbital_end")
        if occ_end is not None:
            self.orbital_spin.setValue(int(occ_end) + 1)
        else:
            alpha = self._last_wfn_info.get("alpha_electrons")
            num_elec = self._last_wfn_info.get("num_electrons")
            if alpha is not None:
                self.orbital_spin.setValue(int(alpha) + 1)
            elif num_elec is not None:
                self.orbital_spin.setValue(int(num_elec) // 2 + 1)
            else:
                QMessageBox.information(
                    self, "提示",
                    "尚未获取波函数信息，无法确定 LUMO 序号。\n"
                    "请先加载文件后再使用此功能。"
                )

    # ====================================================================
    # 执行分析
    # ====================================================================
    def _execute(self):
        """根据当前选择的功能执行分析。"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "操作正在进行中，请稍候...")
            return

        func_key = self.func_combo.currentData()
        if func_key == "structure_info":
            self._load_structure_info()
        elif func_key == "orbital_view":
            self._view_orbital()
        elif func_key == "density_cube":
            self._compute_density_cube()

    # ---- 分子结构信息 ----
    def _load_structure_info(self):
        """加载分子结构信息（菜单 6-1）。"""
        if not self.current_file:
            return
        if self._worker and self._worker.isRunning():
            return

        commands = InputGenerator.generate_wfn_check_commands()
        work_dir = os.path.dirname(self.current_file)

        self._loading = True
        self._set_busy(True, "正在加载结构信息...")
        self.output_text.setText("正在获取分子结构信息...")

        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name="结构信息加载"
        )
        self._worker.finished_ok.connect(self._on_structure_loaded)
        self._worker.failed.connect(self._on_task_failed)
        self._worker.start()

    def _on_structure_loaded(self, result):
        """结构信息加载成功回调。"""
        try:
            output = result.get("output", "")
            self._last_output = output

            try:
                atoms = OutputParser.parse_atom_info(output)
            except Exception as e:
                atoms = []
                self.output_text.setText(f"原子信息解析失败: {e}")

            try:
                wfn_info = OutputParser.parse_wfn_info(output)
            except Exception as e:
                wfn_info = {}
                self.output_text.setText(f"波函数信息解析失败: {e}")

            self._last_atoms = atoms
            self._last_wfn_info = wfn_info

            self._update_atom_table(atoms)
            self._update_output_info(wfn_info, atoms)

            if not atoms:
                self.output_text.append("\n注意：未解析到原子坐标，请检查输入文件是否有效。")
        except Exception as e:
            QMessageBox.warning(self, "解析错误", f"结构信息处理失败: {str(e)}")
            self.output_text.setText(f"结构信息处理失败: {str(e)}")
        finally:
            self._loading = False
            self._set_busy(False)
            self._worker = None

    # ---- 轨道可视化 ----
    def _view_orbital(self):
        """执行轨道可视化（菜单 0-4）。"""
        orbital_index = self.orbital_spin.value()
        isovalue = self.iso_spin.value()

        try:
            commands = InputGenerator.generate_orbital_view_commands(orbital_index, isovalue)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        self._set_busy(True, f"正在生成轨道 {orbital_index} 的 cube 文件...")
        self.output_text.setText(
            f"正在生成轨道 {orbital_index} 的 cube 文件...\n"
            f"等值面值: {isovalue} a.u.\n\n"
            f"对应 Multiwfn 路径: 主菜单 0 → 4 → {orbital_index} → 1 → {isovalue}"
        )

        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"轨道可视化 {orbital_index}"
        )
        self._worker.finished_ok.connect(self._on_orbital_viewed)
        self._worker.failed.connect(self._on_task_failed)
        self._worker.start()

    def _on_orbital_viewed(self, result):
        """轨道可视化完成回调。"""
        try:
            output = result.get("output", "")
            self._last_output = output
            orbital_index = self.orbital_spin.value()
            work_dir = os.path.dirname(self.current_file)

            # 查找生成的 cube 文件
            cube_file = os.path.join(work_dir, f"orbital_{orbital_index}.cub")
            if not os.path.exists(cube_file):
                # 尝试查找工作目录下最新的 .cub 文件
                candidates = [
                    p for p in glob_module.glob(os.path.join(work_dir, "*.cub"))
                    if os.path.isfile(p)
                ]
                if candidates:
                    cube_file = max(candidates, key=os.path.getmtime)

            # 构建输出信息
            info_lines = [
                f"轨道 {orbital_index} 可视化完成",
                f"等值面值: {self.iso_spin.value()} a.u.",
                "",
            ]
            if os.path.exists(cube_file):
                size_kb = os.path.getsize(cube_file) / 1024
                info_lines.append(f"cube 文件: {cube_file}")
                info_lines.append(f"文件大小: {size_kb:.1f} KB")
                info_lines.append("")
                info_lines.append("可用以下软件查看等值面：")
                info_lines.append("  • VMD: File → New Molecule → 加载 cube 文件")
                info_lines.append("  • PyMOL: load cube_file.cub; isosurface orbital, cube_file, 0.02")
                info_lines.append("  • VESTA: File → Open → 选择 cube 文件")
                self.output_text.setText("\n".join(info_lines))
                QMessageBox.information(self, "成功", f"轨道 cube 文件已导出到:\n{cube_file}")
            else:
                info_lines.append("未检测到 cube 文件，请检查 Multiwfn 输出。")
                self.output_text.setText("\n".join(info_lines))
                # 将 Multiwfn 原始输出追加
                self.output_text.append("\n\n--- Multiwfn 原始输出 ---\n")
                self.output_text.append(output[-3000:] if len(output) > 3000 else output)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"轨道处理失败: {str(e)}")
        finally:
            self._set_busy(False)
            self._worker = None

    # ---- 电子密度等值面 ----
    def _compute_density_cube(self):
        """执行电子密度等值面计算（菜单 5-1）。"""
        grid_quality = self.grid_combo.currentText()

        try:
            commands = InputGenerator.generate_realspace_cube_commands(
                "电子密度", grid_quality
            )
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        self._set_busy(True, "正在计算电子密度 cube 文件...")
        self.output_text.setText(
            f"正在计算电子密度等值面...\n"
            f"网格质量: {grid_quality}\n\n"
            f"对应 Multiwfn 路径: 主菜单 5 → 1(电子密度) → {grid_quality} → 2(导出cube)"
        )

        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name="电子密度等值面"
        )
        self._worker.finished_ok.connect(self._on_density_cube_done)
        self._worker.failed.connect(self._on_task_failed)
        self._worker.start()

    def _on_density_cube_done(self, result):
        """电子密度 cube 计算完成回调。"""
        try:
            output = result.get("output", "")
            self._last_output = output
            work_dir = os.path.dirname(self.current_file)

            # 查找 cube 文件
            cube_file = result.get("cube_file")
            if not cube_file or not os.path.exists(cube_file):
                cube_file = os.path.join(work_dir, "output.cub")
            if not os.path.exists(cube_file):
                cube_file = os.path.join(work_dir, "density.cub")
            if not os.path.exists(cube_file):
                # 查找最新的 cube 文件
                candidates = [
                    p for p in glob_module.glob(os.path.join(work_dir, "*.cub"))
                    if os.path.isfile(p)
                ]
                if candidates:
                    cube_file = max(candidates, key=os.path.getmtime)

            info_lines = [
                "电子密度等值面计算完成",
                f"网格质量: {self.grid_combo.currentText()}",
                "",
            ]
            if os.path.exists(cube_file):
                size_mb = os.path.getsize(cube_file) / (1024 * 1024)
                info_lines.append(f"cube 文件: {cube_file}")
                info_lines.append(f"文件大小: {size_mb:.2f} MB")
                info_lines.append("")
                info_lines.append("可用以下软件查看等值面：")
                info_lines.append("  • VMD: 建议等值面值 0.02~0.2 a.u.")
                info_lines.append("  • VESTA: 建议等值面值 0.02~0.2 a.u.")
                self.output_text.setText("\n".join(info_lines))
                QMessageBox.information(self, "成功", f"电子密度 cube 文件已导出到:\n{cube_file}")
            else:
                info_lines.append("未检测到 cube 文件，请检查 Multiwfn 输出。")
                self.output_text.setText("\n".join(info_lines))
                self.output_text.append("\n\n--- Multiwfn 原始输出 ---\n")
                self.output_text.append(output[-3000:] if len(output) > 3000 else output)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"电子密度计算处理失败: {str(e)}")
        finally:
            self._set_busy(False)
            self._worker = None

    # ---- 通用失败回调 ----
    def _on_task_failed(self, error_msg):
        """任务执行失败回调。"""
        self.output_text.setText(f"操作失败:\n{error_msg}")
        self._loading = False
        self._set_busy(False)
        self._worker = None

    # ====================================================================
    # UI 更新
    # ====================================================================
    def _set_busy(self, busy, status_text=""):
        """设置忙碌状态（禁用按钮、显示进度条）。"""
        self.run_btn.setEnabled(not busy)
        self.run_btn.setText("处理中..." if busy else "执行")
        self.progress_bar.setVisible(busy)
        if busy:
            self.progress_bar.setRange(0, 0)  # 忙碌动画
        if status_text:
            self.output_text.setText(status_text)

    def _update_atom_table(self, atoms):
        """更新原子坐标表格。"""
        self.atom_table.setRowCount(0)
        self.atom_table.setSortingEnabled(False)
        for atom in atoms:
            row = self.atom_table.rowCount()
            self.atom_table.insertRow(row)
            self.atom_table.setItem(row, 0, QTableWidgetItem(str(atom["index"])))
            self.atom_table.setItem(row, 1, QTableWidgetItem(atom["symbol"]))
            self.atom_table.setItem(row, 2, QTableWidgetItem(f"{atom['x']:.6f}"))
            self.atom_table.setItem(row, 3, QTableWidgetItem(f"{atom['y']:.6f}"))
            self.atom_table.setItem(row, 4, QTableWidgetItem(f"{atom['z']:.6f}"))
        self.atom_table.setSortingEnabled(True)

    def _update_output_info(self, wfn_info, atoms):
        """更新输出信息文本。"""
        lines = []
        lines.append("=" * 50)
        lines.append("分子结构信息摘要")
        lines.append("=" * 50)

        if wfn_info:
            # 波函数类型
            wf_type = wfn_info.get("wavefunction_type", "未知")
            lines.append(f"  波函数类型:  {wf_type}")

            # 原子数
            num_atoms = wfn_info.get("num_atoms", len(atoms))
            lines.append(f"  原子数:      {num_atoms}")

            # 电子数
            num_elec = wfn_info.get("num_electrons")
            if num_elec is not None:
                lines.append(f"  总电子数:    {num_elec}")
                alpha = wfn_info.get("alpha_electrons")
                beta = wfn_info.get("beta_electrons")
                if alpha is not None:
                    lines.append(f"  Alpha 电子:  {alpha}")
                if beta is not None:
                    lines.append(f"  Beta 电子:   {beta}")

            # 基函数与轨道
            num_orb = wfn_info.get("num_orbitals")
            if num_orb is not None:
                lines.append(f"  基函数数:    {num_orb}")
            num_gtf = wfn_info.get("num_gtf")
            if num_gtf is not None:
                lines.append(f"  原始GTF数:   {num_gtf}")

            # HOMO/LUMO
            homo = wfn_info.get("homo_energy")
            lumo = wfn_info.get("lumo_energy")
            gap = wfn_info.get("homo_lumo_gap")
            if homo is not None:
                lines.append(f"  HOMO 能量:   {homo:.6f} a.u.")
            if lumo is not None:
                lines.append(f"  LUMO 能量:   {lumo:.6f} a.u.")
            if gap is not None:
                lines.append(f"  HOMO-LUMO:   {gap:.6f} a.u. ({gap * 27.2114:.2f} eV)")

            # 占据轨道范围
            occ_start = wfn_info.get("occ_orbital_start")
            occ_end = wfn_info.get("occ_orbital_end")
            if occ_start is not None and occ_end is not None:
                lines.append(f"  占据轨道:    {occ_start} ~ {occ_end}")
                lines.append(f"  → HOMO 序号: {occ_end}")
                lines.append(f"  → LUMO 序号: {occ_end + 1}")

            # 总能量
            energy = wfn_info.get("total_energy")
            if energy is not None:
                lines.append(f"  总能量:      {energy:.8f} a.u.")

            # 偶极矩
            dipole = wfn_info.get("dipole_moment")
            if dipole is not None:
                lines.append(f"  偶极矩:      {dipole:.6f} a.u.")

            # 分子量
            mw = wfn_info.get("molecular_weight")
            if mw is not None:
                lines.append(f"  分子量:      {mw:.4f} amu")

            # 点群
            pg = wfn_info.get("point_group")
            if pg is not None:
                lines.append(f"  点群:        {pg}")

        lines.append("")
        lines.append(f"  已解析原子坐标: {len(atoms)} 个")
        lines.append("=" * 50)

        self.output_text.setText("\n".join(lines))

    # ====================================================================
    # 导出数据提供
    # ====================================================================
    def _get_atom_export_data(self):
        """提供原子坐标导出数据。"""
        if not self._last_atoms:
            if self._last_output:
                return [{"output": self._last_output}], ["output"], {"文件": self.current_file}
            return None
        records = []
        for atom in self._last_atoms:
            records.append({
                "index": atom["index"],
                "symbol": atom["symbol"],
                "x": atom["x"],
                "y": atom["y"],
                "z": atom["z"],
            })
        metadata = {
            "文件": self.current_file,
            "原子数": len(self._last_atoms),
        }
        metadata.update({k: str(v) for k, v in self._last_wfn_info.items()})
        return records, ["index", "symbol", "x", "y", "z"], metadata

    def _get_output_export_data(self):
        """提供输出文本导出数据。"""
        text = self.output_text.toPlainText()
        if not text.strip():
            return None
        return [{"output": text}], ["output"], {"文件": self.current_file}

    # ====================================================================
    # 外部接口
    # ====================================================================
    def set_input_file(self, file_path):
        """外部设置文件路径，并自动加载结构信息。"""
        self.current_file = file_path
        self._load_structure_info()
