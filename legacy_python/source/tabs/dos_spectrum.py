# -*- coding: utf-8 -*-
"""
DOS/态密度分析模块 - 绘制曲线、数据表格、深色主题、完整导出

对应 Multiwfn 主菜单 10 (DOS)。
支持类型：Total DOS、PDOS、OPDOS、Local DOS、COHP、COOP、光电子能谱、带隙分析。
"""

import os
import numpy as np

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QPushButton, QGroupBox, QMessageBox, QProgressBar,
    QSplitter, QCheckBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QDoubleSpinBox
)
from PyQt5.QtCore import Qt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ..core.worker import CalculationWorker
from ..utils.input_generator import InputGenerator
from ..utils.output_parser import OutputParser
from ..utils.export_utils import ExportButtonWidget

# ========== 深色主题颜色常量 ==========
DARK_BG = "#161d27"
DARK_AXIS_BG = "#1e2630"
DARK_TEXT = "#e2e8f0"
DARK_GRID = "#2a3444"
DARK_CURVE = "#4fc3f7"
DARK_FILL = "#4fc3f7"
DARK_FERMI = "#ef5350"

# ========== DOS分析类型详细说明（中文ToolTip） ==========
DOS_INFO = {
    "总态密度(Total DOS)": (
        "计算体系的总态密度(TDOS)，反映所有轨道的能量分布，\n"
        "是分析电子结构的基础。\n\n"
        "TDOS对所有轨道的态密度进行求和，能直观展示价带、\n"
        "导带位置和带隙大小，是DOS分析的第一步。\n\n"
        "Multiwfn菜单10 → 1"
    ),
    "分态密度(PDOS)": (
        "按原子或轨道类型分解的态密度，\n"
        "用于分析各原子/轨道对电子结构的贡献。\n\n"
        "通过PDOS可以确定特定能带主要来自哪些原子的\n"
        "哪些轨道，是理解化学键和电子结构的核心工具。\n"
        "计算时需指定原子分组。\n\n"
        "Multiwfn菜单10 → 2"
    ),
    "重叠分态密度(OPDOS)": (
        "两个片段轨道之间的重叠态密度，\n"
        "用于分析片段间的轨道相互作用。\n\n"
        "OPDOS正值表示成键相互作用，负值表示反键相互作用，\n"
        "是COHP/COOP分析的有力补充。计算时需指定两个片段。\n\n"
        "Multiwfn菜单10 → 3"
    ),
    "局域态密度(Local DOS)": (
        "特定原子或区域的态密度。\n\n"
        "与PDOS类似但更灵活，可选择单个原子或一组原子，\n"
        "分析其对特定能量范围态密度的局域贡献。\n\n"
        "Multiwfn菜单10 → 4"
    ),
    "COHP曲线": (
        "晶体轨道哈密顿布居(COHP)，分析成键/反键贡献。\n\n"
        "COHP将DOS按哈密顿矩阵元加权，正值表示成键贡献，\n"
        "负值表示反键贡献。积分COHP(-ICOHP)常用于定量\n"
        "衡量键的强度，是固体化学键分析的重要工具。\n\n"
        "Multiwfn菜单10 → 5"
    ),
    "COOP曲线": (
        "晶体轨道重叠布居(COOP)，分析成键/反键特征。\n\n"
        "COOP将DOS按重叠矩阵元加权，与COHP类似但基于\n"
        "重叠积分而非哈密顿矩阵元。正值=成键，负值=反键。\n"
        "适用于定性分析键的性质。\n\n"
        "Multiwfn菜单10 → 6"
    ),
    "光电子能谱": (
        "模拟光电子能谱(PES)，反映价带电子的电离能分布。\n\n"
        "PES通过高斯展宽将离散能级转为连续谱，可与实验\n"
        "XPS/UPS谱图直接比较，用于验证计算结果和归属谱峰。\n"
        "需要考虑电离能和展宽参数。\n\n"
        "Multiwfn菜单10 → 10"
    ),
    "带隙分析": (
        "分析HOMO-LUMO带隙，提取能带结构关键信息。\n\n"
        "对于分子体系显示HOMO和LUMO能量及带隙大小；\n"
        "对于周期性体系显示价带顶(VBM)、导带底(CBM)\n"
        "和带隙类型（直接/间接）。是评估材料导电性的基础。\n\n"
        "Multiwfn菜单10 → 8"
    ),
}

