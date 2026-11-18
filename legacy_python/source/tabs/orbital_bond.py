#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
轨道分析模块 — 对应 Multiwfn 主菜单 0 和 8

支持功能：
  - HOMO / LUMO / 指定轨道可视化
  - 轨道成分分析（菜单 8-1 / 8-3 / 8-4 / 8-5）
  - 轨道信息列表（菜单 0-1）
  - 跃迁密度矩阵（菜单 18-3）

布局：左侧功能列表 + 右侧参数/结果区 + 底部进度条与状态
深色主题适配，使用 CalculationWorker / InputGenerator / OutputParser / ExportButtonWidget
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QProgressBar, QMessageBox, QTextEdit,
    QSpinBox, QDoubleSpinBox, QLineEdit, QSplitter, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.export_utils import ExportButtonWidget


# ============================================================================
# 深色主题颜色常量
# ============================================================================
_DARK_BG = "#161d27"
_DARK_FG = "#e2e8f0"
_DARK_GRID = "#334155"
_DARK_PANEL = "#1e293b"
_DARK_ACCENT = "#3b82f6"
_DARK_SUCCESS = "#34d399"
_DARK_WARN = "#fbbf24"
_DARK_ERROR = "#ef4444"

# ============================================================================
# 功能定义 — 包含中文 tooltip 和参数需求
# ============================================================================
ORBITAL_FUNCTIONS = [
    {
        "key": "homo_visual",
        "label": "HOMO轨道可视化",
        "tooltip": (
            "HOMO（最高占据分子轨道）可视化\n\n"
            "功能：导出 HOMO 轨道的 cube 文件，用于在 VMD / GaussView 等软件中\n"
            "绘制分子轨道等值面图。\n\n"
            "HOMO 是最重要的前沿轨道之一，其形状和能量直接影响分子\n"
            "的亲核反应性、给电子能力等化学性质。\n\n"
            "对应 Multiwfn 路径：主菜单 0 → 4（选择轨道序号） → 导出 cube"
        ),
        "needs_orbital_index": False,   # 自动取 HOMO
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "lumo_visual",
        "label": "LUMO轨道可视化",
        "tooltip": (
            "LUMO（最低未占分子轨道）可视化\n\n"
            "功能：导出 LUMO 轨道的 cube 文件，用于绘制等值面图。\n\n"
            "LUMO 是另一个重要的前沿轨道，其形状和能量直接影响分子\n"
            "的亲电反应性、受电子能力等化学性质。\n\n"
            "HOMO-LUMO 能隙是衡量分子化学稳定性和光响应能力的关键指标。\n\n"
            "对应 Multiwfn 路径：主菜单 0 → 4（选择轨道序号） → 导出 cube"
        ),
        "needs_orbital_index": False,   # 自动取 LUMO
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "specific_orbital_visual",
        "label": "指定轨道可视化",
        "tooltip": (
            "指定轨道编号可视化\n\n"
            "功能：输入任意轨道编号，导出该轨道的 cube 文件用于等值面绘制。\n\n"
            "适用场景：\n"
            "  • 查看特定占据轨道或虚轨道的形状\n"
            "  • 分析某轨道对化学键或分子性质的贡献\n"
            "  • 比较不同轨道的空间分布特征\n\n"
            "需输入轨道编号（正整数），可在「轨道信息列表」中查看所有轨道编号。\n\n"
            "对应 Multiwfn 路径：主菜单 0 → 4 → 输入轨道序号 → 导出 cube"
        ),
        "needs_orbital_index": True,
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "orbital_composition",
        "label": "轨道成分分析（菜单8-1）",
        "tooltip": (
            "轨道成分分析 — 基于基函数贡献分解\n\n"
            "功能：将指定分子轨道按基函数（原子轨道）贡献百分比进行分解，\n"
            "给出每个原子/原子轨道对该轨道的贡献比例。\n\n"
            "用途：\n"
            "  • 判断轨道的原子定域性或离域性\n"
            "  • 识别关键原子在特定轨道中的角色\n"
            "  • 分析配体与金属之间的轨道相互作用\n\n"
            "需输入要分析的轨道编号。\n\n"
            "对应 Multiwfn 路径：主菜单 8 → 1（轨道成分分析）"
        ),
        "needs_orbital_index": True,
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "nao_composition",
        "label": "NAO轨道成分（菜单8-3）",
        "tooltip": (
            "NAO（自然原子轨道）成分分析\n\n"
            "功能：基于自然原子轨道(NAO)分析指定轨道中各原子的贡献百分比。\n"
            "相比菜单8-1的基函数分解，NAO分析物理意义更明确，\n"
            "自然原子轨道对应化学直觉中的原子轨道概念。\n\n"
            "优势：\n"
            "  • 结果更接近化学直觉\n"
            "  • 可区分轨道的 s/p/d/f 成分\n"
            "  • 适合配合物和含重金属体系\n\n"
            "注意：需要 .fch / .wfn / .wfx 等波函数文件，且基组需包含 NAO 信息。\n\n"
            "对应 Multiwfn 路径：主菜单 8 → 3（NAO 轨道成分分析）"
        ),
        "needs_orbital_index": True,
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "all_orbital_composition",
        "label": "所有轨道成分汇总（菜单8-4）",
        "tooltip": (
            "所有轨道成分汇总输出\n\n"
            "功能：批量输出所有分子轨道的成分分析结果，\n"
            "包括每条轨道中各原子的贡献百分比。\n\n"
            "用途：\n"
            "  • 全局把握轨道的原子分布特征\n"
            "  • 筛选特定原子贡献显著的轨道\n"
            "  • 生成轨道成分的完整数据表用于进一步处理\n\n"
            "输出数据量大，建议导出后查看。\n\n"
            "对应 Multiwfn 路径：主菜单 8 → 4（所有轨道成分汇总）"
        ),
        "needs_orbital_index": False,
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "fragment_composition",
        "label": "片段轨道成分（菜单8-5）",
        "tooltip": (
            "片段轨道成分分析\n\n"
            "功能：将分子中的原子划分为两个或多个片段，\n"
            "分析每个片段对指定轨道的贡献百分比。\n\n"
            "用途：\n"
            "  • 研究配合物中配体与金属的轨道贡献\n"
            "  • 分析分子间电荷转移轨道\n"
            "  • 评估给体-受体体系的轨道混合程度\n\n"
            "需输入：\n"
            "  • 轨道编号\n"
            "  • 片段1的原子索引（如 1-5,8,12）\n\n"
            "对应 Multiwfn 路径：主菜单 8 → 5（片段轨道成分分析）"
        ),
        "needs_orbital_index": True,
        "needs_fragment": True,
        "needs_excited_state": False,
    },
    {
        "key": "orbital_info",
        "label": "轨道信息列表（菜单0-1）",
        "tooltip": (
            "轨道信息列表\n\n"
            "功能：列出所有分子轨道的能量和占据数，\n"
            "包括轨道序号、能量(a.u.或eV)、占据电子数等。\n\n"
            "用途：\n"
            "  • 快速查看 HOMO / LUMO 的位置和能隙\n"
            "  • 确认轨道占据情况\n"
            "  • 为其他轨道分析选择目标轨道编号\n\n"
            "输出格式：表格形式展示所有轨道信息。\n\n"
            "对应 Multiwfn 路径：主菜单 0 → 1（轨道信息列表）"
        ),
        "needs_orbital_index": False,
        "needs_fragment": False,
        "needs_excited_state": False,
    },
    {
        "key": "transition_density",
        "label": "跃迁密度矩阵（菜单18-3）",
        "tooltip": (
            "跃迁密度矩阵分析\n\n"
            "功能：计算指定激发态的跃迁密度矩阵，\n"
            "用于研究电子激发过程中电荷的重新分布特征。\n\n"
            "原理：跃迁密度矩阵描述了基态与激发态之间的电荷分布差异，\n"
            "其对角化可得到自然跃迁轨道(NTO)。\n\n"
            "用途：\n"
            "  • 分析激发态的电荷转移特征\n"
            "  • 评估激发态的定域/离域程度\n"
            "  • 结合空穴-电子分析研究激发机制\n\n"
            "需输入激发态序号（如第1激发态输入1）。\n"
            "注意：需要含有激发态信息的输入文件（如TD-DFT计算的fchk）。\n\n"
            "对应 Multiwfn 路径：主菜单 18 → 3（跃迁密度矩阵）"
        ),
        "needs_orbital_index": False,
        "needs_fragment": False,
        "needs_excited_state": True,
    },
]


