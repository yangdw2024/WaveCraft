# -*- coding: utf-8 -*-
"""
键级分析模块 - 支持多种键级方法、网络图可视化、数据导出

对应 Multiwfn 主菜单 9 (Bond order analysis)。
支持方法：Mayer、Wiberg、Mulliken、Fuzzy、Laplacian、Deformation、PI(π)、多中心、NAO。
"""

import os
from collections import defaultdict

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QDoubleSpinBox, QStackedWidget, QTabWidget
)
from PyQt5.QtCore import Qt, QSortFilterProxyModel
from PyQt5.QtGui import QColor
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import matplotlib.cm as cm
import numpy as np

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.output_parser import OutputParser
from ..utils.export_utils import ExportButtonWidget

# 深色主题颜色常量
DARK_BG = "#161d27"
DARK_AXIS_BG = "#1e2630"
DARK_TEXT = "#c8d3e0"
DARK_GRID = "#2a3444"

# 键级方法详细说明（中文ToolTip）
BOND_METHOD_INFO = {
    "Mayer键级": (
        "Mayer键级是最常用的键级方法，基于密度矩阵计算。\n"
        "值越大表示键越强，通常单键≈1.0，双键≈2.0，三键≈3.0。\n"
        "对大多数体系都能给出合理的键级值，适用性广。\n"
        "Multiwfn菜单9 → 1"
    ),
    "Mayer键级(含模糊键)": (
        "在Mayer键级基础上加入模糊空间(fuzzy)贡献。\n"
        "适用于复杂成键环境，如金属配合物、弱相互作用等。\n"
        "通常比纯Mayer键级数值略大，能捕捉更多弱键信息。\n"
        "Multiwfn菜单9 → 2"
    ),
    "Wiberg键级": (
        "基于正交化基(NAO)的键级方法，常用于有机分子分析。\n"
        "由于使用了正交化基，数值受基组影响较小，稳定性好。\n"
        "对于有机分子通常与Mayer键级结果接近。\n"
        "Multiwfn菜单9 → 3"
    ),
    "Mulliken键级": (
        "基于Mulliken布居分析的键级，是最经典的键级定义之一。\n"
        "优点：计算简单快速。缺点：对基组依赖较大，\n"
        "扩散基组下可能出现负值或不合理的过大值。\n"
        "Multiwfn菜单9 → 4"
    ),
    "多中心键级": (
        "计算多中心键的键级，用于芳香性分析和多中心键研究。\n"
        "例如苯环的6中心键级，可定量衡量芳香性程度。\n"
        "基于AdNDP(自适应自然密度划分)方法实现。\n"
        "Multiwfn菜单9 → 5"
    ),
    "Fuzzy键级": (
        "基于模糊原子空间(fuzzy atom)的键级方法。\n"
        "使用Becke权重函数划分原子空间，对基组依赖小，\n"
        "物理意义清晰，适合比较不同基组下的键级。\n"
        "Multiwfn菜单9 → 7"
    ),
    "Laplacian键级": (
        "基于电子密度拉普拉斯(∇²ρ)的键级方法。\n"
        "将成键区域的电子密度拉普拉斯值积分作为键级度量。\n"
        "能反映键的共价/离子特征，对弱相互作用敏感。\n"
        "Multiwfn菜单9 → 8"
    ),
    "Deformation键级": (
        "基于变形密度(deformation density)的键级方法。\n"
        "变形密度 = 分子密度 - 自由原子密度之和，\n"
        "反映成键后电子密度的重新分布，可定量评估成键强度。\n"
        "Multiwfn菜单9 → 9"
    ),
    "PI键级(π键级)": (
        "分析π键贡献的键级方法，将总键级分解为σ和π部分。\n"
        "对于含双键/三键的体系特别有用，\n"
        "例如C=C双键的π键级≈1.0，C≡C三键的π键级≈2.0。\n"
        "Multiwfn菜单9 → 10"
    ),
    "NAO键级": (
        "基于自然原子轨道(NAO)的键级方法。\n"
        "使用自然布居分析(NPA)框架下的正交化轨道，\n"
        "数值稳定，对基组选择不太敏感，适合金属配合物。\n"
        "Multiwfn菜单9 → 11"
    ),
}

