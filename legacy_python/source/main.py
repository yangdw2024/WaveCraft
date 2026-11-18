import sys
import os

import matplotlib
matplotlib.use('Qt5Agg')
import matplotlib.pyplot as plt
from matplotlib import rcParams

rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
rcParams['axes.unicode_minus'] = False
rcParams['figure.facecolor'] = '#161d27'
rcParams['axes.facecolor'] = '#1e2630'
rcParams['axes.edgecolor'] = '#334155'
rcParams['axes.labelcolor'] = '#e2e8f0'
rcParams['xtick.color'] = '#94a3b8'
rcParams['ytick.color'] = '#94a3b8'
rcParams['text.color'] = '#e2e8f0'
rcParams['grid.color'] = '#334155'
rcParams['legend.facecolor'] = '#1e2630'
rcParams['legend.edgecolor'] = '#334155'
rcParams['legend.labelcolor'] = '#e2e8f0'
rcParams['axes.titlecolor'] = '#f1f5f9'

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileDialog,
    QMenuBar, QToolBar, QStatusBar, QAction, QLabel,
    QWidget, QVBoxLayout, QHBoxLayout, QMessageBox,
    QPushButton, QProgressBar, QTabWidget, QSizePolicy
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

from .tabs.file_manager import FileManagerTab
from .tabs.realspace_analyzer import RealSpaceAnalyzerTab
from .tabs.charge_analysis import ChargeAnalysisTab
from .tabs.bond_analysis import BondAnalysisTab
from .tabs.dos_spectrum import DOSSpectrumTab
from .tabs.weak_interaction import WeakInteractionTab
from .tabs.structure_viewer import StructureViewerTab
from .tabs.orbital_bond import OrbitalBondTab
from .tabs.spectrum_analyzer import SpectrumAnalyzerTab
from .tabs.advanced_tools import AdvancedToolsTab
from .tabs.function_menu import FunctionMenuTab


