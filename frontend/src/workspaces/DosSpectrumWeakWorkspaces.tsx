import React, { useState } from 'react';
import { Activity, Columns, LayoutGrid, Loader2, Play, Rows, Sparkles, Waves } from 'lucide-react';
import { api } from '../api/client';
import type {
  DosCurve,
  DualIsosurfaceResult,
  ExampleFileInfo,
  MoleculeInspection,
  NciPoint,
  OrbitalInfo,
  SpectrumCurve,
} from '../types/quantum';
import {
  DosChart,
  NciScatterChart,
  SpectrumChart,
} from '../components/ScientificChart';
import { Molecule3DCanvas } from '../components/Molecule3DCanvas';
import { ExportToolbar } from '../components/ExportToolbar';
import { Tooltip } from '../components/Tooltip';

export const DosWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
}> = ({ inspection }) => {
  const [fwhm, setFwhm] = useState(0.6);
  const [broadening, setBroadening] = useState<'Gaussian' | 'Lorentzian'>('Gaussian');
  const [curve, setCurve] = useState<DosCurve | null>(null);
  const [orbitals, setOrbitals] = useState<OrbitalInfo[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runDos = async (nextFwhm?: number, nextBroad?: 'Gaussian' | 'Lorentzian') => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateDos({
        file_path: inspection.file_path,
        fwhm_ev: nextFwhm ?? fwhm,
        broadening: nextBroad ?? broadening,
      });
      setCurve(res.curve);
      setOrbitals(res.orbitals);
    } catch (e: any) {
      setError(e.message || 'DOS 计算失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Activity className="w-4 h-4 text-sky-400" />
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">展宽函数</span>
            <select
              value={broadening}
              onChange={(e) => {
                const b = e.target.value as 'Gaussian' | 'Lorentzian';
                setBroadening(b);
                if (curve) runDos(fwhm, b);
              }}
              className="bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-slate-100"
            >
              <option value="Gaussian">高斯展宽 (Gaussian)</option>
              <option value="Lorentzian">洛伦兹展宽 (Lorentzian)</option>
            </select>
          </div>
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">FWHM (eV)</span>
            <input
              type="range"
              min={0.1}
              max={2.0}
              step={0.05}
              value={fwhm}
              onChange={(e) => {
                const v = parseFloat(e.target.value);
                setFwhm(v);
              }}
              className="w-28 accent-sky-400 cursor-pointer"
            />
            <span className="font-mono text-sky-300 w-10">{fwhm.toFixed(2)}</span>
          </div>
          <button
            disabled={busy || !inspection}
            onClick={() => runDos()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>生成 TDOS 谱图</span>
          </button>
        </div>

        <ExportToolbar
          title={`${inspection?.file_name || 'mol'}_dos`}
          rows={curve?.points}
        />
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-8 glass-panel rounded-2xl p-4">
          {curve ? (
            <DosChart curve={curve} />
          ) : (
            <div className="h-[340px] flex items-center justify-center text-xs text-slate-500">
              点击「生成 TDOS 谱图」绘制总态密度、占据态与虚态密度曲线
            </div>
          )}
        </div>

        <div className="xl:col-span-4 glass-panel rounded-2xl p-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2.5">
            分子轨道能级表 ({(orbitals.length ? orbitals : inspection?.orbitals || []).length})
          </h3>
          <div className="max-h-[320px] overflow-y-auto rounded-xl border border-slate-800">
            <table className="w-full text-xs font-mono">
              <thead className="bg-slate-900 text-slate-400 sticky top-0">
                <tr>
                  <th className="py-1.5 px-2 text-left">MO</th>
                  <th className="py-1.5 px-2 text-right">能量 (eV)</th>
                  <th className="py-1.5 px-2 text-right">占据</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(orbitals.length ? orbitals : inspection?.orbitals || []).map((o) => (
                  <tr
                    key={`${o.index}-${o.spin_type}`}
                    className={
                      o.label === 'HOMO' || o.label === 'LUMO'
                        ? 'bg-sky-500/10 text-sky-200 font-semibold'
                        : 'hover:bg-slate-800/40'
                    }
                  >
                    <td className="py-1 px-2">
                      #{o.index} {o.label ? `(${o.label})` : ''}
                    </td>
                    <td className="py-1 px-2 text-right">{o.energy_ev.toFixed(3)}</td>
                    <td className="py-1 px-2 text-right">{o.occupancy.toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export const SpectrumWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
  examples: ExampleFileInfo[];
  onSelectFile: (path: string) => void;
}> = ({ inspection, examples, onSelectFile }) => {
  const [specType, setSpecType] = useState('UV-Vis');
  const [broadening, setBroadening] = useState<'Gaussian' | 'Lorentzian'>('Gaussian');
  const [fwhm, setFwhm] = useState(20);
  const [curve, setCurve] = useState<SpectrumCurve | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const spectralExamples = examples
    .filter((e) => {
      const rel = e.relative_path.toLowerCase();
      return (
        rel.startsWith('spectra/') &&
        (rel.endsWith('.out') || rel.endsWith('.log')) &&
        !rel.includes('nmr/tms')
      );
    })
    .sort((a, b) => {
      const score = (n: string) => {
        const l = n.toLowerCase();
        if (l.includes('indigo_td-b3lyp_water')) return 0;
        if (l.includes('nh3bf3_freq')) return 1;
        if (l.includes('2-methyloxirane_raman')) return 2;
        if (l.includes('acetic_acid_tddft')) return 3;
        return 4;
      };
      return score(a.name) - score(b.name);
    });

  const runSpectrum = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateSpectrum({
        file_path: inspection.file_path,
        spec_type: specType,
        fwhm,
        broadening,
      });
      setCurve(res.curve);
      if (res.peak_count === 0) {
        setError(
          '当前文件未检测到振动频率或激发态跃迁数据。请从下方推荐的 Gaussian .out 光谱示例一键切换测试！'
        );
      }
    } catch (e: any) {
      setError(e.message || '光谱解析失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Waves className="w-4 h-4 text-violet-400" />
          <select
            value={specType}
            onChange={(e) => setSpecType(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="UV-Vis">UV-Vis 紫外-可见吸收光谱</option>
            <option value="IR">IR 红外振动光谱</option>
            <option value="Raman">Raman 拉曼光谱</option>
            <option value="ECD">ECD 电子圆二色谱</option>
            <option value="VCD">VCD 振动圆二色谱</option>
          </select>

          <select
            value={broadening}
            onChange={(e) => setBroadening(e.target.value as 'Gaussian' | 'Lorentzian')}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="Gaussian">高斯展宽</option>
            <option value="Lorentzian">洛伦兹展宽</option>
          </select>

          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">FWHM</span>
            <input
              type="number"
              min={1}
              max={200}
              value={fwhm}
              onChange={(e) => setFwhm(Number(e.target.value))}
              className="w-16 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 font-mono text-slate-100"
            />
          </div>

          <button
            disabled={busy || !inspection}
            onClick={runSpectrum}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-500 to-fuchsia-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>模拟展宽光谱</span>
          </button>
        </div>

        <ExportToolbar
          title={`${inspection?.file_name || 'spec'}_${specType}`}
          rows={curve?.peaks}
        />
      </div>

      {/* Quick Spectral Example Switcher */}
      {spectralExamples.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap text-xs">
          <span className="text-slate-400">推荐光谱测试文件:</span>
          {spectralExamples.slice(0, 6).map((ex) => (
            <button
              key={ex.path}
              onClick={() => {
                const lower = ex.name.toLowerCase();
                if (lower.includes('freq')) setSpecType('IR');
                else if (lower.includes('raman')) setSpecType('Raman');
                else setSpecType('UV-Vis');
                onSelectFile(ex.path);
              }}
              className={`px-2.5 py-1 rounded-lg border transition cursor-pointer ${
                inspection?.file_path === ex.path
                  ? 'bg-violet-500/20 border-violet-400 text-violet-200'
                  : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-violet-500/40'
              }`}
            >
              {ex.name}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/30 text-xs text-amber-200">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-8 glass-panel rounded-2xl p-4">
          {curve && curve.peaks.length > 0 ? (
            <SpectrumChart curve={curve} />
          ) : (
            <div className="h-[340px] flex items-center justify-center text-xs text-slate-500">
              选择含频率/TDDFT 激发态的 .out/.log 文件并点击「模拟展宽光谱」
            </div>
          )}
        </div>

        <div className="xl:col-span-4 glass-panel rounded-2xl p-4">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2.5">
            跃迁 / 振动峰列表
          </h3>
          <div className="max-h-[320px] overflow-y-auto rounded-xl border border-slate-800">
            <table className="w-full text-xs font-mono">
              <thead className="bg-slate-900 text-slate-400 sticky top-0">
                <tr>
                  <th className="py-1.5 px-2 text-left">#</th>
                  <th className="py-1.5 px-2 text-right">位置</th>
                  <th className="py-1.5 px-2 text-right">强度</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60">
                {(curve?.peaks || []).map((p) => (
                  <tr key={p.index} className="hover:bg-slate-800/40">
                    <td className="py-1 px-2 text-slate-400">{p.index}</td>
                    <td className="py-1 px-2 text-right text-violet-300">
                      {p.x_value.toFixed(2)}
                    </td>
                    <td className="py-1 px-2 text-right text-slate-200">
                      {p.intensity.toFixed(4)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
};

export const WeakInteractionWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
}> = ({ inspection }) => {
  const [method, setMethod] = useState('IGMH');
  const [gridQuality, setGridQuality] = useState('Coarse');
  const [outputMode, setOutputMode] = useState<'scatter' | 'cube' | 'both'>('both');
  const [fragmentAtoms, setFragmentAtoms] = useState('');
  const [isovalue, setIsovalue] = useState(0.005);
  const [layoutMode, setLayoutMode] = useState<'side-by-side' | 'stacked' | '3d-focus' | 'scatter-focus'>('side-by-side');
  const [points, setPoints] = useState<NciPoint[]>([]);
  const [isosurface, setIsosurface] = useState<DualIsosurfaceResult | null>(null);
  const [isoOpacity, setIsoOpacity] = useState(0.65);
  const [stdout, setStdout] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isIgm = method.includes('IGM');

  // Auto dimer fragment suggestion (e.g. 216 atoms -> 1-108)
  const dimerSuggestion = inspection && inspection.atoms.length > 2
    ? `1-${Math.floor(inspection.atoms.length / 2)}`
    : null;

  const runWeak = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateWeakInteraction({
        file_path: inspection.file_path,
        method,
        grid_quality: gridQuality,
        output_mode: outputMode,
        fragment_atoms: fragmentAtoms || undefined,
        isovalue,
      });
      setPoints(res.scatter_points);
      setIsosurface(res.isosurface || null);
      setStdout(res.stdout);
    } catch (e: any) {
      setError(e.message || '弱相互作用计算失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      {/* Top Configuration & Execution Bar */}
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-2.5">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <select
            value={method}
            onChange={(e) => {
              const m = e.target.value;
              setMethod(m);
              if (m === 'IGMH' || m === 'IGM' || m === 'mIGM') {
                setIsovalue(0.005);
              } else {
                setIsovalue(0.5);
              }
            }}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100 font-medium"
          >
            <option value="IGMH">IGMH (Hirshfeld IGM · 二聚体堆积强力推荐)</option>
            <option value="NCI">NCI (经典非共价相互作用 RDG)</option>
            <option value="IGM">IGM (经典独立梯度模型)</option>
            <option value="mIGM">mIGM (改进独立梯度模型)</option>
            <option value="IRI">IRI (相互作用区域指示函数)</option>
            <option value="DORI">DORI (密度重叠区域指示)</option>
            <option value="PROMOL_NCI">Promolecular NCI (前分子 RDG)</option>
          </select>

          <select
            value={outputMode}
            onChange={(e) => setOutputMode(e.target.value as 'scatter' | 'cube' | 'both')}
            className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-100"
          >
            <option value="both">散点图 + 3D等值面</option>
            <option value="scatter">仅散点图</option>
            <option value="cube">仅3D等值面</option>
          </select>

          <select
            value={gridQuality}
            onChange={(e) => setGridQuality(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs text-slate-100"
          >
            <option value="Coarse">粗糙网格 (快速预览)</option>
            <option value="Medium">中等网格 (标准精度)</option>
            <option value="Fine">精细网格 (出版级)</option>
          </select>

          <div className="flex items-center gap-1">
            <Tooltip content="输入片段1原子序号范围（如 1-108），软件将自动与互补集形成双片段进行分子间相互作用分析" title="片段划分">
              <input
                value={fragmentAtoms}
                onChange={(e) => setFragmentAtoms(e.target.value)}
                placeholder="片段1 (如 1-108)"
                className="bg-slate-950 border border-slate-800 rounded-xl px-2.5 py-1.5 text-xs font-mono text-slate-200 w-36"
              />
            </Tooltip>
            {dimerSuggestion && !fragmentAtoms && (
              <Tooltip
                content={`智能检测到二聚体体系 (${inspection?.atoms.length} 原子)，点击一键自动填入 1-${Math.floor((inspection?.atoms.length || 0) / 2)}`}
                title="二聚体自动等分"
              >
                <button
                  onClick={() => setFragmentAtoms(dimerSuggestion)}
                  className="px-2 py-1 rounded-lg bg-sky-500/15 border border-sky-400/30 text-[10px] text-sky-300 hover:bg-sky-500/25 transition cursor-pointer font-mono"
                >
                  二聚体填入
                </button>
              </Tooltip>
            )}
          </div>

          <div className="flex items-center gap-1 text-xs text-slate-400">
            <span>Iso:</span>
            <input
              type="number"
              step={isIgm ? 0.001 : 0.05}
              min={0.001}
              max={2.0}
              value={isovalue}
              onChange={(e) => setIsovalue(Number(e.target.value) || (isIgm ? 0.005 : 0.5))}
              className="bg-slate-950 border border-slate-800 rounded-xl px-2 py-1 text-xs font-mono text-slate-200 w-20"
            />
          </div>

          {/* Quick Isovalue Chips */}
          <div className="hidden sm:flex items-center gap-1 text-[10px] font-mono text-slate-400">
            {isIgm ? (
              <>
                <Tooltip content="0.003 a.u. 广延包络层，展现更外围的微弱作用" title="等值面预设">
                  <button
                    onClick={() => setIsovalue(0.003)}
                    className={`px-1.5 py-0.5 rounded border transition cursor-pointer ${
                      isovalue === 0.003 ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300' : 'bg-slate-900 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    0.003
                  </button>
                </Tooltip>
                <Tooltip content="0.005 a.u. 经典黄金推荐值 (卢天老师强烈建议)" title="推荐阈值">
                  <button
                    onClick={() => setIsovalue(0.005)}
                    className={`px-1.5 py-0.5 rounded border transition cursor-pointer ${
                      isovalue === 0.005 ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300' : 'bg-slate-900 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    0.005★
                  </button>
                </Tooltip>
                <Tooltip content="0.008 a.u. 致密核心层，突出强范德华与氢键核心区域" title="等值面预设">
                  <button
                    onClick={() => setIsovalue(0.008)}
                    className={`px-1.5 py-0.5 rounded border transition cursor-pointer ${
                      isovalue === 0.008 ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300' : 'bg-slate-900 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    0.008
                  </button>
                </Tooltip>
              </>
            ) : (
              <>
                <Tooltip content="0.30 a.u. 扩展包络面">
                  <button
                    onClick={() => setIsovalue(0.3)}
                    className={`px-1.5 py-0.5 rounded border transition cursor-pointer ${
                      isovalue === 0.3 ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300' : 'bg-slate-900 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    0.3
                  </button>
                </Tooltip>
                <Tooltip content="0.50 a.u. NCI 经典标准推荐值" title="推荐阈值">
                  <button
                    onClick={() => setIsovalue(0.5)}
                    className={`px-1.5 py-0.5 rounded border transition cursor-pointer ${
                      isovalue === 0.5 ? 'bg-emerald-500/20 border-emerald-400 text-emerald-300' : 'bg-slate-900 border-slate-800 hover:text-slate-200'
                    }`}
                  >
                    0.5★
                  </button>
                </Tooltip>
              </>
            )}
          </div>

          <button
            disabled={busy || !inspection}
            onClick={runWeak}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50 hover:brightness-110 transition shadow-lg shadow-emerald-500/20"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>计算弱相互作用</span>
          </button>
        </div>

        {/* Layout Switcher & Export */}
        <div className="flex items-center gap-2">
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-xl p-0.5 text-xs">
            <Tooltip content="并排左右双栏 (3D分子视口与2D散点图各占50%宽，实时对照)" title="布局模式">
              <button
                onClick={() => setLayoutMode('side-by-side')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  layoutMode === 'side-by-side'
                    ? 'bg-sky-500/20 text-sky-300 font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Columns className="w-3.5 h-3.5" />
                <span>并排分栏</span>
              </button>
            </Tooltip>

            <Tooltip content="上下垂直堆叠经典布局，纵深感更强" title="布局模式">
              <button
                onClick={() => setLayoutMode('stacked')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  layoutMode === 'stacked'
                    ? 'bg-sky-500/20 text-sky-300 font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Rows className="w-3.5 h-3.5" />
                <span>上下堆叠</span>
              </button>
            </Tooltip>

            <Tooltip content="聚焦 3D 等值面全宽巨幕视口，细致观察三维相互作用区域" title="布局模式">
              <button
                onClick={() => setLayoutMode('3d-focus')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  layoutMode === '3d-focus'
                    ? 'bg-sky-500/20 text-sky-300 font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <LayoutGrid className="w-3.5 h-3.5" />
                <span>聚焦 3D</span>
              </button>
            </Tooltip>

            <Tooltip content="聚焦 2D 散点图全宽精细剖析 sign(λ₂)ρ 峰形与特征区" title="布局模式">
              <button
                onClick={() => setLayoutMode('scatter-focus')}
                className={`flex items-center gap-1 px-2.5 py-1 rounded-lg transition cursor-pointer ${
                  layoutMode === 'scatter-focus'
                    ? 'bg-sky-500/20 text-sky-300 font-semibold shadow'
                    : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Activity className="w-3.5 h-3.5" />
                <span>聚焦散点</span>
              </button>
            </Tooltip>
          </div>

          <ExportToolbar
            title={`${inspection?.file_name || 'mol'}_${method}`}
            rows={points}
            rawText={stdout}
          />
        </div>
      </div>

      {error && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300 flex items-center justify-between">
          <span>{error}</span>
          <button onClick={() => setError(null)} className="text-rose-400 hover:text-rose-200 underline">
            关闭
          </button>
        </div>
      )}

      {/* Main Analysis Visual Area according to LayoutMode */}
      {layoutMode === 'side-by-side' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {/* Left Column: 3D Viewport */}
          <div className="space-y-4">
            {outputMode !== 'scatter' && (
              <Molecule3DCanvas
                atoms={inspection?.atoms || []}
                bonds={inspection?.bonds || []}
                isosurface={isosurface}
                isoOpacity={isoOpacity}
                onIsoOpacityChange={setIsoOpacity}
                onSelectFragmentAtoms={setFragmentAtoms}
                title={`3D ${method} 相互作用等值面 (BGR 色彩映射)`}
                defaultHeight={580}
                resizable={true}
              />
            )}
          </div>

          {/* Right Column: 2D Scatter Chart + Legends + Logs */}
          <div className="space-y-4">
            {outputMode !== 'cube' &&
              (points.length > 0 ? (
                <NciScatterChart points={points} method={method} />
              ) : (
                <div className="h-[360px] flex flex-col items-center justify-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-2xl p-6 bg-slate-950/40">
                  <Sparkles className="w-8 h-8 text-slate-600 mb-2" />
                  <p className="font-medium text-slate-300">未生成相互作用散点数据</p>
                  <p className="text-[11px] mt-1 text-slate-500">
                    点击上方「计算弱相互作用」即可即时生成 {isIgm ? 'δg_inter vs sign(λ₂)ρ' : 'RDG vs sign(λ₂)ρ'} 散点图
                  </p>
                </div>
              ))}

            {/* Scientific Criteria & Raw Logs */}
            <div className="glass-panel rounded-2xl p-4 space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                  物理判据标准与 Multiwfn 计算日志
                </h3>
                <span className="text-[10px] font-mono text-slate-500">
                  {points.length} 散点 · {isosurface ? (isosurface.positive.triangle_count + (isosurface.negative?.triangle_count || 0)) : 0} 三角面
                </span>
              </div>
              <div className="grid grid-cols-3 gap-2 text-[11px]">
                <div className="p-2 rounded-xl bg-blue-500/10 border border-blue-500/30 text-blue-300">
                  <b>蓝色 (sign &lt; -0.015)</b>
                  <div className="text-[10px] text-blue-200/80">强吸引：经典氢键、卤键</div>
                </div>
                <div className="p-2 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
                  <b>绿色 (sign &approx; 0.0)</b>
                  <div className="text-[10px] text-emerald-200/80">弱吸引：范德华 / π-π 堆积夹心</div>
                </div>
                <div className="p-2 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-300">
                  <b>红色 (sign &gt; +0.015)</b>
                  <div className="text-[10px] text-rose-200/80">强排斥：空间位阻排斥、环内张力</div>
                </div>
              </div>
              <pre className="h-[180px] overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap select-all">
                {stdout || 'Multiwfn 弱相互作用引擎输出将显示在此处...'}
              </pre>
            </div>
          </div>
        </div>
      )}

      {layoutMode === 'stacked' && (
        <div className="space-y-4">
          {outputMode !== 'scatter' && (
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              isosurface={isosurface}
              isoOpacity={isoOpacity}
              onIsoOpacityChange={setIsoOpacity}
              onSelectFragmentAtoms={setFragmentAtoms}
              title={`3D ${method} 相互作用等值面 (BGR 色彩映射)`}
              defaultHeight={520}
              resizable={true}
            />
          )}

          {outputMode !== 'cube' &&
            (points.length > 0 ? (
              <NciScatterChart points={points} method={method} />
            ) : (
              <div className="h-[280px] flex items-center justify-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-2xl">
                点击上方「计算弱相互作用」生成交互式散点图
              </div>
            ))}

          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              物理判据与原始计算输出
            </h3>
            <pre className="h-[180px] overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap">
              {stdout || 'Multiwfn 弱相互作用引擎输出将显示在此处...'}
            </pre>
          </div>
        </div>
      )}

      {layoutMode === '3d-focus' && (
        <div className="space-y-4">
          {outputMode !== 'scatter' && (
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              isosurface={isosurface}
              isoOpacity={isoOpacity}
              onIsoOpacityChange={setIsoOpacity}
              onSelectFragmentAtoms={setFragmentAtoms}
              title={`3D ${method} 相互作用等值面 (沉浸巨幕)`}
              defaultHeight={680}
              resizable={true}
            />
          )}
          {outputMode !== 'cube' && points.length > 0 && (
            <NciScatterChart points={points} method={method} />
          )}
        </div>
      )}

      {layoutMode === 'scatter-focus' && (
        <div className="space-y-4">
          {outputMode !== 'cube' &&
            (points.length > 0 ? (
              <NciScatterChart points={points} method={method} />
            ) : (
              <div className="h-[360px] flex items-center justify-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-2xl">
                点击上方「计算弱相互作用」生成精细散点图
              </div>
            ))}
          {outputMode !== 'scatter' && (
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              isosurface={isosurface}
              isoOpacity={isoOpacity}
              onIsoOpacityChange={setIsoOpacity}
              onSelectFragmentAtoms={setFragmentAtoms}
              title={`3D ${method} 相互作用等值面`}
              defaultHeight={420}
              resizable={true}
            />
          )}
        </div>
      )}
    </div>
  );
};