# 方法下拉框ToolTip
METHOD_COMBO_TOOLTIP = (
    "选择键级计算方法。对应 Multiwfn 主菜单 9 (Bond order analysis)。\n\n"
    "常用推荐：\n"
    "  · Mayer键级 — 最通用，适用大多数体系\n"
    "  · Wiberg键级 — 有机分子首选\n"
    "  · Fuzzy键级 — 对基组依赖小\n"
    "  · PI键级 — 分析π键贡献\n"
    "  · 多中心键级 — 芳香性分析\n\n"
    "选择后下方会显示该方法的详细说明。"
)


class BondAnalysisTab(QWidget):
    """键级分析模块 - 支持多种键级方法、网络图可视化、数据导出"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_bond_orders = []
        self._last_output = ""
        self._threshold = 0.05  # 最小键级阈值
        self.init_ui()

    def init_ui(self):
        """初始化界面布局"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        # ========== 顶部控制栏 ==========
        self._build_control_bar(main_layout)

        # ========== 方法说明标签 ==========
        self._build_method_desc(main_layout)

        # ========== 中间分栏：左侧图表 + 右侧表格 ==========
        self._build_content_area(main_layout)

        # ========== 底部：计算摘要 + 导出按钮 ==========
        self._build_bottom_bar(main_layout)

        self.setLayout(main_layout)

        # 初始占位图
        self._draw_placeholder()

    # ------------------------------------------------------------------ #
    #                        界面构建方法                                  #
    # ------------------------------------------------------------------ #

    def _build_control_bar(self, parent_layout):
        """构建顶部控制栏：方法选择 + 阈值过滤 + 计算按钮 + 进度条"""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)

        # 方法选择下拉框
        method_group = QGroupBox("键级计算方法")
        method_layout = QHBoxLayout(method_group)
        method_label = QLabel("方法:")
        self.method_combo = QComboBox()
        self.method_combo.addItems(list(BOND_METHOD_INFO.keys()))
        self.method_combo.setCurrentIndex(0)
        self.method_combo.setToolTip(METHOD_COMBO_TOOLTIP)
        self.method_combo.currentTextChanged.connect(self._update_method_desc)
        method_layout.addWidget(method_label)
        method_layout.addWidget(self.method_combo)
        control_layout.addWidget(method_group)

        # 最小键级阈值过滤
        threshold_group = QGroupBox("阈值过滤")
        threshold_layout = QHBoxLayout(threshold_group)
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 10.0)
        self.threshold_spin.setSingleStep(0.01)
        self.threshold_spin.setValue(0.05)
        self.threshold_spin.setDecimals(3)
        self.threshold_spin.setToolTip(
            "仅显示键级大于此值的键，用于过滤弱相互作用和噪声。\n"
            "默认0.05，设为0显示所有键。值越大过滤越严格。"
        )
        self.threshold_spin.valueChanged.connect(self._on_threshold_changed)
        threshold_layout.addWidget(QLabel("最小键级:"))
        threshold_layout.addWidget(self.threshold_spin)
        control_layout.addWidget(threshold_group)

        # 计算按钮
        self.calculate_btn = QPushButton("计算键级")
        self.calculate_btn.setStyleSheet(
            "background-color: #2ecc71; color: white; font-weight: bold; "
            "padding: 6px 16px; border-radius: 4px;"
        )
        self.calculate_btn.setToolTip(
            "使用选定方法计算所有原子对之间的键级。\n"
            "计算结果可通过阈值过滤，并以网络图/柱状图/表格形式展示。\n"
            "Multiwfn 路径：主菜单 9 → 选择键级模型 → 输出结果。"
        )
        self.calculate_btn.clicked.connect(self.on_calculate)
        control_layout.addWidget(self.calculate_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("计算进度指示。滚动模式表示正在计算中。")
        control_layout.addWidget(self.progress_bar)

        control_layout.addStretch()
        parent_layout.addLayout(control_layout)

    def _build_method_desc(self, parent_layout):
        """构建方法说明标签"""
        self.method_desc_label = QLabel(BOND_METHOD_INFO.get("Mayer键级", ""))
        self.method_desc_label.setWordWrap(True)
        self.method_desc_label.setStyleSheet(
            "color: #a0b0c0; font-size: 11px; padding: 4px 8px; "
            "background-color: #1a2332; border-radius: 4px; border: 1px solid #2a3a4a;"
        )
        self.method_desc_label.setToolTip("当前键级方法的详细说明")
        parent_layout.addWidget(self.method_desc_label)

    def _build_content_area(self, parent_layout):
        """构建中间分栏：左侧网络图/柱状图 + 右侧数据表格"""
        splitter = QSplitter(Qt.Horizontal)

        # --- 左侧：图表区域（网络图/柱状图切换） ---
        chart_widget = QWidget()
        chart_layout = QVBoxLayout(chart_widget)
        chart_layout.setContentsMargins(0, 0, 0, 0)

        # 图表切换标签页
        self.chart_tabs = QTabWidget()
        self.chart_tabs.setToolTip("切换网络图和柱状图两种可视化方式")

        # 网络图
        self.network_fig = Figure(figsize=(8, 6), dpi=100)
        self.network_fig.patch.set_facecolor(DARK_BG)
        self.network_canvas = FigureCanvas(self.network_fig)
        self.network_canvas.setToolTip(
            "键级网络图：节点=原子，边=键级。\n"
            "节点大小正比于原子序数，边粗细正比于键级值，\n"
            "边颜色根据键级大小渐变（蓝→红）。"
        )
        self.chart_tabs.addTab(self.network_canvas, "网络图")

        # 柱状图
        self.bar_fig = Figure(figsize=(8, 6), dpi=100)
        self.bar_fig.patch.set_facecolor(DARK_BG)
        self.bar_canvas = FigureCanvas(self.bar_fig)
        self.bar_canvas.setToolTip(
            "键级柱状图：按键级值从大到小排列。\n"
            "颜色标识键的强度分类：红色=双键及以上，橙色=单键，蓝色=部分键，灰色=弱相互作用。"
        )
        self.chart_tabs.addTab(self.bar_canvas, "柱状图")

        chart_layout.addWidget(self.chart_tabs)
        splitter.addWidget(chart_widget)

        # --- 右侧：数据表格 ---
        table_group = QGroupBox("键级数据")
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["原子1", "原子2", "键级值"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSortingEnabled(True)  # 允许按列排序
        self.table.setToolTip(
            "原子对之间的键级计算结果，可按键级排序。\n"
            "点击列标题可升序/降序排列。\n"
            "键级≥2.0 通常为双键/三键，1.0~2.0 为单键，\n"
            "0.5~1.0 为部分键，<0.5 多为弱相互作用。"
        )
        table_layout.addWidget(self.table)

        # 统计信息
        self.stats_label = QLabel("")
        self.stats_label.setWordWrap(True)
        self.stats_label.setStyleSheet("color: #a0b0c0; font-size: 11px; padding: 2px;")
        self.stats_label.setToolTip("当前数据的统计摘要")
        table_layout.addWidget(self.stats_label)

        splitter.addWidget(table_group)
        splitter.setSizes([600, 400])

        parent_layout.addWidget(splitter)

    def _build_bottom_bar(self, parent_layout):
        """构建底部：计算摘要 + 导出按钮组"""
        bottom_layout = QHBoxLayout()

        # 计算摘要
        summary_group = QGroupBox("计算摘要")
        summary_layout = QHBoxLayout(summary_group)
        self.summary_label = QLabel("就绪 - 请选择方法并点击计算")
        self.summary_label.setStyleSheet("color: #c8d3e0; font-size: 12px;")
        self.summary_label.setToolTip("显示当前分析状态、方法、键数等摘要信息")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        bottom_layout.addWidget(summary_group)

        # 导出按钮组
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="bond_orders"
        )
        self.export_widget.setToolTip("将键级数据导出为 TXT/CSV/Excel 格式")
        bottom_layout.addWidget(self.export_widget)

        parent_layout.addLayout(bottom_layout)

    # ------------------------------------------------------------------ #
    #                        辅助方法                                      #
    # ------------------------------------------------------------------ #

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path

    def _update_method_desc(self, method_name):
        """更新方法说明标签"""
        desc = BOND_METHOD_INFO.get(method_name, "")
        self.method_desc_label.setText(desc)

    def _on_threshold_changed(self, value):
        """阈值变化时重新过滤并刷新显示"""
        self._threshold = value
        if self._last_bond_orders:
            filtered = self._filter_bond_orders(self._last_bond_orders)
            self.update_table(filtered)
            self.plot_network(filtered)
            self.plot_bar_chart(filtered)
            self._update_stats(filtered)

    def _filter_bond_orders(self, bond_orders):
        """根据阈值过滤键级数据"""
        return [bo for bo in bond_orders if bo["bond_order"] >= self._threshold]

    def _classify_bond(self, order):
        """按键级值分类键型"""
        if order >= 3.0:
            return "三键"
        elif order >= 2.0:
            return "双键"
        elif order >= 1.0:
            return "单键"
        elif order >= 0.5:
            return "部分键"
        else:
            return "弱相互作用"

    def _update_stats(self, bond_orders):
        """更新统计信息标签"""
        if not bond_orders:
            self.stats_label.setText("无数据")
            return
        values = [bo["bond_order"] for bo in bond_orders]
        max_bo = max(values)
        min_bo = min(values)
        avg_bo = sum(values) / len(values)
        # 按键型统计
        bond_types = defaultdict(int)
        for bo in bond_orders:
            bond_types[self._classify_bond(bo["bond_order"])] += 1
        type_str = "  ".join(f"{k}:{v}" for k, v in sorted(bond_types.items(), key=lambda x: -x[1]))
        self.stats_label.setText(
            f"总键数: {len(bond_orders)} | 最大: {max_bo:.3f} | "
            f"最小: {min_bo:.3f} | 平均: {avg_bo:.3f}\n{type_str}"
        )

    def _get_export_data(self):
        """为导出功能提供数据"""
        if not self._last_bond_orders:
            if self._last_output:
                return [{"output": self._last_output}], ["output"], {"键级方法": self.method_combo.currentText()}
            return None

        filtered = self._filter_bond_orders(self._last_bond_orders)
        records = []
        for bo in filtered:
            records.append({
                "atom1": bo["atom1"],
                "atom2": bo["atom2"],
                "bond_order": bo["bond_order"],
                "bond_type": self._classify_bond(bo["bond_order"]),
            })
        metadata = {
            "键级方法": self.method_combo.currentText(),
            "原子对数量": len(filtered),
            "最小键级阈值": self._threshold,
            "最大键级": max(bo["bond_order"] for bo in filtered) if filtered else 0,
            "平均键级": round(sum(bo["bond_order"] for bo in filtered) / len(filtered), 4) if filtered else 0,
        }
        return records, ["atom1", "atom2", "bond_order", "bond_type"], metadata

    def _parse_atom_info_from_bond(self, atom_str):
        """从原子标签如 '1(C)' 中解析原子序号和元素符号，返回 (index, element)"""
        import re
        m = re.match(r"(\d+)\(([A-Za-z]+)\s*\)", atom_str)
        if m:
            return int(m.group(1)), m.group(2)
        m = re.match(r"Atom(\d+)", atom_str)
        if m:
            return int(m.group(1)), "?"
        return 0, "?"

    def _get_atomic_number(self, element):
        """根据元素符号获取原子序数（用于节点大小）"""
        element_numbers = {
            "H": 1, "He": 2, "Li": 3, "Be": 4, "B": 5, "C": 6, "N": 7, "O": 8,
            "F": 9, "Ne": 10, "Na": 11, "Mg": 12, "Al": 13, "Si": 14, "P": 15,
            "S": 16, "Cl": 17, "Ar": 18, "K": 19, "Ca": 20, "Sc": 21, "Ti": 22,
            "V": 23, "Cr": 24, "Mn": 25, "Fe": 26, "Co": 27, "Ni": 28, "Cu": 29,
            "Zn": 30, "Ga": 31, "Ge": 32, "As": 33, "Se": 34, "Br": 35, "Kr": 36,
            "Rb": 37, "Sr": 38, "Y": 39, "Zr": 40, "Nb": 41, "Mo": 42, "Ru": 44,
            "Rh": 45, "Pd": 46, "Ag": 47, "Cd": 48, "In": 49, "Sn": 50, "Sb": 51,
            "Te": 52, "I": 53, "Xe": 54, "Cs": 55, "Ba": 56, "La": 57, "Pt": 78,
            "Au": 79, "Hg": 80, "Pb": 82, "Bi": 83,
        }
        return element_numbers.get(element, 6)

    def _draw_placeholder(self):
        """绘制初始占位图"""
        for fig, canvas in [(self.network_fig, self.network_canvas),
                           (self.bar_fig, self.bar_canvas)]:
            fig.clear()
            ax = fig.add_subplot(111)
            ax.set_facecolor(DARK_AXIS_BG)
            ax.text(
                0.5, 0.5, "请选择方法并点击计算",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=14, color=DARK_TEXT, alpha=0.7
            )
            ax.set_xticks([])
            ax.set_yticks([])
            for spine in ax.spines.values():
                spine.set_color(DARK_GRID)
            canvas.draw()

    # ------------------------------------------------------------------ #
    #                        计算逻辑                                      #
    # ------------------------------------------------------------------ #

    def on_calculate(self):
        """启动键级计算"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        method_name = self.method_combo.currentText()
        try:
            commands = InputGenerator.generate_bond_order_commands(method_name)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return
        work_dir = os.path.dirname(self.current_file)

        self.calculate_btn.setEnabled(False)
        self.calculate_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.summary_label.setText(f"正在计算 {method_name} ...")

        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"键级分析: {method_name}"
        )
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_finished(self, result):
        """计算完成回调"""
        try:
            output = result.get("output", "")
            self._last_output = output
            bond_orders = OutputParser.parse_bond_orders(output)
            self._last_bond_orders = bond_orders

            if bond_orders:
                filtered = self._filter_bond_orders(bond_orders)
                self.plot_network(filtered)
                self.plot_bar_chart(filtered)
                self.update_table(filtered)
                self._update_stats(filtered)

                method = self.method_combo.currentText()
                total = len(bond_orders)
                shown = len(filtered)
                if shown < total:
                    self.summary_label.setText(
                        f"{method} | 共{total}条键，过滤后显示{shown}条 (阈值≥{self._threshold})"
                    )
                else:
                    self.summary_label.setText(f"{method} | {total}条键")
            else:
                QMessageBox.warning(
                    self, "警告",
                    "未解析到键级数据\n请检查Multiwfn输出或尝试其他方法"
                )
                self.summary_label.setText("计算完成，但未解析到数据")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
        finally:
            self.calculate_btn.setEnabled(True)
            self.calculate_btn.setText("计算键级")
            self.progress_bar.setVisible(False)
            self._worker = None

    def _on_failed(self, error_msg):
        """计算失败回调"""
        QMessageBox.critical(self, "计算失败", error_msg[:500])
        self.calculate_btn.setEnabled(True)
        self.calculate_btn.setText("计算键级")
        self.progress_bar.setVisible(False)
        self.summary_label.setText("计算失败")
        self._worker = None

    # ------------------------------------------------------------------ #
    #                        网络图绘制                                    #
    # ------------------------------------------------------------------ #

    def plot_network(self, bond_orders):
        """
        绘制键级网络图：
        - 原子为节点，节点大小正比于原子序数
        - 键级为边，边的粗细正比于键级值
        - 边颜色根据键级大小渐变
        - 深色主题适配
        """
        self.network_fig.clear()
        ax = self.network_fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        self.network_fig.patch.set_facecolor(DARK_BG)

        if not bond_orders:
            ax.text(0.5, 0.5, "无数据", ha="center", va="center",
                    transform=ax.transAxes, fontsize=14, color=DARK_TEXT)
            ax.set_xticks([])
            ax.set_yticks([])
            self.network_canvas.draw()
            return

        # 收集所有原子信息
        atoms = {}  # idx -> (element, atomic_num)
        edges = []  # (idx1, idx2, bond_order)

        for bo in bond_orders:
            idx1, elem1 = self._parse_atom_info_from_bond(bo["atom1"])
            idx2, elem2 = self._parse_atom_info_from_bond(bo["atom2"])
            if idx1 not in atoms:
                atoms[idx1] = (elem1, self._get_atomic_number(elem1))
            if idx2 not in atoms:
                atoms[idx2] = (elem2, self._get_atomic_number(elem2))
            edges.append((idx1, idx2, bo["bond_order"]))

        if not atoms:
            ax.text(0.5, 0.5, "无法解析原子信息", ha="center", va="center",
                    transform=ax.transAxes, fontsize=14, color=DARK_TEXT)
            self.network_canvas.draw()
            return

        # 使用弹簧布局算法排列节点（纯numpy实现，无需networkx）
        n_atoms = len(atoms)
        atom_indices = sorted(atoms.keys())
        idx_to_pos = {idx: i for i, idx in enumerate(atom_indices)}

        # 初始化位置：使用圆形布局作为起始
        positions = np.zeros((n_atoms, 2))
        for i in range(n_atoms):
            angle = 2 * np.pi * i / n_atoms
            positions[i] = [np.cos(angle), np.sin(angle)]

        # 简易力导向布局（弹簧模型）
        # 迭代优化节点位置
        adj = np.zeros((n_atoms, n_atoms))
        for idx1, idx2, bo in edges:
            i, j = idx_to_pos[idx1], idx_to_pos[idx2]
            adj[i][j] = bo
            adj[j][i] = bo

        k_spring = 0.3  # 弹簧常数
        k_repulse = 0.5  # 排斥常数
        dt = 0.1  # 步长
        n_iter = 80

        for _ in range(n_iter):
            forces = np.zeros((n_atoms, 2))
            # 排斥力（所有节点对之间）
            for i in range(n_atoms):
                for j in range(i + 1, n_atoms):
                    diff = positions[i] - positions[j]
                    dist = max(np.linalg.norm(diff), 0.01)
                    f_repulse = k_repulse / (dist * dist) * (diff / dist)
                    forces[i] += f_repulse
                    forces[j] -= f_repulse
            # 弹簧力（连接的节点对之间）
            for idx1, idx2, bo in edges:
                i, j = idx_to_pos[idx1], idx_to_pos[idx2]
                diff = positions[j] - positions[i]
                dist = max(np.linalg.norm(diff), 0.01)
                ideal_len = 1.0 / max(bo, 0.1)
                f_spring = k_spring * (dist - ideal_len) * (diff / dist)
                forces[i] += f_spring
                forces[j] -= f_spring
            # 更新位置
            positions += forces * dt
            # 限制位移范围
            positions = np.clip(positions, -3, 3)

        # ---- 绘制边 ----
        if edges:
            bo_values = [e[2] for e in edges]
            bo_min = min(bo_values)
            bo_max = max(bo_values)
            bo_range = bo_max - bo_min if bo_max > bo_min else 1.0

            # 边颜色渐变：蓝色(弱) -> 红色(强)
            cmap = cm.get_cmap("coolwarm")
            norm = Normalize(vmin=bo_min, vmax=bo_max)

            for idx1, idx2, bo in edges:
                i, j = idx_to_pos[idx1], idx_to_pos[idx2]
                x = [positions[i][0], positions[j][0]]
                y = [positions[i][1], positions[j][1]]
                # 边粗细：0.5 ~ 4.0，正比于键级
                lw = 0.5 + 3.5 * (bo - bo_min) / bo_range
                color = cmap(norm(bo))
                ax.plot(x, y, color=color, linewidth=lw, alpha=0.85, zorder=1)

        # ---- 绘制节点 ----
        for idx in atom_indices:
            pos_i = idx_to_pos[idx]
            elem, z = atoms[idx]
            # 节点大小正比于原子序数：30 ~ 300
            node_size = 30 + z * 8
            ax.scatter(
                positions[pos_i][0], positions[pos_i][1],
                s=node_size, c="#4a9eff", edgecolors="white",
                linewidths=0.8, zorder=2, alpha=0.9
            )
            # 原子标签
            ax.text(
                positions[pos_i][0], positions[pos_i][1],
                f"{idx}({elem})",
                ha="center", va="center", fontsize=7,
                color="white", fontweight="bold", zorder=3
            )

        # 颜色条
        if edges and len(edges) > 1:
            sm = cm.ScalarMappable(cmap=cmap, norm=norm)
            sm.set_array([])
            cbar = self.network_fig.colorbar(sm, ax=ax, shrink=0.6, pad=0.02)
            cbar.set_label("键级值", color=DARK_TEXT, fontsize=10)
            cbar.ax.yaxis.set_tick_params(color=DARK_TEXT)
            for label in cbar.ax.get_yticklabels():
                label.set_color(DARK_TEXT)

        method = self.method_combo.currentText()
        ax.set_title(f"{method} - 键级网络图", color=DARK_TEXT, fontsize=13, pad=10)
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)

        self.network_fig.tight_layout()
        self.network_canvas.draw()

    # ------------------------------------------------------------------ #
    #                        柱状图绘制                                    #
    # ------------------------------------------------------------------ #

    def plot_bar_chart(self, bond_orders):
        """
        绘制键级水平柱状图：
        - 按键级从大到小排列
        - 颜色编码键型分类
        - 深色主题适配
        """
        self.bar_fig.clear()
        ax = self.bar_fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        self.bar_fig.patch.set_facecolor(DARK_BG)

        if not bond_orders:
            ax.text(0.5, 0.5, "无数据", ha="center", va="center",
                    transform=ax.transAxes, fontsize=14, color=DARK_TEXT)
            ax.set_xticks([])
            ax.set_yticks([])
            self.bar_canvas.draw()
            return

        # 按键级降序排列
        sorted_bonds = sorted(bond_orders, key=lambda x: x["bond_order"], reverse=True)
        # 限制显示数量，避免图太拥挤
        max_display = 50
        if len(sorted_bonds) > max_display:
            sorted_bonds = sorted_bonds[:max_display]

        labels = [f"{bo['atom1']}-{bo['atom2']}" for bo in sorted_bonds]
        values = [bo["bond_order"] for bo in sorted_bonds]

        # 根据键级分类着色
        color_map = {
            "三键": "#e74c3c",
            "双键": "#e67e22",
            "单键": "#f1c40f",
            "部分键": "#3498db",
            "弱相互作用": "#7f8c8d",
        }
        colors = [color_map.get(self._classify_bond(v), "#95a5a6") for v in values]

        y_pos = np.arange(len(labels))
        bars = ax.barh(y_pos, values, color=colors, edgecolor="#3a4a5a", linewidth=0.5, height=0.7)

        # 在柱状条末端标注数值
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_width() + 0.02,
                bar.get_y() + bar.get_height() / 2.,
                f"{value:.3f}", va="center", fontsize=8, color=DARK_TEXT
            )

        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, fontsize=8, color=DARK_TEXT)
        ax.set_xlabel("键级", fontsize=11, color=DARK_TEXT)
        method = self.method_combo.currentText()
        n_total = len(bond_orders)
        n_shown = len(sorted_bonds)
        title = f"{method} - 键级柱状图"
        if n_shown < n_total:
            title += f" (显示前{n_shown}条)"
        ax.set_title(title, color=DARK_TEXT, fontsize=13, pad=10)
        ax.grid(True, axis="x", alpha=0.2, color=DARK_GRID)
        ax.invert_yaxis()  # 最大值在顶部

        # 刻度颜色
        ax.tick_params(axis="x", colors=DARK_TEXT)
        ax.tick_params(axis="y", colors=DARK_TEXT)
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)

        # 图例
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="#e74c3c", edgecolor="#3a4a5a", label="三键 (≥3.0)"),
            Patch(facecolor="#e67e22", edgecolor="#3a4a5a", label="双键 (2.0~3.0)"),
            Patch(facecolor="#f1c40f", edgecolor="#3a4a5a", label="单键 (1.0~2.0)"),
            Patch(facecolor="#3498db", edgecolor="#3a4a5a", label="部分键 (0.5~1.0)"),
            Patch(facecolor="#7f8c8d", edgecolor="#3a4a5a", label="弱相互作用 (<0.5)"),
        ]
        ax.legend(
            handles=legend_elements, loc="lower right",
            fontsize=8, facecolor=DARK_AXIS_BG, edgecolor=DARK_GRID,
            labelcolor=DARK_TEXT
        )

        self.bar_fig.tight_layout()
        self.bar_canvas.draw()

    # ------------------------------------------------------------------ #
    #                        数据表格                                      #
    # ------------------------------------------------------------------ #

    def update_table(self, bond_orders):
        """
        更新键级数据表格，支持按键级排序
        列：原子1、原子2、键级值
        """
        # 按键级降序排列
        sorted_bonds = sorted(bond_orders, key=lambda x: x["bond_order"], reverse=True)

        self.table.setSortingEnabled(False)  # 先关闭排序，填充数据时更快
        self.table.setRowCount(len(sorted_bonds))

        for i, bo in enumerate(sorted_bonds):
            # 原子1
            item1 = QTableWidgetItem(bo["atom1"])
            item1.setFlags(item1.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 0, item1)

            # 原子2
            item2 = QTableWidgetItem(bo["atom2"])
            item2.setFlags(item2.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(i, 1, item2)

            # 键级值 - 使用数值型排序
            item3 = QTableWidgetItem()
            item3.setData(Qt.DisplayRole, f"{bo['bond_order']:.4f}")
            item3.setData(Qt.UserRole, bo["bond_order"])  # 存储原始数值用于排序
            item3.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item3.setFlags(item3.flags() & ~Qt.ItemIsEditable)

            # 根据键级值设置行背景色
            bo_val = bo["bond_order"]
            if bo_val >= 2.0:
                bg_color = QColor(231, 76, 60, 40)    # 红色半透明
            elif bo_val >= 1.0:
                bg_color = QColor(241, 196, 15, 40)    # 黄色半透明
            elif bo_val >= 0.5:
                bg_color = QColor(52, 152, 219, 40)    # 蓝色半透明
            else:
                bg_color = QColor(149, 165, 166, 25)   # 灰色半透明

            for col in range(3):
                item = self.table.item(i, col)
                if item:
                    item.setBackground(bg_color)

            self.table.setItem(i, 2, item3)

        self.table.setSortingEnabled(True)  # 重新启用排序

    # ------------------------------------------------------------------ #
    #                        表格排序支持                                   #
    # ------------------------------------------------------------------ #

    def _sort_table_by_column(self, column):
        """表格排序：按指定列排序"""
        self.table.sortItems(column)