class MainWindow(QMainWindow):
    """WaveCraft 主窗口 - Multiwfn 中文版可视化分析平台。"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("WaveCraft - Multiwfn 中文版可视化分析平台")
        self.setMinimumSize(1500, 950)
        self.resize(1650, 1000)

        self._apply_dark_theme()
        self.create_menu()
        self.create_toolbar()
        self.create_statusbar()
        self.create_main_layout()
        self.show()

    def _apply_dark_theme(self):
        """应用统一的现代深色主题。"""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #0f1419;
            }
            QTabWidget::pane {
                border: 1px solid #2a3441;
                border-radius: 8px;
                background-color: #161d27;
                top: -1px;
            }
            QTabBar::tab {
                background-color: #1e2630;
                border: 1px solid #2a3441;
                border-bottom: none;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                padding: 12px 24px;
                margin-right: 3px;
                font-size: 13px;
                font-weight: 500;
                color: #9aa5b1;
                min-width: 85px;
            }
            QTabBar::tab:selected {
                background-color: #161d27;
                color: #38bdf8;
                border-bottom: 2px solid #38bdf8;
                margin-bottom: -1px;
            }
            QTabBar::tab:hover {
                color: #38bdf8;
                background-color: #232d3a;
            }
            QGroupBox {
                font-size: 13px;
                font-weight: 600;
                color: #e2e8f0;
                border: 1px solid #2a3441;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 14px;
                background-color: #161d27;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 14px;
                padding: 0 8px;
                color: #38bdf8;
            }
            QPushButton {
                background-color: #0ea5e9;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 9px 22px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #38bdf8;
            }
            QPushButton:pressed {
                background-color: #0284c7;
            }
            QPushButton:disabled {
                background-color: #475569;
                color: #94a3b8;
            }
            QComboBox {
                padding: 7px 14px;
                border: 1px solid #2a3441;
                border-radius: 6px;
                font-size: 13px;
                background-color: #0f1419;
                color: #e2e8f0;
                min-width: 150px;
            }
            QComboBox:hover {
                border-color: #38bdf8;
            }
            QComboBox:focus {
                border-color: #0ea5e9;
                outline: none;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QLabel {
                font-size: 13px;
                color: #e2e8f0;
            }
            QLineEdit {
                padding: 7px 14px;
                border: 1px solid #2a3441;
                border-radius: 6px;
                font-size: 13px;
                background-color: #0f1419;
                color: #e2e8f0;
            }
            QLineEdit:focus {
                border-color: #0ea5e9;
                outline: none;
            }
            QTableWidget {
                border: 1px solid #2a3441;
                border-radius: 6px;
                gridline-color: #1e2630;
                font-size: 12px;
                background-color: #0f1419;
                color: #e2e8f0;
            }
            QHeaderView::section {
                background-color: #1e2630;
                padding: 9px;
                border: none;
                border-bottom: 1px solid #2a3441;
                font-weight: 600;
                color: #38bdf8;
                font-size: 12px;
            }
            QProgressBar {
                border: none;
                border-radius: 10px;
                background-color: #1e2630;
                height: 8px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 10px;
                background-color: #22c55e;
            }
            QCheckBox {
                font-size: 13px;
                color: #e2e8f0;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
                border-radius: 4px;
                border: 1px solid #2a3441;
                background-color: #0f1419;
            }
            QCheckBox::indicator:checked {
                background-color: #0ea5e9;
                border-color: #0ea5e9;
            }
            QTextEdit {
                background-color: #0f1419;
                color: #cbd5e1;
                border: 1px solid #2a3441;
                border-radius: 6px;
                font-family: Consolas, "Courier New", monospace;
                font-size: 12px;
            }
            QSpinBox, QDoubleSpinBox {
                padding: 6px;
                border: 1px solid #2a3441;
                border-radius: 6px;
                background-color: #0f1419;
                color: #e2e8f0;
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #0ea5e9;
            }
            QSplitter::handle {
                background-color: #2a3441;
            }
            QToolTip {
                background-color: #1e2630;
                color: #e2e8f0;
                border: 1px solid #38bdf8;
                border-radius: 4px;
                padding: 6px;
                font-size: 12px;
            }
        """)

    def create_menu(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background-color: #0b0f14;
                color: #cbd5e1;
                font-size: 13px;
                padding: 3px 10px;
                border-bottom: 1px solid #1e2630;
            }
            QMenuBar::item:selected {
                background-color: #0ea5e9;
                color: white;
                border-radius: 4px;
            }
            QMenu {
                background-color: #161d27;
                border: 1px solid #2a3441;
                padding: 5px;
                font-size: 13px;
            }
            QMenu::item {
                padding: 7px 26px;
                border-radius: 4px;
                color: #e2e8f0;
            }
            QMenu::item:selected {
                background-color: #1e3a5f;
                color: #38bdf8;
            }
        """)

        file_menu = menubar.addMenu("文件")
        open_action = QAction("打开文件 (Ctrl+O)", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        help_menu = menubar.addMenu("帮助")
        about_action = QAction("关于 WaveCraft", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        tips_action = QAction("使用提示", self)
        tips_action.triggered.connect(self.show_tips)
        help_menu.addAction(tips_action)

    def create_toolbar(self):
        toolbar = QToolBar()
        toolbar.setMovable(False)
        toolbar.setStyleSheet("""
            QToolBar {
                background-color: #0b0f14;
                border: none;
                spacing: 10px;
                padding: 8px 18px;
                border-bottom: 1px solid #1e2630;
            }
            QToolBar QPushButton {
                background-color: #1e293b;
                color: #e2e8f0;
                border: 1px solid #334155;
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 12px;
            }
            QToolBar QPushButton:hover {
                background-color: #0ea5e9;
                border-color: #0ea5e9;
                color: white;
            }
            QToolBar QLabel {
                color: #94a3b8;
                font-size: 12px;
            }
        """)

        open_btn = QPushButton("打开文件")
        open_btn.setToolTip("加载 Multiwfn 支持的波函数文件 (.fch/.wfn/.mwfn 等)")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)

        toolbar.addSeparator()

        file_label_title = QLabel("当前文件:")
        file_label_title.setStyleSheet("color: #64748b;")
        toolbar.addWidget(file_label_title)

        self.file_label = QLabel("未加载")
        self.file_label.setStyleSheet("color: #38bdf8; font-weight: 500;")
        toolbar.addWidget(self.file_label)

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        self.addToolBar(toolbar)

    def create_statusbar(self):
        self.statusbar = QStatusBar()
        self.statusbar.setStyleSheet("""
            QStatusBar {
                background-color: #0b0f14;
                color: #94a3b8;
                font-size: 12px;
                border-top: 1px solid #1e2630;
            }
        """)
        self.statusbar.showMessage("就绪 - 请打开文件开始分析")
        self.setStatusBar(self.statusbar)

        self.status_progress = QProgressBar()
        self.status_progress.setMinimumWidth(220)
        self.status_progress.setMaximumHeight(16)
        self.status_progress.setVisible(False)
        self.status_progress.setStyleSheet("""
            QProgressBar {
                border: none;
                border-radius: 8px;
                background-color: #1e2630;
                height: 6px;
                text-align: center;
            }
            QProgressBar::chunk {
                border-radius: 8px;
                background-color: #22c55e;
            }
        """)
        self.statusbar.addPermanentWidget(self.status_progress)

    def create_main_layout(self):
        self.tab_widget = QTabWidget()
        self.tab_widget.setIconSize(QSize(20, 20))
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.setToolTip("按功能分类的模块标签页，可在各模块中进行可视化分析")

        self.file_tab = FileManagerTab()
        self.function_menu_tab = FunctionMenuTab()
        self.structure_tab = StructureViewerTab()
        self.realspace_tab = RealSpaceAnalyzerTab()
        self.charge_tab = ChargeAnalysisTab()
        self.bond_tab = BondAnalysisTab()
        self.orbital_tab = OrbitalBondTab()
        self.dos_tab = DOSSpectrumTab()
        self.spectrum_tab = SpectrumAnalyzerTab()
        self.weak_tab = WeakInteractionTab()
        self.advanced_tab = AdvancedToolsTab()

        self.tab_widget.addTab(self.file_tab, "文件管理")
        self.tab_widget.addTab(self.function_menu_tab, "功能菜单")
        self.tab_widget.addTab(self.structure_tab, "结构与轨道")
        self.tab_widget.addTab(self.realspace_tab, "实空间分析")
        self.tab_widget.addTab(self.charge_tab, "电荷分析")
        self.tab_widget.addTab(self.bond_tab, "键级分析")
        self.tab_widget.addTab(self.orbital_tab, "轨道分析")
        self.tab_widget.addTab(self.dos_tab, "DOS/态密度")
        self.tab_widget.addTab(self.spectrum_tab, "光谱分析")
        self.tab_widget.addTab(self.weak_tab, "弱相互作用")
        self.tab_widget.addTab(self.advanced_tab, "高级工具")

        self.setCentralWidget(self.tab_widget)
        self.file_tab.file_selected.connect(self.on_file_selected)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择输入文件", "",
            "Multiwfn输入文件 (*.fch *.fchk *.mwfn *.wfn *.wfx *.molden *.pdb);;所有文件 (*.*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path):
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "错误", "文件不存在")
            return

        self.current_file = file_path
        filename = os.path.basename(file_path)
        self.file_label.setText(filename)
        self.statusbar.showMessage(f"已加载: {filename}")

        self.file_tab.set_input_file(file_path)
        self.function_menu_tab.set_input_file(file_path)
        self.structure_tab.set_input_file(file_path)
        self.realspace_tab.set_input_file(file_path)
        self.charge_tab.set_input_file(file_path)
        self.bond_tab.set_input_file(file_path)
        self.orbital_tab.set_input_file(file_path)
        self.dos_tab.set_input_file(file_path)
        self.spectrum_tab.set_input_file(file_path)
        self.weak_tab.set_input_file(file_path)
        self.advanced_tab.set_input_file(file_path)

        self.tab_widget.setCurrentIndex(1)
        QMessageBox.information(self, "加载成功", f"已加载文件: {filename}\n请切换到对应功能模块进行分析。")

    def on_file_selected(self, file_path):
        self.load_file(file_path)

    def show_about(self):
        about_text = """<h2 style='color:#38bdf8;'>WaveCraft - Multiwfn中文版可视化分析平台</h2>
