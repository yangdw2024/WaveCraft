import React, { useState } from 'react';
import {
  X,
  Folder,
  Download,
  Save,
  Check,
  Copy,
  FileCode,
  FileText,
  Globe,
  Loader2,
  FolderCheck,
} from 'lucide-react';
import { api } from '../api/client';
import { marked } from 'marked';
import katex from 'katex';

interface ExportReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  markdownContent: string;
  sourceFilePath?: string;
  moleculeName?: string;
}

export const ExportReportModal: React.FC<ExportReportModalProps> = ({
  isOpen,
  onClose,
  markdownContent,
  sourceFilePath = '',
  moleculeName = 'Molecule',
}) => {
  // Derive default target directory and filename
  const defaultDir = React.useMemo(() => {
    if (!sourceFilePath) return 'D:\\WaveCraft_Exports';
    const lastSlash = Math.max(sourceFilePath.lastIndexOf('\\'), sourceFilePath.lastIndexOf('/'));
    return lastSlash !== -1 ? sourceFilePath.slice(0, lastSlash) : 'D:\\WaveCraft_Exports';
  }, [sourceFilePath]);

  const defaultStem = React.useMemo(() => {
    if (!sourceFilePath) return moleculeName || 'wavecraft';
    const lastSlash = Math.max(sourceFilePath.lastIndexOf('\\'), sourceFilePath.lastIndexOf('/'));
    const fname = lastSlash !== -1 ? sourceFilePath.slice(lastSlash + 1) : sourceFilePath;
    const dot = fname.lastIndexOf('.');
    return dot !== -1 ? fname.slice(0, dot) : fname;
  }, [sourceFilePath, moleculeName]);

  const [targetDir, setTargetDir] = useState<string>(defaultDir);
  const [filenameStem, setFilenameStem] = useState<string>(`${defaultStem}_academic_report`);
  const [format, setFormat] = useState<'md' | 'html' | 'txt'>('md');
  const [includeKatexScript, setIncludeKatexScript] = useState<boolean>(true);
  const [savingDisk, setSavingDisk] = useState<boolean>(false);
  const [saveResult, setSaveResult] = useState<{ ok: boolean; msg: string; path?: string } | null>(null);
  const [copiedPath, setCopiedPath] = useState<boolean>(false);

  if (!isOpen) return null;

  const fullFilename = `${filenameStem}.${format}`;

  // Helper to generate standalone publication HTML
  const generateStandaloneHtml = (): string => {
    const mathTokens: { [key: string]: string } = {};
    let tokenIndex = 0;

    let processed = markdownContent.replace(/\$\$([\s\S]+?)\$\$/g, (_, math) => {
      const token = `KATEXBLOCKTOKEN${tokenIndex++}X`;
      try {
        mathTokens[token] = katex.renderToString(math.trim(), {
          displayMode: true,
          throwOnError: false,
        });
      } catch (e) {
        mathTokens[token] = `<div class="katex-error">${math}</div>`;
      }
      return token;
    });

    processed = processed.replace(/(?<!\\)\$([^\$\n]+?)(?<!\\)\$/g, (_, math) => {
      const token = `KATEXINLINETOKEN${tokenIndex++}X`;
      try {
        mathTokens[token] = katex.renderToString(math.trim(), {
          displayMode: false,
          throwOnError: false,
        });
      } catch (e) {
        mathTokens[token] = `<span class="katex-error">${math}</span>`;
      }
      return token;
    });

    marked.setOptions({ gfm: true, breaks: true });
    let bodyHtml = marked.parse(processed) as string;

    for (const [token, kHtml] of Object.entries(mathTokens)) {
      bodyHtml = bodyHtml.split(token).join(kHtml);
    }

    return `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>${defaultStem} - 量子化学学术分析报告</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.8/dist/katex.min.css"/>
  <style>
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
      background: #0b1120;
      color: #e2e8f0;
      line-height: 1.75;
      padding: 48px 24px;
      margin: 0;
    }
    .container {
      max-width: 900px;
      margin: 0 auto;
      background: #0f172a;
      border: 1px solid #1e293b;
      border-radius: 16px;
      padding: 40px;
      box-shadow: 0 20px 40px rgba(0,0,0,0.5);
    }
    h1, h2, h3, h4 {
      color: #38bdf8;
      border-bottom: 1px solid #334155;
      padding-bottom: 8px;
      margin-top: 32px;
      margin-bottom: 16px;
    }
    h1 { font-size: 24px; border-bottom: 2px solid #0284c7; }
    h2 { font-size: 20px; }
    h3 { font-size: 16px; }
    table {
      border-collapse: collapse;
      width: 100%;
      margin: 20px 0;
      background: #1e293b;
      border-radius: 8px;
      overflow: hidden;
      font-size: 13px;
    }
    th, td {
      border: 1px solid #334155;
      padding: 10px 14px;
      text-align: left;
    }
    th {
      background: #0c4a6e;
      color: #7dd3fc;
      font-weight: 600;
    }
    tr:nth-child(even) { background: #172554/30; }
    pre {
      background: #020617;
      border: 1px solid #334155;
      border-radius: 8px;
      padding: 16px;
      overflow-x: auto;
      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
      font-size: 12px;
      color: #7dd3fc;
    }
    code {
      background: #1e293b;
      padding: 2px 6px;
      border-radius: 4px;
      font-family: monospace;
      color: #38bdf8;
    }
    blockquote {
      border-left: 4px solid #0284c7;
      margin: 16px 0;
      padding-left: 16px;
      color: #94a3b8;
      background: #0c4a6e/20;
      padding: 8px 16px;
      border-radius: 0 8px 8px 0;
    }
    .footer {
      margin-top: 48px;
      padding-top: 16px;
      border-top: 1px solid #1e293b;
      font-size: 12px;
      color: #64748b;
      text-align: center;
    }
  </style>
</head>
<body>
  <div class="container">
    ${bodyHtml}
    <div class="footer">
      本报告由 WaveCraft GUI (Powered by Multiwfn 核心计算引擎 & Sobko 知识库) 自动渲染生成
    </div>
  </div>
</body>
</html>`;
  };

  // 1. Save to local disk via backend API
  const handleSaveToDisk = async () => {
    setSavingDisk(true);
    setSaveResult(null);

    let contentToSave = markdownContent;
    if (format === 'html') {
      contentToSave = generateStandaloneHtml();
    }

    try {
      const res = await api.exportSave({
        file_path: sourceFilePath || 'D:\\WaveCraft_Export.fchk',
        target_dir: targetDir.trim() || undefined,
        custom_filename: fullFilename,
        report_markdown: contentToSave,
        export_csv: false,
        export_obj: false,
        export_cubes: false,
        export_report: true,
        export_log: false,
      });

      const written = res.files_written?.[0] || `${targetDir}\\${fullFilename}`;
      setSaveResult({
        ok: true,
        msg: `成功保存至磁盘！`,
        path: written,
      });
    } catch (e: any) {
      setSaveResult({
        ok: false,
        msg: `保存失败: ${e.message}`,
      });
    } finally {
      setSavingDisk(false);
    }
  };

  // 2. Direct browser download
  const handleBrowserDownload = () => {
    let contentToDownload = markdownContent;
    let mime = 'text/markdown;charset=utf-8';

    if (format === 'html') {
      contentToDownload = generateStandaloneHtml();
      mime = 'text/html;charset=utf-8';
    } else if (format === 'txt') {
      mime = 'text/plain;charset=utf-8';
    }

    const blob = new Blob([contentToDownload], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fullFilename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const copyPathToClipboard = async (p: string) => {
    try {
      await navigator.clipboard.writeText(p);
      setCopiedPath(true);
      setTimeout(() => setCopiedPath(false), 2000);
    } catch {}
  };

  return (
    <div className="fixed inset-0 z-[99999] bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-4">
      <div className="w-full max-w-lg glass-panel rounded-2xl border border-cyan-500/40 shadow-2xl overflow-hidden flex flex-col animate-in fade-in zoom-in-95 duration-200">
        {/* Modal Header */}
        <div className="flex items-center justify-between p-4 border-b border-slate-800 bg-slate-900/60">
          <div className="flex items-center gap-2">
            <div className="p-1.5 rounded-lg bg-cyan-500/20 text-cyan-400">
              <Download className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold text-slate-100">自定义导出量子化学分析报告</h3>
              <p className="text-[11px] text-slate-400">自定义保存路径、文件名与渲染格式</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 space-y-4 text-xs">
          {/* Target Directory */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300 flex items-center gap-1.5">
              <Folder className="w-3.5 h-3.5 text-cyan-400" />
              <span>目标存储目录 (可手动修改为任意本地路径):</span>
            </label>
            <input
              value={targetDir}
              onChange={(e) => setTargetDir(e.target.value)}
              placeholder="例如: D:\Multiwfn\Reports 或 C:\Users\Administrator\Desktop"
              className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500/60"
            />
          </div>

          {/* Custom Filename */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300 flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-cyan-400" />
              <span>自定义文件主名称:</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                value={filenameStem}
                onChange={(e) => setFilenameStem(e.target.value)}
                placeholder="例如: CH3Cl_Sobko_Analysis"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs font-mono text-slate-100 focus:outline-none focus:border-cyan-500/60"
              />
              <span className="font-mono text-cyan-400 font-bold px-2 py-1.5 rounded-lg bg-slate-900 border border-slate-800">
                .{format}
              </span>
            </div>
          </div>

          {/* Format Selector */}
          <div className="space-y-1.5">
            <label className="font-semibold text-slate-300">导出格式:</label>
            <div className="grid grid-cols-3 gap-2">
              {[
                {
                  id: 'md' as const,
                  label: 'Markdown (.md)',
                  desc: '纯文本标记，支持 LaTeX 公式与 GFM 表格',
                  icon: <FileCode className="w-3.5 h-3.5" />,
                },
                {
                  id: 'html' as const,
                  label: '独立 HTML 网页',
                  desc: '内置样式与 KaTeX 公式，双击浏览器即开即看',
                  icon: <Globe className="w-3.5 h-3.5" />,
                },
                {
                  id: 'txt' as const,
                  label: '纯文本 (.txt)',
                  desc: '无格式纯文本，适合快速查阅或嵌入日志',
                  icon: <FileText className="w-3.5 h-3.5" />,
                },
              ].map((fmt) => (
                <button
                  key={fmt.id}
                  onClick={() => setFormat(fmt.id)}
                  className={`p-2.5 rounded-xl text-left border cursor-pointer transition flex flex-col gap-1 ${
                    format === fmt.id
                      ? 'bg-cyan-500/20 border-cyan-400/60 text-cyan-200'
                      : 'bg-slate-950/60 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-1.5 font-semibold text-xs">
                    {fmt.icon}
                    <span>{fmt.label}</span>
                  </div>
                  <span className="text-[10px] text-slate-500 leading-tight">{fmt.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Feedback Notice */}
          {saveResult && (
            <div
              className={`p-3 rounded-xl border flex items-center justify-between gap-2 text-xs ${
                saveResult.ok
                  ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                  : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
              }`}
            >
              <div className="flex items-center gap-2 min-w-0">
                <FolderCheck className="w-4 h-4 shrink-0 text-emerald-400" />
                <span className="truncate">{saveResult.msg} {saveResult.path}</span>
              </div>
              {saveResult.path && (
                <button
                  onClick={() => copyPathToClipboard(saveResult.path!)}
                  className="px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px] text-slate-300 hover:text-white flex items-center gap-1 cursor-pointer shrink-0"
                >
                  {copiedPath ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                  <span>{copiedPath ? '已复制' : '复制路径'}</span>
                </button>
              )}
            </div>
          )}
        </div>

        {/* Modal Footer */}
        <div className="flex items-center justify-between p-4 border-t border-slate-800 bg-slate-900/60">
          <button
            onClick={onClose}
            className="px-3 py-1.5 rounded-xl border border-slate-800 text-slate-400 hover:text-white hover:bg-slate-800 text-xs transition cursor-pointer"
          >
            关闭
          </button>

          <div className="flex items-center gap-2">
            <button
              onClick={handleBrowserDownload}
              className="px-3.5 py-1.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold flex items-center gap-1.5 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
              <span>浏览器下载</span>
            </button>

            <button
              disabled={savingDisk}
              onClick={handleSaveToDisk}
              className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-cyan-500 to-blue-600 hover:from-cyan-400 hover:to-blue-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow-lg shadow-cyan-500/20 disabled:opacity-50"
            >
              {savingDisk ? (
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Save className="w-3.5 h-3.5" />
              )}
              <span>保存至指定本地磁盘</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