# 方法下拉框汇总ToolTip
DOS_COMBO_TOOLTIP = (
    "选择DOS分析类型。对应Multiwfn主菜单10 (DOS)。\n\n"
    "常用推荐：\n"
    "  · 总态密度 — DOS分析的基础，查看整体电子结构\n"
    "  · 分态密度 — 分析各原子/轨道贡献\n"
    "  · COHP曲线 — 成键/反键分析（固体化学）\n"
    "  · 光电子能谱 — 与实验XPS/UPS对比\n"
    "  · 带隙分析 — 评估带隙大小和类型\n\n"
    "选择后下方会显示该类型的详细说明。"
)


class DOSSpectrumTab(QWidget):
    """DOS/态密度分析模块 - 绘制曲线并导出数据"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_energy = []
        self._last_dos = []
        self._last_output = ""
        self.init_ui()

    def init_ui(self):
        """初始化界面布局"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(8)

        # ========== 顶部控制栏 ==========
        self._build_control_bar(main_layout)

        # ========== 类型说明标签 ==========
        self._build_type_desc(main_layout)

        # ========== 显示选项 ==========
        self._build_display_options(main_layout)

        # ========== 中间分栏：左侧DOS曲线图 + 右侧数据表格 ==========
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
        """构建顶部控制栏：分析类型 + FWHM + 计算按钮 + 进度条"""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)

        # 分析类型选择
        type_group = QGroupBox("分析类型")
        type_layout = QHBoxLayout(type_group)
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(DOS_INFO.keys()))
        self.type_combo.setCurrentIndex(0)
        self.type_combo.setToolTip(DOS_COMBO_TOOLTIP)
        self.type_combo.currentTextChanged.connect(self._update_desc)
        type_layout.addWidget(QLabel("类型:"))
        type_layout.addWidget(self.type_combo)
        control_layout.addWidget(type_group)

        # 半高宽(FWHM)设置
        fwhm_group = QGroupBox("展宽参数")
        fwhm_layout = QHBoxLayout(fwhm_group)
        self.fwhm_spin = QDoubleSpinBox()
        self.fwhm_spin.setRange(0.0, 10.0)
        self.fwhm_spin.setSingleStep(0.05)
        self.fwhm_spin.setValue(0.30)
        self.fwhm_spin.setDecimals(2)
        self.fwhm_spin.setSuffix(" eV")
        self.fwhm_spin.setToolTip(
            "高斯展宽的半高全宽(FWHM)。\n"
            "值越大谱峰越宽越平滑，值越小越接近原始离散谱线。\n"
            "典型值：0.2~0.5 eV（分子体系），0.05~0.2 eV（固体体系）。\n"
            "设为0则不进行展宽。"
        )
        fwhm_layout.addWidget(QLabel("FWHM:"))
        fwhm_layout.addWidget(self.fwhm_spin)
        control_layout.addWidget(fwhm_group)

        # 计算按钮
        self.calculate_btn = QPushButton("计算并绘制")
        self.calculate_btn.setStyleSheet(
            "background-color: #9b59b6; color: white; font-weight: bold; "
            "padding: 6px 16px; border-radius: 4px;"
        )
        self.calculate_btn.setToolTip(
            "执行DOS计算并绘制态密度曲线。\n"
            "Multiwfn路径：主菜单10 → 选择DOS类型 → 设置展宽 → 输出数据。\n"
            "计算完成后自动绘制曲线并填充数据表格。"
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

    def _build_type_desc(self, parent_layout):
        """构建类型说明标签"""
        self.desc_label = QLabel()
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(
            "color: #a0b0c0; font-size: 11px; padding: 4px 8px; "
            "background-color: #1a2332; border-radius: 4px; border: 1px solid #2a3a4a;"
        )
        self.desc_label.setToolTip("当前DOS类型的详细说明")
        parent_layout.addWidget(self.desc_label)
        self._update_desc()

    def _build_display_options(self, parent_layout):
        """构建显示选项区"""
        options_group = QGroupBox("显示选项")
        options_layout = QHBoxLayout(options_group)

        self.show_gaussian = QCheckBox("高斯展宽")
        self.show_gaussian.setChecked(True)
        self.show_gaussian.setToolTip(
            "对DOS曲线进行高斯展宽，使峰形更平滑。\n"
            "展宽仅影响绘图效果，不改变导出的原始数据。\n"
            "FWHM由上方展宽参数控制。"
        )
        options_layout.addWidget(self.show_gaussian)

        self.show_fermi = QCheckBox("费米能级线")
        self.show_fermi.setChecked(True)
        self.show_fermi.setToolTip(
            "在E=0处标记费米能级位置。\n"
            "费米能级是占据态与非占据态的分界线，\n"
            "通常作为能量参考点(能量零点)。"
        )
        options_layout.addWidget(self.show_fermi)

        self.show_fill = QCheckBox("填充面积")
        self.show_fill.setChecked(False)
        self.show_fill.setToolTip("填充DOS曲线下方面积，增强可视化效果")
        options_layout.addWidget(self.show_fill)

        # 信号连接：选项变化时重绘
        self.show_fill.stateChanged.connect(self._redraw_if_data)
        self.show_gaussian.stateChanged.connect(self._redraw_if_data)
        self.show_fermi.stateChanged.connect(self._redraw_if_data)

        options_layout.addStretch()
        parent_layout.addWidget(options_group)

    def _build_content_area(self, parent_layout):
        """构建中间分栏：左侧DOS曲线图(深色主题) + 右侧数据表格"""
        splitter = QSplitter(Qt.Horizontal)

        # --- 左侧：DOS曲线图 ---
        chart_group = QGroupBox("DOS曲线")
        chart_layout = QVBoxLayout(chart_group)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor(DARK_BG)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setToolTip(
            "态密度曲线可视化区域。\n"
            "横轴：能量(eV)，纵轴：态密度。\n"
            "支持高斯展宽、费米能级标记、面积填充等显示选项。"
        )
        chart_layout.addWidget(self.canvas)
        splitter.addWidget(chart_group)

        # --- 右侧：数据表格 ---
        data_group = QGroupBox("DOS数据")
        data_layout = QVBoxLayout(data_group)

        # 信息摘要
        self.info_label = QLabel("等待计算...")
        self.info_label.setStyleSheet("color: #a0b0c0; font-size: 11px; padding: 2px;")
        self.info_label.setToolTip("DOS数据的基本信息：数据点数量、能量范围等")
        data_layout.addWidget(self.info_label)

        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(2)
        self.data_table.setHorizontalHeaderLabels(["能量 (eV)", "态密度"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setSortingEnabled(True)
        self.data_table.setToolTip(
            "DOS曲线的数据点，可按列排序。\n"
            "点击列标题可升序/降序排列。\n"
            "数据可导出为TXT/CSV/Excel格式。"
        )
        data_layout.addWidget(self.data_table)

        splitter.addWidget(data_group)
        splitter.setSizes([600, 300])

        parent_layout.addWidget(splitter)

    def _build_bottom_bar(self, parent_layout):
        """构建底部：计算摘要 + 导出按钮组"""
        bottom_layout = QHBoxLayout()

        # 计算摘要
        summary_group = QGroupBox("计算摘要")
        summary_layout = QHBoxLayout(summary_group)
        self.summary_label = QLabel("就绪 - 请选择分析类型并点击计算")
        self.summary_label.setStyleSheet("color: #c8d3e0; font-size: 12px;")
        self.summary_label.setToolTip("显示当前分析状态、类型、数据点数量等摘要信息")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        bottom_layout.addWidget(summary_group)

        # 导出按钮组
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="dos_data"
        )
        self.export_widget.setToolTip("将DOS数据导出为TXT/CSV/Excel格式（无数据时提示）")
        bottom_layout.addWidget(self.export_widget)

        parent_layout.addLayout(bottom_layout)

    # ------------------------------------------------------------------ #
    #                        辅助方法                                      #
    # ------------------------------------------------------------------ #

    def _update_desc(self):
        """更新类型说明标签"""
        atype = self.type_combo.currentText()
        desc = DOS_INFO.get(atype, "")
        self.desc_label.setText(desc)

    def _redraw_if_data(self):
        """选项变化时，若有数据则重绘"""
        if self._last_energy and self._last_dos:
            self._plot_dos_data(self._last_energy, self._last_dos)

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path

    def _draw_placeholder(self):
        """绘制初始占位图"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        ax.text(
            0.5, 0.5, "请选择分析类型并点击计算",
            ha="center", va="center", transform=ax.transAxes,
            fontsize=14, color=DARK_TEXT, alpha=0.7
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)
        self.canvas.draw()

    # ------------------------------------------------------------------ #
    #                        计算逻辑                                      #
    # ------------------------------------------------------------------ #

    def on_calculate(self):
        """启动DOS计算"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        analysis_type = self.type_combo.currentText()
        try:
            commands = InputGenerator.generate_dos_commands(analysis_type)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        self.calculate_btn.setEnabled(False)
        self.calculate_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.summary_label.setText(f"正在计算 {analysis_type} ...")

        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"DOS分析: {analysis_type}"
        )
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_finished(self, result):
        """计算完成回调"""
        try:
            output = result.get("output", "")
            self._last_output = output
            work_dir = os.path.dirname(self.current_file)

            # 尝试从输出中解析DOS数据
            dos_data = OutputParser.parse_dos(output)
            energy, dos = [], []
            if dos_data and "energy" in dos_data and "dos" in dos_data:
                energy, dos = dos_data["energy"], dos_data["dos"]

            # 若解析失败，尝试从dos_data.txt文件读取
            if not energy:
                dos_file = os.path.join(work_dir, "dos_data.txt")
                if os.path.exists(dos_file):
                    try:
                        data = np.loadtxt(dos_file)
                        if data.ndim == 2 and data.shape[1] >= 2:
                            energy = data[:, 0].tolist()
                            dos = data[:, 1].tolist()
                    except Exception:
                        pass
                    # 清理临时文件
                    try:
                        os.remove(dos_file)
                    except Exception:
                        pass

            # 尝试从DOS.dat文件读取
            if not energy:
                dat_file = os.path.join(work_dir, "DOS.dat")
                if os.path.exists(dat_file):
                    try:
                        data = np.loadtxt(dat_file)
                        if data.ndim == 2 and data.shape[1] >= 2:
                            energy = data[:, 0].tolist()
                            dos = data[:, 1].tolist()
                    except Exception:
                        pass

            if energy and dos:
                self._last_energy = energy
                self._last_dos = dos
                self._plot_dos_data(energy, dos)
                self._update_table(energy, dos)
                self.info_label.setText(
                    f"数据点: {len(energy)} | "
                    f"能量范围: {min(energy):.3f} ~ {max(energy):.3f} eV"
                )
                self.summary_label.setText(
                    f"{self.type_combo.currentText()} | 数据点: {len(energy)}"
                )
            else:
                self._last_energy = []
                self._last_dos = []
                self._draw_placeholder_with_text("未解析到DOS数据")
                self.data_table.setRowCount(0)
                self.info_label.setText("未解析到数据")
                self.summary_label.setText(f"{self.type_combo.currentText()} | 无数据")
                QMessageBox.warning(
                    self, "警告",
                    "未从输出中解析到DOS数据。\n"
                    "请检查输入文件是否包含波函数信息，或尝试其他分析类型。"
                )

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
        finally:
            self.calculate_btn.setEnabled(True)
            self.calculate_btn.setText("计算并绘制")
            self.progress_bar.setVisible(False)
            self._worker = None

    def _on_failed(self, error_msg):
        """计算失败回调"""
        QMessageBox.critical(self, "计算失败", error_msg[:500])
        self.calculate_btn.setEnabled(True)
        self.calculate_btn.setText("计算并绘制")
        self.progress_bar.setVisible(False)
        self.summary_label.setText("计算失败")
        self._worker = None

    # ------------------------------------------------------------------ #
    #                        绘图方法                                      #
    # ------------------------------------------------------------------ #

    def _draw_placeholder_with_text(self, message):
        """绘制带文字的占位图"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        ax.text(
            0.5, 0.5, message,
            ha="center", va="center", transform=ax.transAxes,
            fontsize=14, color=DARK_TEXT, alpha=0.7
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)
        self.canvas.draw()

    def _plot_dos_data(self, energy, dos):
        """
        绘制DOS曲线图（深色主题）：
        - 支持高斯展宽、费米能级线、面积填充
        - 深色主题配色
        """
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        self.fig.patch.set_facecolor(DARK_BG)

        x = np.array(energy)
        y = np.array(dos)

        # 高斯展宽
        if self.show_gaussian.isChecked() and len(x) > 3:
            fwhm = self.fwhm_spin.value()
            if fwhm > 0:
                sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
            else:
                sigma = (x.max() - x.min()) / len(x) * 3

            x_min, x_max = x.min(), x.max()
            margin = (x_max - x_min) * 0.05
            x_new = np.linspace(x_min - margin, x_max + margin, 800)
            y_new = np.zeros_like(x_new)
            for xi, yi in zip(x, y):
                y_new += yi * np.exp(-0.5 * ((x_new - xi) / sigma) ** 2)
            y_new /= (sigma * np.sqrt(2 * np.pi))
            x, y = x_new, y_new

        # 填充面积
        if self.show_fill.isChecked():
            ax.fill_between(x, y, alpha=0.25, color=DARK_FILL)

        # 绘制DOS曲线
        ax.plot(x, y, linewidth=2, color=DARK_CURVE, label='DOS')

        # 费米能级线
        if self.show_fermi.isChecked():
            ax.axvline(
                x=0, color=DARK_FERMI, linestyle='--',
                linewidth=1.2, alpha=0.8, label='费米能级'
            )

        # 轴标签和标题
        analysis_type = self.type_combo.currentText()
        ax.set_xlabel("能量 (eV)", fontsize=12, color=DARK_TEXT)
        ax.set_ylabel("态密度 (a.u.)", fontsize=12, color=DARK_TEXT)
        ax.set_title(f"{analysis_type}", fontsize=14, color=DARK_TEXT, pad=10)

        # 网格和图例
        ax.grid(True, alpha=0.2, color=DARK_GRID)
        ax.legend(
            fontsize=9, loc="upper right",
            facecolor=DARK_AXIS_BG, edgecolor=DARK_GRID,
            labelcolor=DARK_TEXT
        )

        # 刻度颜色
        ax.tick_params(axis="x", colors=DARK_TEXT)
        ax.tick_params(axis="y", colors=DARK_TEXT)
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)

        self.fig.tight_layout()
        self.canvas.draw()

    # ------------------------------------------------------------------ #
    #                        数据表格                                      #
    # ------------------------------------------------------------------ #

    def _update_table(self, energy, dos):
        """更新DOS数据表格，支持排序"""
        self.data_table.setSortingEnabled(False)
        self.data_table.setRowCount(0)

        # 采样显示，避免表格过长
        step = max(1, len(energy) // 300)
        display_indices = list(range(0, len(energy), step))
        self.data_table.setRowCount(len(display_indices))

        for i, idx in enumerate(display_indices):
            # 能量列
            item_e = QTableWidgetItem()
            item_e.setData(Qt.DisplayRole, f"{energy[idx]:.4f}")
            item_e.setData(Qt.UserRole, energy[idx])
            item_e.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_e.setFlags(item_e.flags() & ~Qt.ItemIsEditable)
            self.data_table.setItem(i, 0, item_e)

            # 态密度列
            item_d = QTableWidgetItem()
            item_d.setData(Qt.DisplayRole, f"{dos[idx]:.6f}")
            item_d.setData(Qt.UserRole, dos[idx])
            item_d.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_d.setFlags(item_d.flags() & ~Qt.ItemIsEditable)
            self.data_table.setItem(i, 1, item_d)

        self.data_table.setSortingEnabled(True)

    # ------------------------------------------------------------------ #
    #                        导出功能                                      #
    # ------------------------------------------------------------------ #

    def _get_export_data(self):
        """为导出功能提供数据"""
        if not self._last_energy or not self._last_dos:
            if self._last_output:
                return (
                    [{"output": self._last_output}],
                    ["output"],
                    {"分析类型": self.type_combo.currentText()}
                )
            return None

        records = []
        for e, d in zip(self._last_energy, self._last_dos):
            records.append({"energy_eV": e, "dos": d})

        metadata = {
            "分析类型": self.type_combo.currentText(),
            "FWHM(eV)": self.fwhm_spin.value(),
            "高斯展宽": self.show_gaussian.isChecked(),
            "费米能级线": self.show_fermi.isChecked(),
            "填充面积": self.show_fill.isChecked(),
            "数据点": len(self._last_energy),
        }
        return records, ["energy_eV", "dos"], metadata
