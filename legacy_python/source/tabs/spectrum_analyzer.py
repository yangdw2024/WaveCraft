#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
光谱分析模块 - 绘制光谱曲线、数据表格、深色主题、完整导出

对应 Multiwfn 主菜单 11 (Plot spectrum)。
支持类型：IR、Raman、UV-Vis、ECD、VCD、ROA、NMR。
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
DARK_CURVE = "#66bb6a"
DARK_STICK = "#4fc3f7"
DARK_PEAK = "#ffd54f"

# ========== 光谱类型详细说明（中文ToolTip） ==========
SPECTRUM_INFO = {
    "IR红外光谱": (
        "红外吸收光谱，显示分子振动模式的吸收强度。\n\n"
        "IR光谱基于偶极矩导数计算，只有引起偶极矩变化的\n"
        "振动模式才有红外活性。广泛用于官能团识别、\n"
        "结构确认和振动模式归属。\n"
        "需要频率计算结果（如Gaussian freq计算）。\n\n"
        "Multiwfn菜单11 → 1"
    ),
    "Raman拉曼光谱": (
        "拉曼散射光谱，与红外互补，反映分子极化率变化。\n\n"
        "Raman光谱基于极化率导数计算，只有引起极化率变化\n"
        "的振动模式才有拉曼活性。与IR互补，可检测IR无活性\n"
        "的对称振动，特别适用于水溶液体系（水拉曼信号弱）。\n"
        "需要频率+Raman计算结果。\n\n"
        "Multiwfn菜单11 → 2"
    ),
    "UV-Vis紫外可见光谱": (
        "电子吸收光谱，反映分子的电子激发。\n\n"
        "UV-Vis光谱显示各激发态的吸收波长和振子强度，\n"
        "是研究分子光学性质、发色团和电子跃迁的基础工具。\n"
        "需要TDDFT/CIS/ZINDO等激发态计算结果。\n\n"
        "Multiwfn菜单11 → 3"
    ),
    "ECD电子圆二色谱": (
        "圆二色光谱，用于手性分子的构型确定。\n\n"
        "ECD（电子圆二色谱）测量左/右圆偏振光的吸收差，\n"
        "手性分子产生非零ECD信号。通过与实验谱图比较，\n"
        "可确定绝对构型(R/S)。需要TDDFT激发态+旋光计算。\n\n"
        "Multiwfn菜单11 → 4"
    ),
    "VCD振动圆二色谱": (
        "振动圆二色光谱，手性分子振动模式分析。\n\n"
        "VCD测量红外区域各振动模式的圆二色信号，\n"
        "是ECD的振动对应物。对构型确定的灵敏度往往\n"
        "高于ECD，特别适合柔性分子。需要频率+VCD计算。\n\n"
        "Multiwfn菜单11 → 5"
    ),
    "ROA拉曼光学活性": (
        "拉曼光学活性光谱，手性分子的拉曼散射差。\n\n"
        "ROA测量左/右圆偏振光的拉曼散射强度差，\n"
        "对手性分子的立体结构非常敏感。与VCD互补，\n"
        "在可见/紫外激发波长下测量。需要频率+ROA计算。\n\n"
        "Multiwfn菜单11 → 6"
    ),
    "NMR核磁共振谱": (
        "核磁共振化学位移谱。\n\n"
        "NMR谱显示各原子核的化学位移，是结构解析和\n"
        "信号归属的核心工具。Multiwfn基于GIAO方法计算\n"
        "磁屏蔽张量，再换算为化学位移。需要NMR计算结果。\n\n"
        "Multiwfn菜单11 → 7"
    ),
}

# 光谱类型到InputGenerator键的映射
SPECTRUM_TYPE_MAP = {
    "IR红外光谱": "IR",
    "Raman拉曼光谱": "Raman",
    "UV-Vis紫外可见光谱": "UV-Vis",
    "ECD电子圆二色谱": "ECD",
    "VCD振动圆二色谱": "VCD",
    "ROA拉曼光学活性": "ROA",
    "NMR核磁共振谱": "NMR",
}