<p><b>版本:</b> 3.1</p>
<p><b>核心功能模块:</b></p>
<ul>
<li><b>文件管理</b> - 支持多种波函数文件格式加载与管理</li>
<li><b>功能菜单</b> - 完整模拟Multiwfn中文版命令导航(112个子功能)</li>
<li><b>结构与轨道</b> - 分子结构显示与分子轨道可视化</li>
<li><b>实空间分析</b> - 电子密度、ELF、ESP等22种实空间函数热图</li>
<li><b>电荷分析</b> - 16种原子电荷计算方法</li>
<li><b>键级分析</b> - Mayer、Wiberg、Fuzzy等多种键级计算</li>
<li><b>轨道分析</b> - 轨道成分分析与轨道相互作用</li>
<li><b>DOS/态密度</b> - 总态密度、分态密度、OPDOS、COHP等</li>
<li><b>光谱分析</b> - IR、Raman、UV-Vis、ECD、NMR等光谱</li>
<li><b>弱相互作用</b> - NCI/IGM/mIGM/IGMH/DORI/Hirshfeld surface等</li>
<li><b>高级工具</b> - AIM、芳香性、激发态分析、文件导出等</li>
</ul>
<p><b>使用说明:</b></p>
<ol>
<li>通过"文件管理"Tab或工具栏打开波函数文件(.fch/.fchk等)</li>
<li>切换到对应功能模块Tab</li>
<li>设置计算参数后点击"计算"按钮</li>
<li>查看可视化图表与数据表格，并可导出为TXT/CSV/Excel</li>
</ol>"""
        QMessageBox.about(self, "关于 WaveCraft", about_text)

    def show_tips(self):
        tips = """<h3 style='color:#38bdf8;'>使用提示</h3>
<ul>
<li><b>功能菜单</b>：左侧树状列表完整对应Multiwfn主菜单(0-26,100,200,300)，点击子菜单后在右侧配置参数并执行。</li>
<li><b>参数说明</b>：将鼠标悬停在选项、输入框或按钮上即可查看详细功能说明。</li>
<li><b>数据导出</b>：每个模块的结果区域均提供"导出TXT/CSV/Excel"按钮，支持导出表格数据和原始输出。</li>
<li><b>弱相互作用</b>：支持NCI/IGM/mIGM/IGMH/DORI/aRDG/Hirshfeld surface等多种方法，可生成散点图或cube文件。</li>
<li><b>工作目录</b>：计算生成的cube、chg、txt等文件默认保存在输入文件所在目录。</li>
<li><b>光谱分析</b>：需要输入文件包含对应的振动/激发数据，否则可能无法解析。</li>
</ul>"""
        QMessageBox.information(self, "使用提示", tips)


def main():
    app = QApplication(sys.argv)
    app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    app.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    app.setStyle("Fusion")

    # 设置全局字体
    font = QFont("Microsoft YaHei", 9)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    window = MainWindow()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
