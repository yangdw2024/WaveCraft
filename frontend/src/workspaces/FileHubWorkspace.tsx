import React, { useMemo, useState } from 'react';
import {
  Check,
  Cpu,
  Database,
  FileCode2,
  FolderOpen,
  History,
  Save,
  Search,
  Sparkles,
  UploadCloud,
} from 'lucide-react';
import type {
  ExampleFileInfo,
  HealthInfo,
  MoleculeInspection,
  WaveCraftConfig,
} from '../types/quantum';
import { Molecule3DCanvas } from '../components/Molecule3DCanvas';

interface FileHubWorkspaceProps {
  health: HealthInfo | null;
  config: WaveCraftConfig | null;
  examples: ExampleFileInfo[];
  inspection: MoleculeInspection | null;
  loading: boolean;
  onSelectFile: (path: string) => void;
  onUploadFile: (file: File) => void;
  onSaveConfig: (cfg: WaveCraftConfig) => Promise<void>;
}

export const FileHubWorkspace: React.FC<FileHubWorkspaceProps> = ({
  health,
  config,
  examples,
  inspection,
  loading,
  onSelectFile,
  onUploadFile,
  onSaveConfig,
}) => {
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('ALL');
  const [manualPath, setManualPath] = useState('');
  const [mwfnPathInput, setMwfnPathInput] = useState(config?.multiwfn_path || '');
  const [threadsInput, setThreadsInput] = useState(config?.default_threads || 8);
  const [savedNotice, setSavedNotice] = useState(false);
  const [dragOver, setDragOver] = useState(false);

  React.useEffect(() => {
    if (config) {
      setMwfnPathInput(config.multiwfn_path || '');
      setThreadsInput(config.default_threads || 8);
    }
  }, [config]);

  const categories = useMemo(() => {
    const set = new Set<string>(['ALL']);
    for (const ex of examples) set.add(ex.category);
    return Array.from(set);
  }, [examples]);

  const filteredExamples = useMemo(() => {
    const q = search.trim().toLowerCase();
    return examples.filter((ex) => {
      const catOk = category === 'ALL' || ex.category === category;
      const qOk =
        !q ||
        ex.name.toLowerCase().includes(q) ||
        ex.relative_path.toLowerCase().includes(q) ||
        ex.extension.toLowerCase().includes(q);
      return catOk && qOk;
    });
  }, [examples, search, category]);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onUploadFile(f);
  };

  const handleSaveSettings = async () => {
    if (!config) return;
    await onSaveConfig({
      ...config,
      multiwfn_path: mwfnPathInput.trim() || null,
      default_threads: Number(threadsInput) || 8,
    });
    setSavedNotice(true);
    setTimeout(() => setSavedNotice(false), 2500);
  };

  const s = inspection?.summary;

  return (
    <div className="space-y-5">
      {/* Top KPI + Quick Drop Row */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* Drop Zone & Overview */}
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          className={`xl:col-span-5 glass-panel rounded-2xl p-5 flex flex-col justify-between transition ${
            dragOver ? 'border-sky-400 bg-sky-500/10' : ''
          }`}
        >
          <div>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <UploadCloud className="w-5 h-5 text-sky-400" />
                <h2 className="text-sm font-bold text-slate-100">
                  波函数与量子化学文件入口
                </h2>
              </div>
              <span className="text-[11px] font-mono px-2 py-0.5 rounded-md bg-sky-500/15 text-sky-300">
                13+ 格式支持
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-2 leading-relaxed">
              支持直接拖拽上传 <code className="text-sky-300">.fch / .fchk / .wfn / .wfx / .mwfn / .molden / .pdb / .xyz / .cub / .out</code>，或在右侧示例库一键加载。
            </p>
          </div>

          <label className="mt-4 border-2 border-dashed border-slate-700 hover:border-sky-400/60 rounded-xl p-4 text-center cursor-pointer transition bg-slate-950/50 block">
            <input
              type="file"
              className="hidden"
              accept=".fch,.fchk,.wfn,.wfx,.mwfn,.molden,.pdb,.xyz,.cub,.cube,.out,.log,.gjf"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) onUploadFile(f);
                e.target.value = '';
              }}
            />
            <Sparkles className="w-6 h-6 text-sky-400 mx-auto mb-1.5" />
            <div className="text-xs font-semibold text-slate-200">
              点击选择或拖拽量子化学文件到此处
            </div>
            <div className="text-[11px] text-slate-500 mt-0.5">
              自动提取 3D 原子结构、成键拓扑、轨道能量与 HOMO-LUMO 能隙
            </div>
          </label>

          <div className="mt-3 flex items-center gap-2">
            <input
              type="text"
              value={manualPath}
              onChange={(e) => setManualPath(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && manualPath.trim()) {
                  onSelectFile(manualPath.trim());
                }
              }}
              placeholder="输入本地波函数路径 (如 E:\YDW\Chemdraws\zmy_2\计算数据\zmy01.fchk)"
              className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500"
            />
            <button
              disabled={loading || !manualPath.trim()}
              onClick={() => onSelectFile(manualPath.trim())}
              className="px-3.5 py-1.5 rounded-xl bg-sky-500 hover:bg-sky-400 text-slate-950 font-bold text-xs cursor-pointer disabled:opacity-50 whitespace-nowrap"
            >
              载入/解析
            </button>
          </div>

          {/* Engine Config */}
          <div className="mt-4 pt-4 border-t border-slate-800/80 space-y-2.5">
            <div className="flex items-center justify-between text-xs">
              <span className="font-semibold text-slate-300 flex items-center gap-1.5">
                <Cpu className="w-3.5 h-3.5 text-cyan-400" /> Multiwfn 3.8 核心配置
              </span>
              <span
                className={`text-[11px] ${
                  health?.multiwfn_found ? 'text-emerald-400' : 'text-amber-400'
                }`}
              >
                {health?.multiwfn_found ? '● 可执行文件已连接' : '● 未检测到'}
              </span>
            </div>
            <div className="flex gap-2">
              <input
                value={mwfnPathInput}
                onChange={(e) => setMwfnPathInput(e.target.value)}
                placeholder="Multiwfn.exe 完整路径"
                className="flex-1 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-200 focus:outline-none focus:border-sky-500"
              />
              <input
                type="number"
                min={1}
                max={64}
                value={threadsInput}
                onChange={(e) => setThreadsInput(Number(e.target.value))}
                className="w-16 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs font-mono text-slate-200 text-center"
                title="并发线程数"
              />
              <button
                onClick={handleSaveSettings}
                className="px-3 py-1.5 rounded-lg bg-sky-500/20 hover:bg-sky-500/30 text-sky-300 border border-sky-400/30 text-xs font-medium flex items-center gap-1 cursor-pointer"
              >
                {savedNotice ? <Check className="w-3.5 h-3.5" /> : <Save className="w-3.5 h-3.5" />}
                <span>{savedNotice ? '已保存' : '保存'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* 3D Preview + Wavefunction KPIs */}
        <div className="xl:col-span-7 space-y-4">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
            <div className="glass-card rounded-xl p-3">
              <div className="text-[11px] text-slate-400">分子式 / 点群</div>
              <div className="text-sm font-bold text-sky-300 mt-0.5 whitespace-nowrap">
                {s?.formula || '—'}{' '}
                <span className="text-xs font-mono text-slate-400">
                  {s?.point_group ? `(${s.point_group})` : ''}
                </span>
              </div>
            </div>
            <div className="glass-card rounded-xl p-3">
              <div className="text-[11px] text-slate-400">总能量 (Hartree)</div>
              <div className="text-base font-bold font-mono text-emerald-300 mt-0.5 truncate">
                {s?.total_energy_hartree !== undefined && s?.total_energy_hartree !== null
                  ? s.total_energy_hartree.toFixed(5)
                  : '—'}
              </div>
            </div>
            <div className="glass-card rounded-xl p-3">
              <div className="text-[11px] text-slate-400">基函数 / 电子数</div>
              <div className="text-base font-bold font-mono text-cyan-300 mt-0.5">
                {s?.num_basis_functions ?? '—'} / {s?.num_electrons ?? '—'}
              </div>
            </div>
            <div className="glass-card rounded-xl p-3">
              <div className="text-[11px] text-slate-400">HOMO-LUMO Gap</div>
              <div className="text-base font-bold font-mono text-violet-300 mt-0.5">
                {s?.homo_lumo_gap_ev !== undefined && s?.homo_lumo_gap_ev !== null
                  ? `${s.homo_lumo_gap_ev.toFixed(3)} eV`
                  : '—'}
              </div>
            </div>
          </div>

          <Molecule3DCanvas
            atoms={inspection?.atoms || []}
            bonds={inspection?.bonds || []}
            title={
              inspection
                ? `三维预览 · ${inspection.file_name}`
                : '三维量子分子预览视口'
            }
            heightClass="h-[310px]"
          />
        </div>
      </div>

      {/* Built-in Multiwfn Example Library & Recent Files */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-8 glass-panel rounded-2xl p-4 space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <Database className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-bold text-slate-100">
                Multiwfn 内置量子化学示例库 ({filteredExamples.length})
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <div className="relative">
                <Search className="w-3.5 h-3.5 text-slate-500 absolute left-2.5 top-1/2 -translate-y-1/2" />
                <input
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="过滤文件名 / 格式..."
                  className="bg-slate-950 border border-slate-800 rounded-lg pl-8 pr-3 py-1 text-xs text-slate-200 focus:outline-none focus:border-sky-500"
                />
              </div>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1 text-xs text-slate-200"
              >
                {categories.map((c) => (
                  <option key={c} value={c}>
                    {c === 'ALL' ? '全部分类' : c}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 max-h-[300px] overflow-y-auto pr-1">
            {filteredExamples.map((ex) => {
              const active = inspection?.file_path === ex.path;
              return (
                <button
                  key={ex.path}
                  disabled={loading}
                  onClick={() => onSelectFile(ex.path)}
                  className={`flex items-center justify-between gap-2 px-3 py-2.5 rounded-xl border text-left transition cursor-pointer ${
                    active
                      ? 'bg-sky-500/15 border-sky-400/50 text-sky-100'
                      : 'bg-slate-900/70 border-slate-800 hover:border-sky-500/35 text-slate-300'
                  }`}
                >
                  <div className="min-w-0">
                    <div className="text-xs font-semibold truncate">{ex.name}</div>
                    <div className="text-[10.5px] text-slate-500 truncate mt-0.5">
                      {ex.category} · {(ex.size_bytes / 1024).toFixed(1)} KB
                    </div>
                  </div>
                  <span className="text-[10px] font-mono uppercase px-1.5 py-0.5 rounded bg-slate-800 text-sky-300 shrink-0">
                    {ex.extension}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Recent Files */}
        <div className="xl:col-span-4 glass-panel rounded-2xl p-4 space-y-3">
          <div className="flex items-center gap-2">
            <History className="w-4 h-4 text-violet-400" />
            <h3 className="text-sm font-bold text-slate-100">最近加载记录</h3>
          </div>
          <div className="space-y-1.5 max-h-[300px] overflow-y-auto">
            {(config?.recent_files || []).length === 0 ? (
              <div className="text-xs text-slate-500 py-8 text-center">
                暂无历史记录
              </div>
            ) : (
              config?.recent_files.map((fp) => {
                const name = fp.split(/[\\/]/).pop() || fp;
                return (
                  <button
                    key={fp}
                    onClick={() => onSelectFile(fp)}
                    className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-900/60 hover:bg-slate-800 border border-slate-800/80 text-left transition cursor-pointer"
                  >
                    <FileCode2 className="w-4 h-4 text-sky-400 shrink-0" />
                    <div className="min-w-0 flex-1">
                      <div className="text-xs font-medium text-slate-200 truncate">
                        {name}
                      </div>
                      <div className="text-[10px] text-slate-500 font-mono truncate">
                        {fp}
                      </div>
                    </div>
                    <FolderOpen className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  </button>
                );
              })
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
