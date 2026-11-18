#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
电荷分析模块 - 对应 Multiwfn 主菜单 7 (Population analysis)

支持16种原子电荷计算方法，提供柱状图可视化与数据导出功能。
"""

import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox, QProgressBar,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter,
    QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.output_parser import OutputParser
from ..utils.export_utils import ExportButtonWidget


# ============================================================
# 16种电荷计算方法的详细中文说明
# ============================================================
CHARGE_METHOD_INFO = {
    "Mulliken": (
        "Mulliken电荷: 基于基函数布居划分的原子电荷，计算速度快但对基组敏感，"
        "建议用于定性分析。在极化基组和弥散基组下可能出现不合理结果，"
        "不适合需要精确定量电荷的场景。"
    ),
    "Lowdin": (
        "Lowdin电荷: 基于Lowdin对称正交化布居分析的原子电荷，"
        "比Mulliken电荷对基组选择更稳定，减少了基组依赖性，"
        "适合在中等基组下获得较为合理的电荷分布。"
    ),
    "Hirshfeld": (
        "Hirshfeld电荷: 基于自由原子密度比例划分的原子电荷，物理意义明确，"
        "适合比较不同分子间的电荷转移。对基组不太敏感，"
        "但通常低估电荷转移程度，数值偏小。"
    ),
    "Hirshfeld-I": (
        "Hirshfeld-I电荷: 迭代Hirshfeld电荷，通过自洽迭代修正自由原子参考密度，"
        "克服了Hirshfeld电荷低估电荷转移的问题，精度更高，"
        "推荐用于需要物理意义明确且数值合理的场景。"
    ),
    "VDD": (
        "VDD电荷: Voronoi变形密度电荷，基于Voronoi多面体空间划分，"
        "将分子空间按最近原子原则分配给各原子。对基组不敏感，"
        "适合大分子的电荷分析，但空间划分方式较任意。"
    ),
    "Becke": (
        "Becke电荷: 基于Becke多网格权重函数划分的原子电荷，"
        "使用模糊原子空间定义，避免了VDD中硬边界的任意性。"
        "对基组较稳定，适合一般性电荷分析。"
    ),
    "ADCH": (
        "ADCH电荷: 原子偶极矩校正Hirshfeld电荷，精度高，"
        "推荐用于需要精确电荷值的场景。通过引入原子偶极矩修正项，"
        "使电荷能够更好地重现分子静电势，是综合性能最优的方法之一。"
    ),
    "CHELPG": (
        "CHELPG电荷: 基于静电势拟合(Charge from Electrostatic Potential using Grid)的原子电荷，"
        "在分子周围三维网格点上拟合静电势，适合分子间相互作用模拟、"
        "溶剂化计算和力场参数化。对网格密度敏感。"
    ),
    "MK": (
        "MK电荷: Merz-Kollman静电势拟合电荷，在Connolly分子表面上拟合静电势，"
        "是CHELPG的二维曲面版本。计算速度比CHELPG快，"
        "广泛用于分子动力学力场参数化(如AMBER力场)。"
    ),
    "AIM": (
        "AIM电荷: 基于量子原子拓扑理论(Bader划分)的原子电荷，"
        "通过零通量面定义原子盆，物理基础最严格。"
        "计算量较大，需要高精度网格积分，适合理论研究。"
    ),
    "CM5": (
        "CM5电荷: Charge Model 5，对Hirshfeld电荷进行参数化修正，"
        "利用大量参考数据拟合经验参数，显著改善了Hirshfeld电荷的精度。"
        "适合需要与实验偶极矩吻合的场合，推荐用于热力学计算。"
    ),
    "EEM": (
        "EEM电荷: 电负性均衡方法(Electronegativity Equilibration Method)计算的原子电荷，"
        "基于电负性均衡原理和经验参数，计算速度极快。"
        "适合大分子快速估算，但精度受参数化质量限制。"
    ),
    "SCPA": (
        "SCPA电荷: Ros-Schuit修正的Mulliken布居分析(Symmetrized Cumulative Population Analysis)，"
        "对Mulliken布居进行对称化处理，改善了部分基组下的不合理结果，"
        "在中等基组下表现较好。"
    ),
    "RESP": (
        "RESP电荷: 约束静电势拟合电荷(Restrained Electrostatic Potential)，"
        "在拟合静电势的同时加入约束条件避免非物理电荷，"
        "广泛用于分子动力学模拟(如AMBER RESP力场)，是力场参数化的标准方法。"
    ),
    "Gasteiger": (
        "Gasteiger电荷: Gasteiger-PEOE迭代部分均衡轨道电负性电荷，"
        "纯经验方法，不需要波函数信息，计算速度极快。"
        "广泛用于药物分子和QSAR研究，但精度有限。"
    ),
    "MBIS": (
        "MBIS电荷: 最小基迭代Stockholder电荷(Minimal Basis Iterative Stockholder)，"
        "使用最小基函数迭代求解Stockholder划分，兼具Hirshfeld的物理意义和"
        "Hirshfeld-I的精度优势，是近年来的推荐方法。"
    ),
}

# 16种方法在界面中的排列顺序
CHARGE_METHODS_ORDER = [
    "Mulliken", "Lowdin", "Hirshfeld", "Hirshfeld-I",
    "VDD", "Becke", "ADCH", "CHELPG", "MK",
    "AIM", "CM5", "EEM", "SCPA", "RESP", "Gasteiger", "MBIS",
]

# 深色主题颜色常量
_DARK_BG_FIG = "#161d27"       # 图形背景
_DARK_BG_AX = "#1e2630"        # 坐标轴背景
_DARK_TEXT = "#e2e8f0"         # 文字颜色
_DARK_GRID = "#334155"         # 网格线颜色
_COLOR_POS = "#3b82f6"         # 正电荷柱颜色(蓝)
_COLOR_NEG = "#ef4444"         # 负电荷柱颜色(红)
_COLOR_ZERO = "#94a3b8"        # 零电荷柱颜色(灰)
_BAR_EDGE = "#475569"          # 柱状图边框颜色


class ChargeAnalysisTab(QWidget):
    """电荷分析标签页，对应 Multiwfn 主菜单 7。"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_charges = []    # 上次解析的电荷列表
        self._last_output = ""     # 上次计算的原始输出
        self._init_ui()

    # ------------------------------------------------------------------
    # 界面构建
    # ------------------------------------------------------------------
    def _init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        # === 顶部控制栏 ===
        self._build_control_bar(main_layout)

        # === 方法说明标签 ===
        self._build_method_desc(main_layout)

        # === 中间分栏：左侧柱状图 + 右侧数据表格 ===
        self._build_center_splitter(main_layout)

        # === 底部：计算摘要 + 导出按钮组 ===
        self._build_bottom_bar(main_layout)

        self.setLayout(main_layout)

        # 初始化空图表
        self._draw_placeholder()

    def _build_control_bar(self, parent_layout):
        """构建顶部控制栏：方法选择、计算按钮、进度条。"""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)

        # 方法选择区域
        method_group = QGroupBox("电荷计算方法")
        method_layout = QHBoxLayout(method_group)
        method_layout.setSpacing(8)

        method_label = QLabel("方法:")
        method_label.setStyleSheet("color: #cbd5e1;")
        method_layout.addWidget(method_label)

        self.method_combo = QComboBox()
        self.method_combo.addItems(CHARGE_METHODS_ORDER)
        self.method_combo.setMinimumWidth(140)
        self.method_combo.setToolTip(
            "选择原子电荷计算方法（对应 Multiwfn 主菜单 7）。\n"
            "下方会显示该方法的详细说明；\n"
            "计算结果可导出为 TXT / CSV / Excel。"
        )
        # 下拉框中每项也设置独立 tooltip
        for i, method in enumerate(CHARGE_METHODS_ORDER):
            self.method_combo.setItemData(i, CHARGE_METHOD_INFO.get(method, ""), Qt.ToolTipRole)
        self.method_combo.currentTextChanged.connect(self._on_method_changed)
        method_layout.addWidget(self.method_combo)

        control_layout.addWidget(method_group)

        # 计算按钮
        self.calculate_btn = QPushButton("计算电荷")
        self.calculate_btn.setFixedHeight(32)
        self.calculate_btn.setStyleSheet(
            "QPushButton { background-color: #e74c3c; color: white; font-weight: bold; "
            "border-radius: 4px; padding: 0 16px; }"
            "QPushButton:hover { background-color: #c0392b; }"
            "QPushButton:disabled { background-color: #6b7280; }"
        )
        self.calculate_btn.setToolTip(
            "使用选定方法计算所有原子的电荷。\n"
            "Multiwfn 路径：主菜单 7 → 选择电荷模型 → 输出结果。"
        )
        self.calculate_btn.clicked.connect(self._on_calculate)
        control_layout.addWidget(self.calculate_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setVisible(False)
        self.progress_bar.setToolTip("计算进度指示，滚动模式表示正在计算中。")
        control_layout.addWidget(self.progress_bar)

        control_layout.addStretch()
        parent_layout.addLayout(control_layout)

    def _build_method_desc(self, parent_layout):
        """构建方法说明标签，选择方法后显示详细说明。"""
        desc_frame = QFrame()
        desc_frame.setFrameShape(QFrame.StyledPanel)
        desc_frame.setStyleSheet(
            "QFrame { background-color: #1e293b; border: 1px solid #334155; "
            "border-radius: 4px; padding: 6px; }"
        )
        desc_layout = QVBoxLayout(desc_frame)
        desc_layout.setContentsMargins(10, 6, 10, 6)

        self.method_desc_label = QLabel(CHARGE_METHOD_INFO.get("Mulliken", ""))
        self.method_desc_label.setWordWrap(True)
        self.method_desc_label.setStyleSheet(
            "color: #93c5fd; font-size: 12px; line-height: 1.5;"
        )
        self.method_desc_label.setToolTip("当前电荷计算方法的详细说明")
        desc_layout.addWidget(self.method_desc_label)

        parent_layout.addWidget(desc_frame)

    def _build_center_splitter(self, parent_layout):
        """构建中间分栏：左侧柱状图 + 右侧数据表格。"""
        splitter = QSplitter(Qt.Horizontal)

        # --- 左侧：柱状图 ---
        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor(_DARK_BG_FIG)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.canvas.setToolTip("原子电荷柱状图可视化区域（深色主题）")
        splitter.addWidget(self.canvas)

        # --- 右侧：数据表格 ---
        table_group = QGroupBox("电荷数据")
        table_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        table_layout = QVBoxLayout(table_group)

        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["序号", "原子", "电荷值"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(
            "QTableWidget { background-color: #1e2630; color: #e2e8f0; "
            "gridline-color: #334155; alternate-background-color: #243040; }"
            "QHeaderView::section { background-color: #334155; color: #e2e8f0; "
            "font-weight: bold; border: 1px solid #475569; padding: 4px; }"
        )
        self.table.setToolTip(
            "各原子的电荷计算结果。\n"
            "正值表示失去电子（缺电子），负值表示得到电子（富电子）。\n"
            "数据可导出为 TXT / CSV / Excel。"
        )
        table_layout.addWidget(self.table)

        # 总电荷标签
        self.total_label = QLabel("总电荷: --")
        self.total_label.setStyleSheet(
            "color: #fbbf24; font-size: 13px; font-weight: bold; padding: 4px;"
        )
        self.total_label.setToolTip("所有原子电荷的代数和，理想情况下应接近分子总电荷。")
        table_layout.addWidget(self.total_label)

        splitter.addWidget(table_group)
        splitter.setSizes([650, 350])

        parent_layout.addWidget(splitter, stretch=1)

    def _build_bottom_bar(self, parent_layout):
        """构建底部栏：计算摘要 + 导出按钮组。"""
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(12)

        # 计算摘要
        summary_group = QGroupBox("计算摘要")
        summary_group.setStyleSheet(
            "QGroupBox { color: #e2e8f0; font-weight: bold; }"
        )
        summary_inner = QHBoxLayout(summary_group)
        self.summary_label = QLabel("就绪 — 请选择方法并点击计算")
        self.summary_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        self.summary_label.setToolTip("显示当前分析状态、使用方法和原子数等摘要信息")
        summary_inner.addWidget(self.summary_label)
        bottom_layout.addWidget(summary_group, stretch=1)

        # 导出按钮组
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="charges"
        )
        self.export_widget.setToolTip("将电荷数据导出为 TXT / CSV / Excel 格式")
        bottom_layout.addWidget(self.export_widget)

        parent_layout.addLayout(bottom_layout)

    # ------------------------------------------------------------------
    # 图表绘制
    # ------------------------------------------------------------------
    def _draw_placeholder(self):
        """绘制空状态占位文字。"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(_DARK_BG_AX)
        ax.text(
            0.5, 0.5, "请选择方法并点击计算",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=16, color=_DARK_TEXT, alpha=0.5
        )
        # 隐藏坐标轴刻度
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_visible(False)
        self.fig.tight_layout()
        self.canvas.draw()

    def _plot_charges(self, charges):
        """绘制电荷柱状图（深色主题）。"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        # 深色主题背景
        ax.set_facecolor(_DARK_BG_AX)

        # 提取数据
        indices = [c["index"] for c in charges]
        values = [c["charge"] for c in charges]
        elements = [c["element"] for c in charges]

        # 构建原子标签：如 "1(C)" "2(O)"
        labels = [f"{idx}({elem})" for idx, elem in zip(indices, elements)]

        # 根据电荷正负设置柱颜色
        colors = []
        for v in values:
            if v > 0.0005:
                colors.append(_COLOR_POS)
            elif v < -0.0005:
                colors.append(_COLOR_NEG)
            else:
                colors.append(_COLOR_ZERO)

        # 绘制柱状图
        x_pos = np.arange(len(indices))
        bars = ax.bar(
            x_pos, values, color=colors,
            edgecolor=_BAR_EDGE, linewidth=0.6, width=0.7
        )

        # 在柱顶部/底部标注元素符号
        for bar, elem, val in zip(bars, elements, values):
            height = bar.get_height()
            va = "bottom" if height >= 0 else "top"
            offset = 0.002 if height >= 0 else -0.002
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height + offset,
                elem,
                ha="center", va=va,
                fontsize=8, color=_DARK_TEXT, fontweight="bold"
            )

        # 零线
        ax.axhline(y=0, color=_DARK_TEXT, linewidth=0.8, alpha=0.5)

        # 坐标轴标签与标题
        method_name = self.method_combo.currentText()
        ax.set_xlabel("原子", fontsize=12, color=_DARK_TEXT)
        ax.set_ylabel("电荷值 (e)", fontsize=12, color=_DARK_TEXT)
        ax.set_title(f"{method_name} 原子电荷", fontsize=14, color=_DARK_TEXT, fontweight="bold")

        # 设置横轴刻度
        ax.set_xticks(x_pos)
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=8, color=_DARK_TEXT)

        # 网格线
        ax.grid(True, axis="y", color=_DARK_GRID, alpha=0.6, linestyle="--", linewidth=0.5)
        ax.tick_params(axis="y", colors=_DARK_TEXT, labelsize=9)
        ax.tick_params(axis="x", colors=_DARK_TEXT)

        # 边框颜色
        for spine in ax.spines.values():
            spine.set_color(_DARK_GRID)

        self.fig.tight_layout()
        self.canvas.draw()

    # ------------------------------------------------------------------
    # 表格更新
    # ------------------------------------------------------------------
    def _update_table(self, charges):
        """更新电荷数据表格。"""
        self.table.setRowCount(len(charges))
        for i, charge in enumerate(charges):
            # 序号
            idx_item = QTableWidgetItem(str(charge["index"]))
            idx_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 0, idx_item)

            # 原子标签
            elem_item = QTableWidgetItem(charge["element"])
            elem_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(i, 1, elem_item)

            # 电荷值（右对齐，4位小数）
            val_item = QTableWidgetItem(f"{charge['charge']:.4f}")
            val_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.table.setItem(i, 2, val_item)

    # ------------------------------------------------------------------
    # 事件处理
    # ------------------------------------------------------------------
    def set_input_file(self, file_path):
        """设置当前输入文件路径。"""
        self.current_file = file_path

    def _on_method_changed(self, method_name):
        """方法下拉框选择变化时，更新方法说明文字。"""
        desc = CHARGE_METHOD_INFO.get(method_name, "")
        self.method_desc_label.setText(desc)

    def _on_calculate(self):
        """点击计算按钮，启动电荷计算。"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        method_name = self.method_combo.currentText()

        # 生成 Multiwfn 命令序列
        try:
            commands = InputGenerator.generate_charge_commands(method_name)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        # 禁用按钮，显示进度条
        self.calculate_btn.setEnabled(False)
        self.calculate_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 滚动模式
        self.summary_label.setText(f"正在计算 {method_name} 电荷...")
        self.summary_label.setStyleSheet("color: #fbbf24; font-size: 12px;")

        # 启动后台计算线程
        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"电荷分析: {method_name}"
        )
        self._worker.finished_ok.connect(self._on_calc_finished)
        self._worker.failed.connect(self._on_calc_failed)
        self._worker.start()

    def _on_calc_finished(self, result):
        """计算成功完成，解析并展示结果。"""
        try:
            output = result.get("output", "")
            self._last_output = output
            charges = OutputParser.parse_charges(output)
            self._last_charges = charges

            if charges:
                # 更新柱状图和表格
                self._plot_charges(charges)
                self._update_table(charges)

                # 更新总电荷
                total_charge = sum(c["charge"] for c in charges)
                self.total_label.setText(f"总电荷: {total_charge:.4f}")

                # 更新摘要
                method_name = self.method_combo.currentText()
                self.summary_label.setText(
                    f"✓ {method_name} 电荷分析完成 | {len(charges)} 个原子 | "
                    f"总电荷: {total_charge:.4f}"
                )
                self.summary_label.setStyleSheet("color: #34d399; font-size: 12px;")
            else:
                QMessageBox.warning(
                    self, "警告",
                    "未解析到电荷数据。\n请检查 Multiwfn 输出或尝试其他方法。"
                )
                self.summary_label.setText("计算完成，但未解析到数据")
                self.summary_label.setStyleSheet("color: #f59e0b; font-size: 12px;")

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
            self.summary_label.setText(f"结果处理失败: {str(e)[:60]}")
            self.summary_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        finally:
            self._reset_ui_state()

    def _on_calc_failed(self, error_msg):
        """计算失败，显示错误信息。"""
        QMessageBox.critical(self, "计算失败", error_msg[:500])
        self.summary_label.setText("计算失败")
        self.summary_label.setStyleSheet("color: #ef4444; font-size: 12px;")
        self._reset_ui_state()

    def _reset_ui_state(self):
        """重置按钮和进度条到初始状态。"""
        self.calculate_btn.setEnabled(True)
        self.calculate_btn.setText("计算电荷")
        self.progress_bar.setVisible(False)
        self._worker = None

    # ------------------------------------------------------------------
    # 数据导出
    # ------------------------------------------------------------------
    def _get_export_data(self):
        """为 ExportButtonWidget 提供导出数据。

        返回:
            (records, headers, metadata) 三元组，或 None（无数据时）。
            records: [{"序号": i, "原子": atom, "电荷值": charge}, ...]
            headers: ["序号", "原子", "电荷值"]
            metadata: {"方法": method_name, "文件": filename}
        """
        if not self._last_charges:
            # 无电荷数据时，若有原始输出则导出原始文本
            if self._last_output:
                return (
                    [{"原始输出": self._last_output}],
                    ["原始输出"],
                    {"电荷方法": self.method_combo.currentText()}
                )
            return None

        # 构建中文键名的记录列表
        records = []
        for c in self._last_charges:
            records.append({
                "序号": c["index"],
                "原子": c["element"],
                "电荷值": round(c["charge"], 6),
            })

        headers = ["序号", "原子", "电荷值"]

        # 元数据
        method_name = self.method_combo.currentText()
        filename = os.path.basename(self.current_file) if self.current_file else "未知"
        metadata = {
            "方法": method_name,
            "文件": filename,
            "原子数": len(self._last_charges),
            "总电荷": round(sum(c["charge"] for c in self._last_charges), 6),
        }

        return records, headers, metadata
