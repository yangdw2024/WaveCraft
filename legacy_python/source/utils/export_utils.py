#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用结果导出工具 - 为各Tab提供统一的数据导出支持
"""
import os
import csv
from datetime import datetime
from pathlib import Path

from PyQt5.QtWidgets import (
    QWidget, QPushButton, QFileDialog, QMessageBox, QHBoxLayout
)
from PyQt5.QtCore import Qt


class ExportButtonWidget(QWidget):
    """通用导出按钮组件，支持 txt/csv/xlsx"""

    def __init__(self, parent=None, data_provider=None, default_filename="result"):
        super().__init__(parent)
        self.data_provider = data_provider  # 函数，返回 (data_list, headers, metadata)
        self.default_filename = default_filename
        self._init_ui()

    def _init_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self.export_txt_btn = QPushButton("导出 TXT")
        self.export_txt_btn.setToolTip("导出为纯文本格式")
        self.export_txt_btn.clicked.connect(lambda: self._do_export("txt"))
        layout.addWidget(self.export_txt_btn)

        self.export_csv_btn = QPushButton("导出 CSV")
        self.export_csv_btn.setToolTip("导出为CSV格式，可用Excel打开")
        self.export_csv_btn.clicked.connect(lambda: self._do_export("csv"))
        layout.addWidget(self.export_csv_btn)

        self.export_xlsx_btn = QPushButton("导出 Excel")
        self.export_xlsx_btn.setToolTip("导出为Excel工作簿")
        self.export_xlsx_btn.clicked.connect(lambda: self._do_export("xlsx"))
        layout.addWidget(self.export_xlsx_btn)

        layout.addStretch()
        self.setLayout(layout)

    def _do_export(self, fmt):
        if self.data_provider is None:
            QMessageBox.warning(self, "警告", "未设置数据提供函数")
            return

        data = self.data_provider()
        if data is None or len(data) == 0:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return

        # data 可以是 (records, headers, metadata) 或 (records, headers)
        if isinstance(data, tuple):
            if len(data) == 3:
                records, headers, metadata = data
            elif len(data) == 2:
                records, headers = data
                metadata = {}
            else:
                records = data[0]
                headers = []
                metadata = {}
        else:
            records = data
            headers = []
            metadata = {}

        if not records:
            QMessageBox.warning(self, "警告", "没有可导出的数据")
            return

        suffix = f".{fmt}"
        default_name = f"{self.default_filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}{suffix}"

        file_path, _ = QFileDialog.getSaveFileName(
            self, f"导出 {fmt.upper()}", default_name,
            f"{fmt.upper()} Files (*.{fmt});;All Files (*)"
        )
        if not file_path:
            return

        try:
            if fmt == "txt":
                export_records_to_txt(records, headers, file_path, metadata)
            elif fmt == "csv":
                export_records_to_csv(records, headers, file_path, metadata)
            elif fmt == "xlsx":
                result = export_records_to_xlsx(records, headers, file_path, metadata)
                if not result.get("success", False):
                    raise RuntimeError(result.get("error", "Excel导出失败"))

            QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "导出失败", str(e))


def export_records_to_txt(records, headers, file_path, metadata=None):
    """导出记录列表为txt"""
    lines = [
        "=" * 70,
        "WaveCraft - Multiwfn 计算结果导出",
        f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "=" * 70,
        "",
    ]

    if metadata:
        lines.append("[计算参数]")
        for key, value in metadata.items():
            lines.append(f"{key}: {value}")
        lines.append("")

    if headers:
        lines.append("[数据]")
        header_line = "    ".join(str(h) for h in headers)
        lines.append(header_line)
        lines.append("-" * len(header_line))

    for record in records:
        if isinstance(record, dict):
            values = [str(record.get(h, "")) for h in headers]
        else:
            values = [str(v) for v in record]
        lines.append("    ".join(values))

    lines.extend(["", "=" * 70, "导出完成"])

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return {"success": True, "records": len(records)}


def export_records_to_csv(records, headers, file_path, metadata=None):
    """导出记录列表为csv"""
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["WaveCraft Export"])
        writer.writerow(["Export Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
        if metadata:
            for key, value in metadata.items():
                writer.writerow([key, value])
        writer.writerow([])

        if headers:
            writer.writerow(headers)

        for record in records:
            if isinstance(record, dict):
                row = [record.get(h, "") for h in headers]
            else:
                row = list(record)
            writer.writerow(row)

    return {"success": True, "records": len(records)}


def export_records_to_xlsx(records, headers, file_path, metadata=None):
    """导出记录列表为xlsx"""
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    except ImportError:
        csv_path = file_path.rsplit(".", 1)[0] + ".csv"
        export_records_to_csv(records, headers, csv_path, metadata)
        return {
            "success": True,
            "warning": "未安装 openpyxl，已导出为 CSV 格式",
            "actual_path": csv_path,
            "records": len(records),
        }

    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "计算结果"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="3498DB", end_color="3498DB", fill_type="solid")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin")
    )

    ws["A1"] = "WaveCraft 计算结果导出"
    ws["A1"].font = Font(bold=True, size=14)
    ws["A2"] = f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    row = 4
    if metadata:
        ws.cell(row=row, column=1, value="计算参数").font = Font(bold=True)
        row += 1
        for key, value in metadata.items():
            ws.cell(row=row, column=1, value=key)
            ws.cell(row=row, column=2, value=str(value))
            row += 1
        row += 1

    if headers:
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = thin_border

        data_start = row + 1
        for i, record in enumerate(records):
            r = data_start + i
            if isinstance(record, dict):
                row_values = [record.get(h, "") for h in headers]
            else:
                row_values = list(record)
            for col, value in enumerate(row_values, 1):
                cell = ws.cell(row=r, column=col, value=value)
                cell.border = thin_border

    # 自动调整列宽
    for col in range(1, len(headers) + 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(col)].width = 15

    wb.save(file_path)
    return {"success": True, "records": len(records)}


def export_raw_text(text, file_path):
    """导出原始文本"""
    os.makedirs(os.path.dirname(file_path) or ".", exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(text)
    return {"success": True, "chars": len(text)}
