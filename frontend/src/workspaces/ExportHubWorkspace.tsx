import React, { useMemo, useState } from 'react';
import {
  Check,
  CheckCircle2,
  Copy,
  DownloadCloud,
  FileBox,
  FileCode,
  FileSpreadsheet,
  FileText,
  Folder,
  FolderOpen,
  HardDrive,
  Loader2,
  Sparkles,
} from 'lucide-react';
import { api } from '../api/client';
import type { MoleculeInspection } from '../types/quantum';

interface ExportHubWorkspaceProps {
  inspection: MoleculeInspection | null;
}

export const ExportHubWorkspace: React.FC<ExportHubWorkspaceProps> = ({ inspection }) => {
  // Default target directory is the molecule's parent directory
  const defaultDir = useMemo(() => {
    if (!inspection?.file_path) return 'D:\\WaveCraft_Export';
    const lastSlash = Math.max(
      inspection.file_path.lastIndexOf('\\'),
      inspection.file_path.lastIndexOf('/')
    );
    return lastSlash !== -1
      ? inspection.file_path.substring(0, lastSlash)
      : 'D:\\WaveCraft_Export';
  }, [inspection?.file_path]);

  const [targetDir, setTargetDir] = useState(defaultDir);
  const [exportCsv, setExportCsv] = useState(true);
  const [exportObj, setExportObj] = useState(true);
  const [exportCubes, setExportCubes] = useState(true);
  const [exportLog, setExportLog] = useState(true);
  const [exportReport, setExportReport] = useState(true);

  const [busy, setBusy] = useState(false);
  const [resultMessage, setResultMessage] = useState<string | null>(null);
  const [filesWritten, setFilesWritten] = useState<string[]>([]);
  const [copiedIdx, setCopiedIdx] = useState<number | null>(null);

  const handleExport = async () => {
    if (!inspection) return;
    setBusy(true);
    setResultMessage(null);
    setFilesWritten([]);

    try {
      const res = await api.exportSave({
        file_path: inspection.file_path,
        target_dir: targetDir || undefined,
        export_csv: exportCsv,
        export_obj: exportObj,
        export_cubes: exportCubes,
        export_log: exportLog,
        export_report: exportReport,
        log_content: inspection.raw_output,
        report_markdown: `# ${inspection.file_name} 量子化学分析总结\n\n- 文件路径: ${inspection.file_path}\n- 原子数: ${inspection.atoms.length}\n- 化学键数: ${inspection.bonds.length}\n- 导出时间: ${new Date().toLocaleString()}\n`,
      });

      setResultMessage(res.message);
      setFilesWritten(res.files_written);
    } catch (e: any) {
      setResultMessage(`导出失败: ${e.message}`);
    } finally {
      setBusy(false);
    }
  };

  const copyPath = (path: string, idx: number) => {
    navigator.clipboard.writeText(path);
    setCopiedIdx(idx);
    setTimeout(() => setCopiedIdx(null), 2000);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3 bg-gradient-to-r from-slate-950 via-sky-950/20 to-slate-950 border-sky-500/20">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-400 to-cyan-600 flex items-center justify-center text-slate-950 font-bold shadow-lg shadow-emerald-500/25">
            <DownloadCloud className="w-6 h-6 text-slate-950" />
          </div>
          <div>
            <h2 className="text-sm font-bold text-slate-100 flex items-center gap-2">
              <span>导出与本地归档管理中心</span>
              <span className="text-[10px] px-2 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-300 font-mono">
                本地直接写入 · 原目录同位归档
              </span>
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">
              一键在分子源文件所在目录下保存 Multiwfn 散点 CSV、3D 彩色 OBJ 模型、Cubes 格点数据与学术报告
            </p>
          </div>
        </div>
      </div>

      {/* Directory Configuration Card */}
      <div className="glass-panel rounded-2xl p-4 space-y-3">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <Folder className="w-3.5 h-3.5 text-sky-400" />
          <span>导出存储路径设置</span>
        </h3>

        <div className="space-y-2">
          <div className="flex items-center justify-between text-xs text-slate-400">
            <span>当前分析分子绝对路径:</span>
            <span className="font-mono text-slate-300 truncate max-w-xl">
              {inspection?.file_path || '未选择分子文件'}
            </span>
          </div>

          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <input
                value={targetDir}
                onChange={(e) => setTargetDir(e.target.value)}
                placeholder="请输入或选择导出目录 (如 E:\YDW\Chemdraws\zmy_2\计算数据)"
                className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3.5 py-2.5 text-xs font-mono text-slate-200 placeholder-slate-600 focus:outline-none focus:border-sky-500/60"
              />
            </div>
            <button
              onClick={() => setTargetDir(defaultDir)}
              className="px-3 py-2.5 rounded-xl bg-slate-900 border border-slate-800 text-xs text-slate-300 hover:text-white transition cursor-pointer shrink-0 font-medium"
              title="重置为当前分子的相同源目录"
            >
              恢复分子同目录
            </button>
          </div>
        </div>
      </div>

      {/* Items selection */}
      <div className="glass-panel rounded-2xl p-4 space-y-3">
        <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-1.5">
          <FileCode className="w-3.5 h-3.5 text-indigo-400" />
          <span>选择导出的数据文件类型</span>
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 text-xs">
          <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={exportCsv}
              onChange={(e) => setExportCsv(e.target.checked)}
              className="mt-0.5 accent-sky-400"
            />
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-400" />
                <span>弱相互作用散点数据表 (.csv)</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                包含 sign(λ2)ρ, δg_inter, δg_intra, δg_total 全套量化列
              </p>
            </div>
          </label>

          <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={exportObj}
              onChange={(e) => setExportObj(e.target.checked)}
              className="mt-0.5 accent-sky-400"
            />
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <FileBox className="w-3.5 h-3.5 text-cyan-400" />
                <span>3D 彩色等值面模型 (.obj)</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                带 BGR 顶点颜色，可直接导入 Blender / VMD / MeshLab
              </p>
            </div>
          </label>

          <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={exportCubes}
              onChange={(e) => setExportCubes(e.target.checked)}
              className="mt-0.5 accent-sky-400"
            />
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <HardDrive className="w-3.5 h-3.5 text-violet-400" />
                <span>3D 体积格点网格文件 (.cub)</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                包含 dg_inter.cub (相互作用) 与 sl2r.cub (色彩场)
              </p>
            </div>
          </label>

          <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={exportLog}
              onChange={(e) => setExportLog(e.target.checked)}
              className="mt-0.5 accent-sky-400"
            />
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <FileText className="w-3.5 h-3.5 text-amber-400" />
                <span>Multiwfn 计算原始终端日志 (.log)</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                完整记录 Multiwfn 标准输出，便于学术溯源与复核
              </p>
            </div>
          </label>

          <label className="flex items-start gap-2.5 p-3 rounded-xl bg-slate-950/80 border border-slate-800 cursor-pointer hover:border-slate-700 transition">
            <input
              type="checkbox"
              checked={exportReport}
              onChange={(e) => setExportReport(e.target.checked)}
              className="mt-0.5 accent-sky-400"
            />
            <div>
              <div className="font-semibold text-slate-200 flex items-center gap-1.5">
                <Sparkles className="w-3.5 h-3.5 text-rose-400" />
                <span>AI 学术分析报告概要 (.md)</span>
              </div>
              <p className="text-[11px] text-slate-500 mt-0.5">
                结构化 Markdown 报告，含物理化学定标与结论
              </p>
            </div>
          </label>
        </div>

        <div className="pt-2 flex items-center justify-end">
          <button
            disabled={busy || !inspection}
            onClick={handleExport}
            className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-2 cursor-pointer disabled:opacity-50 shadow-lg shadow-emerald-500/20 hover:brightness-110 transition"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <DownloadCloud className="w-4 h-4" />}
            <span>一键导出至指定本地目录</span>
          </button>
        </div>
      </div>

      {/* Export Result Notification & Files List */}
      {resultMessage && (
        <div className="glass-panel rounded-2xl p-4 space-y-3 border-emerald-500/30">
          <div className="flex items-center gap-2 text-xs font-semibold text-emerald-300">
            <CheckCircle2 className="w-4 h-4" />
            <span>{resultMessage}</span>
          </div>

          {filesWritten.length > 0 && (
            <div className="space-y-1.5 pt-1">
              <span className="text-[11px] text-slate-400 font-semibold">已写入磁盘的完整文件列表:</span>
              <div className="space-y-1">
                {filesWritten.map((filePath, idx) => (
                  <div
                    key={idx}
                    className="flex items-center justify-between gap-2 p-2 rounded-lg bg-slate-950 border border-slate-800 font-mono text-[11px] text-slate-200"
                  >
                    <span className="truncate">{filePath}</span>
                    <button
                      onClick={() => copyPath(filePath, idx)}
                      className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-400 hover:text-white transition cursor-pointer flex items-center gap-1 shrink-0"
                    >
                      {copiedIdx === idx ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                      <span>{copiedIdx === idx ? '已复制' : '复制路径'}</span>
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
