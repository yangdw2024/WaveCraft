import React, { useMemo, useState } from 'react';
import {
  CheckCircle2,
  Clock,
  Download,
  GitMerge,
  Hexagon,
  Loader2,
  Play,
  Search,
  Share2,
  Terminal,
  Trash2,
} from 'lucide-react';
import { api } from '../api/client';
import type {
  AromaticityResult,
  CdftAtomEntry,
  CriticalPoint,
  FuzzyResult,
  MenuCategory,
  MenuFunctionTemplate,
  MoleculeInspection,
  MultipoleResult,
  TaskRecord,
} from '../types/quantum';
import { Molecule3DCanvas } from '../components/Molecule3DCanvas';
import { ExportToolbar } from '../components/ExportToolbar';

export const AdvancedToolsWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
}> = ({ inspection }) => {
  const [cps, setCps] = useState<CriticalPoint[]>([]);
  const [aromMethod, setAromMethod] = useState('Shannon');
  const [aromRes, setAromRes] = useState<AromaticityResult | null>(null);
  const [exportFmt, setExportFmt] = useState('xyz');
  const [exportedInfo, setExportedInfo] = useState<{
    filename: string;
    exported_path: string;
    size_bytes: number;
    preview: string;
  } | null>(null);
  const [stdout, setStdout] = useState('');
  const [fuzzyRes, setFuzzyRes] = useState<FuzzyResult | null>(null);
  const [cdftEntries, setCdftEntries] = useState<CdftAtomEntry[]>([]);
  const [multipoleRes, setMultipoleRes] = useState<MultipoleResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runFuzzy = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateFuzzy(inspection.file_path, 'li_di');
      setFuzzyRes(res.fuzzy);
      setStdout(res.stdout);
    } catch (e: any) {
      setError(e.message || 'Fuzzy 原子空间分析失败');
    } finally {
      setBusy(false);
    }
  };

  const runCdftAndMultipole = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const [cRes, mRes] = await Promise.all([
        api.calculateCdft(inspection.file_path, 'ow_fukui'),
        api.calculateMultipole(inspection.file_path),
      ]);
      setCdftEntries(cRes.entries);
      setMultipoleRes(mRes.multipole);
      setStdout(cRes.stdout + '\n\n' + mRes.stdout);
    } catch (e: any) {
      setError(e.message || 'CDFT / 电多极矩分析失败');
    } finally {
      setBusy(false);
    }
  };

  const runAim = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateAim(inspection.file_path);
      setCps(res.critical_points);
      setStdout(res.stdout);
    } catch (e: any) {
      setError(e.message || 'AIM 拓扑分析失败');
    } finally {
      setBusy(false);
    }
  };

  const runAromaticity = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateAromaticity(inspection.file_path, aromMethod);
      setAromRes(res.aromaticity);
      setStdout(res.stdout);
    } catch (e: any) {
      setError(e.message || '芳香性计算失败');
    } finally {
      setBusy(false);
    }
  };

  const runExport = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.exportStructure(inspection.file_path, exportFmt);
      setExportedInfo(res);
    } catch (e: any) {
      setError(e.message || '文件导出失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        {/* AIM 3D Topology */}
        <div className="xl:col-span-7 space-y-4">
          <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <GitMerge className="w-4 h-4 text-orange-400" />
              <h3 className="text-sm font-bold text-slate-100">
                AIM QTAIM 临界点拓扑分析
              </h3>
            </div>
            <div className="flex items-center gap-2">
              <ExportToolbar
                title={`${inspection?.file_name || 'mol'}_aim_cps`}
                rows={cps}
                rawText={stdout}
              />
              <button
                disabled={busy || !inspection}
                onClick={runAim}
                className="px-4 py-1.5 rounded-xl bg-gradient-to-r from-orange-500 to-amber-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
                <span>搜索全部临界点</span>
              </button>
            </div>
          </div>

          <Molecule3DCanvas
            atoms={inspection?.atoms || []}
            bonds={inspection?.bonds || []}
            criticalPoints={cps}
            title={`3D AIM 临界点图谱 (${cps.length} 个临界点)`}
            heightClass="h-[370px]"
          />

          <div className="glass-panel rounded-2xl p-4">
            <div className="max-h-[190px] overflow-y-auto rounded-xl border border-slate-800">
              <table className="w-full text-xs font-mono">
                <thead className="bg-slate-900 text-slate-400 sticky top-0">
                  <tr>
                    <th className="py-1.5 px-2 text-left">CP</th>
                    <th className="py-1.5 px-2 text-left">类型</th>
                    <th className="py-1.5 px-2 text-right">坐标 (Å)</th>
                    <th className="py-1.5 px-2 text-right">ρ(r)</th>
                    <th className="py-1.5 px-2 text-right">∇²ρ(r)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {cps.map((cp) => (
                    <tr key={cp.index} className="hover:bg-slate-800/40">
                      <td className="py-1 px-2 text-slate-300">#{cp.index}</td>
                      <td className="py-1 px-2 text-orange-300">{cp.cp_type_label}</td>
                      <td className="py-1 px-2 text-right text-slate-400">
                        ({cp.x.toFixed(2)}, {cp.y.toFixed(2)}, {cp.z.toFixed(2)})
                      </td>
                      <td className="py-1 px-2 text-right text-sky-300">
                        {cp.rho !== undefined && cp.rho !== null ? cp.rho.toFixed(4) : '—'}
                      </td>
                      <td className="py-1 px-2 text-right text-cyan-300">
                        {cp.laplacian !== undefined && cp.laplacian !== null
                          ? cp.laplacian.toFixed(4)
                          : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right: Aromaticity & Export */}
        <div className="xl:col-span-5 space-y-4">
          {/* Aromaticity */}
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Hexagon className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  芳香性与电子离域分析 (Menu 25)
                </h3>
              </div>
            </div>
            <div className="flex gap-2">
              <select
                value={aromMethod}
                onChange={(e) => setAromMethod(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
              >
                <option value="Shannon">Shannon 芳香性指数</option>
                <option value="HOMA">HOMA / Bird 几何芳香性</option>
                <option value="FLU">FLU 芳香性波动指数</option>
                <option value="PDI">PDI 对位离域指数</option>
              </select>
              <button
                disabled={busy || !inspection}
                onClick={runAromaticity}
                className="px-4 py-1.5 rounded-xl bg-sky-500/20 hover:bg-sky-500/30 text-sky-200 border border-sky-400/35 text-xs font-semibold cursor-pointer disabled:opacity-50"
              >
                计算指数
              </button>
            </div>
            {aromRes && (
              <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  Shannon: <b className="text-sky-300">{aromRes.shannon_index ?? '—'}</b>
                </div>
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  HOMA: <b className="text-emerald-300">{aromRes.homa ?? '—'}</b>
                </div>
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  FLU: <b className="text-violet-300">{aromRes.flu ?? '—'}</b>
                </div>
                <div className="p-2 rounded-lg bg-slate-900 border border-slate-800">
                  PDI: <b className="text-amber-300">{aromRes.pdi ?? '—'}</b>
                </div>
              </div>
            )}
          </div>

          {/* Multi-format Converter */}
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <div className="flex items-center gap-2">
              <Share2 className="w-4 h-4 text-emerald-400" />
              <h3 className="text-sm font-bold text-slate-100">
                波函数与结构格式转换 (Menu 100-2)
              </h3>
            </div>
            <div className="flex gap-2">
              <select
                value={exportFmt}
                onChange={(e) => setExportFmt(e.target.value)}
                className="flex-1 bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
              >
                <option value="xyz">XYZ 笛卡尔坐标 (.xyz)</option>
                <option value="pdb">PDB 结构格式 (.pdb)</option>
                <option value="wfn">WFN 波函数格式 (.wfn)</option>
                <option value="wfx">WFX 扩展波函数 (.wfx)</option>
                <option value="molden">Molden 格式 (.molden)</option>
                <option value="mwfn">Multiwfn 现代波函数 (.mwfn)</option>
                <option value="fch">Gaussian FCHK (.fch)</option>
              </select>
              <button
                disabled={busy || !inspection}
                onClick={runExport}
                className="px-4 py-1.5 rounded-xl bg-emerald-500/20 hover:bg-emerald-500/30 text-emerald-200 border border-emerald-400/35 text-xs font-semibold cursor-pointer disabled:opacity-50"
              >
                转换导出
              </button>
            </div>
            {exportedInfo && (
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-emerald-300 font-mono">
                    {exportedInfo.filename} ({(exportedInfo.size_bytes / 1024).toFixed(1)} KB)
                  </span>
                  <a
                    href={api.downloadUrl(exportedInfo.exported_path)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-lg bg-emerald-500 text-slate-950 font-bold hover:bg-emerald-400"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>下载文件</span>
                  </a>
                </div>
                <pre className="max-h-36 overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-2.5 text-[11px] font-mono text-slate-300">
                  {exportedInfo.preview}
                </pre>
              </div>
            )}
          </div>

          <div className="glass-panel rounded-2xl p-4">
            <h3 className="text-xs font-bold text-slate-300 mb-2">原始计算输出</h3>
            <pre className="h-[155px] overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-2.5 text-[11px] font-mono text-slate-400 whitespace-pre-wrap">
              {stdout || '执行 AIM 或芳香性分析后，Multiwfn 终端输出将显示于此。'}
            </pre>
          </div>
        </div>
      </div>

      {/* Fuzzy Atomic Space (Menu 15) & CDFT + Multipole (Menu 22 & 300-5) */}
      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-6 glass-panel rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-bold text-slate-100">
              Fuzzy 模糊原子空间 · 局域/离域指数 (Menu 15)
            </h3>
            <button
              disabled={busy || !inspection}
              onClick={runFuzzy}
              className="px-3.5 py-1.5 rounded-xl bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border border-cyan-400/35 text-xs font-semibold cursor-pointer disabled:opacity-50"
            >
              计算 LI / DI 矩阵
            </button>
          </div>

          {fuzzyRes && fuzzyRes.li_entries.length > 0 ? (
            <div className="space-y-3">
              <div className="flex flex-wrap gap-2">
                {fuzzyRes.li_entries.map((e) => (
                  <div
                    key={e.index}
                    className="px-2.5 py-1.5 rounded-lg bg-slate-900 border border-slate-800 text-xs font-mono"
                  >
                    <span className="text-slate-400">
                      {e.index}({e.element}):{' '}
                    </span>
                    <span className="text-cyan-300 font-bold">{e.localization_index.toFixed(3)}</span>
                  </div>
                ))}
              </div>
              {fuzzyRes.di_matrix.length > 0 && (
                <div className="max-h-40 overflow-auto rounded-xl border border-slate-800">
                  <table className="w-full text-[11px] font-mono">
                    <thead className="bg-slate-900 text-slate-400">
                      <tr>
                        <th className="py-1 px-2 text-left">DI 矩阵</th>
                        {fuzzyRes.di_matrix[0].map((_, j) => (
                          <th key={j} className="py-1 px-2 text-right">
                            #{j + 1}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-800/60">
                      {fuzzyRes.di_matrix.map((row, i) => (
                        <tr key={i}>
                          <td className="py-1 px-2 text-slate-400">#{i + 1}</td>
                          {row.map((val, j) => (
                            <td key={j} className="py-1 px-2 text-right text-slate-200">
                              {val.toFixed(3)}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
              点击「计算 LI / DI 矩阵」解析原子电子定域化指数与多原子键共享电子对数
            </div>
          )}
        </div>

        <div className="xl:col-span-6 glass-panel rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between gap-2">
            <h3 className="text-sm font-bold text-slate-100">
              概念 DFT (OW-Fukui) 与电多极矩 (Menu 22 / 300)
            </h3>
            <button
              disabled={busy || !inspection}
              onClick={runCdftAndMultipole}
              className="px-3.5 py-1.5 rounded-xl bg-violet-500/20 hover:bg-violet-500/30 text-violet-200 border border-violet-400/35 text-xs font-semibold cursor-pointer disabled:opacity-50"
            >
              计算反应性与偶极矩
            </button>
          </div>

          {multipoleRes && (
            <div className="grid grid-cols-2 gap-2 text-xs font-mono">
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                总偶极矩:{' '}
                <b className="text-sky-300">
                  {multipoleRes.dipole_debye !== undefined && multipoleRes.dipole_debye !== null
                    ? `${multipoleRes.dipole_debye.toFixed(4)} Debye`
                    : '—'}
                </b>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800">
                电子空间范围 &lt;R²&gt;:{' '}
                <b className="text-violet-300">
                  {multipoleRes.spatial_extent_r2 !== undefined &&
                  multipoleRes.spatial_extent_r2 !== null
                    ? `${multipoleRes.spatial_extent_r2.toFixed(2)} a.u.`
                    : '—'}
                </b>
              </div>
            </div>
          )}

          {cdftEntries.length > 0 ? (
            <div className="max-h-44 overflow-y-auto rounded-xl border border-slate-800">
              <table className="w-full text-xs font-mono">
                <thead className="bg-slate-900 text-slate-400 sticky top-0">
                  <tr>
                    <th className="py-1.5 px-2 text-left">原子</th>
                    <th className="py-1.5 px-2 text-right">f⁻ (亲电)</th>
                    <th className="py-1.5 px-2 text-right">f⁺ (亲核)</th>
                    <th className="py-1.5 px-2 text-right">Δf (双描述符)</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {cdftEntries.map((c) => (
                    <tr key={c.index}>
                      <td className="py-1 px-2 text-slate-200">
                        {c.index}({c.element})
                      </td>
                      <td className="py-1 px-2 text-right text-sky-300">
                        {c.f_minus?.toFixed(4) ?? '—'}
                      </td>
                      <td className="py-1 px-2 text-right text-emerald-300">
                        {c.f_plus?.toFixed(4) ?? '—'}
                      </td>
                      <td className="py-1 px-2 text-right text-violet-300">
                        {c.dual_descriptor?.toFixed(4) ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <div className="py-8 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
              点击「计算反应性与偶极矩」一键获取轨道权重 Fukui 指标及偶极矩/空间范围
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export const FunctionMenuWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
  categories: MenuCategory[];
  tasks: TaskRecord[];
  selectedTemplate: MenuFunctionTemplate | null;
  onSelectTemplate: (fn: MenuFunctionTemplate) => void;
  onRefreshTasks: () => void;
}> = ({
  inspection,
  categories,
  tasks,
  selectedTemplate,
  onSelectTemplate,
  onRefreshTasks,
}) => {
  const [filter, setFilter] = useState('');
  const [paramValues, setParamValues] = useState<Record<string, string>>({});
  const [customCmdText, setCustomCmdText] = useState('');
  const [stdout, setStdout] = useState('');
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (!selectedTemplate && categories.length > 0 && categories[0].items.length > 0) {
      onSelectTemplate(categories[0].items[0]);
    }
  }, [categories, selectedTemplate, onSelectTemplate]);

  React.useEffect(() => {
    if (!selectedTemplate) return;
    const init: Record<string, string> = {};
    for (const p of selectedTemplate.params) {
      init[p.key] = p.default_value;
    }
    setParamValues(init);
  }, [selectedTemplate]);

  const resolvedCommands = useMemo(() => {
    if (!selectedTemplate) return [];
    return selectedTemplate.command_template.map((cmd) => {
      if (cmd.startsWith('{') && cmd.endsWith('}')) {
        const key = cmd.slice(1, -1);
        const val = paramValues[key] ?? '';
        return val.includes(':') ? val.split(':')[0] : val;
      }
      return cmd;
    });
  }, [selectedTemplate, paramValues]);

  React.useEffect(() => {
    setCustomCmdText(resolvedCommands.join('\n'));
  }, [resolvedCommands]);

  const runCommand = async () => {
    if (!inspection) return;
    const cmds = customCmdText
      .split(/\r?\n/)
      .map((s) => s.trimEnd());
    setBusy(true);
    setError(null);
    try {
      const res = await api.executeRaw(
        inspection.file_path,
        cmds,
        selectedTemplate ? `${selectedTemplate.id} ${selectedTemplate.name}` : '自定义指令'
      );
      setStdout(res.stdout);
      setDurationMs(res.duration_ms);
      onRefreshTasks();
    } catch (e: any) {
      setError(e.message || '执行 Multiwfn 指令失败');
      onRefreshTasks();
    } finally {
      setBusy(false);
    }
  };

  const handleClearTasks = async () => {
    await api.clearTasks();
    onRefreshTasks();
  };

  return (
    <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
      {/* Left: Menu Tree */}
      <div className="xl:col-span-4 glass-panel rounded-2xl p-4 space-y-3">
        <div className="relative">
          <Search className="w-3.5 h-3.5 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            placeholder="过滤 Multiwfn 功能 (如 电荷/ELF/AIM/NCI)..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-8 pr-3 py-2 text-xs text-slate-100"
          />
        </div>

        <div className="max-h-[560px] overflow-y-auto space-y-3 pr-1">
          {categories.map((cat) => {
            const q = filter.trim().toLowerCase();
            const matched = cat.items.filter(
              (item) =>
                !q ||
                item.name.toLowerCase().includes(q) ||
                item.description.toLowerCase().includes(q) ||
                item.id.toLowerCase().includes(q) ||
                cat.name.toLowerCase().includes(q)
            );
            if (matched.length === 0) return null;
            return (
              <div key={cat.id} className="space-y-1">
                <div className="text-[11px] font-bold text-sky-400 px-1">{cat.name}</div>
                {matched.map((item) => {
                  const active = selectedTemplate?.id === item.id;
                  return (
                    <button
                      key={item.id}
                      onClick={() => onSelectTemplate(item)}
                      className={`w-full text-left px-2.5 py-2 rounded-xl text-xs transition cursor-pointer border ${
                        active
                          ? 'bg-sky-500/20 border-sky-400/50 text-sky-100'
                          : 'bg-slate-900/60 border-transparent hover:border-slate-700 text-slate-300'
                      }`}
                    >
                      <span className="font-mono text-cyan-400 mr-1.5">[{item.id}]</span>
                      <span className="font-medium">{item.name}</span>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      </div>

      {/* Right: Parameter Form, Command Stream, Output & Task Queue */}
      <div className="xl:col-span-8 space-y-4">
        <div className="glass-panel rounded-2xl p-4 space-y-3">
          <div className="flex items-center justify-between flex-wrap gap-2">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-sky-400" />
              <h3 className="text-sm font-bold text-slate-100">
                {selectedTemplate
                  ? `[${selectedTemplate.id}] ${selectedTemplate.name}`
                  : 'Multiwfn 指令执行器'}
              </h3>
            </div>
            {durationMs !== null && (
              <span className="text-xs font-mono text-emerald-300">
                耗时 {(durationMs / 1000).toFixed(2)}s
              </span>
            )}
          </div>

          {selectedTemplate && (
            <p className="text-xs text-slate-400">{selectedTemplate.description}</p>
          )}

          {selectedTemplate && selectedTemplate.params.length > 0 && (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
              {selectedTemplate.params.map((p) => (
                <div key={p.key}>
                  <label className="block text-[11px] text-slate-400 mb-1">
                    {p.name}
                  </label>
                  {p.param_type === 'select' ? (
                    <select
                      value={paramValues[p.key] ?? p.default_value}
                      onChange={(e) =>
                        setParamValues((prev) => ({ ...prev, [p.key]: e.target.value }))
                      }
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs text-slate-100"
                    >
                      {p.options.map((opt) => (
                        <option key={opt} value={opt}>
                          {opt}
                        </option>
                      ))}
                    </select>
                  ) : (
                    <input
                      value={paramValues[p.key] ?? p.default_value}
                      onChange={(e) =>
                        setParamValues((prev) => ({ ...prev, [p.key]: e.target.value }))
                      }
                      className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-100"
                    />
                  )}
                </div>
              ))}
            </div>
          )}

          <div className="grid grid-cols-1 md:grid-cols-12 gap-3 items-start">
            <div className="md:col-span-4">
              <label className="block text-[11px] text-slate-400 mb-1">
                实际命令流 (可自定义编辑)
              </label>
              <textarea
                rows={5}
                value={customCmdText}
                onChange={(e) => setCustomCmdText(e.target.value)}
                className="w-full bg-slate-950 border border-slate-800 rounded-xl p-2.5 text-xs font-mono text-cyan-300"
              />
              <button
                disabled={busy || !inspection}
                onClick={runCommand}
                className="mt-2 w-full py-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center justify-center gap-1.5 cursor-pointer disabled:opacity-50"
              >
                {busy ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <Play className="w-3.5 h-3.5" />
                )}
                <span>执行 Multiwfn 命令序列</span>
              </button>
            </div>

            <div className="md:col-span-8">
              <div className="flex items-center justify-between mb-1">
                <label className="text-[11px] text-slate-400">Multiwfn 标准输出流</label>
                <ExportToolbar title="multiwfn_raw_output" rawText={stdout} />
              </div>
              <pre className="h-[195px] overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap">
                {stdout || '选择功能项并点击执行后，Multiwfn 实时输出将显示在此处...'}
              </pre>
            </div>
          </div>

          {error && (
            <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
              {error}
            </div>
          )}
        </div>

        {/* Task Execution Queue History */}
        <div className="glass-panel rounded-2xl p-4 space-y-2.5">
          <div className="flex items-center justify-between">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider flex items-center gap-2">
              <Clock className="w-3.5 h-3.5 text-sky-400" />
              <span>异步计算任务审计日志 ({tasks.length})</span>
            </h3>
            {tasks.length > 0 && (
              <button
                onClick={handleClearTasks}
                className="flex items-center gap-1 text-[11px] text-slate-400 hover:text-rose-300 cursor-pointer"
              >
                <Trash2 className="w-3 h-3" /> 清空历史
              </button>
            )}
          </div>
          <div className="max-h-[200px] overflow-y-auto space-y-1.5">
            {tasks.length === 0 ? (
              <div className="text-xs text-slate-500 py-4 text-center">暂无任务记录</div>
            ) : (
              tasks.map((t) => (
                <div
                  key={t.id}
                  className="px-3 py-2 rounded-xl bg-slate-900/70 border border-slate-800 flex items-center justify-between gap-2 text-xs"
                >
                  <div className="flex items-center gap-2 min-w-0">
                    <CheckCircle2
                      className={`w-3.5 h-3.5 shrink-0 ${
                        t.status === 'completed'
                          ? 'text-emerald-400'
                          : t.status === 'failed'
                            ? 'text-rose-400'
                            : 'text-sky-400 animate-pulse'
                      }`}
                    />
                    <span className="font-semibold text-slate-200 truncate">{t.name}</span>
                    <span className="text-[11px] font-mono text-slate-500 truncate">
                      [{t.commands.join(' → ')}]
                    </span>
                  </div>
                  <span className="text-[11px] font-mono text-slate-400 shrink-0">
                    {t.duration_ms !== undefined && t.duration_ms !== null
                      ? `${(t.duration_ms / 1000).toFixed(2)}s`
                      : t.status}
                  </span>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
