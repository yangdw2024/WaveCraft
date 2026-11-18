#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
功能菜单Tab - 中文版Multiwfn完整命令导航

完整模拟Multiwfn 3.8主菜单(0-26,100,200,300)及其全部子菜单，
提供可视化参数配置、命令生成、结果展示和数据导出。
左侧树形菜单导航，右侧动态参数配置面板+结果显示区。
"""
import os
import re

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTreeWidget, QTreeWidgetItem, QGroupBox, QMessageBox,
    QTextEdit, QSplitter, QProgressBar, QLineEdit, QComboBox,
    QSpinBox, QDoubleSpinBox, QFormLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QStackedWidget, QCheckBox,
    QScrollArea, QSizePolicy, QApplication,
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor, QBrush

from ..core.worker import CalculationWorker
from ..utils.menu_data import MultiwfnMenu
from ..utils.output_parser import OutputParser
from ..utils.export_utils import ExportButtonWidget


# ──────────────────── 深色主题样式常量 ────────────────────
_DARK_BG = "#0f1419"
_DARK_BG2 = "#1e2630"
_DARK_BG3 = "#243040"
_DARK_TEXT = "#e2e8f0"
_DARK_TEXT2 = "#94a3b8"
_DARK_ACCENT = "#38bdf8"
_DARK_BORDER = "#2a3441"
_DARK_GRID = "#334155"
_DARK_SELECT = "#1e3a5f"
_DARK_INPUT_BG = "#0f1419"
_DARK_GROUP = "#1a2332"


class FunctionMenuTab(QWidget):
    """中文版Multiwfn功能菜单导航 - 完整主菜单+子菜单"""

    def __init__(self):
        super().__init__()
        self.current_file = ""
        self._worker = None
        self._param_widgets = {}       # key → 输入控件
        self._current_template = None  # 当前选中的子菜单模板
        self._last_output = ""         # 最近一次原始输出
        self._last_result = {}         # 最近一次完整结果字典
        self._last_parsed = None       # 最近一次解析结果
        self._last_parsed_type = None  # 最近一次结果类型
        self._init_ui()

    # ──────────────────────── 界面初始化 ────────────────────────

    def _init_ui(self):
        """构建主界面：左侧树形菜单 + 右侧配置/结果区"""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(6, 6, 6, 6)

        # ====== 左侧：功能菜单树 ======
        left_panel = self._build_left_panel()
        main_layout.addWidget(left_panel, stretch=1)

        # ====== 右侧：参数配置 + 结果展示 ======
        right_panel = self._build_right_panel()
        main_layout.addWidget(right_panel, stretch=3)

        self.setLayout(main_layout)

    def _build_left_panel(self):
        """构建左侧树形菜单面板"""
        group = QGroupBox("Multiwfn 中文功能菜单")
        group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_TEXT}; font-weight: bold; "
            f"background-color: {_DARK_GROUP}; border: 1px solid {_DARK_BORDER}; "
            f"border-radius: 6px; margin-top: 10px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}"
        )
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # 操作提示
        help_label = QLabel(
            "点击主菜单展开/折叠，点击子菜单在右侧配置参数并执行计算。"
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet(
            f"color: {_DARK_TEXT2}; font-size: 11px; padding: 2px 4px;"
        )
        help_label.setToolTip("功能菜单使用说明")
        layout.addWidget(help_label)

        # 搜索框
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索功能名称...")
        self.search_input.setStyleSheet(
            f"QLineEdit {{ background-color: {_DARK_INPUT_BG}; color: {_DARK_TEXT}; "
            f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 4px 8px; font-size: 12px; }}"
            f"QLineEdit:focus {{ border-color: {_DARK_ACCENT}; }}"
        )
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.setToolTip("输入关键词筛选菜单项")
        layout.addWidget(self.search_input)

        # 树形菜单
        self.menu_tree = QTreeWidget()
        self.menu_tree.setHeaderLabel("主菜单 → 子菜单")
        self.menu_tree.setMinimumWidth(340)
        self.menu_tree.setMaximumWidth(500)
        self.menu_tree.setAlternatingRowColors(True)
        self.menu_tree.setStyleSheet(
            f"QTreeWidget {{ background-color: {_DARK_BG}; color: {_DARK_TEXT}; "
            f"font-size: 12px; border: 1px solid {_DARK_BORDER}; border-radius: 4px; "
            f"alternate-background-color: {_DARK_BG2}; }}"
            f"QTreeWidget::item:selected {{ background-color: {_DARK_SELECT}; }}"
            f"QTreeWidget::item:hover {{ background-color: #263850; }}"
            f"QHeaderView::section {{ background-color: {_DARK_GRID}; color: {_DARK_TEXT}; "
            f"font-weight: bold; border: none; padding: 4px; }}"
        )
        self._build_menu_tree()
        self.menu_tree.itemClicked.connect(self._on_menu_selected)
        layout.addWidget(self.menu_tree)

        return group

    def _build_right_panel(self):
        """构建右侧面板：上方参数配置 + 下方结果展示"""
        right_splitter = QSplitter(Qt.Vertical)

        # ── 上半：参数配置区（可滚动） ──
        param_scroll = QScrollArea()
        param_scroll.setWidgetResizable(True)
        param_scroll.setStyleSheet(
            f"QScrollArea {{ border: none; background-color: transparent; }}"
            f"QScrollBar:vertical {{ background-color: {_DARK_BG2}; width: 8px; }}"
            f"QScrollBar::handle:vertical {{ background-color: {_DARK_GRID}; border-radius: 4px; }}"
        )

        self.param_container = QWidget()
        self.param_outer_layout = QVBoxLayout(self.param_container)
        self.param_outer_layout.setContentsMargins(4, 4, 4, 4)

        self.param_group = QGroupBox("参数配置")
        self.param_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_TEXT}; font-weight: bold; "
            f"background-color: {_DARK_GROUP}; border: 1px solid {_DARK_BORDER}; "
            f"border-radius: 6px; margin-top: 10px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}"
        )
        self.param_layout = QVBoxLayout(self.param_group)

        # 功能描述
        self.desc_label = QLabel("请在左侧选择功能菜单项，配置参数后执行计算")
        self.desc_label.setWordWrap(True)
        self.desc_label.setStyleSheet(
            f"color: {_DARK_TEXT2}; font-size: 13px; padding: 6px;"
        )
        self.desc_label.setToolTip("当前选中功能的名称、说明和命令路径")
        self.param_layout.addWidget(self.desc_label)

        # 命令预览
        self.cmd_preview = QLabel("")
        self.cmd_preview.setWordWrap(True)
        self.cmd_preview.setStyleSheet(
            f"color: {_DARK_TEXT2}; font-size: 11px; padding: 2px 6px; "
            f"background-color: {_DARK_BG}; border: 1px solid {_DARK_BORDER}; "
            f"border-radius: 3px; font-family: Consolas, monospace;"
        )
        self.cmd_preview.setToolTip("生成的Multiwfn命令序列预览")
        self.cmd_preview.setVisible(False)
        self.param_layout.addWidget(self.cmd_preview)

        # 参数表单
        self.param_form = QFormLayout()
        self.param_form.setLabelAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.param_form.setSpacing(6)
        self.param_layout.addLayout(self.param_form)

        self.param_layout.addStretch()

        # 执行按钮
        btn_row = QHBoxLayout()
        self.run_btn = QPushButton("执行计算")
        self.run_btn.setStyleSheet(
            f"QPushButton {{ background-color: #0ea5e9; color: white; font-weight: bold; "
            f"padding: 10px 24px; border-radius: 6px; font-size: 14px; }}"
            f"QPushButton:hover {{ background-color: #0284c7; }}"
            f"QPushButton:pressed {{ background-color: #0369a1; }}"
            f"QPushButton:disabled {{ background-color: #334155; color: #64748b; }}"
        )
        self.run_btn.setEnabled(False)
        self.run_btn.setToolTip("根据当前选择的菜单和参数执行Multiwfn计算")
        self.run_btn.clicked.connect(self._run_calculation)
        btn_row.addWidget(self.run_btn)

        self.cmd_copy_btn = QPushButton("复制命令")
        self.cmd_copy_btn.setStyleSheet(
            f"QPushButton {{ background-color: #334155; color: {_DARK_TEXT}; "
            f"padding: 10px 16px; border-radius: 6px; font-size: 13px; }}"
            f"QPushButton:hover {{ background-color: #475569; }}"
            f"QPushButton:disabled {{ background-color: #1e293b; color: #475569; }}"
        )
        self.cmd_copy_btn.setEnabled(False)
        self.cmd_copy_btn.setToolTip("复制生成的命令序列到剪贴板")
        self.cmd_copy_btn.clicked.connect(self._copy_commands)
        btn_row.addWidget(self.cmd_copy_btn)

        self.param_layout.addLayout(btn_row)

        self.param_outer_layout.addWidget(self.param_group)
        param_scroll.setWidget(self.param_container)
        right_splitter.addWidget(param_scroll)

        # ── 下半：结果展示区 ──
        result_group = QGroupBox("计算结果")
        result_group.setStyleSheet(
            f"QGroupBox {{ color: {_DARK_TEXT}; font-weight: bold; "
            f"background-color: {_DARK_GROUP}; border: 1px solid {_DARK_BORDER}; "
            f"border-radius: 6px; margin-top: 10px; padding-top: 16px; }}"
            f"QGroupBox::title {{ subcontrol-origin: margin; left: 10px; padding: 0 5px; }}"
        )
        result_layout = QVBoxLayout(result_group)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {_DARK_BG2}; border: 1px solid {_DARK_BORDER}; "
            f"border-radius: 4px; text-align: center; color: {_DARK_TEXT}; height: 18px; }}"
            f"QProgressBar::chunk {{ background-color: {_DARK_ACCENT}; border-radius: 3px; }}"
        )
        result_layout.addWidget(self.progress_bar)

        # 堆叠页面：文本输出 / 数据表格
        self.result_stack = QStackedWidget()

        # 文本输出页
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("计算输出将显示在这里...")
        self.output_text.setToolTip("Multiwfn原始输出文本")
        self.output_text.setStyleSheet(
            f"QTextEdit {{ background-color: {_DARK_BG}; color: {_DARK_TEXT}; "
            f"font-family: Consolas, 'Courier New', monospace; font-size: 12px; "
            f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 6px; }}"
        )
        self.result_stack.addWidget(self.output_text)

        # 数据表格页
        self.result_table = QTableWidget()
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.result_table.setAlternatingRowColors(True)
        self.result_table.setStyleSheet(
            f"QTableWidget {{ background-color: {_DARK_BG}; color: {_DARK_TEXT}; "
            f"gridline-color: {_DARK_GRID}; alternate-background-color: {_DARK_BG2}; "
            f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; font-size: 12px; }}"
            f"QHeaderView::section {{ background-color: {_DARK_GRID}; color: {_DARK_TEXT}; "
            f"font-weight: bold; border: 1px solid #475569; padding: 4px; }}"
            f"QTableWidget::item:selected {{ background-color: {_DARK_SELECT}; }}"
        )
        self.result_table.setToolTip("解析后的结构化数据，支持导出")
        self.result_stack.addWidget(self.result_table)

        result_layout.addWidget(self.result_stack)

        # 导出按钮
        self.export_widget = ExportButtonWidget(
            self,
            data_provider=self._get_export_data,
            default_filename="function_menu_result",
        )
        self.export_widget.setToolTip("将当前结果导出为TXT/CSV/Excel格式")
        result_layout.addWidget(self.export_widget)

        right_splitter.addWidget(result_group)
        right_splitter.setSizes([380, 520])

        return right_splitter

    # ──────────────────────── 菜单树构建 ────────────────────────

    def _build_menu_tree(self):
        """构建主菜单+子菜单树形结构"""
        MultiwfnMenu._ensure_templates()
        main_items = MultiwfnMenu.get_main_menu_items()

        for menu_id, menu_info in main_items:
            tree_item = QTreeWidgetItem(self.menu_tree)
            tree_item.setText(0, f"{menu_id:>3}  {menu_info['name']}")
            tree_item.setToolTip(
                0,
                f"主菜单 {menu_id}: {menu_info['name']}\n"
                f"{menu_info['desc']}\n"
                f"点击展开查看该菜单下的子选项",
            )
            tree_item.setData(0, Qt.UserRole, {"type": "main", "id": menu_id})
            # 主菜单项加粗
            font = tree_item.font(0)
            font.setBold(True)
            tree_item.setFont(0, font)

            sub_menus = MultiwfnMenu.get_sub_menu(menu_id)
            for sub_id, sub_info in sorted(
                sub_menus.items(),
                key=lambda x: int(x[0]) if x[0].isdigit() else 999,
            ):
                sub_item = QTreeWidgetItem(tree_item)
                sub_item.setText(0, f"  {sub_id}. {sub_info['name']}")
                sub_item.setToolTip(
                    0,
                    f"子菜单 {menu_id}-{sub_id}: {sub_info['name']}\n"
                    f"{sub_info.get('desc', '')}\n"
                    f"点击后在右侧配置参数并执行计算",
                )
                sub_item.setData(
                    0, Qt.UserRole, {"type": "sub", "main": menu_id, "sub": sub_id}
                )

        self.menu_tree.expandToDepth(0)

    def _on_search(self, text):
        """搜索框文本变化时过滤菜单项"""
        keyword = text.strip().lower()
        root = self.menu_tree.invisibleRootItem()
        for i in range(root.childCount()):
            main_item = root.child(i)
            if not keyword:
                main_item.setHidden(False)
                for j in range(main_item.childCount()):
                    main_item.child(j).setHidden(False)
                continue

            main_text = main_item.text(0).lower()
            main_match = keyword in main_text

            any_sub_visible = False
            for j in range(main_item.childCount()):
                sub_item = main_item.child(j)
                sub_text = sub_item.text(0).lower()
                sub_tooltip = sub_item.toolTip(0).lower()
                if keyword in sub_text or keyword in sub_tooltip:
                    sub_item.setHidden(False)
                    any_sub_visible = True
                else:
                    sub_item.setHidden(True)

            if main_match or any_sub_visible:
                main_item.setHidden(False)
                if any_sub_visible:
                    main_item.setExpanded(True)
            else:
                main_item.setHidden(True)

    # ──────────────────────── 菜单选中处理 ────────────────────────

    def _on_menu_selected(self, item, column):
        """处理菜单项点击：主菜单展开/折叠，子菜单更新参数面板"""
        data = item.data(0, Qt.UserRole)
        if not data:
            return

        if data.get("type") == "main":
            # 点击主菜单项：展开/折叠
            item.setExpanded(not item.isExpanded())
            return

        if data.get("type") != "sub":
            return

        main_id = data["main"]
        sub_id = data["sub"]
        template = MultiwfnMenu.get_command_template(main_id, sub_id)
        self._current_template = template
        self._update_param_panel()

    # ──────────────────────── 参数面板 ────────────────────────

    def _update_param_panel(self):
        """根据当前模板刷新右侧参数配置面板"""
        # 清空旧参数控件
        while self.param_form.rowCount() > 0:
            self.param_form.removeRow(0)
        self._param_widgets.clear()

        if not self._current_template:
            self.desc_label.setText("请在左侧选择功能菜单项")
            self.run_btn.setEnabled(False)
            self.cmd_copy_btn.setEnabled(False)
            self.cmd_preview.setVisible(False)
            return

        name = self._current_template.get("name", "")
        desc = self._current_template.get("desc", "")
        commands = self._current_template.get("commands", [])
        path_str = " → ".join(str(c) for c in commands[:6])
        if len(commands) > 6:
            path_str += " → ..."

        # 更新描述
        self.desc_label.setText(
            f"<b style='color:{_DARK_ACCENT};'>{name}</b><br>"
            f"<span style='color:{_DARK_TEXT};'>{desc}</span><br>"
            f"<span style='color:{_DARK_TEXT2};'>Multiwfn路径: {path_str}</span>"
        )
        self.desc_label.setToolTip(
            f"{name}\n{desc}\n命令序列: {' -> '.join(str(c) for c in commands)}"
        )

        # 命令预览
        self._refresh_cmd_preview()

        # 启用按钮
        self.run_btn.setEnabled(True)
        self.run_btn.setToolTip(f"执行 {name}: {desc}")
        self.cmd_copy_btn.setEnabled(True)

        # 构建参数控件
        params = self._current_template.get("params", [])
        if not params:
            label = QLabel("<i>该功能无需额外参数，直接点击执行计算即可</i>")
            label.setStyleSheet(f"color: #64748b; font-size: 12px;")
            label.setToolTip("此子菜单没有可配置的参数")
            self.param_form.addRow(label, QLabel(""))
        else:
            for param in params:
                widget = self._create_param_widget(param)
                tooltip = param.get("desc", param.get("name", ""))
                key = param.get("key", param.get("name", ""))

                if param.get("type") == "checkbox":
                    self.param_form.addRow(widget)
                else:
                    label = QLabel(param.get("name", key))
                    label.setToolTip(tooltip)
                    label.setStyleSheet(f"color: {_DARK_TEXT}; font-size: 12px;")
                    self.param_form.addRow(label, widget)

                self._param_widgets[key] = widget
                # 参数值变化时更新命令预览
                self._connect_widget_signal(widget, self._refresh_cmd_preview)

    def _connect_widget_signal(self, widget, callback):
        """为控件连接值变化信号"""
        if isinstance(widget, QSpinBox) or isinstance(widget, QDoubleSpinBox):
            widget.valueChanged.connect(callback)
        elif isinstance(widget, QComboBox):
            widget.currentIndexChanged.connect(callback)
        elif isinstance(widget, QLineEdit):
            widget.textChanged.connect(callback)
        elif isinstance(widget, QCheckBox):
            widget.stateChanged.connect(callback)

    def _create_param_widget(self, param):
        """根据参数定义创建对应的输入控件"""
        ptype = param.get("type", "combo")

        if ptype == "combo":
            widget = QComboBox()
            widget.addItems(param.get("options", []))
            default = param.get("default", 0)
            if isinstance(default, int) and 0 <= default < widget.count():
                widget.setCurrentIndex(default)
            elif isinstance(default, str) and default in param.get("options", []):
                widget.setCurrentText(default)
            widget.setStyleSheet(
                f"QComboBox {{ background-color: {_DARK_INPUT_BG}; color: {_DARK_TEXT}; "
                f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 4px 8px; "
                f"font-size: 12px; min-width: 120px; }}"
                f"QComboBox::drop-down {{ border: none; }}"
                f"QComboBox QAbstractItemView {{ background-color: {_DARK_BG2}; "
                f"color: {_DARK_TEXT}; selection-background-color: {_DARK_SELECT}; }}"
            )
            desc = param.get("desc", "")
            if desc:
                widget.setToolTip(desc)

        elif ptype in ("int", "spin"):
            widget = QSpinBox()
            widget.setRange(param.get("min", 0), param.get("max", 9999))
            widget.setValue(param.get("default", 0))
            widget.setStyleSheet(
                f"QSpinBox {{ background-color: {_DARK_INPUT_BG}; color: {_DARK_TEXT}; "
                f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 4px 8px; "
                f"font-size: 12px; }}"
                f"QSpinBox::up-button, QSpinBox::down-button {{ "
                f"background-color: {_DARK_GRID}; border: none; width: 16px; }}"
            )
            if param.get("desc"):
                widget.setToolTip(param["desc"])

        elif ptype == "double":
            widget = QDoubleSpinBox()
            widget.setRange(param.get("min", -9999.0), param.get("max", 9999.0))
            widget.setValue(param.get("default", 0.0))
            widget.setSingleStep(param.get("step", 0.1))
            widget.setDecimals(param.get("decimals", 3))
            widget.setStyleSheet(
                f"QDoubleSpinBox {{ background-color: {_DARK_INPUT_BG}; color: {_DARK_TEXT}; "
                f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 4px 8px; "
                f"font-size: 12px; }}"
                f"QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{ "
                f"background-color: {_DARK_GRID}; border: none; width: 16px; }}"
            )
            if param.get("desc"):
                widget.setToolTip(param["desc"])

        elif ptype == "checkbox":
            widget = QCheckBox(param.get("name", ""))
            widget.setChecked(bool(param.get("default", False)))
            widget.setStyleSheet(
                f"QCheckBox {{ color: {_DARK_TEXT}; font-size: 12px; spacing: 8px; }}"
                f"QCheckBox::indicator {{ width: 16px; height: 16px; "
                f"border: 1px solid {_DARK_BORDER}; border-radius: 3px; "
                f"background-color: {_DARK_INPUT_BG}; }}"
                f"QCheckBox::indicator:checked {{ background-color: {_DARK_ACCENT}; "
                f"border-color: {_DARK_ACCENT}; }}"
            )
            if param.get("desc"):
                widget.setToolTip(param["desc"])

        elif ptype == "line":
            widget = QLineEdit(str(param.get("default", "")))
            widget.setPlaceholderText(param.get("desc", ""))
            widget.setStyleSheet(
                f"QLineEdit {{ background-color: {_DARK_INPUT_BG}; color: {_DARK_TEXT}; "
                f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 4px 8px; "
                f"font-size: 12px; }}"
                f"QLineEdit:focus {{ border-color: {_DARK_ACCENT}; }}"
            )
            if param.get("desc"):
                widget.setToolTip(param["desc"])

        else:
            # 兜底：文本输入
            widget = QLineEdit(str(param.get("default", "")))
            widget.setPlaceholderText(param.get("desc", ""))
            widget.setStyleSheet(
                f"QLineEdit {{ background-color: {_DARK_INPUT_BG}; color: {_DARK_TEXT}; "
                f"border: 1px solid {_DARK_BORDER}; border-radius: 4px; padding: 4px 8px; "
                f"font-size: 12px; }}"
            )
            if param.get("desc"):
                widget.setToolTip(param["desc"])

        return widget

    # ──────────────────────── 命令生成 ────────────────────────

    def _get_param_values(self):
        """收集所有参数控件的当前值，对ComboBox进行映射"""
        values = {}
        template = self._current_template
        if not template:
            return values

        for key, widget in self._param_widgets.items():
            if isinstance(widget, QComboBox):
                val = widget.currentText()
                # grid_map 映射（中文 → 数字）
                if "grid_map" in template:
                    values[key] = template["grid_map"].get(val, val)
                # output_map 映射
                elif "output_map" in template:
                    values[key] = template["output_map"].get(val, val)
                else:
                    values[key] = val
            elif isinstance(widget, QSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QDoubleSpinBox):
                values[key] = widget.value()
            elif isinstance(widget, QCheckBox):
                values[key] = "1" if widget.isChecked() else "0"
            elif isinstance(widget, QLineEdit):
                values[key] = widget.text()
        return values

    def _resolve_commands(self):
        """根据模板和参数生成最终命令序列"""
        if not self._current_template:
            return []

        template = self._current_template
        commands = list(template.get("commands", []))
        param_values = self._get_param_values()

        # 替换占位符 {key} → 实际值
        resolved = []
        for cmd in commands:
            cmd_str = str(cmd)
            if cmd_str.startswith("{") and cmd_str.endswith("}"):
                key = cmd_str[1:-1]
                value = param_values.get(key, cmd_str)
                resolved.append(str(value))
            else:
                resolved.append(cmd_str)

        return resolved

    def _refresh_cmd_preview(self):
        """刷新命令预览区域"""
        if not self._current_template:
            self.cmd_preview.setVisible(False)
            return

        resolved = self._resolve_commands()
        if resolved:
            preview = " → ".join(resolved)
            self.cmd_preview.setText(f"命令: {preview}")
            self.cmd_preview.setVisible(True)
        else:
            self.cmd_preview.setVisible(False)

    def _copy_commands(self):
        """复制生成的命令序列到剪贴板"""
        resolved = self._resolve_commands()
        if resolved:
            text = "\n".join(resolved)
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.cmd_copy_btn.setText("已复制!")
            QTimer.singleShot(1500, lambda: self.cmd_copy_btn.setText("复制命令"))

    # ──────────────────────── 计算执行 ────────────────────────

    def _run_calculation(self):
        """执行Multiwfn计算"""
        if not self.current_file:
            QMessageBox.warning(self, "警告", "请先加载输入文件")
            return

        if self._worker and self._worker.isRunning():
            QMessageBox.information(self, "提示", "计算正在进行中，请稍候...")
            return

        if not self._current_template:
            return

        commands = self._resolve_commands()
        work_dir = os.path.dirname(self.current_file)

        # 更新UI状态
        self.run_btn.setEnabled(False)
        self.run_btn.setText("计算中...")
        self.cmd_copy_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # 不确定进度
        self.output_text.clear()
        self.result_table.setRowCount(0)
        self.result_stack.setCurrentIndex(0)

        task_name = self._current_template.get("name", "功能菜单计算")
        self._worker = CalculationWorker(
            self.current_file, commands, work_dir,
            task_name=f"功能菜单: {task_name}",
            template=self._current_template,
        )
        self._worker.finished_ok.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def _on_finished(self, result):
        """计算成功完成"""
        try:
            output = result.get("output", "")
            self._last_output = output
            self._last_result = result
            self.output_text.setPlainText(output[:50000])

            template = result.get("template", {})
            result_type = template.get("result_type", "text")
            self._last_parsed_type = result_type

            # 根据结果类型选择解析方式
            parsed = None
            if result_type == "charge":
                parsed = OutputParser.parse_charges(output)
                if not parsed and result.get("chg_data"):
                    parsed = result.get("chg_data")
            elif result_type == "bond":
                parsed = OutputParser.parse_bond_orders(output)
            elif result_type == "dos":
                parsed = self._parse_dos_result(result, output)
            elif result_type == "spectrum":
                parsed = self._parse_spectrum_result(result, output)
            elif result_type == "nci":
                parsed = self._parse_nci(output)
            elif result_type == "cube":
                parsed = self._parse_cube_result(result, output)
            else:
                # text 或其他未指定类型
                parsed = self._parse_text_summary(output)

            self._last_parsed = parsed
            if parsed:
                self._show_parsed_data(parsed, result_type)

        except Exception as e:
            QMessageBox.warning(self, "错误", f"结果处理失败: {str(e)}")
        finally:
            self.run_btn.setEnabled(True)
            self.run_btn.setText("执行计算")
            self.cmd_copy_btn.setEnabled(True)
            self.progress_bar.setVisible(False)
            self._worker = None

    def _on_failed(self, error_msg):
        """计算失败"""
        QMessageBox.critical(self, "计算失败", error_msg[:1500])
        self.run_btn.setEnabled(True)
        self.run_btn.setText("执行计算")
        self.cmd_copy_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self._worker = None

    # ──────────────────────── 结果解析 ────────────────────────

    def _parse_nci(self, output):
        """解析NCI/IGM散点图数据"""
        data = []
        # 匹配 NCI 散点数据行：rho RDG ? sign_lambda2*rho ...
        pattern = re.compile(
            r"([-\d.Ee]+)\s+([-\d.Ee]+)\s+([-\d.Ee]+)\s+([-\d.Ee]+)\s+([-\d.Ee]+)"
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
                    # 过滤异常值
                    if -1.0 < sign_val < 1.0 and 0 < rdg < 10:
                        interaction = (
                            "吸引作用" if sign_val < -0.02
                            else "排斥作用" if sign_val > 0.02
                            else "范德华作用"
                        )
                        data.append({
                            "rho": rho,
                            "RDG": rdg,
                            "sign(λ₂)ρ": sign_val,
                            "相互作用类型": interaction,
                        })
                except ValueError:
                    continue
        return data

    def _parse_text_summary(self, output):
        """为text类型提取关键汇总行"""
        lines = output.strip().split("\n")
        summary = []
        keywords = [
            "energy", "Energy", "energy:", "Total energy",
            "charge", "Charge", "population", "Population",
            "bond order", "Bond order", "bondOrder", "Mayer",
            "NICS", "FLU", "HOMA", "MCI",
            "dipole", "Dipole",
            "Critical point", "critical point", "CP",
            ".excited", "Excited", "Excitation",
            "orbital", "Orbital", "HOMO", "LUMO",
            "frequency", "Frequency",
        ]
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("---") or stripped.startswith("=="):
                continue
            if any(kw in stripped for kw in keywords):
                summary.append({"关键信息": stripped})
                if len(summary) >= 25:
                    break
        if not summary:
            # 无关键词匹配时取最后若干非空行
            for line in lines[-50:]:
                stripped = line.strip()
                if stripped and not stripped.startswith("---"):
                    summary.append({"关键信息": stripped})
                    if len(summary) >= 15:
                        break
        return summary

    def _parse_cube_result(self, result, output):
        """解析cube文件结果，返回文件信息摘要"""
        cube_file = result.get("cube_file", "")
        if cube_file and os.path.exists(cube_file):
            size = os.path.getsize(cube_file)
            if size > 1024 * 1024:
                size_str = f"{size / 1024 / 1024:.2f} MB"
            else:
                size_str = f"{size / 1024:.2f} KB"
            info = {
                "状态": "Cube文件已生成",
                "文件路径": cube_file,
                "文件大小": size_str,
            }
            self._last_output = (
                output
                + f"\n\n--- Cube文件信息 ---\n"
                f"路径: {cube_file}\n"
                f"大小: {size_str}\n"
            )
            self.output_text.setPlainText(self._last_output[:50000])
            return info
        return {"状态": "未检测到cube文件", "文件路径": ""}

    def _parse_spectrum_result(self, result, output):
        """依次尝试用多种方式解析光谱数据"""
        # 先尝试读取已知的光谱数据文件
        spec_files = [
            "spectrum.txt", "UV-Vis.txt", "IR.txt", "Raman.txt",
            "ECD.txt", "VCD.txt", "NMR.txt", "ROA.txt",
        ]
        work_dir = os.path.dirname(self.current_file) if self.current_file else "."
        for fname in spec_files:
            fpath = os.path.join(work_dir, fname)
            if os.path.exists(fpath):
                parsed = OutputParser.parse_spectrum_data(fpath)
                if parsed:
                    return parsed

        # 依次尝试不同的解析方法
        for method in [
            OutputParser.parse_spectrum_data,
            OutputParser.parse_spectrum,
            OutputParser.parse_spectrum_table,
            OutputParser.parse_spectrum_lines,
        ]:
            try:
                parsed = method(output)
                if parsed:
                    return parsed
            except Exception:
                continue

        return {"状态": "未解析到光谱数据"}

    def _parse_dos_result(self, result, output):
        """依次尝试用多种方式解析DOS数据"""
        work_dir = os.path.dirname(self.current_file) if self.current_file else "."
        # 尝试读取已知DOS数据文件
        for fname in ["dos_data.txt", "DOS.dat", "dos_out.txt"]:
            fpath = os.path.join(work_dir, fname)
            if os.path.exists(fpath):
                parsed = OutputParser.parse_dos_data(fpath)
                if parsed and parsed.get("energy"):
                    return [
                        {"Energy": e, "DOS": d}
                        for e, d in zip(parsed["energy"], parsed["density"])
                    ]

        # 从原始输出中解析
        for method in [OutputParser.parse_dos, OutputParser.parse_dos_table]:
            try:
                parsed = method(output)
                if parsed:
                    if "energy" in parsed and "dos" in parsed:
                        return [
                            {"Energy": e, "DOS": d}
                            for e, d in zip(parsed["energy"], parsed["dos"])
                        ]
                    elif "energy" in parsed and "density" in parsed:
                        return [
                            {"Energy": e, "DOS": d}
                            for e, d in zip(parsed["energy"], parsed["density"])
                        ]
                    return parsed
            except Exception:
                continue

        return {"状态": "未解析到DOS数据"}

    # ──────────────────────── 结果展示 ────────────────────────

    def _show_parsed_data(self, parsed, result_type):
        """将解析后的结构化数据展示在表格中"""
        if not parsed:
            return

        # 将字典列表或嵌套字典统一转换为行列表
        display_data = parsed
        if isinstance(parsed, dict):
            # 光谱格式：frequency + intensity
            if "frequency" in parsed and "intensity" in parsed:
                display_data = [
                    {"Frequency": f, "Intensity": i}
                    for f, i in zip(parsed["frequency"], parsed["intensity"])
                ]
            # DOS格式：energy + dos
            elif "energy" in parsed and "dos" in parsed:
                display_data = [
                    {"Energy": e, "DOS": d}
                    for e, d in zip(parsed["energy"], parsed["dos"])
                ]
            elif "energy" in parsed and "density" in parsed:
                display_data = [
                    {"Energy": e, "DOS": d}
                    for e, d in zip(parsed["energy"], parsed["density"])
                ]
            # 简单键值对
            else:
                display_data = [
                    {"属性": k, "数值": v} for k, v in parsed.items()
                ]

        # 渲染到表格
        if (
            isinstance(display_data, list)
            and len(display_data) > 0
            and isinstance(display_data[0], dict)
        ):
            self.result_table.setRowCount(0)
            headers = list(display_data[0].keys())
            self.result_table.setColumnCount(len(headers))
            self.result_table.setHorizontalHeaderLabels(headers)

            for i, record in enumerate(display_data):
                self.result_table.insertRow(i)
                for j, key in enumerate(headers):
                    value = record.get(key, "")
                    if isinstance(value, float):
                        text = f"{value:.6f}"
                    else:
                        text = str(value)
                    item = QTableWidgetItem(text)
                    if isinstance(value, str):
                        item.setTextAlignment(Qt.AlignCenter)
                    else:
                        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                    self.result_table.setItem(i, j, item)

            self.result_stack.setCurrentIndex(1)

        elif isinstance(display_data, dict):
            # 简单键值表格
            self.result_table.setRowCount(0)
            self.result_table.setColumnCount(2)
            self.result_table.setHorizontalHeaderLabels(["属性", "数值"])
            for i, (key, value) in enumerate(display_data.items()):
                self.result_table.insertRow(i)
                self.result_table.setItem(i, 0, QTableWidgetItem(str(key)))
                self.result_table.setItem(i, 1, QTableWidgetItem(str(value)))
            self.result_stack.setCurrentIndex(1)

    # ──────────────────────── 导出 ────────────────────────

    def _get_export_data(self):
        """为导出按钮提供数据"""
        metadata = {
            "功能": self._current_template.get("name", "") if self._current_template else "",
            "说明": self._current_template.get("desc", "") if self._current_template else "",
        }

        # 优先导出结构化表格数据
        if self.result_stack.currentIndex() == 1 and self._last_parsed:
            parsed = self._last_parsed
            if isinstance(parsed, list) and len(parsed) > 0:
                if isinstance(parsed[0], dict):
                    return parsed, list(parsed[0].keys()), metadata
                else:
                    return [{"value": v} for v in parsed], ["value"], metadata
            elif isinstance(parsed, dict):
                if "frequency" in parsed and "intensity" in parsed:
                    records = [
                        {"Frequency": f, "Intensity": i}
                        for f, i in zip(parsed["frequency"], parsed["intensity"])
                    ]
                    return records, ["Frequency", "Intensity"], metadata
                elif "energy" in parsed and "dos" in parsed:
                    records = [
                        {"Energy": e, "DOS": d}
                        for e, d in zip(parsed["energy"], parsed["dos"])
                    ]
                    return records, ["Energy", "DOS"], metadata
                elif "energy" in parsed and "density" in parsed:
                    records = [
                        {"Energy": e, "DOS": d}
                        for e, d in zip(parsed["energy"], parsed["density"])
                    ]
                    return records, ["Energy", "DOS"], metadata
                else:
                    records = [{"属性": k, "数值": v} for k, v in parsed.items()]
                    return records, ["属性", "数值"], metadata

        # 兜底：导出原始文本
        if self._last_output:
            return [{"output": self._last_output}], ["output"], metadata
        return None

    # ──────────────────────── 外部接口 ────────────────────────

    def set_input_file(self, file_path):
        """设置当前输入文件路径"""
        self.current_file = file_path