# 各类光谱的横轴标签和单位
SPECTRUM_AXIS_LABELS = {
    "IR红外光谱": ("波数 (cm⁻¹)", "强度 (km/mol)"),
    "Raman拉曼光谱": ("波数 (cm⁻¹)", "强度 (Å⁴/amu)"),
    "UV-Vis紫外可见光谱": ("波长 (nm)", "ε (L·mol⁻¹·cm⁻¹)"),
    "ECD电子圆二色谱": ("波长 (nm)", "Δε (L·mol⁻¹·cm⁻¹)"),
    "VCD振动圆二色谱": ("波数 (cm⁻¹)", "强度"),
    "ROA拉曼光学活性": ("波数 (cm⁻¹)", "强度"),
    "NMR核磁共振谱": ("化学位移 (ppm)", "强度"),
}

# 各类光谱的默认FWHM
SPECTRUM_DEFAULT_FWHM = {
    "IR红外光谱": 15.0,
    "Raman拉曼光谱": 15.0,
    "UV-Vis紫外可见光谱": 0.30,
    "ECD电子圆二色谱": 0.30,
    "VCD振动圆二色谱": 15.0,
    "ROA拉曼光学活性": 15.0,
    "NMR核磁共振谱": 0.05,
}

# 各类光谱所需输入文件关键词（用于输入检查提示）
SPECTRUM_REQUIRED_KEYWORDS = {
    "IR红外光谱": ["frequencies", "freq", "infrared"],
    "Raman拉曼光谱": ["raman", "freq", "frequencies"],
    "UV-Vis紫外可见光谱": ["excited", "tddft", "cis", "td"],
    "ECD电子圆二色谱": ["excited", "tddft", "cis", "td"],
    "VCD振动圆二色谱": ["vcd", "freq", "frequencies"],
    "ROA拉曼光学活性": ["roa", "freq", "frequencies"],
    "NMR核磁共振谱": ["nmr", "magnetic shielding"],
}

# 方法下拉框汇总ToolTip
SPECTRUM_COMBO_TOOLTIP = (
    "选择要计算的光谱类型。对应Multiwfn主菜单11 (Plot spectrum)。\n\n"
    "输入要求：\n"
    "  · IR/Raman/VCD/ROA → 需要频率计算结果\n"
    "  · UV-Vis/ECD → 需要激发态(TDDFT/CIS)计算结果\n"
    "  · NMR → 需要NMR(GIAO)计算结果\n\n"
    "选择后下方会显示该类型的详细说明。"
)


