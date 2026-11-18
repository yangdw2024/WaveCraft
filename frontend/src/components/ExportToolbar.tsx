import React from 'react';
import { Download, FileJson, FileSpreadsheet, FileText } from 'lucide-react';

interface ExportToolbarProps {
  title: string;
  rows?: Record<string, any>[];
  rawText?: string;
}

function downloadBlob(filename: string, content: string, mime: string) {
  const blob = new Blob([content], { type: mime });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export const ExportToolbar: React.FC<ExportToolbarProps> = ({
  title,
  rows,
  rawText,
}) => {
  if (!rawText && (!rows || rows.length === 0)) {
    return null;
  }
  const safeName = title.replace(/[^a-zA-Z0-9_\u4e00-\u9fa5-]+/g, '_');

  const handleCsv = () => {
    if (!rows || rows.length === 0) return;
    const keys = Object.keys(rows[0]);
    const csv = [
      keys.join(','),
      ...rows.map((r) =>
        keys
          .map((k) => {
            const v = r[k] ?? '';
            const s = String(v).replace(/"/g, '""');
            return s.includes(',') ? `"${s}"` : s;
          })
          .join(',')
      ),
    ].join('\n');
    downloadBlob(`${safeName}.csv`, '\uFEFF' + csv, 'text/csv;charset=utf-8');
  };

  const handleJson = () => {
    const payload = rows && rows.length > 0 ? rows : { title, rawText };
    downloadBlob(
      `${safeName}.json`,
      JSON.stringify(payload, null, 2),
      'application/json;charset=utf-8'
    );
  };

  const handleTxt = () => {
    const text =
      rawText ||
      (rows ? rows.map((r) => JSON.stringify(r)).join('\n') : '');
    downloadBlob(`${safeName}.txt`, text, 'text/plain;charset=utf-8');
  };

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {rows && rows.length > 0 && (
        <button
          onClick={handleCsv}
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-slate-800/90 hover:bg-emerald-500/20 text-slate-300 hover:text-emerald-300 border border-slate-700 hover:border-emerald-500/40 transition cursor-pointer"
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          <span>CSV</span>
        </button>
      )}
      <button
        onClick={handleJson}
        className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-slate-800/90 hover:bg-sky-500/20 text-slate-300 hover:text-sky-300 border border-slate-700 hover:border-sky-500/40 transition cursor-pointer"
      >
        <FileJson className="w-3.5 h-3.5" />
        <span>JSON</span>
      </button>
      {rawText && (
        <button
          onClick={handleTxt}
          className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-xs bg-slate-800/90 hover:bg-violet-500/20 text-slate-300 hover:text-violet-300 border border-slate-700 hover:border-violet-500/40 transition cursor-pointer"
        >
          <FileText className="w-3.5 h-3.5" />
          <span>原始输出</span>
        </button>
      )}
    </div>
  );
};
