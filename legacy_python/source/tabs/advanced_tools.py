#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
高级工具模块 — 对应 Multiwfn 主菜单 2 / 14 / 16 / 17 / 18 / 19 / 22 / 23 / 24 / 25 / 100

支持功能：
  - AIM 拓扑分析（菜单 2）
  - 芳香性分析（菜单 25）
  - 电子激发分析（菜单 18）
  - 概念 DFT（菜单 22）
  - ETS-NOCV 分析（菜单 23）
  - CDA 电荷分解（菜单 16）
  - 盆分析（菜单 17）
  - 极化率分析（菜单 24）
  - 轨道定域化（菜单 19）
  - AdNDP 分析（菜单 14）
  - 文件格式转换（菜单 100）

布局：左侧功能分类树 + 右侧参数/结果区 + 底部进度条与状态
深色主题适配，使用 CalculationWorker / InputGenerator / OutputParser / ExportButtonWidget
"""

import os
import glob
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTreeWidget, QTreeWidgetItem,
    QPushButton, QGroupBox, QProgressBar, QMessageBox, QTextEdit,
    QComboBox, QSpinBox, QLineEdit, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView
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
# 功能定义 — 树形分类 + 详细中文 tooltip
# ============================================================================
# 每个功能定义包含: key, label, tooltip, category, parameters(参数需求)
# category: 用于在树形控件中分组

ADVANCED_FUNCTIONS = {
    # ---- AIM 分析 ----
    "aim_topology": {
        "label": "AIM拓扑分析（菜单2）",
        "category": "AIM分析",
        "tooltip": (
            "AIM（Atoms in Molecules）拓扑分析\n\n"
            "功能：基于 Bader 的量子原子拓扑理论，搜索电子密度的临界点(CP)，\n"
            "包括核临界点(3,-3)、键临界点(3,-1)、环临界点(3,+1)和笼临界点(3,+3)。\n\n"
            "输出：\n"
            "  • 临界点坐标与类型\n"
            "  • 临界点处的电子密度、拉普拉斯值、能量密度等\n"
            "  • 分子图（键径连接）\n\n"
            "用途：\n"
            "  • 确认化学键的存在与强度\n"
            "  • 分析分子中的电子密度拓扑特征\n"
            "  • 为 AIM 原子电荷计算提供基础\n\n"
            "对应 Multiwfn 路径：主菜单 2"
        ),
        "parameters": [],  # 无额外参数
    },

    # ---- 芳香性 ----
    "aromaticity": {
        "label": "芳香性分析（菜单25）",
        "category": "芳香性",
        "tooltip": (
            "芳香性分析\n\n"
            "功能：计算多种芳香性指标，评估环状体系的芳香性/反芳香性。\n\n"
            "支持指标：\n"
            "  • NICS（核独立化学位移）：在环中心/上方计算磁屏蔽值，\n"
            "    负值表示芳香性，正值表示反芳香性\n"
            "  • FLU（芳香性涨落指标）：基于电子定域化函数(ELF)的涨落分析\n"
            "  • HOMA（芳香性调和 oscillator 指标）：基于键长均匀性\n"
            "  • MCI（多中心指数）：基于电子相关\n\n"
            "需选择分析方法并指定环序号（适用于 NICS 等）。\n\n"
            "对应 Multiwfn 路径：主菜单 25"
        ),
        "parameters": ["arom_method", "ring_index"],
    },

    # ---- 电子激发 ----
    "excitation": {
        "label": "电子激发分析（菜单18）",
        "category": "电子激发",
        "tooltip": (
            "电子激发态分析\n\n"
            "功能：对 TD-DFT / CIS 等激发态计算结果进行深入分析。\n\n"
            "支持方法：\n"
            "  • 空穴-电子分析：分解激发态为空穴(电子离开)和电子(电子到达)分布，\n"
            "    计算 Sm/Δr/Dt 等指数评估激发特征\n"
            "  • 电荷转移分析：定量计算激发态的电荷转移距离与转移量\n"
            "  • 自然跃迁轨道(NTO)：将跃迁密度对角化，\n"
            "    得到最主要的空穴-电子轨道对，简化激发态描述\n\n"
            "需选择分析方法并指定激发态序号。\n"
            "注意：需要含有激发态信息的输入文件。\n\n"
            "对应 Multiwfn 路径：主菜单 18"
        ),
        "parameters": ["exc_method", "excited_state"],
    },

    # ---- 概念 DFT ----
    "concept_dft": {
        "label": "概念DFT（菜单22）",
        "category": "概念DFT",
        "tooltip": (
            "概念密度泛函理论(Conceptual DFT)分析\n\n"
            "功能：计算概念 DFT 定义的各种反应性指标，\n"
            "用于预测分子的化学反应活性和位点选择性。\n\n"
            "主要指标：\n"
            "  • Fukui 函数 f⁺/f⁻/f⁰：分别预测亲核/亲电/自由基攻击位点\n"
            "  • 双描述符(dual descriptor) Δf：f⁺ - f⁻，正区域利于亲核攻击\n"
            "  • 局部软度(local softness)：全局软度的局部分布\n"
            "  • 局部亲电/亲核指数：评估各原子的亲电/亲核性\n"
            "  • 全局指标：化学势μ、化学硬度η、软度S、亲电指数ω\n\n"
            "注意：需要中性、阳离子、阴离子三个态的波函数文件。\n\n"
            "对应 Multiwfn 路径：主菜单 22"
        ),
        "parameters": ["dft_index"],
    },

    # ---- ETS-NOCV ----
    "ets_nocv": {
        "label": "ETS-NOCV分析（菜单23）",
        "category": "其他分析",
        "tooltip": (
            "ETS-NOCV（扩展过渡态-自然轨道化学价）分析\n\n"
            "功能：将片段间的相互作用能分解为不同对称性/方向的贡献，\n"
            "同时将电荷变形密度分解为成对的自然轨道化学价(NOCV)分量。\n\n"
            "原理：\n"
            "  • ETS（扩展过渡态）：将相互作用能分解为静电、Pauli 排斥、\n"
            "    轨道混合等分量\n"
            "  • NOCV：将变形密度分解为主要通道，每个通道对应特定的\n"
            "    给体-受体相互作用（如 σ-供与、π-反馈等）\n\n"
            "用途：\n"
            "  • 量化金属-配体键中的 σ/π/δ 贡献\n"
            "  • 分析分子间相互作用的本质\n"
            "  • 可视化各 NOCV 通道的变形密度\n\n"
            "需定义两个片段的原子范围。\n\n"
            "对应 Multiwfn 路径：主菜单 23"
        ),
        "parameters": ["fragment1", "fragment2"],
    },

    # ---- CDA ----
    "cda": {
        "label": "CDA电荷分解（菜单16）",
        "category": "其他分析",
        "tooltip": (
            "CDA（Charge Decomposition Analysis）电荷分解分析\n\n"
            "功能：将配合物中片段间的电荷转移分解为：\n"
            "  • d（给体→受体混合）：配体向金属的电子供给\n"
            "  • b（受体→给体反馈）：金属向配体的电子反馈\n"
            "  • r（极化残留项）：片段内的极化效应\n\n"
            "d > b 表示净供给，d < b 表示净反馈。\n\n"
            "用途：\n"
            "  • 分析配合物的给体-受体性质\n"
            "  • 比较不同配体的供给/反馈能力\n"
            "  • 量化 Dewar-Chatt-Duncanson 模型\n\n"
            "需准备三个波函数文件：配合物、片段1、片段2。\n\n"
            "对应 Multiwfn 路径：主菜单 16"
        ),
        "parameters": ["frag1_file", "frag2_file"],
    },

    # ---- 盆分析 ----
    "basin_analysis": {
        "label": "盆分析（菜单17）",
        "category": "其他分析",
        "tooltip": (
            "盆分析(Basin Analysis)\n\n"
            "功能：在实空间中划分原子盆(AIM)或定域化盆(ELF/LOL)，\n"
            "并在各盆内积分电子数、动能、能量等物理量。\n\n"
            "支持划分方式：\n"
            "  • AIM 盆：基于 Bader 零通量面划分（对应原子）\n"
            "  • ELF 盆：基于电子定域化函数等值面划分\n"
            "  • LOL 盆：基于定域轨道定位函数等值面划分\n\n"
            "输出：\n"
            "  • 各盆内的电子数（可推算 AIM 原子电荷）\n"
            "  • 盆体积和空间范围\n"
            "  • 积分精度信息\n\n"
            "对应 Multiwfn 路径：主菜单 17"
        ),
        "parameters": ["basin_type"],
    },

    # ---- 极化率 ----
    "polarizability": {
        "label": "极化率分析（菜单24）",
        "category": "其他分析",
        "tooltip": (
            "极化率与超极化率分析\n\n"
            "功能：计算分子的(超)极化率张量及相关指标。\n\n"
            "主要输出：\n"
            "  • 各向同性极化率 α_iso\n"
            "  • 各向异性极化率 Δα\n"
            "  • 第一超极化率 β（倍频效应）\n"
            "  • 第二超极化率 γ（Kerr 效应等）\n"
            "  • 极化率椭球参数\n\n"
            "用途：\n"
            "  • 评估分子的非线性光学(NLO)性质\n"
            "  • 预测折射率、介电常数等宏观性质\n"
            "  • 筛选 NLO 材料\n\n"
            "注意：需要波函数文件包含偶极矩和极化率信息（如Gaussian的polar计算）。\n\n"
            "对应 Multiwfn 路径：主菜单 24"
        ),
        "parameters": [],
    },

    # ---- 轨道定域化 ----
    "orbital_localization": {
        "label": "轨道定域化（菜单19）",
        "category": "其他分析",
        "tooltip": (
            "轨道定域化分析\n\n"
            "功能：将正则分子轨道(CMO)转换为定域化分子轨道(LMO)，\n"
            "使轨道在空间上更加定域化，更符合化学键的直觉图像。\n\n"
            "支持方法：\n"
            "  • Foster-Boys (FB)：最小化轨道空间展幅，\n"
            "    适合 σ/π 键和孤对电子的定域化\n"
            "  • Pipek-Mezey (PM)：最大化 Mulliken 布居对角性，\n"
            "    适合保留 σ/π 分离的定域化\n\n"
            "用途：\n"
            "  • 获得直观的化学键轨道\n"
            "  • 分析轨道间相互作用\n"
            "  • 为局部相关方法提供输入\n\n"
            "对应 Multiwfn 路径：主菜单 19"
        ),
        "parameters": ["loc_method"],
    },

    # ---- AdNDP ----
    "adndp": {
        "label": "AdNDP分析（菜单14）",
        "category": "其他分析",
        "tooltip": (
            "AdNDP（自适应自然密度划分）分析\n\n"
            "功能：将多中心键按电子对数逐步搜索，\n"
            "从2c-2e（双中心双电子键）到nc-2e（n中心双电子键），\n"
            "找到占据数最高的自然轨道。\n\n"
            "原理：\n"
            "  AdNDP 是 NBO 方法的推广，不仅搜索1c-2e（孤对电子）\n"
            "  和 2c-2e（双中心键），还搜索多中心键（如3c-2e、4c-2e等），\n"
            "  对硼烷、金属团簇等含多中心键体系特别有效。\n\n"
            "输出：\n"
            "  • 各级自然轨道的占据数和轨道形状\n"
            "  • 多中心键的识别与可视化\n\n"
            "对应 Multiwfn 路径：主菜单 14"
        ),
        "parameters": [],
    },

    # ---- 文件导出 ----
    "file_export": {
        "label": "文件格式转换（菜单100）",
        "category": "文件导出",
        "tooltip": (
            "文件格式转换与导出\n\n"
            "功能：将当前波函数文件转换为其他格式，\n"
            "便于在不同软件之间交换数据。\n\n"
            "支持格式：\n"
            "  • wfn：Gaussian 波函数文件，适用于部分后处理程序\n"
            "  • wfx：Gaussian 扩展波函数格式\n"
            "  • molden：Molden 可视化格式，包含轨道信息\n"
            "  • xyz：仅原子坐标，格式简单通用\n"
            "  • pdb：蛋白质数据库格式，常用于分子可视化\n"
            "  • mol：MDL MOL 文件，包含连接表信息\n"
            "  • gjf：Gaussian 输入文件，可直接用于提交计算\n"
            "  • mwfn：Multiwfn 原生波函数格式，保留最完整信息\n\n"
            "对应 Multiwfn 路径：主菜单 100 → 2"
        ),
        "parameters": ["export_format"],
    },
}

# 树形分类的顺序
CATEGORY_ORDER = ["AIM分析", "芳香性", "电子激发", "概念DFT", "其他分析", "文件导出"]

# 芳香性分析方法
AROM_METHODS = {
    "NICS": "1",
    "NICS-scan": "1",
    "FLU": "2",
    "HOMA": "3",
    "MCI": "4",
    "ACID": "5",
    "ELF-pi": "6",
}

AROM_METHOD_TOOLTIPS = {
    "NICS": "核独立化学位移：在环中心计算磁屏蔽值，负值=芳香性",
    "NICS-scan": "沿垂直环平面直线扫描NICS值，分析芳香性空间分布",
    "FLU": "芳香性涨落指标：基于ELF计算，衡量电子离域均匀性",
    "HOMA": "芳香性调和指标：基于键长均匀性，几何方法评估芳香性",
    "MCI": "多中心指数：基于电子相关的芳香性指标",
    "ACID": "各向同性电流密度分析：通过感应电流判断芳香/反芳香性",
    "ELF-pi": "基于π电子ELF分析：判断π芳香性",
}

# 电子激发分析方法
EXC_METHODS = {
    "空穴-电子分析": "1",
    "电荷转移分析": "3",
    "自然跃迁轨道(NTO)": "4",
}

EXC_METHOD_TOOLTIPS = {
    "空穴-电子分析": "分解激发态为空穴和电子分布，计算Sm/Δr/Dt等指数",
    "电荷转移分析": "定量计算激发态中的电荷转移距离与转移量",
    "自然跃迁轨道(NTO)": "将跃迁密度对角化，得到主要空穴-电子轨道对",
}

# 盆分析类型
BASIN_TYPES = {
    "AIM盆积分": "1",
    "ELF盆积分": "2",
    "LOL盆积分": "3",
}

BASIN_TYPE_TOOLTIPS = {
    "AIM盆积分": "基于Bader零通量面划分原子盆并积分电子数",
    "ELF盆积分": "基于电子定域化函数等值面划分定域化盆",
    "LOL盆积分": "基于定域轨道定位函数等值面划分定域化盆",
}

# 轨道定域化方法
LOC_METHODS = {
    "Foster-Boys": "1",
    "Pipek-Mezey": "2",
}

LOC_METHOD_TOOLTIPS = {
    "Foster-Boys": "最小化轨道空间展幅，适合σ/π键和孤对电子定域化",
    "Pipek-Mezey": "最大化Mulliken布居对角性，保留σ/π分离",
}


class AdvancedToolsTab(QWidget):
    """高级工具标签页，对应 Multiwfn 多个主菜单。"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_output = ""
        self._last_table_data = []
        self._current_func_key = ""
        self._init_ui()

    # ====================================================================
    # 界面构建
    # ====================================================================

    def _init_ui(self):
        """构建完整界面：左侧功能分类树 + 右侧参数/结果区 + 底部状态"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # 左右分栏
        splitter = QSplitter(Qt.Horizontal)

        # ---- 左侧：功能分类树 ----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        tree_group = QGroupBox("高级工具")
        tree_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        tree_inner = QVBoxLayout(tree_group)

        self.func_tree = QTreeWidget()
        self.func_tree.setHeaderHidden(True)
        self.func_tree.setStyleSheet(
            "QTreeWidget { background-color: #1e2630; color: #e2e8f0; "
            "border: 1px solid #334155; border-radius: 4px; }"
            "QTreeWidget::item { padding: 6px 4px; }"
            "QTreeWidget::item:selected { background-color: #e74c3c; color: white; }"
            "QTreeWidget::item:hover { background-color: #2a3f5f; }"
        )
        self.func_tree.setToolTip("选择要执行的高级分析功能")

        # 按分类构建树
        self._category_items = {}
        self._func_items = {}  # key -> QTreeWidgetItem

        for cat in CATEGORY_ORDER:
            cat_item = QTreeWidgetItem(self.func_tree, [cat])
            cat_item.setExpanded(True)
            cat_item.setToolTip(0, f"{cat}分类")
            # 分类项使用粗体
            font = cat_item.font(0)
            font.setBold(True)
            cat_item.setFont(0, font)
            self._category_items[cat] = cat_item

        for key, func_info in ADVANCED_FUNCTIONS.items():
            cat = func_info["category"]
            cat_item = self._category_items.get(cat)
            if cat_item is None:
                continue
            func_item = QTreeWidgetItem(cat_item, [func_info["label"]])
            func_item.setData(0, Qt.UserRole, key)
            func_item.setToolTip(0, func_info["tooltip"])
            self._func_items[key] = func_item

        self.func_tree.currentItemChanged.connect(self._on_tree_item_changed)
        tree_inner.addWidget(self.func_tree)

        # 功能说明标签
        self.func_desc_label = QLabel("请在左侧选择分析功能")
        self.func_desc_label.setWordWrap(True)
        self.func_desc_label.setStyleSheet(
            "color: #93c5fd; font-size: 11px; padding: 6px; "
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 4px;"
        )
        self.func_desc_label.setMinimumHeight(50)
        self.func_desc_label.setMaximumHeight(80)
        tree_inner.addWidget(self.func_desc_label)

        left_layout.addWidget(tree_group)
        splitter.addWidget(left_widget)

        # ---- 右侧：参数 + 结果 ----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        # 参数配置区
        self.param_group = QGroupBox("参数配置")
        self.param_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        self.param_layout = QVBoxLayout(self.param_group)

        # === 通用参数行（根据选择的功能动态显示） ===

        # 行1：芳香性方法 + 环序号
        arom_row = QHBoxLayout()
        arom_method_label = QLabel("分析方法:")
        arom_method_label.setStyleSheet("color: #cbd5e1;")
        arom_row.addWidget(arom_method_label)
        self.arom_method_combo = QComboBox()
        self.arom_method_combo.addItems(list(AROM_METHODS.keys()))
        self.arom_method_combo.setToolTip("选择芳香性分析方法")
        for i, method in enumerate(AROM_METHODS.keys()):
            self.arom_method_combo.setItemData(
                i, AROM_METHOD_TOOLTIPS.get(method, ""), Qt.ToolTipRole
            )
        arom_row.addWidget(self.arom_method_combo)
        ring_label = QLabel("环序号:")
        ring_label.setStyleSheet("color: #cbd5e1;")
        arom_row.addWidget(ring_label)
        self.ring_spin = QSpinBox()
        self.ring_spin.setRange(1, 99)
        self.ring_spin.setValue(1)
        self.ring_spin.setToolTip("要分析的环序号（适用于NICS等需要指定环的方法）")
        arom_row.addWidget(self.ring_spin)
        arom_row.addStretch()
        self._arom_row_widget = QWidget()
        self._arom_row_widget.setLayout(arom_row)
        self.param_layout.addWidget(self._arom_row_widget)

        # 行2：电子激发方法 + 激发态序号
        exc_row = QHBoxLayout()
        exc_method_label = QLabel("分析方法:")
        exc_method_label.setStyleSheet("color: #cbd5e1;")
        exc_row.addWidget(exc_method_label)
        self.exc_method_combo = QComboBox()
        self.exc_method_combo.addItems(list(EXC_METHODS.keys()))
        self.exc_method_combo.setToolTip("选择电子激发分析方法")
        for i, method in enumerate(EXC_METHODS.keys()):
            self.exc_method_combo.setItemData(
                i, EXC_METHOD_TOOLTIPS.get(method, ""), Qt.ToolTipRole
            )
        exc_row.addWidget(self.exc_method_combo)
        exc_state_label = QLabel("激发态序号:")
        exc_state_label.setStyleSheet("color: #cbd5e1;")
        exc_row.addWidget(exc_state_label)
        self.exc_state_spin = QSpinBox()
        self.exc_state_spin.setRange(1, 999)
        self.exc_state_spin.setValue(1)
        self.exc_state_spin.setToolTip("指定要分析的激发态序号（第1激发态输入1）")
        exc_row.addWidget(self.exc_state_spin)
        exc_row.addStretch()
        self._exc_row_widget = QWidget()
        self._exc_row_widget.setLayout(exc_row)
        self.param_layout.addWidget(self._exc_row_widget)

        # 行3：概念DFT指标
        dft_row = QHBoxLayout()
        dft_label = QLabel("反应性指标:")
        dft_label.setStyleSheet("color: #cbd5e1;")
        dft_row.addWidget(dft_label)
        self.dft_index_combo = QComboBox()
        self.dft_index_combo.addItems([
            "Fukui函数",
            "双描述符",
            "局部软度",
            "局部亲电指数",
            "全部指标",
        ])
        self.dft_index_combo.setToolTip(
            "Fukui函数: 预测亲核/亲电攻击位点\n"
            "双描述符: f⁺ - f⁻，正区域利于亲核攻击\n"
            "局部软度: 全局软度的局部分布\n"
            "局部亲电指数: 评估各原子亲电性\n"
            "全部指标: 输出所有概念DFT指标"
        )
        dft_row.addWidget(self.dft_index_combo)
        dft_row.addStretch()
        self._dft_row_widget = QWidget()
        self._dft_row_widget.setLayout(dft_row)
        self.param_layout.addWidget(self._dft_row_widget)

        # 行4：ETS-NOCV 片段定义
        ets_row = QHBoxLayout()
        frag1_label = QLabel("片段1原子:")
        frag1_label.setStyleSheet("color: #cbd5e1;")
        ets_row.addWidget(frag1_label)
        self.frag1_edit = QLineEdit()
        self.frag1_edit.setPlaceholderText("如: 1-5,8")
        self.frag1_edit.setToolTip("片段1的原子索引（如 1-5,8,12-15）")
        ets_row.addWidget(self.frag1_edit)
        frag2_label = QLabel("片段2原子:")
        frag2_label.setStyleSheet("color: #cbd5e1;")
        ets_row.addWidget(frag2_label)
        self.frag2_edit = QLineEdit()
        self.frag2_edit.setPlaceholderText("如: 6-7,9-10")
        self.frag2_edit.setToolTip("片段2的原子索引（如 6-7,9-10）")
        ets_row.addWidget(self.frag2_edit)
        ets_row.addStretch()
        self._ets_row_widget = QWidget()
        self._ets_row_widget.setLayout(ets_row)
        self.param_layout.addWidget(self._ets_row_widget)

        # 行5：CDA 片段文件
        cda_row = QHBoxLayout()
        cda_frag1_label = QLabel("片段1文件:")
        cda_frag1_label.setStyleSheet("color: #cbd5e1;")
        cda_row.addWidget(cda_frag1_label)
        self.cda_frag1_edit = QLineEdit()
        self.cda_frag1_edit.setPlaceholderText("片段1的波函数文件路径")
        self.cda_frag1_edit.setToolTip("片段1（如配体）的波函数文件路径")
        cda_row.addWidget(self.cda_frag1_edit)
        cda_frag2_label = QLabel("片段2文件:")
        cda_frag2_label.setStyleSheet("color: #cbd5e1;")
        cda_row.addWidget(cda_frag2_label)
        self.cda_frag2_edit = QLineEdit()
        self.cda_frag2_edit.setPlaceholderText("片段2的波函数文件路径")
        self.cda_frag2_edit.setToolTip("片段2（如金属片段）的波函数文件路径")
        cda_row.addWidget(self.cda_frag2_edit)
        cda_row.addStretch()
        self._cda_row_widget = QWidget()
        self._cda_row_widget.setLayout(cda_row)
        self.param_layout.addWidget(self._cda_row_widget)

        # 行6：盆分析类型
        basin_row = QHBoxLayout()
        basin_label = QLabel("盆类型:")
        basin_label.setStyleSheet("color: #cbd5e1;")
        basin_row.addWidget(basin_label)
        self.basin_type_combo = QComboBox()
        self.basin_type_combo.addItems(list(BASIN_TYPES.keys()))
        self.basin_type_combo.setToolTip("选择盆分析的类型")
        for i, btype in enumerate(BASIN_TYPES.keys()):
            self.basin_type_combo.setItemData(
                i, BASIN_TYPE_TOOLTIPS.get(btype, ""), Qt.ToolTipRole
            )
        basin_row.addWidget(self.basin_type_combo)
        basin_row.addStretch()
        self._basin_row_widget = QWidget()
        self._basin_row_widget.setLayout(basin_row)
        self.param_layout.addWidget(self._basin_row_widget)

        # 行7：轨道定域化方法
        loc_row = QHBoxLayout()
        loc_label = QLabel("定域化方法:")
        loc_label.setStyleSheet("color: #cbd5e1;")
        loc_row.addWidget(loc_label)
        self.loc_method_combo = QComboBox()
        self.loc_method_combo.addItems(list(LOC_METHODS.keys()))
        self.loc_method_combo.setToolTip("选择轨道定域化方法")
        for i, method in enumerate(LOC_METHODS.keys()):
            self.loc_method_combo.setItemData(
                i, LOC_METHOD_TOOLTIPS.get(method, ""), Qt.ToolTipRole
            )
        loc_row.addWidget(self.loc_method_combo)
        loc_row.addStretch()
        self._loc_row_widget = QWidget()
        self._loc_row_widget.setLayout(loc_row)
        self.param_layout.addWidget(self._loc_row_widget)

        # 行8：文件导出格式
        export_row = QHBoxLayout()
        export_label = QLabel("导出格式:")
        export_label.setStyleSheet("color: #cbd5e1;")
        export_row.addWidget(export_label)
        self.export_format_combo = QComboBox()
        self.export_format_combo.addItems(
            ["wfn", "wfx", "molden", "xyz", "pdb", "mol", "gjf", "mwfn"]
        )
        self.export_format_combo.setToolTip("选择要导出的文件格式")
        export_row.addWidget(self.export_format_combo)
        export_row.addStretch()
        self._export_row_widget = QWidget()
        self._export_row_widget.setLayout(export_row)
        self.param_layout.addWidget(self._export_row_widget)

        # 计算按钮
        btn_row = QHBoxLayout()
        self.calc_btn = QPushButton("开始计算")
        self.calc_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #c0392b; }"
            "QPushButton:disabled { background-color: #6b7280; }"
        )
        self.calc_btn.setToolTip("执行当前选择的高级分析功能")
        self.calc_btn.clicked.connect(self._on_calculate)
        btn_row.addWidget(self.calc_btn)
        btn_row.addStretch()
        self.param_layout.addLayout(btn_row)

        right_layout.addWidget(self.param_group)

        # 结果展示区：文本 + 表格
        result_group = QGroupBox("计算结果")
        result_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        result_layout = QVBoxLayout(result_group)

        # 结果文本
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMaximumHeight(200)
        self.output_text.setPlaceholderText("计算结果将显示在此处...")
        self.output_text.setStyleSheet(
            "QTextEdit { background-color: #1e2630; color: #e2e8f0; "
            "border: 1px solid #334155; border-radius: 4px; font-family: Consolas, monospace; }"
        )
        self.output_text.setToolTip("Multiwfn 高级工具计算的原始输出文本")
        result_layout.addWidget(self.output_text)

        # 数据表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(
            ["序号", "项目", "数值", "单位/说明"]
        )
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setStyleSheet(
            "QTableWidget { background-color: #1e2630; color: #e2e8f0; "
            "gridline-color: #334155; alternate-background-color: #243040; }"
            "QHeaderView::section { background-color: #334155; color: #e2e8f0; "
            "font-weight: bold; border: 1px solid #475569; padding: 4px; }"
        )
        self.result_table.setToolTip("高级分析的结构化数据结果，可导出为 TXT/CSV/Excel")
        result_layout.addWidget(self.result_table)

        # 导出按钮
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="advanced_analysis"
        )
        self.export_widget.setToolTip("将当前结果导出为 TXT/CSV/Excel 格式")
        result_layout.addWidget(self.export_widget)

        right_layout.addWidget(result_group, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setSizes([240, 760])

        main_layout.addWidget(splitter, stretch=1)

        # ---- 底部：进度条 + 状态标签 ----
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setFixedHeight(18)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("计算进度指示，滚动模式表示正在计算中")
        bottom_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("就绪 — 请选择功能并点击计算")
        self.status_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.status_label.setToolTip("当前分析状态")
        bottom_layout.addWidget(self.status_label, stretch=1)

        main_layout.addLayout(bottom_layout)

        self.setLayout(main_layout)

        # 初始隐藏所有参数行
        self._hide_all_param_rows()

        # 默认选中第一个功能
        first_cat = self.func_tree.topLevelItem(0)
        if first_cat and first_cat.childCount() > 0:
            self.func_tree.setCurrentItem(first_cat.child(0))

    # ====================================================================
    # 控件状态更新
    # ====================================================================

    def _hide_all_param_rows(self):
        """隐藏所有参数行"""
        self._arom_row_widget.setVisible(False)
        self._exc_row_widget.setVisible(False)
        self._dft_row_widget.setVisible(False)
        self._ets_row_widget.setVisible(False)
        self._cda_row_widget.setVisible(False)
        self._basin_row_widget.setVisible(False)
        self._loc_row_widget.setVisible(False)
        self._export_row_widget.setVisible(False)

    def _on_tree_item_changed(self, current, previous):
        """树形控件选择变化时更新右侧参数区和说明"""
        if current is None:
            return

        func_key = current.data(0, Qt.UserRole)
        if func_key is None:
            # 选中了分类项，不做处理
            return

        self._current_func_key = func_key
        func_info = ADVANCED_FUNCTIONS.get(func_key, {})

        # 更新说明标签
        tooltip = func_info.get("tooltip", "")
        first_para = tooltip.split("\n\n")[0] if tooltip else ""
        self.func_desc_label.setText(
            f"<b>{func_info.get('label', '')}</b><br>{first_para}"
        )

        # 根据功能需求显示/隐藏参数控件
        self._hide_all_param_rows()
        params = func_info.get("parameters", [])
        for p in params:
            if p == "arom_method" or p == "ring_index":
                self._arom_row_widget.setVisible(True)
            elif p == "exc_method" or p == "excited_state":
                self._exc_row_widget.setVisible(True)
            elif p == "dft_index":
                self._dft_row_widget.setVisible(True)
            elif p == "fragment1" or p == "fragment2":
                self._ets_row_widget.setVisible(True)
            elif p == "frag1_file" or p == "frag2_file":
                self._cda_row_widget.setVisible(True)
            elif p == "basin_type":
                self._basin_row_widget.setVisible(True)
            elif p == "loc_method":
                self._loc_row_widget.setVisible(True)
            elif p == "export_format":
                self._export_row_widget.setVisible(True)

    # ====================================================================
    # 命令生成
    # ====================================================================

    def _generate_commands(self):
        """根据当前选择的功能生成 Multiwfn 命令序列"""
        key = self._current_func_key

        if key == "aim_topology":
            # 菜单 2：AIM 拓扑分析
            return InputGenerator.generate_aim_commands()

        elif key == "aromaticity":
            # 菜单 25：芳香性分析
            method = self.arom_method_combo.currentText()
            ring_idx = self.ring_spin.value()
            return InputGenerator.generate_aromaticity_commands(method, ring_idx)

        elif key == "excitation":
            # 菜单 18：电子激发分析
            method = self.exc_method_combo.currentText()
            state_idx = self.exc_state_spin.value()
            # 根据方法生成命令
            method_lower = method.lower()
            if "空穴" in method or "hole" in method_lower:
                commands = ["18", "1", str(state_idx), "q"]
            elif "电荷转移" in method or "charge" in method_lower:
                commands = ["18", "3", str(state_idx), "q"]
            elif "nto" in method_lower or "自然" in method:
                commands = ["18", "4", str(state_idx), "q"]
            else:
                commands = ["18", "1", str(state_idx), "q"]
            return commands

        elif key == "concept_dft":
            # 菜单 22：概念 DFT
            index_text = self.dft_index_combo.currentText()
            index_map = {
                "Fukui函数": "1",
                "双描述符": "2",
                "局部软度": "3",
                "局部亲电指数": "4",
                "全部指标": "5",
            }
            sub_cmd = index_map.get(index_text, "5")
            return ["22", sub_cmd, "q"]

        elif key == "ets_nocv":
            # 菜单 23：ETS-NOCV
            frag1 = self.frag1_edit.text().strip()
            frag2 = self.frag2_edit.text().strip()
            if not frag1 or not frag2:
                raise ValueError("ETS-NOCV 分析需要指定片段1和片段2的原子范围")
            return ["23", frag1, frag2, "q"]

        elif key == "cda":
            # 菜单 16：CDA 电荷分解
            # CDA 需要在 Multiwfn 中指定片段文件路径
            frag1_path = self.cda_frag1_edit.text().strip()
            frag2_path = self.cda_frag2_edit.text().strip()
            if not frag1_path or not frag2_path:
                raise ValueError("CDA 分析需要指定片段1和片段2的波函数文件路径")
            return ["16", frag1_path, frag2_path, "q"]

        elif key == "basin_analysis":
            # 菜单 17：盆分析
            basin_type = self.basin_type_combo.currentText()
            basin_num = BASIN_TYPES.get(basin_type, "1")
            return ["17", basin_num, "q"]

        elif key == "polarizability":
            # 菜单 24：极化率分析
            return ["24", "q"]

        elif key == "orbital_localization":
            # 菜单 19：轨道定域化
            loc_method = self.loc_method_combo.currentText()
            loc_num = LOC_METHODS.get(loc_method, "1")
            return ["19", loc_num, "q"]

        elif key == "adndp":
            # 菜单 14：AdNDP 分析
            return ["14", "q"]

        elif key == "file_export":
            # 菜单 100：文件格式转换
            fmt = self.export_format_combo.currentText()
            return InputGenerator.generate_export_commands(fmt)

        else:
            raise ValueError(f"未知的功能类型: {key}")

    # ====================================================================
    # 计算入口
    # ====================================================================

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path

    def _on_calculate(self):
        """点击计算按钮，启动分析"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        # 生成命令
        try:
            commands = self._generate_commands()
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        # 获取功能标签
        func_info = ADVANCED_FUNCTIONS.get(self._current_func_key, {})
        func_label = func_info.get("label", "高级分析")

        # 更新 UI 状态
        self.calc_btn.setEnabled(False)
        self.calc_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.status_label.setText(f"正在计算 {func_label}...")
        self.status_label.setStyleSheet(f"color: {_DARK_WARN}; font-size: 12px;")

        # 启动后台计算线程
        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=func_label
        )
        self._worker.finished_ok.connect(self._on_calc_finished)
        self._worker.failed.connect(self._on_calc_failed)
        self._worker.start()

    def _reset_ui_state(self):
        """重置按钮和进度条状态"""
        self.calc_btn.setEnabled(True)
        self.calc_btn.setText("开始计算")
        self.progress_bar.setVisible(False)
        self._worker = None

    # ====================================================================
    # 计算完成回调
    # ====================================================================

    def _on_calc_finished(self, result):
        """计算成功完成，解析并展示结果"""
        try:
            output = result.get("output", "")
            self._last_output = output
            self.output_text.setPlainText(output[:8000])

            # 根据功能类型解析结果
            key = self._current_func_key
            self._last_table_data = []

            if key == "aim_topology":
                self._parse_aim_result(output)
            elif key == "aromaticity":
                self._parse_aromaticity_result(output)
            elif key == "excitation":
                self._parse_excitation_result(output)
            elif key == "concept_dft":
                self._parse_concept_dft_result(output)
            elif key == "file_export":
                self._handle_export_result(output)
            elif key == "basin_analysis":
                self._parse_basin_result(output)
            elif key == "polarizability":
                self._parse_polarizability_result(output)
            elif key == "orbital_localization":
                self._parse_localization_result(output)
            else:
                # 通用解析
                self.result_table.setRowCount(0)

            # 更新状态
            func_info = ADVANCED_FUNCTIONS.get(key, {})
            func_label = func_info.get("label", "分析")
            self.status_label.setText(f"✓ {func_label} 完成")
            self.status_label.setStyleSheet(f"color: {_DARK_SUCCESS}; font-size: 12px;")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
            self.status_label.setText("结果处理失败")
            self.status_label.setStyleSheet(f"color: {_DARK_ERROR}; font-size: 12px;")
        finally:
            self._reset_ui_state()

    def _on_calc_failed(self, error_msg):
        """计算失败"""
        QMessageBox.critical(self, "计算失败", error_msg[:800])
        self.status_label.setText("计算失败")
        self.status_label.setStyleSheet(f"color: {_DARK_ERROR}; font-size: 12px;")
        self._reset_ui_state()

    # ====================================================================
    # 结果解析
    # ====================================================================

    def _parse_aim_result(self, output):
        """解析 AIM 临界点结果"""
        cps = OutputParser.parse_critical_points(output)
        self._last_table_data = [
            {
                "index": cp.get("index", i + 1),
                "label": f"CP-{cp.get('index', i + 1)}",
                "value_x": cp.get("x", 0),
                "value_y": cp.get("y", 0),
                "value_z": cp.get("z", 0),
            }
            for i, cp in enumerate(cps)
        ]

        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(5)
        self.result_table.setHorizontalHeaderLabels(
            ["序号", "临界点", "X", "Y", "Z"]
        )
        for r in self._last_table_data:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(str(r["index"])))
            self.result_table.setItem(row, 1, QTableWidgetItem(r["label"]))
            self.result_table.setItem(row, 2, QTableWidgetItem(f"{r['value_x']:.6f}"))
            self.result_table.setItem(row, 3, QTableWidgetItem(f"{r['value_y']:.6f}"))
            self.result_table.setItem(row, 4, QTableWidgetItem(f"{r['value_z']:.6f}"))

        if cps:
            self.status_label.setText(
                f"✓ AIM拓扑分析完成 | 发现 {len(cps)} 个临界点"
            )

    def _parse_aromaticity_result(self, output):
        """解析芳香性分析结果"""
        import re
        results = OutputParser.parse_aromaticity_results(output)
        self._last_table_data = []

        for key, value in results.items():
            if isinstance(value, list):
                for i, v in enumerate(value):
                    self._last_table_data.append({
                        "index": i + 1,
                        "label": f"{key}[{i}]",
                        "value": v,
                        "unit": "ppm" if "NICS" in key else "",
                    })
            else:
                self._last_table_data.append({
                    "index": len(self._last_table_data) + 1,
                    "label": key,
                    "value": value,
                    "unit": "ppm" if "NICS" in key else "",
                })

        # 额外解析 NICS 值
        nics_pattern = re.compile(
            r"NICS.*?[:=]\s*([-+\d.]+)", re.IGNORECASE
        )
        for match in nics_pattern.finditer(output):
            try:
                val = float(match.group(1))
                already_exists = any(
                    r["label"].startswith("NICS") for r in self._last_table_data
                )
                if not already_exists:
                    self._last_table_data.append({
                        "index": len(self._last_table_data) + 1,
                        "label": "NICS",
                        "value": val,
                        "unit": "ppm",
                    })
            except ValueError:
                continue

        self._fill_generic_table(self._last_table_data)

    def _parse_excitation_result(self, output):
        """解析电子激发分析结果"""
        import re
        self._last_table_data = []

        # 尝试解析 Sm 指数、电荷转移距离等
        patterns = {
            "Sm指数": re.compile(r"Sm\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "电荷转移距离": re.compile(r"(?:Charge transfer distance|D_ct|Δr)\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "Dt指数": re.compile(r"Dt\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "激发能": re.compile(r"Excitation energy\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "振荡强度": re.compile(r"Oscillator strength\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
        }

        for label, pattern in patterns.items():
            match = pattern.search(output)
            if match:
                try:
                    val = float(match.group(1))
                    self._last_table_data.append({
                        "index": len(self._last_table_data) + 1,
                        "label": label,
                        "value": val,
                        "unit": "",
                    })
                except ValueError:
                    continue

        self._fill_generic_table(self._last_table_data)

    def _parse_concept_dft_result(self, output):
        """解析概念DFT结果"""
        import re
        self._last_table_data = []

        # 解析全局指标
        global_patterns = {
            "化学势μ": re.compile(r"Chemical potential\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "化学硬度η": re.compile(r"Chemical hardness\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "软度S": re.compile(r"Softness\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "亲电指数ω": re.compile(r"Electrophilicity\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
            "电负性χ": re.compile(r"Electronegativity\s*[:=]\s*([-+\d.Ee]+)", re.IGNORECASE),
        }

        for label, pattern in global_patterns.items():
            match = pattern.search(output)
            if match:
                try:
                    val = float(match.group(1))
                    self._last_table_data.append({
                        "index": len(self._last_table_data) + 1,
                        "label": label,
                        "value": val,
                        "unit": "a.u.",
                    })
                except ValueError:
                    continue

        # 解析原子级指标（如 Fukui 函数值）
        fukui_pattern = re.compile(
            r"Atom\s+(\d+)\(([A-Za-z]+)\s*\).*?Fukui\s+.*?[:=]\s*([-+\d.Ee]+)",
            re.IGNORECASE
        )
        for match in fukui_pattern.finditer(output):
            try:
                idx = int(match.group(1))
                elem = match.group(2)
                val = float(match.group(3))
                self._last_table_data.append({
                    "index": idx,
                    "label": f"Fukui({elem}{idx})",
                    "value": val,
                    "unit": "",
                })
            except (ValueError, IndexError):
                continue

        self._fill_generic_table(self._last_table_data)

    def _parse_basin_result(self, output):
        """解析盆分析结果"""
        import re
        self._last_table_data = []

        # 解析盆积分结果
        # 格式示例: Basin 1: Electron population = 5.234
        basin_pattern = re.compile(
            r"Basin\s+(\d+).*?(?:population|electron)\s*[:=]\s*([-+\d.Ee]+)",
            re.IGNORECASE
        )
        for match in basin_pattern.finditer(output):
            try:
                idx = int(match.group(1))
                val = float(match.group(2))
                self._last_table_data.append({
                    "index": idx,
                    "label": f"Basin {idx}",
                    "value": val,
                    "unit": "e",
                })
            except (ValueError, IndexError):
                continue

        self._fill_generic_table(self._last_table_data)

    def _parse_polarizability_result(self, output):
        """解析极化率分析结果"""
        import re
        self._last_table_data = []

        patterns = {
            "各向同性极化率α_iso": re.compile(
                r"(?:Isotropic|alpha_iso)\s*(?:polarizability)?\s*[:=]\s*([-+\d.Ee]+)",
                re.IGNORECASE
            ),
            "各向异性极化率Δα": re.compile(
                r"(?:Anisotropic|alpha_aniso|Delta_alpha)\s*[:=]\s*([-+\d.Ee]+)",
                re.IGNORECASE
            ),
            "第一超极化率β": re.compile(
                r"(?:First hyperpolarizability|beta_tot)\s*[:=]\s*([-+\d.Ee]+)",
                re.IGNORECASE
            ),
        }

        for label, pattern in patterns.items():
            match = pattern.search(output)
            if match:
                try:
                    val = float(match.group(1))
                    self._last_table_data.append({
                        "index": len(self._last_table_data) + 1,
                        "label": label,
                        "value": val,
                        "unit": "a.u.",
                    })
                except ValueError:
                    continue

        # 也尝试解析张量分量
        tensor_pattern = re.compile(
            r"(alpha|beta)_(xx|yy|zz|xy|xz|yz)\s*[:=]\s*([-+\d.Ee]+)",
            re.IGNORECASE
        )
        for match in tensor_pattern.finditer(output):
            try:
                component = f"{match.group(1)}_{match.group(2)}"
                val = float(match.group(3))
                self._last_table_data.append({
                    "index": len(self._last_table_data) + 1,
                    "label": component,
                    "value": val,
                    "unit": "a.u.",
                })
            except (ValueError, IndexError):
                continue

        self._fill_generic_table(self._last_table_data)

    def _parse_localization_result(self, output):
        """解析轨道定域化结果"""
        self._last_table_data = []
        # 轨道定域化主要输出LMO信息
        self._fill_generic_table(self._last_table_data)

    def _handle_export_result(self, output):
        """处理文件导出结果"""
        work_dir = os.path.dirname(self.current_file) if self.current_file else "."
        fmt = self.export_format_combo.currentText()

        # 查找导出的文件
        exported_file = self._find_exported_file(work_dir, fmt)

        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["项目", "值"])

        if exported_file:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem("导出文件"))
            self.result_table.setItem(row, 1, QTableWidgetItem(exported_file))

            self._last_table_data = [{"项目": "导出文件", "值": exported_file}]
            self.status_label.setText(f"✓ 文件已导出: {exported_file}")
        else:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem("状态"))
            self.result_table.setItem(row, 1, QTableWidgetItem("导出命令已执行，请检查工作目录"))

            self.status_label.setText("✓ 文件导出命令已执行")

    def _fill_generic_table(self, records):
        """通用表格填充方法"""
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(
            ["序号", "项目", "数值", "单位/说明"]
        )

        for r in records:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(str(r.get("index", ""))))
            self.result_table.setItem(row, 1, QTableWidgetItem(str(r.get("label", ""))))
            val = r.get("value", r.get("contribution", ""))
            if isinstance(val, float):
                self.result_table.setItem(row, 2, QTableWidgetItem(f"{val:.6f}"))
            else:
                self.result_table.setItem(row, 2, QTableWidgetItem(str(val)))
            self.result_table.setItem(row, 3, QTableWidgetItem(str(r.get("unit", ""))))

    # ====================================================================
    # 辅助方法
    # ====================================================================

    def _find_exported_file(self, work_dir, ext):
        """扫描目录，返回最新的具有指定扩展名的文件路径"""
        # 优先匹配 output.ext
        direct = os.path.join(work_dir, f"output.{ext}")
        if os.path.exists(direct):
            return direct
        # 扫描所有该扩展名文件，取最新修改
        pattern = os.path.join(work_dir, f"*.{ext}")
        candidates = [p for p in glob.glob(pattern) if os.path.isfile(p)]
        if candidates:
            return max(candidates, key=os.path.getmtime)
        return None

    # ====================================================================
    # 数据导出
    # ====================================================================

    def _get_export_data(self):
        """为 ExportButtonWidget 提供导出数据"""
        if self._last_table_data:
            func_info = ADVANCED_FUNCTIONS.get(self._current_func_key, {})
            func_label = func_info.get("label", "高级分析")

            # 统一使用通用列名
            headers = ["序号", "项目", "数值", "单位/说明"]
            records = []
            for r in self._last_table_data:
                records.append({
                    "序号": r.get("index", ""),
                    "项目": r.get("label", ""),
                    "数值": r.get("value", r.get("contribution", "")),
                    "单位/说明": r.get("unit", ""),
                })

            metadata = {
                "分析功能": func_label,
                "文件": os.path.basename(self.current_file) if self.current_file else "未知",
                "数据行数": len(records),
            }
            return records, headers, metadata

        # 无表格数据时导出原始输出
        if self._last_output:
            func_info = ADVANCED_FUNCTIONS.get(self._current_func_key, {})
            func_label = func_info.get("label", "高级分析")
            return (
                [{"原始输出": self._last_output[:5000]}],
                ["原始输出"],
                {"分析功能": func_label}
            )
        return None