class SpectrumAnalyzerTab(QWidget):
    """光谱分析模块 - 绘制光谱曲线、数据表格、导出数据"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._last_spectrum = []
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

        # ========== 中间分栏：左侧光谱曲线图 + 右侧数据表格 ==========
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
        """构建顶部控制栏：光谱类型 + FWHM + 计算按钮 + 进度条"""
        control_layout = QHBoxLayout()
        control_layout.setSpacing(12)

        # 光谱类型选择
        type_group = QGroupBox("光谱类型")
        type_layout = QHBoxLayout(type_group)
        self.spectrum_combo = QComboBox()
        self.spectrum_combo.addItems(list(SPECTRUM_INFO.keys()))
        self.spectrum_combo.setCurrentIndex(0)
        self.spectrum_combo.setToolTip(SPECTRUM_COMBO_TOOLTIP)
        self.spectrum_combo.currentTextChanged.connect(self._on_type_changed)
        type_layout.addWidget(QLabel("类型:"))
        type_layout.addWidget(self.spectrum_combo)
        control_layout.addWidget(type_group)

        # 半高宽(FWHM)设置
        fwhm_group = QGroupBox("展宽参数")
        fwhm_layout = QHBoxLayout(fwhm_group)
        self.fwhm_spin = QDoubleSpinBox()
        self.fwhm_spin.setRange(0.0, 100.0)
        self.fwhm_spin.setSingleStep(0.1)
        self.fwhm_spin.setValue(15.0)
        self.fwhm_spin.setDecimals(2)
        self.fwhm_spin.setToolTip(
            "高斯展宽的半高全宽(FWHM)。\n"
            "值越大谱峰越宽越平滑，值越小越接近原始离散谱线。\n"
            "典型值：IR/Raman/VCD ≈ 10~20 cm⁻¹，UV-Vis/ECD ≈ 0.2~0.5 eV，\n"
            "NMR ≈ 0.01~0.05 ppm。切换光谱类型时自动更新默认值。"
        )
        fwhm_layout.addWidget(QLabel("FWHM:"))
        fwhm_layout.addWidget(self.fwhm_spin)
        control_layout.addWidget(fwhm_group)

        # 计算按钮
        self.calculate_btn = QPushButton("计算光谱")
        self.calculate_btn.setStyleSheet(
            "background-color: #3498db; color: white; font-weight: bold; "
            "padding: 6px 16px; border-radius: 4px;"
        )
        self.calculate_btn.setToolTip(
            "执行选定的光谱计算并绘制曲线。\n"
            "Multiwfn路径：主菜单11 → 选择光谱类型 → 输入展宽参数 → 输出数据。\n"
            "计算完成后自动绘制光谱曲线并填充数据表格。"
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
        self.desc_label.setToolTip("当前光谱类型的详细说明")
        parent_layout.addWidget(self.desc_label)
        self._update_desc()

    def _build_display_options(self, parent_layout):
        """构建显示选项区"""
        options_group = QGroupBox("显示选项")
        options_layout = QHBoxLayout(options_group)

        self.show_peaks = QCheckBox("峰值标注")
        self.show_peaks.setChecked(True)
        self.show_peaks.setToolTip(
            "在光谱曲线上标注各峰的位置和强度值。\n"
            "仅对高斯展宽后的连续谱有效。"
        )
        options_layout.addWidget(self.show_peaks)

        self.show_smooth = QCheckBox("平滑曲线")
        self.show_smooth.setChecked(True)
        self.show_smooth.setToolTip(
            "使用高斯函数对离散谱线进行展宽，生成连续光谱曲线。\n"
            "展宽参数由上方FWHM控制。"
        )
        options_layout.addWidget(self.show_smooth)

        self.show_stick = QCheckBox("棒状谱")
        self.show_stick.setChecked(True)
        self.show_stick.setToolTip(
            "叠加显示原始离散谱线（棒状谱），\n"
            "便于与展宽后的连续谱对比。"
        )
        options_layout.addWidget(self.show_stick)

        # 信号连接：选项变化时重绘
        self.show_peaks.stateChanged.connect(self._redraw_if_data)
        self.show_smooth.stateChanged.connect(self._redraw_if_data)
        self.show_stick.stateChanged.connect(self._redraw_if_data)

        options_layout.addStretch()
        parent_layout.addWidget(options_group)

    def _build_content_area(self, parent_layout):
        """构建中间分栏：左侧光谱曲线图(深色主题) + 右侧数据表格"""
        splitter = QSplitter(Qt.Horizontal)

        # --- 左侧：光谱曲线图 ---
        chart_group = QGroupBox("光谱图")
        chart_layout = QVBoxLayout(chart_group)

        self.fig = Figure(figsize=(8, 6), dpi=100)
        self.fig.patch.set_facecolor(DARK_BG)
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setToolTip(
            "光谱可视化区域，支持高斯展宽、棒状谱叠加和峰值标注。\n"
            "横轴和纵轴单位随光谱类型自动切换。"
        )
        chart_layout.addWidget(self.canvas)
        splitter.addWidget(chart_group)

        # --- 右侧：数据表格 ---
        data_group = QGroupBox("光谱数据")
        data_layout = QVBoxLayout(data_group)

        # 信息摘要
        self.info_label = QLabel("等待计算...")
        self.info_label.setStyleSheet("color: #a0b0c0; font-size: 11px; padding: 2px;")
        self.info_label.setToolTip("光谱数据的基本信息：激发态/振动模式数量等")
        data_layout.addWidget(self.info_label)

        # 数据表格
        self.data_table = QTableWidget()
        self.data_table.setColumnCount(4)
        self.data_table.setHorizontalHeaderLabels(
            ["状态", "能量(eV)", "波长(nm)", "强度"]
        )
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.setSortingEnabled(True)
        self.data_table.setToolTip(
            "光谱激发态/振动模式的能量、波长和强度数据。\n"
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
        self.summary_label = QLabel("就绪 - 请选择光谱类型并点击计算")
        self.summary_label.setStyleSheet("color: #c8d3e0; font-size: 12px;")
        self.summary_label.setToolTip("显示当前分析状态、类型、数据点数量等摘要信息")
        summary_layout.addWidget(self.summary_label)
        summary_layout.addStretch()
        bottom_layout.addWidget(summary_group)

        # 导出按钮组
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="spectrum"
        )
        self.export_widget.setToolTip("将光谱数据导出为TXT/CSV/Excel格式（无数据时提示）")
        bottom_layout.addWidget(self.export_widget)

        parent_layout.addLayout(bottom_layout)

    # ------------------------------------------------------------------ #
    #                        辅助方法                                      #
    # ------------------------------------------------------------------ #

    def _on_type_changed(self, type_name):
        """光谱类型变化时更新说明和FWHM默认值"""
        self._update_desc()
        # 自动更新FWHM默认值
        default_fwhm = SPECTRUM_DEFAULT_FWHM.get(type_name, 15.0)
        self.fwhm_spin.setValue(default_fwhm)

    def _update_desc(self):
        """更新类型说明标签"""
        spec_type = self.spectrum_combo.currentText()
        desc = SPECTRUM_INFO.get(spec_type, "")
        self.desc_label.setText(desc)

    def _redraw_if_data(self):
        """选项变化时，若有数据则重绘"""
        if self._last_spectrum:
            self._plot_spectrum(self._last_spectrum)

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path

    def _draw_placeholder(self):
        """绘制初始占位图"""
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        ax.text(
            0.5, 0.5, '请选择光谱类型并点击"计算光谱"',
            ha="center", va="center", transform=ax.transAxes,
            fontsize=14, color=DARK_TEXT, alpha=0.7
        )
        ax.set_xticks([])
        ax.set_yticks([])
        for spine in ax.spines.values():
            spine.set_color(DARK_GRID)
        self.canvas.draw()

    def _check_spectrum_input(self):
        """简单的输入文件内容检查：若文件为空或不包含所需关键词则给出提示，但不阻止计算。"""
        if not self.current_file or not os.path.exists(self.current_file):
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return False
        if os.path.getsize(self.current_file) == 0:
            QMessageBox.warning(self, "警告", "输入文件为空，无法计算光谱")
            return False

        spec_type = self.spectrum_combo.currentText()
        keywords = SPECTRUM_REQUIRED_KEYWORDS.get(spec_type, [])
        if keywords:
            try:
                with open(self.current_file, "r", encoding="utf-8", errors="ignore") as f:
                    head = f.read(8192).lower()
                if not any(kw.lower() in head for kw in keywords):
                    reply = QMessageBox.question(
                        self, "输入检查",
                        f"当前文件头未检测到 {spec_type} 所需关键词（{', '.join(keywords)}）。\n"
                        "若输入文件确实缺少频率/激发数据，计算可能无结果。是否仍要继续？",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return False
            except Exception:
                pass
        return True

    # ------------------------------------------------------------------ #
    #                        计算逻辑                                      #
    # ------------------------------------------------------------------ #

    def on_calculate(self):
        """启动光谱计算"""
        if not self._check_spectrum_input():
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        spec_type_display = self.spectrum_combo.currentText()
        spec_type_key = SPECTRUM_TYPE_MAP.get(spec_type_display, "IR")
        fwhm = self.fwhm_spin.value()

        try:
            commands = InputGenerator.generate_spectrum_commands(spec_type_key, fwhm=fwhm)
        except ValueError as e:
            QMessageBox.critical(self, "错误", str(e))
            return

        work_dir = os.path.dirname(self.current_file)

        self.calculate_btn.setEnabled(False)
        self.calculate_btn.setText("计算中...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.summary_label.setText(f"正在计算 {spec_type_display} ...")

        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"光谱分析: {spec_type_display}"
        )
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_finished(self, result):
        """计算完成回调"""
        try:
            output = result.get("output", "")
            self._last_output = output

            # 尝试解析光谱数据
            try:
                spectrum_data = OutputParser.parse_spectrum_data(output)
            except Exception:
                spectrum_data = []

            # 若解析失败，尝试用另一种解析方法
            if not spectrum_data:
                try:
                    spectrum_data = OutputParser.parse_spectrum_lines(output)
                except Exception:
                    pass

            self._last_spectrum = spectrum_data

            if spectrum_data:
                self._plot_spectrum(spectrum_data)
                self._update_table(spectrum_data)
                self.info_label.setText(
                    f"数据点: {len(spectrum_data)} | "
                    f"类型: {self.spectrum_combo.currentText()}"
                )
                self.summary_label.setText(
                    f"{self.spectrum_combo.currentText()} | {len(spectrum_data)}条数据"
                )
            else:
                self._last_spectrum = []
                self._draw_placeholder_with_text("未解析到光谱数据")
                self.data_table.setRowCount(0)
                self.info_label.setText("未解析到数据")
                self.summary_label.setText(
                    f"{self.spectrum_combo.currentText()} | 无数据"
                )
                QMessageBox.warning(
                    self, "无数据",
                    "未从输出中解析到光谱数据。\n"
                    "可能当前输入文件缺少频率/激发态信息，\n"
                    "请检查输入文件类型是否匹配所选光谱。"
                )

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
        finally:
            self.calculate_btn.setEnabled(True)
            self.calculate_btn.setText("计算光谱")
            self.progress_bar.setVisible(False)
            self._worker = None

    def _on_failed(self, error_msg):
        """计算失败回调"""
        QMessageBox.critical(self, "计算失败", error_msg[:500])
        self.calculate_btn.setEnabled(True)
        self.calculate_btn.setText("计算光谱")
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

    def _plot_spectrum(self, spectrum_data):
        """
        绘制光谱曲线图（深色主题）：
        - 支持高斯展宽、棒状谱叠加、峰值标注
        - 深色主题配色
        - 横轴/纵轴标签随光谱类型自动切换
        """
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(DARK_AXIS_BG)
        self.fig.patch.set_facecolor(DARK_BG)

        if not spectrum_data:
            self._draw_placeholder_with_text("未解析到光谱数据")
            return

        # 提取数据
        energies = np.array([d["energy_eV"] for d in spectrum_data])
        intensities = np.array([d["intensity"] for d in spectrum_data])

        # 判断是否为振动谱（IR/Raman/VCD/ROA用波数cm⁻¹作为横轴）
        spec_type_display = self.spectrum_combo.currentText()
        is_vibrational = spec_type_display in (
            "IR红外光谱", "Raman拉曼光谱", "VCD振动圆二色谱", "ROA拉曼光学活性"
        )

        # 横轴：振动谱用波数(cm⁻¹)，电子谱用波长(nm)，NMR用ppm
        if is_vibrational:
            # 波数 = energy_eV 中已经存的是波数值（从parse_spectrum_data来的）
            x_data = energies
        elif spec_type_display == "NMR核磁共振谱":
            x_data = energies  # ppm
        else:
            # UV-Vis/ECD：波长(nm)
            x_data = np.array([
                d.get("wavelength_nm", 1240.0 / d["energy_eV"] if d["energy_eV"] != 0 else 0)
                for d in spectrum_data
            ])

        # 棒状谱
        if self.show_stick.isChecked():
            ax.vlines(
                x_data, 0, intensities,
                colors=DARK_STICK, linestyles="-",
                linewidths=1.5, alpha=0.7, label="棒状谱"
            )

        # 高斯展宽平滑曲线
        peak_positions = []
        peak_values = []
        if self.show_smooth.isChecked() and len(x_data) > 0:
            fwhm = self.fwhm_spin.value()
            if fwhm > 0:
                sigma = fwhm / (2.0 * np.sqrt(2.0 * np.log(2.0)))
            else:
                sigma = 0.15 if not is_vibrational else 15.0

            x_min, x_max = x_data.min(), x_data.max()
            if is_vibrational:
                margin = (x_max - x_min) * 0.05 if x_max > x_min else 50
            elif spec_type_display == "NMR核磁共振谱":
                margin = (x_max - x_min) * 0.1 if x_max > x_min else 2
            else:
                margin = (x_max - x_min) * 0.05 if x_max > x_min else 20

            x_grid = np.linspace(x_min - margin, x_max + margin, 800)
            broadened = np.zeros_like(x_grid)

            for x_val, intensity in zip(x_data, intensities):
                broadened += intensity * np.exp(-0.5 * ((x_grid - x_val) / sigma) ** 2)

            # 归一化到原始最大强度
            if broadened.max() > 0 and intensities.max() > 0:
                broadened = broadened * (intensities.max() / broadened.max())

            ax.plot(
                x_grid, broadened,
                color=DARK_CURVE, linewidth=2, label="高斯展宽"
            )

            # 检测峰值用于标注
            if self.show_peaks.isChecked():
                # 简易峰值检测：寻找局部极大值
                for i in range(1, len(broadened) - 1):
                    if broadened[i] > broadened[i - 1] and broadened[i] > broadened[i + 1]:
                        if broadened[i] > intensities.max() * 0.05:  # 过滤噪声小峰
                            peak_positions.append(x_grid[i])
                            peak_values.append(broadened[i])

        # 峰值标注
        if self.show_peaks.isChecked() and peak_positions:
            # 限制标注数量，避免图太拥挤
            max_annotations = 20
            # 按强度排序，只标注最强的峰
            sorted_peaks = sorted(
                zip(peak_positions, peak_values),
                key=lambda p: p[1], reverse=True
            )
            if len(sorted_peaks) > max_annotations:
                sorted_peaks = sorted_peaks[:max_annotations]

            for px, py in sorted_peaks:
                ax.annotate(
                    f"{px:.1f}",
                    xy=(px, py), xytext=(0, 10),
                    textcoords="offset points",
                    fontsize=7, color=DARK_PEAK,
                    ha="center", va="bottom",
                    arrowprops=dict(
                        arrowstyle="-", color=DARK_PEAK,
                        lw=0.5, alpha=0.6
                    )
                )

        # 轴标签
        xlabel, ylabel = SPECTRUM_AXIS_LABELS.get(
            spec_type_display, ("能量 (eV)", "强度")
        )
        ax.set_xlabel(xlabel, fontsize=12, color=DARK_TEXT)
        ax.set_ylabel(ylabel, fontsize=12, color=DARK_TEXT)
        ax.set_title(f"{spec_type_display}", fontsize=14, color=DARK_TEXT, pad=10)

        # 网格和图例
        ax.grid(True, alpha=0.2, color=DARK_GRID)
        if self.show_stick.isChecked() or self.show_smooth.isChecked():
            ax.legend(
                fontsize=9, loc="upper right",
                facecolor=DARK_AXIS_BG, edgecolor=DARK_GRID,
                labelcolor=DARK_TEXT
            )

        # NMR谱通常从右到左（化学位移减小方向）
        if spec_type_display == "NMR核磁共振谱":
            ax.invert_xaxis()

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

    def _update_table(self, spectrum_data):
        """更新光谱数据表格，支持排序"""
        self.data_table.setSortingEnabled(False)
        self.data_table.setRowCount(0)
        self.data_table.setRowCount(len(spectrum_data))

        for i, data in enumerate(spectrum_data):
            # 状态列
            item_state = QTableWidgetItem(str(data.get("state", i + 1)))
            item_state.setFlags(item_state.flags() & ~Qt.ItemIsEditable)
            self.data_table.setItem(i, 0, item_state)

            # 能量列
            item_energy = QTableWidgetItem()
            item_energy.setData(Qt.DisplayRole, f"{data['energy_eV']:.4f}")
            item_energy.setData(Qt.UserRole, data["energy_eV"])
            item_energy.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_energy.setFlags(item_energy.flags() & ~Qt.ItemIsEditable)
            self.data_table.setItem(i, 1, item_energy)

            # 波长列
            wl = data.get("wavelength_nm", 0)
            item_wl = QTableWidgetItem()
            item_wl.setData(Qt.DisplayRole, f"{wl:.2f}")
            item_wl.setData(Qt.UserRole, wl)
            item_wl.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_wl.setFlags(item_wl.flags() & ~Qt.ItemIsEditable)
            self.data_table.setItem(i, 2, item_wl)

            # 强度列
            item_int = QTableWidgetItem()
            item_int.setData(Qt.DisplayRole, f"{data['intensity']:.4f}")
            item_int.setData(Qt.UserRole, data["intensity"])
            item_int.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            item_int.setFlags(item_int.flags() & ~Qt.ItemIsEditable)
            self.data_table.setItem(i, 3, item_int)

        self.data_table.setSortingEnabled(True)

    # ------------------------------------------------------------------ #
    #                        导出功能                                      #
    # ------------------------------------------------------------------ #

    def _get_export_data(self):
        """为导出功能提供数据"""
        if not self._last_spectrum:
            if self._last_output:
                return (
                    [{"output": self._last_output}],
                    ["output"],
                    {"光谱类型": self.spectrum_combo.currentText()}
                )
            return None

        records = []
        for d in self._last_spectrum:
            records.append({
                "state": d.get("state", 0),
                "energy_eV": d["energy_eV"],
                "wavelength_nm": d.get("wavelength_nm", 0),
                "intensity": d["intensity"],
            })

        metadata = {
            "光谱类型": self.spectrum_combo.currentText(),
            "FWHM": self.fwhm_spin.value(),
            "显示峰值标注": self.show_peaks.isChecked(),
            "平滑曲线": self.show_smooth.isChecked(),
            "显示棒状谱": self.show_stick.isChecked(),
            "数据点": len(self._last_spectrum),
        }
        return records, ["state", "energy_eV", "wavelength_nm", "intensity"], metadata
