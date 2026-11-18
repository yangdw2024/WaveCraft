#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
结果导出管理器 - GB/T 8566 compliant export module
支持 txt/csv/xlsx 格式导出，含进度提示、日志记录
"""
import os
import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class ExportManager:
    """计算结果导出管理器"""

    SUPPORTED_FORMATS = {
        "txt": "纯文本格式 (*.txt)",
        "csv": "逗号分隔值 (*.csv)",
        "xlsx": "Excel 工作簿 (*.xlsx)",
    }

    def __init__(self, logger=None):
        self.logger = logger
        self._export_history: List[Dict] = []

    def export_charges(self, charges: List[Dict], file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """导出原子电荷数据"""
        ext = Path(file_path).suffix.lower().lstrip(".")
        if ext not in self.SUPPORTED_FORMATS:
            return {"success": False, "error": f"不支持的格式: {ext}"}

        try:
            if ext == "txt":
                result = self._export_txt(charges, file_path, metadata)
            elif ext == "csv":
                result = self._export_csv(charges, file_path, metadata)
            elif ext == "xlsx":
                result = self._export_xlsx(charges, file_path, metadata)
            else:
                result = {"success": False, "error": f"未实现格式: {ext}"}

            if result["success"]:
                self._record_export("charges", file_path, len(charges))
                if self.logger:
                    self.logger.info(f"电荷数据已导出: {file_path}")
            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"导出失败: {e}")
            return {"success": False, "error": str(e)}

    def _export_txt(self, charges: List[Dict], file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """导出为纯文本格式"""
        lines = [
            "=" * 60,
            "WaveCraft - Multiwfn 计算结果导出",
            f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            "",
        ]

        if metadata:
            lines.append("[计算参数]")
            for key, value in metadata.items():
                lines.append(f"{key}: {value}")
            lines.append("")

        lines.extend([
            "[原子电荷数据]",
            f"{'原子序号':<10} {'元素符号':<10} {'电荷值':<15}",
            "-" * 40,
        ])

        for charge in charges:
            lines.append(f"{charge['index']:<10} {charge['symbol']:<10} {charge['charge']:<15.6f}")

        lines.extend(["", "=" * 60, "导出完成"])

        with open(file_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        return {"success": True, "records": len(charges), "format": "txt"}

    def _export_csv(self, charges: List[Dict], file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """导出为 CSV 格式"""
        with open(file_path, "w", encoding="utf-8-sig", newline="") as f:
            writer = csv.writer(f)

            # 元数据头
            writer.writerow(["WaveCraft Export"])
            writer.writerow(["Export Time", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            if metadata:
                for key, value in metadata.items():
                    writer.writerow([key, value])
            writer.writerow([])

            # 数据头
            writer.writerow(["index", "symbol", "charge"])

            # 数据
            for charge in charges:
                writer.writerow([charge["index"], charge["symbol"], f"{charge['charge']:.6f}"])

        return {"success": True, "records": len(charges), "format": "csv"}

    def _export_xlsx(self, charges: List[Dict], file_path: str, metadata: Optional[Dict] = None) -> Dict:
        """导出为 Excel 格式（如果 openpyxl 可用）"""
        try:
            import openpyxl
            from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
        except ImportError:
            # 回退到 CSV 并修改扩展名
            csv_path = file_path.rsplit(".", 1)[0] + ".csv"
            result = self._export_csv(charges, csv_path, metadata)
            if result["success"]:
                result["warning"] = "未安装 openpyxl，已导出为 CSV 格式"
                result["actual_path"] = csv_path
            return result

        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "电荷数据"

        # 标题样式
        header_font = Font(bold=True, color="FFFFFF")
        header_fill = PatternFill(start_color="3498DB", end_color="3498DB", fill_type="solid")
        thin_border = Border(
            left=Side(style="thin"), right=Side(style="thin"),
            top=Side(style="thin"), bottom=Side(style="thin")
        )

        # 元数据
        ws["A1"] = "WaveCraft 计算结果导出"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        row = 4
        if metadata:
            cell = ws.cell(row=row, column=1, value="计算参数")
            cell.font = Font(bold=True)
            row += 1
            for key, value in metadata.items():
                ws.cell(row=row, column=1, value=key)
                ws.cell(row=row, column=2, value=str(value))
                row += 1
            row += 1

        # 表头
        headers = ["原子序号", "元素符号", "电荷值"]
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal="center")
            cell.border = thin_border

        # 数据
        data_start = row + 1
        for i, charge in enumerate(charges):
            r = data_start + i
            ws.cell(row=r, column=1, value=charge["index"]).border = thin_border
            ws.cell(row=r, column=2, value=charge["symbol"]).border = thin_border
            ws.cell(row=r, column=3, value=charge["charge"]).border = thin_border
            ws.cell(row=r, column=3).number_format = "0.000000"

        # 调整列宽
        ws.column_dimensions["A"].width = 12
        ws.column_dimensions["B"].width = 12
        ws.column_dimensions["C"].width = 15

        wb.save(file_path)
        return {"success": True, "records": len(charges), "format": "xlsx"}

    def export_raw_output(self, output_text: str, file_path: str) -> Dict:
        """导出原始 Multiwfn 输出文本"""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(output_text)
            self._record_export("raw_output", file_path, len(output_text))
            return {"success": True, "chars": len(output_text)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def batch_export(self, export_items: List[Dict], output_dir: str) -> Dict:
        """批量导出多个结果文件"""
        results = []
        success_count = 0

        os.makedirs(output_dir, exist_ok=True)

        for item in export_items:
            file_path = os.path.join(output_dir, item["filename"])
            if item["type"] == "charges":
                result = self.export_charges(item["data"], file_path, item.get("metadata"))
            elif item["type"] == "raw":
                result = self.export_raw_output(item["data"], file_path)
            else:
                result = {"success": False, "error": f"未知类型: {item['type']}"}

            results.append({"filename": item["filename"], **result})
            if result["success"]:
                success_count += 1

        return {
            "success": success_count == len(export_items),
            "total": len(export_items),
            "success_count": success_count,
            "details": results,
        }

    def _record_export(self, export_type: str, file_path: str, record_count: int):
        """记录导出历史"""
        self._export_history.append({
            "timestamp": datetime.now().isoformat(),
            "type": export_type,
            "path": file_path,
            "records": record_count,
        })

    def get_export_history(self, limit: int = 50) -> List[Dict]:
        """获取导出历史"""
        return self._export_history[-limit:]

    def get_supported_formats(self) -> Dict[str, str]:
        """获取支持的导出格式"""
        return dict(self.SUPPORTED_FORMATS)