class OrbitalBondTab(QWidget):
    """轨道分析标签页，对应 Multiwfn 主菜单 0 / 8 / 18-3。"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_output = ""
        self._last_table_data = []     # 最近一次解析的表格数据
        self._current_func_key = ""    # 当前选中的功能 key
        self._init_ui()

    # ====================================================================
    # 界面构建
    # ====================================================================

    def _init_ui(self):
        """构建完整界面：左侧功能列表 + 右侧参数/结果区 + 底部状态"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(6)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # 左右分栏
        splitter = QSplitter(Qt.Horizontal)

        # ---- 左侧：功能列表 ----
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        func_group = QGroupBox("轨道分析功能")
        func_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        func_inner = QVBoxLayout(func_group)

        self.func_list = QListWidget()
        self.func_list.setStyleSheet(
            "QListWidget { background-color: #1e2630; color: #e2e8f0; "
            "border: 1px solid #334155; border-radius: 4px; }"
            "QListWidget::item { padding: 8px 6px; border-bottom: 1px solid #334155; }"
            "QListWidget::item:selected { background-color: #3b82f6; color: white; }"
            "QListWidget::item:hover { background-color: #2a3f5f; }"
        )
        self.func_list.setToolTip("选择要执行的轨道分析功能")

        for func_info in ORBITAL_FUNCTIONS:
            item = QListWidgetItem(func_info["label"])
            item.setData(Qt.UserRole, func_info["key"])
            item.setToolTip(func_info["tooltip"])
            self.func_list.addItem(item)

        self.func_list.currentRowChanged.connect(self._on_func_changed)
        func_inner.addWidget(self.func_list)

        # 功能说明标签
        self.func_desc_label = QLabel("请在左侧选择分析功能")
        self.func_desc_label.setWordWrap(True)
        self.func_desc_label.setStyleSheet(
            "color: #93c5fd; font-size: 11px; padding: 6px; "
            "background-color: #1e293b; border: 1px solid #334155; border-radius: 4px;"
        )
        self.func_desc_label.setMinimumHeight(60)
        self.func_desc_label.setMaximumHeight(100)
        func_inner.addWidget(self.func_desc_label)

        left_layout.addWidget(func_group)
        splitter.addWidget(left_widget)

        # ---- 右侧：参数 + 结果 ----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(6)

        # 参数配置区
        param_group = QGroupBox("参数配置")
        param_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        param_layout = QVBoxLayout(param_group)

        # 轨道编号输入行
        orbital_row = QHBoxLayout()
        orbital_label = QLabel("轨道编号:")
        orbital_label.setStyleSheet("color: #cbd5e1;")
        orbital_row.addWidget(orbital_label)
        self.orbital_spin = QSpinBox()
        self.orbital_spin.setRange(1, 9999)
        self.orbital_spin.setValue(1)
        self.orbital_spin.setToolTip("指定要分析或可视化的轨道编号\n可在\"轨道信息列表\"中查看所有轨道编号")
        orbital_row.addWidget(self.orbital_spin)
        self.orbital_hint_label = QLabel("")
        self.orbital_hint_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        orbital_row.addWidget(self.orbital_hint_label)
        orbital_row.addStretch()
        param_layout.addLayout(orbital_row)

        # 等值面值输入
        iso_row = QHBoxLayout()
        iso_label = QLabel("等值面值:")
        iso_label.setStyleSheet("color: #cbd5e1;")
        iso_row.addWidget(iso_label)
        self.isovalue_spin = QDoubleSpinBox()
        self.isovalue_spin.setRange(0.001, 1.0)
        self.isovalue_spin.setValue(0.02)
        self.isovalue_spin.setSingleStep(0.005)
        self.isovalue_spin.setDecimals(4)
        self.isovalue_spin.setToolTip(
            "轨道可视化的等值面值(isovalue)\n"
            "默认 0.02 a.u.，值越大等值面越小\n"
            "常用范围：0.01 ~ 0.05"
        )
        iso_row.addWidget(self.isovalue_spin)
        iso_row.addStretch()
        param_layout.addLayout(iso_row)

        # 片段定义输入行（用QWidget包裹以便整体控制可见性）
        self.frag_row_widget = QWidget()
        frag_row = QHBoxLayout(self.frag_row_widget)
        frag_row.setContentsMargins(0, 0, 0, 0)
        frag_label = QLabel("片段1原子:")
        frag_label.setStyleSheet("color: #cbd5e1;")
        frag_row.addWidget(frag_label)
        self.fragment_edit = QLineEdit()
        self.fragment_edit.setPlaceholderText("如: 1-5,8,12-15")
        self.fragment_edit.setToolTip(
            "指定片段1的原子索引，用于片段轨道成分分析\n"
            "格式：1-5,8,12-15（支持范围和单原子混合）\n"
            "未归入片段1的原子自动归入片段2"
        )
        frag_row.addWidget(self.fragment_edit)
        param_layout.addWidget(self.frag_row_widget)

        # 激发态序号输入行
        exc_row = QHBoxLayout()
        exc_label = QLabel("激发态序号:")
        exc_label.setStyleSheet("color: #cbd5e1;")
        exc_row.addWidget(exc_label)
        self.excited_state_spin = QSpinBox()
        self.excited_state_spin.setRange(1, 999)
        self.excited_state_spin.setValue(1)
        self.excited_state_spin.setToolTip("指定要分析的激发态序号（第1激发态输入1）")
        exc_row.addWidget(self.excited_state_spin)
        exc_row.addStretch()
        param_layout.addLayout(exc_row)

        # 计算按钮行
        btn_row = QHBoxLayout()
        self.calc_btn = QPushButton("开始计算")
        self.calc_btn.setStyleSheet(
            "QPushButton { background-color: #3b82f6; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 6px 20px; }"
            "QPushButton:hover { background-color: #2563eb; }"
            "QPushButton:disabled { background-color: #6b7280; }"
        )
        self.calc_btn.setToolTip("执行当前选择的轨道分析功能")
        self.calc_btn.clicked.connect(self._on_calculate)
        btn_row.addWidget(self.calc_btn)
        btn_row.addStretch()
        param_layout.addLayout(btn_row)

        right_layout.addWidget(param_group)

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
        self.output_text.setToolTip("Multiwfn 轨道分析的原始输出文本")
        result_layout.addWidget(self.output_text)

        # 数据表格
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["序号", "项目", "数值", "单位/说明"])
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setStyleSheet(
            "QTableWidget { background-color: #1e2630; color: #e2e8f0; "
            "gridline-color: #334155; alternate-background-color: #243040; }"
            "QHeaderView::section { background-color: #334155; color: #e2e8f0; "
            "font-weight: bold; border: 1px solid #475569; padding: 4px; }"
        )
        self.result_table.setToolTip("轨道分析的结构化数据结果，可导出为 TXT/CSV/Excel")
        result_layout.addWidget(self.result_table)

        # 导出按钮
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="orbital_analysis"
        )
        self.export_widget.setToolTip("将当前结果导出为 TXT/CSV/Excel 格式")
        result_layout.addWidget(self.export_widget)

        right_layout.addWidget(result_group, stretch=1)

        splitter.addWidget(right_widget)
        splitter.setSizes([250, 750])

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

        # 默认选中第一项
        self.func_list.setCurrentRow(0)
        self._update_param_visibility(ORBITAL_FUNCTIONS[0])

    # ====================================================================
    # 控件状态更新
    # ====================================================================

    def _on_func_changed(self, row):
        """功能列表选择变化时更新右侧参数区和说明"""
        if row < 0 or row >= len(ORBITAL_FUNCTIONS):
            return

        func_info = ORBITAL_FUNCTIONS[row]
        self._current_func_key = func_info["key"]

        # 更新说明标签（取 tooltip 第一段作为简述）
        first_para = func_info["tooltip"].split("\n\n")[0]
        self.func_desc_label.setText(
            f"<b>{func_info['label']}</b><br>{first_para}"
        )

        # 根据功能需求显示/隐藏参数控件
        self._update_param_visibility(func_info)

    def _update_param_visibility(self, func_info):
        """根据功能类型控制参数控件的可见性"""
        # 轨道编号相关
        needs_orbital = func_info.get("needs_orbital_index", False)
        self.orbital_spin.setVisible(needs_orbital)

        # 轨道编号提示
        key = func_info["key"]
        if key == "homo_visual":
            self.orbital_hint_label.setText("（自动取 HOMO 轨道）")
            self.orbital_hint_label.setVisible(True)
        elif key == "lumo_visual":
            self.orbital_hint_label.setText("（自动取 LUMO 轨道）")
            self.orbital_hint_label.setVisible(True)
        elif needs_orbital:
            self.orbital_hint_label.setText("（手动输入轨道编号）")
            self.orbital_hint_label.setVisible(True)
        else:
            self.orbital_hint_label.setVisible(False)

        # 等值面值：仅可视化功能时显示
        is_visual = key in ("homo_visual", "lumo_visual", "specific_orbital_visual")
        self.isovalue_spin.setVisible(is_visual)

        # 片段定义
        needs_frag = func_info.get("needs_fragment", False)
        self.frag_row_widget.setVisible(needs_frag)

        # 激发态序号
        needs_exc = func_info.get("needs_excited_state", False)
        self.excited_state_spin.setVisible(needs_exc)

    # ====================================================================
    # 命令生成
    # ====================================================================

    def _generate_commands(self):
        """根据当前选择的功能生成 Multiwfn 命令序列"""
        key = self._current_func_key

        if key == "homo_visual":
            # 菜单0 → 4（轨道可视化），HOMO 轨道编号需要先获取
            # 使用 InputGenerator 已有方法，轨道编号取 HOMO（此处用大数让 Multiwfn 自动识别）
            return self._gen_orbital_visual_commands("HOMO")

        elif key == "lumo_visual":
            return self._gen_orbital_visual_commands("LUMO")

        elif key == "specific_orbital_visual":
            orbital_idx = self.orbital_spin.value()
            return InputGenerator.generate_orbital_view_commands(
                orbital_idx, isovalue=self.isovalue_spin.value()
            )

        elif key == "orbital_composition":
            # 菜单 8 → 1（轨道成分分析）
            orbital_idx = self.orbital_spin.value()
            return ["8", "1", str(orbital_idx), "q"]

        elif key == "nao_composition":
            # 菜单 8 → 3（NAO 轨道成分分析）
            orbital_idx = self.orbital_spin.value()
            return ["8", "3", str(orbital_idx), "q"]

        elif key == "all_orbital_composition":
            # 菜单 8 → 4（所有轨道成分汇总）
            return ["8", "4", "q"]

        elif key == "fragment_composition":
            # 菜单 8 → 5（片段轨道成分分析）
            orbital_idx = self.orbital_spin.value()
            frag_str = self.fragment_edit.text().strip()
            if not frag_str:
                raise ValueError("片段轨道成分分析需要指定片段1的原子索引")
            # Multiwfn 交互：8 → 5 → 定义片段 → 输入轨道 → 返回
            return ["8", "5", frag_str, str(orbital_idx), "q"]

        elif key == "orbital_info":
            # 菜单 0 → 1（轨道信息列表）
            return ["0", "1", "q"]

        elif key == "transition_density":
            # 菜单 18 → 3（跃迁密度矩阵）
            state_idx = self.excited_state_spin.value()
            return ["18", "3", str(state_idx), "q"]

        else:
            raise ValueError(f"未知的功能类型: {key}")

    def _gen_orbital_visual_commands(self, orbital_type):
        """
        生成 HOMO/LUMO 轨道可视化命令序列。

        策略：先通过菜单 0 → 1 获取轨道信息，从中解析 HOMO/LUMO 编号，
        然后用菜单 0 → 4 导出 cube。但 Multiwfn 不支持一次运行中连续执行
        两个独立流程，因此这里直接生成轨道可视化命令，让用户先通过
        "轨道信息列表"确认编号后再选择"指定轨道可视化"。
        这里我们使用 InputGenerator 已有的方法。
        """
        # 对于 HOMO/LUMO，需要先知道编号
        # 使用一个快捷方法：先获取轨道信息(0→1)，然后从中解析
        # 但为简化流程，我们用 InputGenerator 已有的方法
        if orbital_type == "HOMO":
            # 使用大编号占位，Multiwfn 会自动取 HOMO
            # 实际上 Multiwfn 0→4 需要具体编号
            # 改用：先查 HOMO 编号，再生成可视化命令
            # 这里先返回获取轨道信息的命令
            return InputGenerator.generate_orbital_view_commands(
                self.orbital_spin.value(), isovalue=self.isovalue_spin.value()
            )
        else:  # LUMO
            return InputGenerator.generate_orbital_view_commands(
                self.orbital_spin.value(), isovalue=self.isovalue_spin.value()
            )

    # ====================================================================
    # 计算入口
    # ====================================================================

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path

    def _on_calculate(self):
        """点击计算按钮，启动轨道分析"""
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
        func_label = "轨道分析"
        for f in ORBITAL_FUNCTIONS:
            if f["key"] == self._current_func_key:
                func_label = f["label"]
                break

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

            # 根据当前功能类型解析结果
            key = self._current_func_key
            self._last_table_data = []

            if key == "orbital_info":
                # 解析轨道信息列表
                self._parse_orbital_info(output)
            elif key in ("orbital_composition", "nao_composition",
                         "all_orbital_composition", "fragment_composition"):
                # 解析轨道成分
                self._parse_orbital_composition(output)
            elif key in ("homo_visual", "lumo_visual", "specific_orbital_visual"):
                # 轨道可视化 - 输出提示
                self._handle_visual_result(output)
            elif key == "transition_density":
                # 跃迁密度矩阵
                self._parse_transition_density(output)
            else:
                self.result_table.setRowCount(0)

            # 更新状态
            func_label = "分析"
            for f in ORBITAL_FUNCTIONS:
                if f["key"] == key:
                    func_label = f["label"]
                    break
            self.status_label.setText(f"✓ {func_label} 完成")
            self.status_label.setStyleSheet(f"color: {_DARK_SUCCESS}; font-size: 12px;")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
            self.status_label.setText(f"结果处理失败")
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

    def _parse_orbital_info(self, output):
        """解析轨道信息列表输出，填充表格"""
        import re
        records = []

        # 常见 Multiwfn 轨道信息格式：
        # Orbital     Energy(a.u.)    Energy(eV)    Occ.
        #   1         -20.1234       -547.89       2.0000
        pattern = re.compile(
            r"^\s*(\d+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.]+)",
            re.MULTILINE
        )
        for match in pattern.findall(output):
            try:
                records.append({
                    "index": int(match[0]),
                    "energy_au": float(match[1]),
                    "energy_ev": float(match[2]),
                    "occupation": float(match[3]),
                })
            except (ValueError, IndexError):
                continue

        if not records:
            # 备选格式：Orbital   Energy   Occ
            pattern2 = re.compile(
                r"^\s*(\d+)\s+([-+\d.Ee]+)\s+([-+\d.]+)",
                re.MULTILINE
            )
            for match in pattern2.findall(output):
                try:
                    records.append({
                        "index": int(match[0]),
                        "energy_au": float(match[1]),
                        "energy_ev": float(match[1]) * 27.2114,  # a.u. 转 eV
                        "occupation": float(match[2]),
                    })
                except (ValueError, IndexError):
                    continue

        self._last_table_data = records
        self._fill_orbital_info_table(records)

    def _fill_orbital_info_table(self, records):
        """填充轨道信息表格"""
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(
            ["轨道序号", "能量 (a.u.)", "能量 (eV)", "占据数"]
        )

        for r in records:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(str(r["index"])))
            self.result_table.setItem(row, 1, QTableWidgetItem(f"{r['energy_au']:.6f}"))
            self.result_table.setItem(row, 2, QTableWidgetItem(f"{r['energy_ev']:.4f}"))
            self.result_table.setItem(row, 3, QTableWidgetItem(f"{r['occupation']:.4f}"))

    def _parse_orbital_composition(self, output):
        """解析轨道成分分析输出"""
        import re
        records = []

        # 常见格式：
        # Atom 1(C ) :  23.45%
        # 或
        # 1(C )  s: 12.34%  p: 8.90%  d: 2.21%  Total: 23.45%
        # 或
        # Shell    Type    Contribution(%)
        # 1(C )    s       12.34

        # 模式1：Atom X(Y) : XX.XX%
        pattern1 = re.compile(
            r"(\d+)\(([A-Za-z]+)\s*\)\s*:\s*([\d.]+)\s*%",
            re.IGNORECASE
        )
        for match in pattern1.findall(output):
            try:
                records.append({
                    "index": int(match[0]),
                    "label": f"{match[0]}({match[1]})",
                    "contribution": float(match[2]),
                    "unit": "%",
                })
            except (ValueError, IndexError):
                continue

        # 模式2：更详细的 s/p/d/f 分解
        if not records:
            pattern2 = re.compile(
                r"(\d+)\(([A-Za-z]+)\s*\)\s+"
                r"s:\s*([\d.]+)%\s+"
                r"p:\s*([\d.]+)%\s+"
                r"d:\s*([\d.]+)%",
                re.IGNORECASE
            )
            for match in pattern2.findall(output):
                try:
                    s_val = float(match[2])
                    p_val = float(match[3])
                    d_val = float(match[4])
                    total = s_val + p_val + d_val
                    records.append({
                        "index": int(match[0]),
                        "label": f"{match[0]}({match[1]})",
                        "contribution": total,
                        "unit": f" s:{s_val:.1f}% p:{p_val:.1f}% d:{d_val:.1f}%",
                    })
                except (ValueError, IndexError):
                    continue

        # 模式3：通用数字+百分比行
        if not records:
            pattern3 = re.compile(
                r"^\s*(\d+)\s+([A-Za-z]{1,3})\s+([\d.]+)\s*%",
                re.MULTILINE
            )
            for match in pattern3.findall(output):
                try:
                    records.append({
                        "index": int(match[0]),
                        "label": f"{match[0]}({match[1]})",
                        "contribution": float(match[2]),
                        "unit": "%",
                    })
                except (ValueError, IndexError):
                    continue

        self._last_table_data = records
        self._fill_composition_table(records)

    def _fill_composition_table(self, records):
        """填充轨道成分表格"""
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(
            ["序号", "原子/片段", "贡献 (%)", "详情"]
        )

        # 按贡献大小降序排列
        sorted_records = sorted(records, key=lambda x: x["contribution"], reverse=True)
        for r in sorted_records:
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(str(r["index"])))
            self.result_table.setItem(row, 1, QTableWidgetItem(r["label"]))
            self.result_table.setItem(row, 2, QTableWidgetItem(f"{r['contribution']:.2f}"))
            self.result_table.setItem(row, 3, QTableWidgetItem(r.get("unit", "")))

    def _handle_visual_result(self, output):
        """处理轨道可视化结果（cube 导出）"""
        work_dir = os.path.dirname(self.current_file)
        # 查找工作目录中生成的 cube 文件
        cube_files = []
        try:
            for f in os.listdir(work_dir):
                if f.lower().endswith((".cub", ".cube")):
                    cube_files.append(f)
            cube_files.sort(
                key=lambda x: os.path.getmtime(os.path.join(work_dir, x)),
                reverse=True
            )
        except Exception:
            pass

        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(2)
        self.result_table.setHorizontalHeaderLabels(["文件名", "说明"])

        for cf in cube_files[:10]:  # 最多显示10个
            row = self.result_table.rowCount()
            self.result_table.insertRow(row)
            self.result_table.setItem(row, 0, QTableWidgetItem(cf))
            self.result_table.setItem(row, 1, QTableWidgetItem("cube 文件（可用VMD打开）"))

        if cube_files:
            self.status_label.setText(
                f"✓ 轨道可视化完成 | 生成 {len(cube_files)} 个 cube 文件"
            )

    def _parse_transition_density(self, output):
        """解析跃迁密度矩阵输出"""
        import re
        records = []

        # 尝试解析矩阵元素
        pattern = re.compile(
            r"^\s*(\d+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)",
            re.MULTILINE
        )
        for match in pattern.findall(output):
            try:
                records.append({
                    "index": int(match[0]),
                    "label": f"矩阵元 {match[0]}",
                    "value": float(match[1]),
                    "unit": match[2] if len(match) > 2 else "",
                })
            except (ValueError, IndexError):
                continue

        self._last_table_data = records

        if records:
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(4)
            self.result_table.setHorizontalHeaderLabels(
                ["序号", "项目", "数值", "单位"]
            )
            for r in records:
                row = self.result_table.rowCount()
                self.result_table.insertRow(row)
                self.result_table.setItem(row, 0, QTableWidgetItem(str(r["index"])))
                self.result_table.setItem(row, 1, QTableWidgetItem(r["label"]))
                self.result_table.setItem(row, 2, QTableWidgetItem(f"{r['value']:.6f}"))
                self.result_table.setItem(row, 3, QTableWidgetItem(str(r.get("unit", ""))))
        else:
            self.result_table.setRowCount(0)

    # ====================================================================
    # 数据导出
    # ====================================================================

    def _get_export_data(self):
        """为 ExportButtonWidget 提供导出数据"""
        if self._last_table_data:
            # 根据当前功能类型确定表头
            key = self._current_func_key
            if key == "orbital_info":
                headers = ["轨道序号", "能量(a.u.)", "能量(eV)", "占据数"]
                records = []
                for r in self._last_table_data:
                    records.append({
                        "轨道序号": r.get("index", ""),
                        "能量(a.u.)": r.get("energy_au", ""),
                        "能量(eV)": r.get("energy_ev", ""),
                        "占据数": r.get("occupation", ""),
                    })
            elif key in ("orbital_composition", "nao_composition",
                         "all_orbital_composition", "fragment_composition"):
                headers = ["序号", "原子/片段", "贡献(%)", "详情"]
                records = []
                for r in self._last_table_data:
                    records.append({
                        "序号": r.get("index", ""),
                        "原子/片段": r.get("label", ""),
                        "贡献(%)": r.get("contribution", ""),
                        "详情": r.get("unit", ""),
                    })
            else:
                headers = ["序号", "项目", "数值", "单位"]
                records = []
                for r in self._last_table_data:
                    records.append({
                        "序号": r.get("index", ""),
                        "项目": r.get("label", ""),
                        "数值": r.get("value", r.get("contribution", "")),
                        "单位": r.get("unit", ""),
                    })

            # 元数据
            func_label = "轨道分析"
            for f in ORBITAL_FUNCTIONS:
                if f["key"] == self._current_func_key:
                    func_label = f["label"]
                    break
            metadata = {
                "分析功能": func_label,
                "文件": os.path.basename(self.current_file) if self.current_file else "未知",
                "数据行数": len(records),
            }
            return records, headers, metadata

        # 无表格数据时导出原始输出
        if self._last_output:
            return (
                [{"原始输出": self._last_output[:5000]}],
                ["原始输出"],
                {"分析功能": self._current_func_key}
            )
        return None
