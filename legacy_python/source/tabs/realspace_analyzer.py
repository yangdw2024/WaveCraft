#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
实空间函数分析模块 - 对应 Multiwfn 主菜单 5
支持电子密度、密度梯度模、拉普拉斯、ELF、LOL、NCI相关量、
动能密度、局部电离能、静电势、密度差、Fukui函数、双描述符、自旋密度等
计算cube文件并绘制2D切面热图，支持多种颜色映射与数据导出
"""

import os
import numpy as np
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox, QProgressBar,
    QSplitter, QTableWidget, QTableWidgetItem,
    QHeaderView, QDoubleSpinBox, QSpinBox, QFormLayout
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.cube_parser import CubeParser
from ..utils.export_utils import ExportButtonWidget


# ============================================================================
# 实空间函数详细说明字典
# 键名必须与 InputGenerator.REALSPACE_FUNCTIONS 中的键匹配
# ============================================================================
REALSPACE_INFO = {
    "Electron density": {
        "label": "电子密度 (1)",
        "short": "ρ(r)",
        "desc": (
            "电子密度 ρ(r)，描述电子在三维空间中的概率分布，"
            "是最基本、最常用的实空间函数。在原子核附近电子密度最大，"
            "远离分子区域则趋于零。用于AIM拓扑分析、电荷密度差分析等。"
        ),
    },
    "Gradient norm": {
        "label": "密度梯度模 (2)",
        "short": "|∇ρ(r)|",
        "desc": (
            "电子密度梯度模 |∇ρ(r)|，反映电子密度在空间中变化的速率。"
            "在化学键区域梯度模较小（密度变化平缓），而在原子核附近梯度模极大。"
            "可用于识别化学键区域和原子壳层结构。"
        ),
    },
    "Laplacian of density": {
        "label": "密度拉普拉斯 (3)",
        "short": "∇²ρ(r)",
        "desc": (
            "电子密度拉普拉斯 ∇²ρ(r) = ∂²ρ/∂x² + ∂²ρ/∂y² + ∂²ρ/∂z²，"
            "是AIM分析的核心量。拉普拉斯为负值表示电子聚集（共价键、孤对电子区），"
            "正值表示电子耗竭（原子壳层间区域、闭壳层作用区）。"
        ),
    },
    "ELF": {
        "label": "ELF (4)",
        "short": "ELF",
        "desc": (
            "电子定域化函数(Electron Localization Function)，取值0~1之间。"
            "ELF越接近1表示电子定域性越强（如孤对电子、共价键区），"
            "越接近0表示电子离域性越强。是分析化学键类型和电子结构的重要工具。"
        ),
    },
    "LOL": {
        "label": "LOL (5)",
        "short": "LOL",
        "desc": (
            "局部轨道定位函数(Localized Orbital Locator)，与ELF类似但物理意义略有不同。"
            "LOL高值区域对应轨道高度定域化，可以清晰地划分原子壳层和化学键区域。"
            "在某些体系中LOL的图像比ELF更直观、更易于解释。"
        ),
    },
    "Sign(lambda2)*rho": {
        "label": "sign(λ₂)ρ (6)",
        "short": "sign(λ₂)ρ",
        "desc": (
            "sign(λ₂)ρ 是NCI(Noncovalent Interaction)分析的核心量。"
            "λ₂为电子密度Hessian矩阵的第二个特征值。"
            "sign(λ₂) < 0 表示吸引作用（氢键、偶极-偶极），"
            "sign(λ₂) > 0 表示排斥作用（位阻效应），"
            "sign(λ₂) ≈ 0 表示范德华作用。"
        ),
    },
    "RDG": {
        "label": "RDG (7)",
        "short": "RDG",
        "desc": (
            "约化密度梯度(Reduced Density Gradient)，NCI分析的核心量之一。"
            "RDG = 1/(2(3π²)^(1/3)) × |∇ρ|/ρ^(4/3)，"
            "在远离分子的区域RDG很大，而在弱相互作用区域RDG趋近于0。"
            "与sign(λ₂)ρ联合绘制散点图或等值面，可直观展示弱相互作用。"
        ),
    },
    "Hamiltonian kinetic energy density": {
        "label": "Hamiltonian动能密度 (8)",
        "short": "K(r)",
        "desc": (
            "Hamiltonian动能密度 K(r) = -½Σᵢ φᵢ*∇²φᵢ，"
            "用于化学键分析。在共价键区域K(r)为负值（电子聚集、动能降低），"
            "在闭壳层作用区K(r)为正值。K(r)与G(r)的差值可判断化学键类型。"
        ),
    },
    "Lagrangian kinetic energy density": {
        "label": "Lagrange动能密度 (9)",
        "short": "G(r)",
        "desc": (
            "Lagrange动能密度 G(r) = ½Σᵢ |∇φᵢ|²，恒为非负值。"
            "G(r)描述电子动能的空间分布，在原子核附近和化学键区域都有显著值。"
            "G(r)与K(r)的比值 -K/G 可用于化学键分类（>1为共价键，<1为闭壳层键）。"
        ),
    },
    "Local ionization energy": {
        "label": "局部电离能 (11)",
        "short": "Ī(r)",
        "desc": (
            "局部电离能 Ī(r) = Σᵢ ρᵢ(r)|εᵢ|/ρ(r)，"
            "是分子表面反应性的重要指标。"
            "Ī(r)越小表示该区域电子越容易被电离，对应亲核反应位点；"
            "Ī(r)越大表示电子束缚越紧，对应亲电位点。常用于分子表面分析。"
        ),
    },
    "ESP": {
        "label": "静电势 (13)",
        "short": "V(r)",
        "desc": (
            "静电势(Electrostatic Potential) V(r) = Σ_A Z_A/|r-R_A| - ∫ρ(r')/|r-r'|dr'，"
            "描述分子周围空间中单位正电荷所受的静电作用。"
            "V(r) > 0 为正静电势（缺电子区，亲核攻击位点），"
            "V(r) < 0 为负静电势（富电子区，亲电攻击位点）。"
        ),
    },
    "Density difference": {
        "label": "密度差 (15)",
        "short": "Δρ(r)",
        "desc": (
            "电子密度差 Δρ(r) = ρ_complex(r) - Σ ρ_fragment(r)，"
            "对比两个状态（或分子与片段）的电子密度变化。"
            "Δρ > 0 表示电子聚集区域，Δρ < 0 表示电子耗竭区域。"
            "广泛用于分析化学键形成过程中的电子转移与极化。"
        ),
    },
    "Fukui function": {
        "label": "Fukui函数 (16)",
        "short": "f(r)",
        "desc": (
            "Fukui函数 f(r) = (∂ρ(r)/∂N)_v，是概念DFT框架下的核心反应性指标。"
            "f⁺(r) 对应亲核攻击灵敏度（电子增加时密度变化），"
            "f⁻(r) 对应亲电攻击灵敏度（电子减少时密度变化），"
            "f⁰(r) 为自由基攻击灵敏度。用于预测分子反应位点。"
        ),
    },
    "Dual descriptor": {
        "label": "双描述符 (17)",
        "short": "Δf(r)",
        "desc": (
            "双描述符 Δf(r) = f⁺(r) - f⁻(r) = (∂²ρ/∂N²)_v，"
            "同时表征亲电性和亲核性。Δf > 0 的区域倾向亲核反应，"
            "Δf < 0 的区域倾向亲电反应。比单独的Fukui函数提供更明确的反应性判据。"
        ),
    },
    "Spin density": {
        "label": "自旋密度 (5/开壳层)",
        "short": "ρ_α-ρ_β",
        "desc": (
            "自旋密度 ρ_α(r) - ρ_β(r)，仅对开壳层体系有物理意义。"
            "正值区域α电子占主导，负值区域β电子占主导。"
            "用于分析自由基的未配对电子分布、磁性体系和过渡金属配合物的自旋态。"
        ),
    },
}

# 下拉框显示名称 -> InputGenerator.REALSPACE_FUNCTIONS 键名映射
# 显示名称含编号和中文说明，便于用户选择
FUNC_DISPLAY_TO_KEY = {
    "1  电子密度 ρ(r)": "Electron density",
    "2  密度梯度模 |∇ρ(r)|": "Gradient norm",
    "3  密度拉普拉斯 ∇²ρ(r)": "Laplacian of density",
    "4  ELF 电子定域化函数": "ELF",
    "5  LOL 局部轨道定位函数": "LOL",
    "6  sign(λ₂)ρ NCI分析": "Sign(lambda2)*rho",
    "7  RDG 约化密度梯度": "RDG",
    "8  Hamiltonian动能密度 K(r)": "Hamiltonian kinetic energy density",
    "9  Lagrange动能密度 G(r)": "Lagrangian kinetic energy density",
    "11 局部电离能 Ī(r)": "Local ionization energy",
    "13 静电势 V(r)": "ESP",
    "15 密度差 Δρ(r)": "Density difference",
    "16 Fukui函数 f(r)": "Fukui function",
    "17 双描述符 Δf(r)": "Dual descriptor",
    "5* 自旋密度 ρ_α-ρ_β": "Spin density",
}

# 网格质量选项（显示名称 -> InputGenerator.GRID_QUALITIES 键名）
GRID_DISPLAY_TO_KEY = {
    "粗糙（快）": "Coarse",
    "中等（推荐）": "Medium",
    "精细（慢）": "Fine",
    "超精细（很慢）": "Ultra fine",
}

# 可选颜色映射列表
COLORMAPS = [
    "viridis", "plasma", "inferno", "magma", "cividis",
    "jet", "coolwarm", "RdBu", "RdBu_r", "bwr",
    "seismic", "PiYG", "PRGn", "BrBG", "RdYlBu",
    "RdYlGn", "Spectral", "rainbow", "hot", "afmhot",
    "gnuplot2", "Blues", "Reds", "Greens", "Oranges",
]

# 推荐的颜色映射：根据函数特性自动推荐
RECOMMENDED_CMAPS = {
    "Electron density": "viridis",
    "Gradient norm": "inferno",
    "Laplacian of density": "RdBu",
    "ELF": "RdYlBu",
    "LOL": "RdYlBu",
    "Sign(lambda2)*rho": "RdBu_r",
    "RDG": "viridis",
    "Hamiltonian kinetic energy density": "coolwarm",
    "Lagrangian kinetic energy density": "viridis",
    "Local ionization energy": "RdYlGn_r",
    "ESP": "RdBu_r",
    "Density difference": "RdBu",
    "Fukui function": "RdBu_r",
    "Dual descriptor": "RdBu_r",
    "Spin density": "RdBu_r",
}


class RealSpaceAnalyzerTab(QWidget):
    """实空间函数分析模块 - 计算cube并绘制2D切面热图，支持多种颜色映射与数据导出"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        # 保存最近一次计算结果，供导出使用
        self._last_slice_data = None
        self._last_parser = None
        self._last_plane = None
        self._last_func_key = None
        self._last_grid = None
        self._last_slice_idx = None
        self.init_ui()

    # ====================================================================
    # 界面初始化
    # ====================================================================
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)

        # ---- 顶部控制栏 ----
        self._build_control_bar(main_layout)

        # ---- 函数说明标签 ----
        self._build_desc_label(main_layout)

        # ---- 中间分栏：左侧热图 + 右侧信息面板 ----
        self._build_main_splitter(main_layout)

        # ---- 底部：计算摘要 + 导出按钮组 ----
        self._build_bottom_bar(main_layout)

        self.setLayout(main_layout)

        # 绘制初始占位图
        self._draw_placeholder()

    # ------------------------------------------------------------------
    # 顶部控制栏
    # ------------------------------------------------------------------
    def _build_control_bar(self, parent_layout):
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # 函数选择
        func_group = QGroupBox("实空间函数")
        func_layout = QHBoxLayout(func_group)
        func_layout.setContentsMargins(6, 4, 6, 4)

        func_label = QLabel("函数类型:")
        self.func_combo = QComboBox()
        self.func_combo.setMinimumWidth(260)
        # 填充下拉框选项
        for display_name in FUNC_DISPLAY_TO_KEY:
            self.func_combo.addItem(display_name)
        self.func_combo.setCurrentIndex(0)
        self.func_combo.currentIndexChanged.connect(self._on_func_changed)
        # 设置tooltip：显示当前选项的详细说明
        self.func_combo.setToolTip(
            "选择要计算的实空间函数类型（对应 Multiwfn 主菜单 5）。\n"
            "每个函数前的编号对应 Multiwfn 中的功能编号。"
        )
        func_layout.addWidget(func_label)
        func_layout.addWidget(self.func_combo)
        control_layout.addWidget(func_group)

        # 网格质量
        grid_group = QGroupBox("网格质量")
        grid_layout = QHBoxLayout(grid_group)
        grid_layout.setContentsMargins(6, 4, 6, 4)

        grid_label = QLabel("质量:")
        self.grid_combo = QComboBox()
        self.grid_combo.setMinimumWidth(130)
        for display_name in GRID_DISPLAY_TO_KEY:
            self.grid_combo.addItem(display_name)
        # 默认选中"中等"
        self.grid_combo.setCurrentIndex(1)
        self.grid_combo.setToolTip(
            "设置实空间函数cube的格点密度（对应 Multiwfn 菜单5的网格质量选项）。\n"
            "粗糙：约75×75×75格点，计算快，适合预览；\n"
            "中等：约120×120×120，平衡速度与精度（推荐）；\n"
            "精细：约200×200×200，精度高但较慢；\n"
            "超精细：约250×250×250，极慢，用于发表级图像。"
        )
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_combo)
        control_layout.addWidget(grid_group)

        # 切面方向
        plane_group = QGroupBox("切面方向")
        plane_layout = QHBoxLayout(plane_group)
        plane_layout.setContentsMargins(6, 4, 6, 4)

        plane_label = QLabel("方向:")
        self.plane_combo = QComboBox()
        self.plane_combo.addItems(["xy", "xz", "yz"])
        self.plane_combo.setToolTip(
            "选择2D热图的切面方向：\n"
            "xy - 水平切面（垂直于z轴），适合平面分子；\n"
            "xz - 纵向切面（垂直于y轴）；\n"
            "yz - 纵向切面（垂直于x轴）。"
        )
        plane_layout.addWidget(plane_label)
        plane_layout.addWidget(self.plane_combo)
        control_layout.addWidget(plane_group)

        # 切片位置
        slice_group = QGroupBox("切片位置")
        slice_layout = QHBoxLayout(slice_group)
        slice_layout.setContentsMargins(6, 4, 6, 4)

        slice_label = QLabel("偏移:")
        self.slice_spin = QDoubleSpinBox()
        self.slice_spin.setRange(-999.0, 999.0)
        self.slice_spin.setValue(0.0)
        self.slice_spin.setDecimals(3)
        self.slice_spin.setSingleStep(0.1)
        self.slice_spin.setSuffix(" Bohr")
        self.slice_spin.setToolTip(
            "切片面相对于分子几何中心的偏移量（单位：Bohr）。\n"
            "0.000 表示经过分子中心的切面，\n"
            "正值/负值表示沿切面法线方向偏移。"
        )
        slice_layout.addWidget(slice_label)
        slice_layout.addWidget(self.slice_spin)
        control_layout.addWidget(slice_group)

        # 颜色映射
        cmap_group = QGroupBox("颜色映射")
        cmap_layout = QHBoxLayout(cmap_group)
        cmap_layout.setContentsMargins(6, 4, 6, 4)

        cmap_label = QLabel("配色:")
        self.cmap_combo = QComboBox()
        self.cmap_combo.addItems(COLORMAPS)
        self.cmap_combo.setToolTip(
            "选择热图的颜色映射方案。\n"
            "viridis/jet等适合连续量，RdBu/coolwarm适合有正负值的量。\n"
            "选择函数后会自动推荐最合适的颜色映射。"
        )
        cmap_layout.addWidget(cmap_label)
        cmap_layout.addWidget(self.cmap_combo)
        control_layout.addWidget(cmap_group)

        # 计算按钮
        self.calculate_btn = QPushButton("⚡ 计算并绘制")
        self.calculate_btn.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold; "
            "padding: 6px 16px; border-radius: 4px;"
        )
        self.calculate_btn.setToolTip(
            "计算实空间函数cube文件并绘制2D切面热图。\n"
            "Multiwfn路径：主菜单5 → 选择函数 → 网格质量 → 默认盒子 → 导出cube。"
        )
        self.calculate_btn.clicked.connect(self.on_calculate)
        control_layout.addWidget(self.calculate_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(160)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("计算进度指示，忙碌状态下显示滚动动画。")
        control_layout.addWidget(self.progress_bar)

        control_layout.addStretch()
        parent_layout.addLayout(control_layout)

    # ------------------------------------------------------------------
    # 函数说明标签
    # ------------------------------------------------------------------
    def _build_desc_label(self, parent_layout):
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(
            "color: #a8c7e2; font-size: 12px; padding: 4px 8px; "
            "background-color: #1a2332; border-radius: 4px; border: 1px solid #2a3a4a;"
        )
        self.desc_label.setToolTip("当前选中实空间函数的详细物理意义说明")
        parent_layout.addWidget(self.desc_label)
        # 初始化说明
        self._update_desc()

    # ------------------------------------------------------------------
    # 中间分栏：热图 + 信息面板
    # ------------------------------------------------------------------
    def _build_main_splitter(self, parent_layout):
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：matplotlib 热图
        self.fig = Figure(figsize=(8, 6), dpi=100)
        # 深色主题适配
        self.fig.patch.set_facecolor('#161d27')
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setToolTip("实空间函数2D切面热图可视化区域，鼠标悬停可查看坐标与数值")
        splitter.addWidget(self.canvas)

        # 右侧：信息面板
        info_group = QGroupBox("信息面板")
        info_layout = QVBoxLayout(info_group)

        # 基本信息
        self.info_text = QLabel("等待计算...")
        self.info_text.setWordWrap(True)
        self.info_text.setStyleSheet("color: #c8d6e5; font-size: 11px;")
        self.info_text.setToolTip("cube文件的基本信息：网格尺寸、原子数、取值范围等")
        info_layout.addWidget(self.info_text)

        # 原子位置表
        table_label = QLabel("切面原子投影:")
        table_label.setStyleSheet("color: #a0b0c0; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(table_label)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["原子", "坐标1", "坐标2"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setMaximumHeight(250)
        self.table.setToolTip("切面上原子投影位置（以切面两个坐标轴表示）")
        info_layout.addWidget(self.table)

        # 取值统计
        stats_label = QLabel("取值统计:")
        stats_label.setStyleSheet("color: #a0b0c0; font-weight: bold; font-size: 11px;")
        info_layout.addWidget(stats_label)

        self.stats_text = QLabel("-")
        self.stats_text.setWordWrap(True)
        self.stats_text.setStyleSheet("color: #c8d6e5; font-size: 11px;")
        self.stats_text.setToolTip("切面数据的统计信息：最小值、最大值、均值、标准差等")
        info_layout.addWidget(self.stats_text)

        info_layout.addStretch()
        splitter.addWidget(info_group)
        splitter.setSizes([700, 280])

        parent_layout.addWidget(splitter)

    # ------------------------------------------------------------------
    # 底部栏：计算摘要 + 导出按钮组
    # ------------------------------------------------------------------
    def _build_bottom_bar(self, parent_layout):
        bottom_layout = QHBoxLayout()

        # 计算摘要
        summary_group = QGroupBox("计算摘要")
        summary_layout = QHBoxLayout(summary_group)
        summary_layout.setContentsMargins(6, 4, 6, 4)

        self.summary_label = QLabel("就绪 - 请选择参数并点击计算")
        self.summary_label.setStyleSheet("color: #a0b0c0; font-size: 11px;")
        self.summary_label.setToolTip("显示当前函数、切面方向和取值范围等摘要信息")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        bottom_layout.addWidget(summary_group, stretch=3)

        # 导出按钮组
        export_group = QGroupBox("导出切面数据")
        export_layout = QHBoxLayout(export_group)
        export_layout.setContentsMargins(6, 4, 6, 4)

        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="realspace_slice"
        )
        self.export_widget.setToolTip("将切面网格数据导出为 TXT / CSV / Excel 格式（无数据时弹出提示）")
        export_layout.addWidget(self.export_widget)
        bottom_layout.addWidget(export_group, stretch=2)

        parent_layout.addLayout(bottom_layout)

    # ====================================================================
    # 函数选择与说明更新
    # ====================================================================
    def _on_func_changed(self):
        """函数选择变化时，更新说明标签和推荐颜色映射"""
        self._update_desc()
        self._update_recommended_cmap()

    def _update_desc(self):
        """更新函数说明标签"""
        func_key = self._get_current_func_key()
        info = REALSPACE_INFO.get(func_key)
        if info:
            label = info["label"]
            short = info["short"]
            desc = info["desc"]
            self.desc_label.setText(
                f"<b>{label}</b>  [{short}]<br>{desc}"
            )
        else:
            self.desc_label.setText("")

    def _update_recommended_cmap(self):
        """根据当前函数自动推荐颜色映射"""
        func_key = self._get_current_func_key()
        recommended = RECOMMENDED_CMAPS.get(func_key, "viridis")
        idx = self.cmap_combo.findText(recommended)
        if idx >= 0:
            self.cmap_combo.setCurrentIndex(idx)

    def _get_current_func_key(self) -> str:
        """获取当前下拉框选项对应的 InputGenerator 键名"""
        display_name = self.func_combo.currentText()
        return FUNC_DISPLAY_TO_KEY.get(display_name, "Electron density")

    def _get_grid_key(self) -> str:
        """获取当前网格质量对应的 InputGenerator 键名"""
        display_name = self.grid_combo.currentText()
        return GRID_DISPLAY_TO_KEY.get(display_name, "Medium")

    # ====================================================================
    # 计算入口
    # ====================================================================
    def set_input_file(self, file_path):
        """外部设置当前输入文件路径"""
        self.current_file = file_path

    def on_calculate(self):
        """点击"计算并绘制"按钮后触发"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        func_key = self._get_current_func_key()
        grid_quality = self._get_grid_key()

        # 尝试生成命令序列，验证函数是否被 InputGenerator 支持
        try:
            commands = InputGenerator.generate_realspace_cube_commands(func_key, grid_quality)
        except ValueError as e:
            QMessageBox.critical(
                self, "错误",
                f"函数 '{func_key}' 尚未在 InputGenerator 中注册命令映射。\n{e}"
            )
            return

        work_dir = os.path.dirname(self.current_file)

        # 保存本次计算参数
        self._last_func_key = func_key
        self._last_grid = grid_quality

        # 更新界面状态
        self.calculate_btn.setEnabled(False)
        self.calculate_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 忙碌状态滚动条
        func_info = REALSPACE_INFO.get(func_key, {})
        func_label = func_info.get("label", func_key)
        self.summary_label.setText(f"正在计算 {func_label} ...")

        # 启动后台计算线程
        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"实空间分析: {func_label}"
        )
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    # ====================================================================
    # 计算完成回调
    # ====================================================================
    def _on_finished(self, result):
        """计算成功完成后的回调"""
        try:
            cube_file = result.get("cube_file")
            work_dir = os.path.dirname(self.current_file)

            # 若结果中未直接提供cube文件路径，在工作目录中查找
            if not cube_file:
                for f in os.listdir(work_dir):
                    if f.endswith(".cub"):
                        cube_file = os.path.join(work_dir, f)
                        break

            if cube_file and os.path.exists(cube_file):
                self._process_cube(cube_file)
            else:
                QMessageBox.warning(
                    self, "警告",
                    "未生成cube文件\n请检查函数类型是否受当前输入文件支持"
                )
                self.summary_label.setText("计算完成，但未生成可视化数据")
        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
        finally:
            self._reset_calculation_ui()

    def _process_cube(self, cube_file):
        """解析cube文件并绘制热图、更新信息面板"""
        parser = CubeParser(cube_file)
        dims = parser.get_dimensions()
        plane = self.plane_combo.currentText()
        slice_offset = self.slice_spin.value()

        # 根据偏移量计算切片索引
        slice_idx = self._calc_slice_index(parser, plane, slice_offset)
        slice_data = parser.get_plane_slice(plane, slice_idx)

        # 保存计算结果供导出使用
        self._last_slice_data = slice_data
        self._last_parser = parser
        self._last_plane = plane
        self._last_slice_idx = slice_idx

        # 绘制热图
        self.plot_heatmap(slice_data, parser, plane, slice_idx)

        # 更新信息面板
        self._update_info_panel(parser, dims, slice_data, plane)

        # 更新计算摘要
        func_info = REALSPACE_INFO.get(self._last_func_key, {})
        func_label = func_info.get("label", self._last_func_key)
        self.summary_label.setText(
            f"{func_label} | {plane.upper()} 切面 | "
            f"偏移 {slice_offset:.3f} Bohr | "
            f"范围: {slice_data.min():.6f} ~ {slice_data.max():.6f}"
        )

        # 计算完毕后删除临时cube文件
        try:
            os.remove(cube_file)
        except Exception:
            pass

    def _calc_slice_index(self, parser, plane, offset_bohr):
        """根据偏移量计算切面在cube网格中的索引"""
        dims = parser.get_dimensions()
        origin = parser.origin
        axes = parser.axes

        if plane == "xy":
            # z方向
            n = dims[2]
            step = abs(axes[2][2]) if abs(axes[2][2]) > 1e-10 else 1.0
            center = origin[2] + axes[2][2] * (n - 1) / 2.0
            target = center + offset_bohr
            idx = int(round((target - origin[2]) / step))
        elif plane == "xz":
            # y方向
            n = dims[1]
            step = abs(axes[1][1]) if abs(axes[1][1]) > 1e-10 else 1.0
            center = origin[1] + axes[1][1] * (n - 1) / 2.0
            target = center + offset_bohr
            idx = int(round((target - origin[1]) / step))
        elif plane == "yz":
            # x方向
            n = dims[0]
            step = abs(axes[0][0]) if abs(axes[0][0]) > 1e-10 else 1.0
            center = origin[0] + axes[0][0] * (n - 1) / 2.0
            target = center + offset_bohr
            idx = int(round((target - origin[0]) / step))
        else:
            idx = 0

        # 限制在合法范围内
        max_idx = dims[2] if plane == "xy" else dims[1] if plane == "xz" else dims[0]
        return max(0, min(idx, max_idx - 1))

    def _update_info_panel(self, parser, dims, slice_data, plane):
        """更新右侧信息面板"""
        # 基本信息
        self.info_text.setText(
            f"网格尺寸: {dims[0]} × {dims[1]} × {dims[2]}\n"
            f"原子数: {len(parser.atoms)}\n"
            f"切面: {plane.upper()} 平面"
        )

        # 原子投影表
        axis1_label = plane[0].upper()
        axis2_label = plane[1].upper()
        self.table.setHorizontalHeaderLabels(["原子", f"{axis1_label} (Bohr)", f"{axis2_label} (Bohr)"])
        atom_positions = parser.get_atom_positions(plane)
        self.table.setRowCount(len(atom_positions))
        for i, (ax, ay, element) in enumerate(atom_positions):
            self.table.setItem(i, 0, QTableWidgetItem(f"{element}{i+1}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{ax:.3f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{ay:.3f}"))

        # 取值统计
        self.stats_text.setText(
            f"最小值: {slice_data.min():.6f}\n"
            f"最大值: {slice_data.max():.6f}\n"
            f"均值: {slice_data.mean():.6f}\n"
            f"标准差: {slice_data.std():.6f}\n"
            f"5%分位: {np.percentile(slice_data, 5):.6f}\n"
            f"95%分位: {np.percentile(slice_data, 95):.6f}"
        )

    def _on_failed(self, error_msg):
        """计算失败回调"""
        QMessageBox.critical(self, "计算失败", error_msg[:500])
        self.summary_label.setText("计算失败")
        self._reset_calculation_ui()

    def _reset_calculation_ui(self):
        """重置计算相关UI状态"""
        self.calculate_btn.setEnabled(True)
        self.calculate_btn.setText("⚡ 计算并绘制")
        self.progress_bar.setVisible(False)
        self._worker = None

    # ====================================================================
    # 热图绘制
    # ====================================================================
    def plot_heatmap(self, data, parser, plane, slice_idx):
        """绘制2D切面热图"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)

        # 深色主题适配
        self.fig.patch.set_facecolor('#161d27')
        self.ax.set_facecolor('#1e2630')

        # 获取坐标轴范围
        x_coords = parser.get_coordinates(plane[0])
        y_coords = parser.get_coordinates(plane[1])

        # 自动确定颜色范围：使用5%-95%分位数避免极值影响
        vmin = np.percentile(data, 5)
        vmax = np.percentile(data, 95)
        if vmin == vmax:
            vmin = data.min()
            vmax = data.max()

        # 获取颜色映射
        cmap_name = self.cmap_combo.currentText()

        # 绘制热图
        im = self.ax.imshow(
            data.T,
            extent=[x_coords[0], x_coords[-1], y_coords[0], y_coords[-1]],
            origin='lower',
            cmap=cmap_name,
            aspect='auto',
            vmin=vmin,
            vmax=vmax,
            interpolation='bilinear',
        )

        # 添加 colorbar
        func_info = REALSPACE_INFO.get(self._last_func_key, {})
        colorbar_label = func_info.get("short", self._last_func_key or "Value")
        cbar = self.fig.colorbar(im, ax=self.ax, shrink=0.85, pad=0.02)
        cbar.set_label(colorbar_label, color='#c8d6e5', fontsize=10)
        cbar.ax.yaxis.set_tick_params(color='#c8d6e5')
        for label in cbar.ax.yaxis.get_ticklabels():
            label.set_color('#c8d6e5')

        # 标记原子位置
        atom_positions = parser.get_atom_positions(plane)
        for x, y, element in atom_positions:
            # 绘制原子圆点
            self.ax.scatter(
                x, y, c='white', s=40, zorder=5,
                edgecolors='black', linewidths=0.8
            )
            # 标注元素符号
            self.ax.text(
                x, y, element,
                ha='center', va='center',
                color='black', fontsize=7, fontweight='bold', zorder=6
            )

        # 设置坐标轴标签和标题
        axis1 = plane[0].upper()
        axis2 = plane[1].upper()
        func_label = func_info.get("label", self._last_func_key or "")
        self.ax.set_xlabel(f"{axis1} (Bohr)", color='#c8d6e5', fontsize=10)
        self.ax.set_ylabel(f"{axis2} (Bohr)", color='#c8d6e5', fontsize=10)
        self.ax.set_title(
            f"{func_label} — {axis1}{axis2} 切面",
            color='#e2e8f0', fontsize=13, fontweight='bold', pad=10
        )

        # 坐标轴刻度颜色适配深色主题
        self.ax.tick_params(colors='#a0b0c0', labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color('#3a4a5a')

        self.fig.tight_layout()
        self.canvas.draw()

    def _draw_placeholder(self):
        """绘制初始占位图"""
        self.ax = self.fig.add_subplot(111)
        self.fig.patch.set_facecolor('#161d27')
        self.ax.set_facecolor('#1e2630')
        self.ax.text(
            0.5, 0.5, "请选择参数并点击计算",
            ha="center", va="center", transform=self.ax.transAxes,
            fontsize=14, color="#5a7a9a"
        )
        self.ax.tick_params(colors='#3a4a5a')
        for spine in self.ax.spines.values():
            spine.set_color('#2a3a4a')
        self.canvas.draw()

    # ====================================================================
    # 导出数据
    # ====================================================================
    def _get_export_data(self):
        """为导出组件提供数据，返回 (records, headers, metadata) 或 None"""
        if self._last_slice_data is None or self._last_parser is None:
            return None

        data = self._last_slice_data
        plane = self._last_plane
        x_coords = self._last_parser.get_coordinates(plane[0])
        y_coords = self._last_parser.get_coordinates(plane[1])

        axis1 = f"{plane[0].upper()}(Bohr)"
        axis2 = f"{plane[1].upper()}(Bohr)"

        records = []
        for i, x in enumerate(x_coords):
            for j, y in enumerate(y_coords):
                records.append({
                    axis1: x,
                    axis2: y,
                    "value": data[j, i],
                })

        func_info = REALSPACE_INFO.get(self._last_func_key, {})
        metadata = {
            "函数类型": func_info.get("label", self._last_func_key or ""),
            "函数简称": func_info.get("short", ""),
            "切面方向": plane.upper(),
            "切片偏移(Bohr)": self.slice_spin.value(),
            "网格尺寸": "×".join(str(d) for d in self._last_parser.get_dimensions()),
            "网格质量": self._last_grid or self._get_grid_key(),
            "数据最小值": f"{data.min():.6f}",
            "数据最大值": f"{data.max():.6f}",
            "数据均值": f"{data.mean():.6f}",
        }
        headers = [axis1, axis2, "value"]
        return records, headers, metadata
