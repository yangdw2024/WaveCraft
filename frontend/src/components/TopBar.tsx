import React from 'react';
import {
  Atom,
  CheckCircle2,
  Cpu,
  FileUp,
  FolderOpen,
  Search,
  Sparkles,
  AlertTriangle,
} from 'lucide-react';
import type { ExampleFileInfo, HealthInfo, MoleculeInspection } from '../types/quantum';
import { Tooltip } from './Tooltip';

interface TopBarProps {
  health: HealthInfo | null;
  inspection: MoleculeInspection | null;
  examples: ExampleFileInfo[];
  loading: boolean;
  onSelectFile: (path: string) => void;
  onUploadFile: (file: File) => void;
  onOpenPalette: () => void;
  onJumpToFileHub: () => void;
}

export const TopBar: React.FC<TopBarProps> = ({
  health,
  inspection,
  examples,
  loading,
  onSelectFile,
  onUploadFile,
  onOpenPalette,
  onJumpToFileHub,
}) => {
  const fileInputRef = React.useRef<HTMLInputElement>(null);
  const featured = examples.slice(0, 24);
  const summary = inspection?.summary;

  return (
    <header className="h-14 shrink-0 border-b border-slate-800/80 bg-[#080c14]/95 backdrop-blur-xl px-4 flex items-center justify-between gap-3 z-30">
      {/* Brand */}
      <div className="flex items-center gap-3 min-w-0">
        <div
          onClick={onJumpToFileHub}
          className="cursor-pointer flex items-center gap-2.5 group"
        >
          <div className="relative w-9 h-9 rounded-xl bg-gradient-to-br from-sky-500/25 via-cyan-500/15 to-violet-500/25 border border-sky-400/35 flex items-center justify-center shadow-[0_0_20px_rgba(56,189,248,0.22)] group-hover:border-sky-300 transition">
            <Atom className="w-5 h-5 text-sky-400 group-hover:rotate-45 transition-transform duration-500" />
          </div>
          <div className="whitespace-nowrap">
            <div className="flex items-center gap-1.5">
              <span className="font-bold tracking-tight text-slate-100 text-sm">
                WaveCraft
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-md bg-sky-500/15 text-sky-300 border border-sky-400/25">
                v4.0 Rust
              </span>
            </div>
            <p className="text-[11px] text-slate-400 leading-none mt-0.5">
              Multiwfn 量子分析台
            </p>
          </div>
        </div>

        {/* Active Molecule Pill */}
        {inspection ? (
          <div className="hidden xl:flex items-center gap-2 ml-2 px-2.5 py-1 rounded-xl bg-slate-900/90 border border-slate-700/70 text-xs whitespace-nowrap min-w-0 max-w-[420px] overflow-hidden">
            <span className="px-2 py-0.5 rounded-md bg-cyan-500/15 text-cyan-300 font-semibold border border-cyan-500/25">
              {summary?.formula || inspection.file_name}
            </span>
            <span className="text-slate-300 font-mono truncate max-w-[160px]" title={inspection.file_path}>
              {inspection.file_name}
            </span>
            {summary?.point_group && (
              <span className="hidden xl:inline text-slate-400 border-l border-slate-700 pl-2">
                点群 <b className="text-slate-200">{summary.point_group}</b>
              </span>
            )}
            {summary?.total_energy_hartree !== undefined &&
              summary?.total_energy_hartree !== null && (
                <span className="text-slate-400 border-l border-slate-700 pl-2 font-mono">
                  E = <b className="text-emerald-300">{summary.total_energy_hartree.toFixed(4)}</b> Ha
                </span>
              )}
            {summary?.homo_lumo_gap_ev !== undefined &&
              summary?.homo_lumo_gap_ev !== null && (
                <span className="hidden xl:inline text-slate-400 border-l border-slate-700 pl-2 font-mono">
                  Gap = <b className="text-violet-300">{summary.homo_lumo_gap_ev.toFixed(2)}</b> eV
                </span>
              )}
          </div>
        ) : (
          <div className="hidden xl:flex items-center gap-2 ml-3 px-3 py-1.5 rounded-xl bg-slate-900/50 border border-slate-800 text-xs text-slate-400">
            <Sparkles className="w-3.5 h-3.5 text-sky-400" />
            <span>请选择左侧示例分子或上传波函数文件开始分析</span>
          </div>
        )}
      </div>

      {/* Controls */}
      <div className="flex items-center gap-2.5 shrink-0">
        {/* Quick Example Selector */}
        <div className="hidden md:flex items-center gap-1.5 bg-slate-900/80 border border-slate-700/70 rounded-xl px-2.5 py-1">
          <FolderOpen className="w-3.5 h-3.5 text-sky-400 shrink-0" />
          <select
            className="bg-transparent text-xs text-slate-200 focus:outline-none max-w-[185px] cursor-pointer"
            value={inspection?.file_path || ''}
            disabled={loading}
            onChange={(e) => {
              if (e.target.value) onSelectFile(e.target.value);
            }}
          >
            <option value="" className="bg-slate-900">
              快速切换 Multiwfn 示例...
            </option>
            {featured.map((ex) => (
              <option key={ex.path} value={ex.path} className="bg-slate-900">
                [{ex.category}] {ex.name}
              </option>
            ))}
          </select>
        </div>

        {/* Upload Button */}
        <input
          ref={fileInputRef}
          type="file"
          className="hidden"
          accept=".fch,.fchk,.wfn,.wfx,.mwfn,.molden,.pdb,.xyz,.cub,.cube,.out,.log,.gjf,.com,.mol,.cml"
          onChange={(e) => {
            const f = e.target.files?.[0];
            if (f) onUploadFile(f);
            e.target.value = '';
          }}
        />
        <button
          onClick={() => fileInputRef.current?.click()}
          disabled={loading}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-sky-500/15 hover:bg-sky-500/25 text-sky-300 border border-sky-400/30 transition cursor-pointer disabled:opacity-50"
        >
          <FileUp className="w-3.5 h-3.5" />
          <span>打开文件</span>
        </button>

        {/* Ctrl+K Command Palette Trigger */}
        <Tooltip content="快速检索 Multiwfn 全部主菜单与子功能模块" title="全局命令调色板" shortcut="Ctrl+K" position="bottom">
          <button
            onClick={onOpenPalette}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl text-xs text-slate-300 bg-slate-900/90 hover:bg-slate-800 border border-slate-700/80 transition cursor-pointer"
          >
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <span className="hidden sm:inline">命令检索</span>
            <kbd className="text-[10px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-400 border border-slate-700 font-mono">
              Ctrl+K
            </kbd>
          </button>
        </Tooltip>

        {/* Engine Status Pill */}
        <Tooltip
          content={health?.multiwfn_path ? `内核路径: ${health.multiwfn_path}` : '未检测到 Multiwfn.exe，请在配置中指定路径'}
          title="计算内核状态"
          position="bottom"
        >
          <div
            className={`flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-xs border ${
              health?.multiwfn_found
                ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                : 'bg-amber-500/10 border-amber-500/30 text-amber-300'
            }`}
          >
            {health?.multiwfn_found ? (
              <CheckCircle2 className="w-3.5 h-3.5" />
            ) : (
              <AlertTriangle className="w-3.5 h-3.5" />
            )}
            <span className="hidden lg:inline font-medium">
              {loading ? '计算中...' : health?.multiwfn_found ? 'Multiwfn 3.8 就绪' : '未配置内核'}
            </span>
            <Cpu className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-sky-400' : ''}`} />
          </div>
        </Tooltip>
      </div>
    </header>
  );
};
