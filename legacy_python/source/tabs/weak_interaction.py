#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
弱相互作用分析Tab - 完整重写版

支持 Multiwfn 主菜单20下的所有弱相互作用分析类型：
NCI / IGM / mIGM / IGMH / DORI / aRDG / Hirshfeld surface

每种方法均可选择输出散点图或导出cube文件（Hirshfeld surface除外）。
IGM / IGMH 需要额外指定片段原子定义。

深色主题适配：图表背景使用 #161d27。
"""

import os
import re
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox, QSplitter, QProgressBar,
    QRadioButton, QButtonGroup, QDoubleSpinBox, QSpinBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QTextEdit, QLineEdit
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.pyplot as plt

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.export_utils import ExportButtonWidget


# ============================================================================
# 分析类型定义 — 包含详细中文说明
# ============================================================================

ANALYSIS_TYPES = {
    "NCI": {
        "label": "NCI（约化密度梯度）",
        "tooltip": (
            "NCI (Noncovalent Interaction) 约化密度梯度分析\n\n"
            "原理：通过约化密度梯度(RDG)与 sign(λ₂)ρ 的关系识别弱相互作用。\n"
            "• sign(λ₂)ρ < 0：吸引作用（氢键、卤键等）\n"
            "• sign(λ₂)ρ ≈ 0：范德华作用\n"
            "• sign(λ₂)ρ > 0：排斥作用（位阻效应等）\n\n"
            "输出：散点图可直观区分不同类型弱相互作用区域；\n"
            "      cube文件可在VMD/PyMOL中绘制sign(λ₂)ρ着色的RDG等值面。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 1"
        ),
        "multiwfn_submenu": "1",
        "needs_fragment": False,    # 是否需要片段定义
        "has_scatter": True,        # 是否支持散点图输出
        "has_cube": True,           # 是否支持cube导出
        "scatter_file": "NCI_data.txt",
    },
    "IGM": {
        "label": "IGM（独立梯度模型）",
        "tooltip": (
            "IGM (Independent Gradient Model) 独立梯度模型分析\n\n"
            "原理：将电子密度梯度分解为原子贡献的独立梯度(δg)，\n"
            "从而区分分子内与分子间弱相互作用。\n"
            "δg_inter 衡量分子间相互作用强度，δg_intra 衡量分子内相互作用。\n\n"
            "需要定义片段：指定一个片段的原子范围，\n"
            "未归入该片段的原子自动构成另一个片段。\n"
            "片段定义格式如 1-10,15-20\n\n"
            "输出：散点图展示 δg vs ρ 或 δg_inter vs ρ；\n"
            "      cube文件可在VMD中绘制 δg/δg_inter 等值面。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 2"
        ),
        "multiwfn_submenu": "2",
        "needs_fragment": True,
        "has_scatter": True,
        "has_cube": True,
        "scatter_file": "IGM_data.txt",
    },
    "mIGM": {
        "label": "mIGM（改进独立梯度模型）",
        "tooltip": (
            "mIGM (modified Independent Gradient Model) 改进独立梯度模型\n\n"
            "原理：IGM的改进版本，对强相互作用区域（如氢键、共轭体系）\n"
            "更加敏感，能更好地反映电子密度的真实梯度特征。\n"
            "相比IGM，mIGM在处理强相互作用时结果更准确。\n\n"
            "不需要片段定义：mIGM自动区分分子内/分子间相互作用。\n\n"
            "输出：散点图展示改进的梯度指标 vs 电子密度；\n"
            "      cube文件可在VMD中绘制等值面。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 3"
        ),
        "multiwfn_submenu": "3",
        "needs_fragment": False,
        "has_scatter": True,
        "has_cube": True,
        "scatter_file": "mIGM_data.txt",
    },
    "IGMH": {
        "label": "IGMH（基于Hirshfeld划分的IGM）",
        "tooltip": (
            "IGMH (IGM based on Hirshfeld partition) 基于Hirshfeld划分的IGM\n\n"
            "原理：使用Hirshfeld原子权重替代自由原子密度来分解梯度，\n"
            "相比原始IGM，物理意义更明确，计算效率更高，适用于大体系。\n"
            "IGMH是目前推荐使用的IGM变体。\n\n"
            "需要定义片段：与IGM相同，需指定片段原子范围。\n"
            "片段定义格式如 1-10,15-20\n\n"
            "输出：散点图展示 δg^Hirsh vs ρ 或 δg_inter^Hirsh vs ρ；\n"
            "      cube文件可在VMD中绘制等值面。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 4"
        ),
        "multiwfn_submenu": "4",
        "needs_fragment": True,
        "has_scatter": True,
        "has_cube": True,
        "scatter_file": "IGMH_data.txt",
    },
    "DORI": {
        "label": "DORI（密度重叠区域指示器）",
        "tooltip": (
            "DORI (Density Overlap Regions Indicator) 密度重叠区域指示器\n\n"
            "原理：通过电子密度重叠程度识别化学键和弱相互作用区域，\n"
            "与NCI互补。NCI擅长非共价作用，DORI则可同时识别\n"
            "共价键区域和非共价作用边界。\n\n"
            "DORI值接近0表示电子密度重叠显著（共价键区域），\n"
            "DORI值接近1表示电子密度重叠微弱（非共价区域）。\n\n"
            "输出：散点图展示 DORI vs ρ；\n"
            "      cube文件可在VMD中绘制DORI等值面。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 5"
        ),
        "multiwfn_submenu": "5",
        "needs_fragment": False,
        "has_scatter": True,
        "has_cube": True,
        "scatter_file": "DORI_data.txt",
    },
    "aRDG": {
        "label": "aRDG（平均约化密度梯度）",
        "tooltip": (
            "aRDG (average Reduced Density Gradient) 平均约化密度梯度\n\n"
            "原理：NCI的周期性体系扩展版本，适用于晶体、表面等\n"
            "具有平移对称性的体系。aRDG对周期性边界条件下的\n"
            "弱相互作用进行可视化和分析。\n\n"
            "需要周期性输入文件（如cif格式）。\n\n"
            "输出：散点图展示平均RDG vs sign(λ₂)ρ；\n"
            "      cube文件可在VMD中绘制等值面。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 6"
        ),
        "multiwfn_submenu": "6",
        "needs_fragment": False,
        "has_scatter": True,
        "has_cube": True,
        "scatter_file": "aRDG_data.txt",
    },
    "Hirshfeld surface": {
        "label": "Hirshfeld surface（Hirshfeld表面分析）",
        "tooltip": (
            "Hirshfeld surface 分子表面分析\n\n"
            "原理：根据Hirshfeld权重定义的分子表面，\n"
            "用于研究分子间接触特征和晶体堆积效应。\n"
            "Hirshfeld表面上的d_i（到表面内部原子距离）和\n"
            "d_e（到表面外部原子距离）可生成2D指纹图(fingerprint plot)，\n"
            "用于定量分析不同分子间接触类型（H…H、H…O等）的贡献。\n\n"
            "输出：Hirshfeld表面相关文件，可用第三方软件可视化。\n"
            "      本方法不支持散点图输出，仅生成表面数据。\n\n"
            "对应Multiwfn菜单：主菜单 20 → 7"
        ),
        "multiwfn_submenu": "7",
        "needs_fragment": False,
        "has_scatter": False,   # Hirshfeld surface 不支持散点图
        "has_cube": False,      # 也不导出传统cube
        "scatter_file": None,
    },
}

# 可能包含散点数据的输出文件名候选列表
DATA_FILE_CANDIDATES = [
    "NCI_data.txt", "IGM_data.txt", "mIGM_data.txt",
    "IGMH_data.txt", "DORI_data.txt", "aRDG_data.txt",
    "RDG_data.txt", "output.txt", "dos_data.txt",
]

# 深色主题颜色常量
DARK_BG = "#161d27"
DARK_FG = "#e0e0e0"
DARK_GRID = "#2a3444"
DARK_ACCENT = "#9b59b6"


class WeakInteractionTab(QWidget):
    """
    弱相互作用可视化分析模块 — 完整重写版

    功能：
    - 支持 NCI / IGM / mIGM / IGMH / DORI / aRDG / Hirshfeld surface 七种方法
    - 输出模式可选散点图或cube文件导出
    - IGM/IGMH 支持片段原子定义
    - NCI显示参数可调（RDG上限、sign范围、点大小）
    - 等值面值设置（用于cube导出时）
    - 深色主题 matplotlib 图表
    - 结果导出（TXT/CSV/Excel）
    """

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_data = []          # 最近解析的散点数据
        self._last_output = ""        # 最近Multiwfn原始输出
        self._last_cube_files = []    # 最近生成的cube文件列表
        self._last_info = {}          # 最近分析的类型信息
        self.init_ui()

    # ====================================================================
    # UI 构建
    # ====================================================================

    def init_ui(self):
        """构建完整界面"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        # --- 第一行：分析类型 + 输出模式 + 网格质量 ---
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(12)

        # 分析类型选择
        type_group = QGroupBox("分析类型")
        type_layout = QHBoxLayout(type_group)
        self.type_combo = QComboBox()
        type_keys = list(ANALYSIS_TYPES.keys())
        type_labels = [ANALYSIS_TYPES[k]["label"] for k in type_keys]
        self.type_combo.addItems(type_labels)
        # 存储key列表，方便通过索引取回
        self._type_keys = type_keys
        self.type_combo.setToolTip(
            "选择弱相互作用分析方法：\n\n"
            "• NCI：约化密度梯度，识别氢键/范德华/位阻\n"
            "• IGM：独立梯度模型，需指定片段，区分分子内/间作用\n"
            "• mIGM：改进IGM，对强作用更敏感\n"
            "• IGMH：Hirshfeld划分IGM，效率高，推荐使用\n"
            "• DORI：密度重叠指示器，与NCI互补\n"
            "• aRDG：周期性体系NCI扩展\n"
            "• Hirshfeld surface：分子表面与指纹图分析"
        )
        self.type_combo.currentIndexChanged.connect(self._on_type_changed)
        type_label = QLabel("方法:")
        type_label.setToolTip("弱相互作用分析类型")
        type_layout.addWidget(type_label)
        type_layout.addWidget(self.type_combo)
        row1_layout.addWidget(type_group)

        # 输出模式选择
        mode_group = QGroupBox("输出模式")
        mode_layout = QHBoxLayout(mode_group)
        self.mode_btn_group = QButtonGroup(self)
        self.radio_scatter = QRadioButton("散点图")
        self.radio_scatter.setToolTip(
            "生成散点图（如 RDG vs sign(λ₂)ρ），\n"
            "在左侧图表区绘制，右侧表格显示数据点。\n"
            "适用于NCI/IGM/mIGM/IGMH/DORI/aRDG。"
        )
        self.radio_cube = QRadioButton("导出cube文件")
        self.radio_cube.setToolTip(
            "导出cube格式的三维格点文件，\n"
            "可在VMD、PyMOL、Chimera等软件中绘制等值面图。\n"
            "适用于NCI/IGM/mIGM/IGMH/DORI/aRDG。"
        )
        self.radio_scatter.setChecked(True)
        self.mode_btn_group.addButton(self.radio_scatter, 0)
        self.mode_btn_group.addButton(self.radio_cube, 1)
        mode_layout.addWidget(self.radio_scatter)
        mode_layout.addWidget(self.radio_cube)
        row1_layout.addWidget(mode_group)

        # 网格质量控制
        grid_group = QGroupBox("网格质量")
        grid_layout = QHBoxLayout(grid_group)
        self.grid_combo = QComboBox()
        self.grid_combo.addItems(["粗糙（快）", "中等", "精细（慢）", "超精细（很慢）"])
        self.grid_combo.setCurrentIndex(1)
        self.grid_combo.setToolTip(
            "计算网格的密度级别：\n\n"
            "• 粗糙：格点少，计算快，结果粗糙，适合初步测试\n"
            "• 中等：平衡速度与精度，适合大多数分析（推荐）\n"
            "• 精细：格点多，结果平滑，计算较慢\n"
            "• 超精细：格点极多，结果最佳，计算耗时很长\n\n"
            "等值面分析建议至少中等网格；散点图对网格要求相对较低。\n"
            "对应Multiwfn网格选项：1=粗糙 2=中等 3=精细 4=超精细"
        )
        grid_label = QLabel("网格:")
        grid_label.setToolTip("Multiwfn网格质量选项")
        grid_layout.addWidget(grid_label)
        grid_layout.addWidget(self.grid_combo)
        row1_layout.addWidget(grid_group)

        # 计算按钮 + 进度条
        self.calculate_btn = QPushButton("⚡ 计算弱相互作用")
        self.calculate_btn.setStyleSheet(
            f"background-color: {DARK_ACCENT}; color: white; font-weight: bold; "
            "padding: 6px 16px; border-radius: 4px;"
        )
        self.calculate_btn.setToolTip(
            "执行当前选择的弱相互作用分析：\n\n"
            "• 散点图模式：在左侧绘制图表，右侧表格显示数据点\n"
            "• cube导出模式：在工作目录生成cube文件，可供VMD等可视化\n"
            "• Hirshfeld surface：生成分子表面相关文件\n\n"
            "计算过程中按钮会变为禁用状态，请耐心等待。"
        )
        self.calculate_btn.clicked.connect(self.on_calculate)
        row1_layout.addWidget(self.calculate_btn)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(180)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("计算进度（Multiwfn无精确进度，仅显示进行中）")
        row1_layout.addWidget(self.progress_bar)

        row1_layout.addStretch()
        main_layout.addLayout(row1_layout)

        # --- 第二行：片段定义 + NCI显示参数 + 等值面值 ---
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(12)

        # 片段原子定义（仅IGM/IGMH时有效显示）
        fragment_group = QGroupBox("片段原子定义")
        fragment_layout = QHBoxLayout(fragment_group)
        self.fragment_edit = QLineEdit()
        self.fragment_edit.setPlaceholderText("例如: 1-10 或 1-5,11-15 或 1,3,5,7-10")
        self.fragment_edit.setToolTip(
            "指定一个片段的原子索引，用于IGM/IGMH区分分子内/分子间相互作用。\n\n"
            "支持的格式：\n"
            "  • 连续范围：1-10\n"
            "  • 多个范围/原子：1-5,11-15 或 1,3,5,7\n"
            "  • 混合格式：1-5,8,12-15\n\n"
            "未归入该片段的原子自动构成另一个片段。\n"
            "留空时Multiwfn将每个原子视为独立片段，结果可能不符合预期。\n\n"
            "⚠ 仅 IGM 和 IGMH 分析需要此输入，其他方法可忽略。"
        )
        fragment_label = QLabel("片段:")
        fragment_label.setToolTip("IGM/IGMH分析所需的片段原子索引")
        fragment_layout.addWidget(fragment_label)
        fragment_layout.addWidget(self.fragment_edit)
        self.fragment_group_widget = fragment_group
        row2_layout.addWidget(fragment_group)

        # NCI显示参数
        nci_group = QGroupBox("NCI显示参数")
        nci_layout = QHBoxLayout(nci_group)

        self.rdg_max_spin = QDoubleSpinBox()
        self.rdg_max_spin.setRange(0.1, 5.0)
        self.rdg_max_spin.setValue(0.8)
        self.rdg_max_spin.setSingleStep(0.1)
        self.rdg_max_spin.setDecimals(2)
        self.rdg_max_spin.setToolTip(
            "RDG（约化密度梯度）显示上限。\n\n"
            "散点图中超过此值的RDG数据点不显示。\n"
            "建议范围 0.3~1.0，默认0.8。\n"
            "值越小只保留低RDG（弱相互作用核心区域），\n"
            "值越大则包含更多外围数据点。"
        )
        rdg_label = QLabel("RDG上限:")
        rdg_label.setToolTip("约化密度梯度(RDG)纵轴显示上限")
        nci_layout.addWidget(rdg_label)
        nci_layout.addWidget(self.rdg_max_spin)

        self.sign_min_spin = QDoubleSpinBox()
        self.sign_min_spin.setRange(-1.0, 0.0)
        self.sign_min_spin.setValue(-0.15)
        self.sign_min_spin.setSingleStep(0.01)
        self.sign_min_spin.setDecimals(3)
        self.sign_min_spin.setToolTip(
            "sign(λ₂)ρ 横轴显示下限。\n\n"
            "负值区域对应吸引作用（氢键、卤键等）。\n"
            "默认 -0.15，范围建议 -0.5~0。\n"
            "缩小范围可聚焦特定相互作用区域。"
        )
        sign_min_label = QLabel("sign下限:")
        sign_min_label.setToolTip("sign(λ₂)ρ横轴下限")
        nci_layout.addWidget(sign_min_label)
        nci_layout.addWidget(self.sign_min_spin)

        self.sign_max_spin = QDoubleSpinBox()
        self.sign_max_spin.setRange(0.0, 1.0)
        self.sign_max_spin.setValue(0.15)
        self.sign_max_spin.setSingleStep(0.01)
        self.sign_max_spin.setDecimals(3)
        self.sign_max_spin.setToolTip(
            "sign(λ₂)ρ 横轴显示上限。\n\n"
            "正值区域对应排斥作用（位阻效应等）。\n"
            "默认 0.15，范围建议 0~0.5。"
        )
        sign_max_label = QLabel("sign上限:")
        sign_max_label.setToolTip("sign(λ₂)ρ横轴上限")
        nci_layout.addWidget(sign_max_label)
        nci_layout.addWidget(self.sign_max_spin)

        self.point_size_spin = QSpinBox()
        self.point_size_spin.setRange(1, 50)
        self.point_size_spin.setValue(8)
        self.point_size_spin.setToolTip(
            "散点图中每个数据点的像素大小。\n\n"
            "数据点密集时可调小（如2~4），稀疏时调大（如10~15）。\n"
            "默认8。"
        )
        point_size_label = QLabel("点大小:")
        point_size_label.setToolTip("散点大小（像素）")
        nci_layout.addWidget(point_size_label)
        nci_layout.addWidget(self.point_size_spin)

        row2_layout.addWidget(nci_group)

        # 等值面值设置
        isovalue_group = QGroupBox("等值面值")
        isovalue_layout = QHBoxLayout(isovalue_group)
        self.isovalue_spin = QDoubleSpinBox()
        self.isovalue_spin.setRange(0.001, 10.0)
        self.isovalue_spin.setValue(0.5)
        self.isovalue_spin.setSingleStep(0.05)
        self.isovalue_spin.setDecimals(3)
        self.isovalue_spin.setToolTip(
            "cube导出时用于等值面绘制的等值面值(isovalue)。\n\n"
            "• NCI RDG等值面：常用 0.5\n"
            "• IGM δg等值面：常用 0.01~0.05\n"
            "• DORI等值面：常用 0.5~0.8\n\n"
            "此值影响VMD/PyMOL中等值面的显示范围，\n"
            "值越大等值面越小（仅显示强作用区域），\n"
            "值越小等值面越大（包含更多弱作用区域）。"
        )
        isovalue_label = QLabel("isovalue:")
        isovalue_label.setToolTip("等值面值（用于cube可视化）")
        isovalue_layout.addWidget(isovalue_label)
        isovalue_layout.addWidget(self.isovalue_spin)
        row2_layout.addWidget(isovalue_group)

        row2_layout.addStretch()
        main_layout.addLayout(row2_layout)

        # --- 说明标签 ---
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet("color: #94a3b8; font-size: 12px; padding: 4px 8px;")
        self.desc_label.setToolTip("当前分析类型的功能说明及对应Multiwfn菜单路径")
        main_layout.addWidget(self.desc_label)

        # --- 结果展示区：左右分栏 ---
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：matplotlib图表
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor=DARK_BG)
        self.canvas = FigureCanvas(self.fig)
        self.ax = self.fig.add_subplot(111)
        self._setup_dark_axes(self.ax)
        self.ax.text(
            0.5, 0.5, "请选择分析类型并点击计算",
            ha="center", va="center", transform=self.ax.transAxes,
            fontsize=13, color=DARK_FG
        )
        self.canvas.setToolTip(
            "弱相互作用散点图显示区域\n\n"
            "• 散点图模式：绘制 RDG/DORI/δg vs sign(λ₂)ρ/ρ 散点图\n"
            "• cube导出模式：显示计算摘要和生成的cube文件列表\n"
            "• 颜色编码：红色=吸引作用，蓝色=排斥作用，黄色=范德华作用"
        )
        self.canvas.draw()
        splitter.addWidget(self.canvas)

        # 右侧：数据表格 + 输出 + 导出
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # 数据表格
        table_group = QGroupBox("散点数据")
        table_layout = QVBoxLayout(table_group)
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ρ", "RDG/δg", "sign(λ₂)ρ", "作用类型"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setToolTip(
            "NCI/IGM/mIGM/IGMH/DORI/aRDG 散点图的数据点表格\n\n"
            "• ρ：电子密度\n"
            "• RDG/δg：约化密度梯度或独立梯度值\n"
            "• sign(λ₂)ρ：电子密度乘以λ₂符号\n"
            "• 作用类型：根据sign(λ₂)ρ值自动分类\n\n"
            "可导出为 TXT/CSV/Excel 格式"
        )
        table_layout.addWidget(self.table)

        # 导出按钮组
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="weak_interaction"
        )
        self.export_widget.setToolTip("将当前结果导出为 TXT/CSV/Excel 格式")
        table_layout.addWidget(self.export_widget)
        right_layout.addWidget(table_group)

        # 计算输出文本
        output_group = QGroupBox("计算输出")
        output_layout = QVBoxLayout(output_group)
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(160)
        self.output_text.setPlaceholderText("Multiwfn原始输出将显示在此处...")
        self.output_text.setToolTip(
            "Multiwfn命令行原始输出文本\n\n"
            "可用于诊断计算过程、确认参数设置、排查错误等。"
        )
        output_layout.addWidget(self.output_text)
        right_layout.addWidget(output_group)

        splitter.addWidget(right_widget)
        splitter.setSizes([700, 300])

        main_layout.addWidget(splitter)

        # --- 摘要区 ---
        summary_group = QGroupBox("计算摘要")
        summary_layout = QHBoxLayout(summary_group)
        self.summary_label = QLabel("就绪 — 请选择分析类型并点击计算")
        self.summary_label.setStyleSheet("font-size: 12px; color: #b0bec5;")
        self.summary_label.setToolTip(
            "最近一次计算的状态摘要\n\n"
            "显示：分析类型、计算状态、数据点数、生成的cube文件数等"
        )
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        main_layout.addWidget(summary_group)

        self.setLayout(main_layout)

        # 初始化控件可见性
        self._on_type_changed(self.type_combo.currentIndex())

    # ====================================================================
    # 控件状态更新
    # ====================================================================

    def _on_type_changed(self, index):
        """分析类型改变时更新说明、控件可见性"""
        if index < 0 or index >= len(self._type_keys):
            return

        key = self._type_keys[index]
        info = ANALYSIS_TYPES[key]

        # 更新说明标签
        desc = info["tooltip"].split("\n\n")[0]  # 取第一段作为简短说明
        text = f"<b>{info['label']}</b> — {desc}<br>"
        text += f"<span style='color:#1890ff;'>对应Multiwfn菜单：主菜单 20 → {info['multiwfn_submenu']}</span>"
        self.desc_label.setText(text)

        # 更新片段定义组的可见性
        self.fragment_group_widget.setVisible(info["needs_fragment"])

        # 更新输出模式控件状态
        if not info["has_scatter"] and not info["has_cube"]:
            # Hirshfeld surface：两种模式都不可用
            self.radio_scatter.setEnabled(False)
            self.radio_cube.setEnabled(False)
        elif not info["has_scatter"]:
            self.radio_scatter.setEnabled(False)
            self.radio_cube.setEnabled(True)
            self.radio_cube.setChecked(True)
        elif not info["has_cube"]:
            self.radio_scatter.setEnabled(True)
            self.radio_cube.setEnabled(False)
            self.radio_scatter.setChecked(True)
        else:
            self.radio_scatter.setEnabled(True)
            self.radio_cube.setEnabled(True)
            # 默认选择散点图
            if not self.radio_cube.isChecked():
                self.radio_scatter.setChecked(True)

    def _setup_dark_axes(self, ax):
        """配置matplotlib坐标轴的深色主题样式"""
        ax.set_facecolor(DARK_BG)
        ax.tick_params(colors=DARK_FG, which='both')
        ax.xaxis.label.set_color(DARK_FG)
        ax.yaxis.label.set_color(DARK_FG)
        ax.title.set_color(DARK_FG)
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)

    # ====================================================================
    # 辅助方法
    # ====================================================================

    def _get_current_type_key(self):
        """获取当前选择的分析类型key"""
        idx = self.type_combo.currentIndex()
        if 0 <= idx < len(self._type_keys):
            return self._type_keys[idx]
        return "NCI"

    def _get_grid_quality_text(self):
        """获取当前网格质量对应的中文文本"""
        return self.grid_combo.currentText()

    def _get_grid_num(self):
        """将网格质量中文描述转换为Multiwfn数字"""
        grid_map = {
            "粗糙（快）": 1, "中等": 2, "精细（慢）": 3, "超精细（很慢）": 4
        }
        return grid_map.get(self.grid_combo.currentText(), 2)

    def _is_scatter_mode(self):
        """当前是否为散点图输出模式"""
        return self.radio_scatter.isChecked() and self.radio_scatter.isEnabled()

    def _is_cube_mode(self):
        """当前是否为cube导出模式"""
        return self.radio_cube.isChecked() and self.radio_cube.isEnabled()

    def _validate_fragment_atoms(self, fragment_text):
        """
        验证片段原子输入格式

        返回: (是否有效, 错误信息, 格式化后的字符串)
        """
        text = fragment_text.strip()
        if not text:
            return True, "", ""

        parts = [p.strip() for p in text.split(",") if p.strip()]
        if not parts:
            return True, "", ""

        formatted_parts = []
        for part in parts:
            if "-" in part:
                rng = part.split("-")
                if len(rng) != 2:
                    return False, f"片段范围格式错误: '{part}'", ""
                try:
                    start = int(rng[0])
                    end = int(rng[1])
                except ValueError:
                    return False, f"片段范围必须为整数: '{part}'", ""
                if start <= 0 or end <= 0:
                    return False, f"原子索引必须为正整数: '{part}'", ""
                if start > end:
                    return False, f"范围起始不能大于结束: '{part}'", ""
                formatted_parts.append(f"{start}-{end}")
            else:
                try:
                    idx = int(part)
                except ValueError:
                    return False, f"原子索引必须为整数: '{part}'", ""
                if idx <= 0:
                    return False, f"原子索引必须为正整数: '{part}'", ""
                formatted_parts.append(str(idx))

        return True, "", ",".join(formatted_parts)

    # ====================================================================
    # 命令生成
    # ====================================================================

    def _generate_commands(self):
        """
        根据当前设置生成Multiwfn命令序列

        使用 InputGenerator.generate_weak_interaction_commands()
        分析类型名根据当前选择和输出模式动态确定
        """
        type_key = self._get_current_type_key()
        grid_quality = self._get_grid_quality_text()
        fragment_text = self.fragment_edit.text()
        _, _, fragment_str = self._validate_fragment_atoms(fragment_text)
        fragment_atoms = fragment_str if fragment_str else None

        # 根据输出模式确定分析类型名（映射到InputGenerator的WEAK_INTERACTION_TYPES）
        if type_key == "Hirshfeld surface":
            analysis_type = "Hirshfeld surface"
        elif self._is_cube_mode():
            analysis_type = f"{type_key}等值面"
        else:
            analysis_type = f"{type_key}散点图"

        commands = InputGenerator.generate_weak_interaction_commands(
            analysis_type, grid_quality=grid_quality, fragment_atoms=fragment_atoms
        )
        return commands, analysis_type

    # ====================================================================
    # 计算入口
    # ====================================================================

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path

    def on_calculate(self):
        """点击计算按钮的入口"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        type_key = self._get_current_type_key()
        info = ANALYSIS_TYPES[type_key]

        # 验证片段输入
        fragment_text = self.fragment_edit.text()
        valid, err_msg, _ = self._validate_fragment_atoms(fragment_text)
        if not valid:
            QMessageBox.warning(self, "片段输入错误", err_msg)
            return

        # IGM/IGMH 需要片段定义，未填写时给出提示但允许继续
        if info["needs_fragment"] and not fragment_text.strip():
            reply = QMessageBox.question(
                self, "片段未指定",
                f"{info['label']} 需要指定片段原子范围。\n\n"
                "未指定片段时Multiwfn可能将每个原子视为独立片段，\n"
                "结果可能不符合预期。\n\n"
                "是否仍要继续计算？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # 生成命令
        try:
            commands, analysis_type = self._generate_commands()
        except ValueError as e:
            QMessageBox.warning(self, "命令生成错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        # 更新UI状态
        self.calculate_btn.setEnabled(False)
        self.calculate_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度模式
        self.summary_label.setText(f"正在计算 {info['label']}...")

        # 启动计算工作线程
        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"弱相互作用分析: {analysis_type}"
        )
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _reset_ui_state(self):
        """恢复计算按钮和进度条状态"""
        self.calculate_btn.setEnabled(True)
        self.calculate_btn.setText("⚡ 计算弱相互作用")
        self.progress_bar.setVisible(False)
        self._worker = None

    # ====================================================================
    # 计算完成回调
    # ====================================================================

    def _on_finished(self, result):
        """计算成功完成"""
        try:
            output = result.get("output", "")
            self._last_output = output
            self.output_text.setPlainText(output[:10000])

            work_dir = os.path.dirname(self.current_file)
            type_key = self._get_current_type_key()
            info = ANALYSIS_TYPES[type_key]

            self._last_info = info
            self._last_cube_files = self._find_cube_files(work_dir)

            is_scatter = self._is_scatter_mode()
            is_hirshfeld = (type_key == "Hirshfeld surface")

            if is_scatter and info.get("has_scatter"):
                # 散点图模式：解析数据并绘制
                data = self._parse_scatter_data(work_dir, output, type_key)
                self._last_data = data
                self._plot_scatter(data, info)
                self._update_table(data)
                n_points = len(data)
                n_cubes = len(self._last_cube_files)
                cube_msg = f" | cube文件: {n_cubes}个" if n_cubes > 0 else ""
                self.summary_label.setText(
                    f"✅ {info['label']} 散点图 | 数据点: {n_points}{cube_msg}"
                )
            else:
                # cube导出模式或Hirshfeld surface：显示摘要
                self._last_data = []
                self.table.setRowCount(0)

                cube_lines = ""
                n_cubes = len(self._last_cube_files)
                if self._last_cube_files:
                    cube_lines = "\n".join(
                        f"  • {os.path.basename(f)}" for f in self._last_cube_files
                    )

                if is_hirshfeld:
                    placeholder = f"{info['label']} 计算完成\n\n请查看工作目录输出文件"
                    self.summary_label.setText(
                        f"✅ {info['label']} | 计算完成"
                    )
                else:
                    placeholder = f"{info['label']} cube导出完成"
                    if cube_lines:
                        placeholder += f"\n\n生成的cube文件({n_cubes}个):\n{cube_lines}"
                    else:
                        placeholder += "\n\n请查看工作目录中的.cube/.cub文件"
                    self.summary_label.setText(
                        f"✅ {info['label']} cube导出 | 生成文件: {n_cubes}个"
                    )

                self._plot_placeholder(placeholder)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
        finally:
            self._reset_ui_state()

    def _on_failed(self, error_msg):
        """计算失败"""
        self.summary_label.setText(f"❌ 计算失败")
        QMessageBox.critical(self, "计算失败", error_msg[:1000])
        self._reset_ui_state()

    # ====================================================================
    # 数据解析
    # ====================================================================

    def _find_cube_files(self, work_dir):
        """在工作目录中查找最近生成的cube文件"""
        cubes = []
        try:
            for f in os.listdir(work_dir):
                if f.lower().endswith(".cub") or f.lower().endswith(".cube"):
                    cubes.append(os.path.join(work_dir, f))
            # 按修改时间降序排列
            cubes.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        except Exception:
            pass
        return cubes

    def _parse_scatter_data(self, work_dir, output, type_key):
        """
        解析散点数据

        依次尝试：1) 常见输出文件  2) 从Multiwfn原始输出文本解析
        """
        # 先尝试从文件解析
        for filename in DATA_FILE_CANDIDATES:
            filepath = os.path.join(work_dir, filename)
            if os.path.exists(filepath):
                data = self._parse_data_file(filepath)
                if data:
                    # 解析成功后删除临时文件，避免影响下次计算
                    try:
                        os.remove(filepath)
                    except Exception:
                        pass
                    return data

        # 从原始输出文本解析
        return self._parse_data_from_output(output)

    def _parse_data_file(self, filepath):
        """从单个文本文件解析散点数据"""
        data = []
        try:
            arr = np.loadtxt(filepath, comments='#')
            if arr.ndim == 1:
                arr = arr.reshape(1, -1)

            n_cols = arr.shape[1] if arr.ndim == 2 else 0

            if n_cols >= 5:
                # 标准5列格式: rho, RDG/δg, ?, sign(λ₂)ρ, ...
                for row in arr:
                    rho = float(row[0])
                    rdg = float(row[1])
                    sign_val = float(row[3])
                    data.append({
                        "rho": rho,
                        "rdg": rdg,
                        "sign_lambda2_rho": sign_val,
                        "interaction": self._classify_interaction(sign_val),
                    })
            elif n_cols == 4:
                # 4列格式: rho, RDG/δg, ?, sign(λ₂)ρ
                for row in arr:
                    rho = float(row[0])
                    rdg = float(row[1])
                    sign_val = float(row[3])
                    data.append({
                        "rho": rho,
                        "rdg": rdg,
                        "sign_lambda2_rho": sign_val,
                        "interaction": self._classify_interaction(sign_val),
                    })
            elif n_cols == 3:
                # 3列格式: rho, RDG/δg, sign(λ₂)ρ
                for row in arr:
                    rho = float(row[0])
                    rdg = float(row[1])
                    sign_val = float(row[2])
                    data.append({
                        "rho": rho,
                        "rdg": rdg,
                        "sign_lambda2_rho": sign_val,
                        "interaction": self._classify_interaction(sign_val),
                    })
            elif n_cols == 2:
                # 2列格式: rho, RDG/δg (无sign信息)
                for row in arr:
                    rho = float(row[0])
                    rdg = float(row[1])
                    data.append({
                        "rho": rho,
                        "rdg": rdg,
                        "sign_lambda2_rho": 0.0,
                        "interaction": "未知",
                    })
        except Exception:
            pass
        return data

    def _parse_data_from_output(self, output):
        """从Multiwfn原始输出文本中解析散点数据行"""
        data = []
        # 匹配5列或更多数值行
        pattern = re.compile(
            r"^\s*([-\d.Ee]+)\s+([-\d.Ee]+)\s+([-\d.Ee]+)\s+([-\d.Ee]+)\s+([-\d.Ee]+)"
        )
        for line in output.split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            match = pattern.match(line)
            if match:
                try:
                    rho = float(match.group(1))
                    rdg = float(match.group(2))
                    sign_val = float(match.group(4))
                    # 基本合理性过滤
                    if -2.0 < sign_val < 2.0 and 0 < rdg < 100:
                        data.append({
                            "rho": rho,
                            "rdg": rdg,
                            "sign_lambda2_rho": sign_val,
                            "interaction": self._classify_interaction(sign_val),
                        })
                except ValueError:
                    continue
        return data

    def _classify_interaction(self, sign_val):
        """根据 sign(λ₂)ρ 值分类相互作用类型"""
        if sign_val < -0.02:
            return "吸引作用"
        elif sign_val > 0.02:
            return "排斥作用"
        else:
            return "范德华作用"

    # ====================================================================
    # 图表绘制
    # ====================================================================

    def _plot_scatter(self, data, info):
        """绘制弱相互作用散点图（深色主题）"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self._setup_dark_axes(self.ax)

        if not data:
            self.ax.text(
                0.5, 0.5, "未解析到弱相互作用数据\n请检查输出文件",
                ha="center", va="center", transform=self.ax.transAxes,
                fontsize=13, color=DARK_FG
            )
            self.canvas.draw()
            return

        # 获取显示参数
        rdg_max = self.rdg_max_spin.value()
        sign_min = self.sign_min_spin.value()
        sign_max = self.sign_max_spin.value()
        point_size = self.point_size_spin.value()

        # 提取数据
        rho_vals = np.array([d["rho"] for d in data])
        rdg_vals = np.array([d["rdg"] for d in data])
        sign_vals = np.array([d["sign_lambda2_rho"] for d in data])

        # 过滤：仅保留在显示范围内的数据
        mask = (
            (rdg_vals > 0)
            & (rdg_vals < rdg_max)
            & (sign_vals > sign_min)
            & (sign_vals < sign_max)
        )
        sign_filtered = sign_vals[mask]
        rdg_filtered = rdg_vals[mask]

        if len(sign_filtered) == 0:
            self.ax.text(
                0.5, 0.5,
                "当前参数下无数据显示\n请调整 RDG/sign 范围",
                ha="center", va="center", transform=self.ax.transAxes,
                fontsize=13, color=DARK_FG
            )
            self.canvas.draw()
            return

        # 按 sign(λ₂)ρ 连续着色：红（吸引）→ 黄（范德华）→ 蓝（排斥）
        cmap = LinearSegmentedColormap.from_list(
            "nci_cmap", ["#e74c3c", "#f1c40f", "#3498db"]
        )
        norm = Normalize(vmin=sign_min, vmax=sign_max)
        colors = cmap(norm(sign_filtered))

        # 绘制散点
        self.ax.scatter(
            sign_filtered, rdg_filtered,
            c=colors, s=point_size, alpha=0.6, edgecolors="none"
        )

        # 坐标轴标签和标题
        self.ax.set_xlabel("sign(λ₂)ρ", fontsize=12, color=DARK_FG)
        self.ax.set_ylabel("RDG", fontsize=12, color=DARK_FG)
        self.ax.set_title(f"{info['label']} 散点图", fontsize=14, color=DARK_FG)
        self.ax.set_xlim(sign_min, sign_max)
        self.ax.set_ylim(0, rdg_max)

        # 参考线
        self.ax.axhline(y=0.5, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)
        self.ax.axvline(x=0, color="gray", linestyle="--", linewidth=0.5, alpha=0.5)

        # 图例
        legend_handles = [
            plt.Line2D([0], [0], marker='o', color='#e74c3c',
                       label='吸引作用（氢键等）', linestyle='', markersize=8),
            plt.Line2D([0], [0], marker='o', color='#3498db',
                       label='排斥作用（位阻等）', linestyle='', markersize=8),
            plt.Line2D([0], [0], marker='o', color='#f1c40f',
                       label='范德华作用', linestyle='', markersize=8),
        ]
        legend = self.ax.legend(
            handles=legend_handles, loc='upper right', fontsize=10,
            facecolor=DARK_BG, edgecolor=DARK_GRID, labelcolor=DARK_FG
        )

        # 网格
        self.ax.grid(True, alpha=0.3, color=DARK_GRID)

        self.fig.tight_layout()
        self.canvas.draw()

    def _plot_placeholder(self, text):
        """在图表区显示占位文本（深色主题）"""
        self.fig.clear()
        self.ax = self.fig.add_subplot(111)
        self._setup_dark_axes(self.ax)
        self.ax.text(
            0.5, 0.5, text,
            ha="center", va="center", transform=self.ax.transAxes,
            fontsize=12, color=DARK_FG, linespacing=1.6
        )
        self.fig.tight_layout()
        self.canvas.draw()

    # ====================================================================
    # 数据表格更新
    # ====================================================================

    def _update_table(self, data):
        """更新右侧数据表格"""
        self.table.setRowCount(0)
        if not data:
            return

        # 数据量过大时抽样显示，避免表格卡顿
        max_display = 500
        if len(data) > max_display:
            step = max(1, len(data) // max_display)
            display_data = data[::step]
        else:
            display_data = data

        self.table.setRowCount(len(display_data))
        for i, d in enumerate(display_data):
            self.table.setItem(i, 0, QTableWidgetItem(f"{d['rho']:.6f}"))
            self.table.setItem(i, 1, QTableWidgetItem(f"{d['rdg']:.6f}"))
            self.table.setItem(i, 2, QTableWidgetItem(f"{d['sign_lambda2_rho']:.6f}"))
            self.table.setItem(i, 3, QTableWidgetItem(d["interaction"]))

    # ====================================================================
    # 导出数据
    # ====================================================================

    def _get_export_data(self):
        """
        为ExportButtonWidget提供导出数据

        返回: (records, headers, metadata) 或 None
        """
        if not self._last_data:
            # 无散点数据时尝试导出原始输出
            if self._last_output:
                return (
                    [{"output": self._last_output}],
                    ["output"],
                    {"分析类型": self._get_current_type_key()}
                )
            return None

        # 导出散点数据
        records = []
        for d in self._last_data:
            records.append({
                "rho": d["rho"],
                "rdg": d["rdg"],
                "sign_lambda2_rho": d["sign_lambda2_rho"],
                "interaction_type": d["interaction"],
            })

        metadata = {
            "分析类型": self._last_info.get("label", ""),
            "网格质量": self.grid_combo.currentText(),
            "RDG上限": self.rdg_max_spin.value(),
            "sign范围": f"[{self.sign_min_spin.value()}, {self.sign_max_spin.value()}]",
            "等值面值": self.isovalue_spin.value(),
        }
        if self._last_cube_files:
            metadata["cube文件"] = "; ".join(
                os.path.basename(f) for f in self._last_cube_files
            )

        return (
            records,
            ["rho", "rdg", "sign_lambda2_rho", "interaction_type"],
            metadata
        )
