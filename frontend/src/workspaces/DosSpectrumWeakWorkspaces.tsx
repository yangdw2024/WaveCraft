import React, { useState } from 'react';
import { Activity, Loader2, Play, Sparkles, Waves } from 'lucide-react';
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
  const [method, setMethod] = useState('NCI');
  const [gridQuality, setGridQuality] = useState('Coarse');
  const [outputMode, setOutputMode] = useState<'scatter' | 'cube'>('scatter');
  const [fragmentAtoms, setFragmentAtoms] = useState('');
  const [points, setPoints] = useState<NciPoint[]>([]);
  const [isosurface, setIsosurface] = useState<DualIsosurfaceResult | null>(null);
  const [isoOpacity, setIsoOpacity] = useState(0.65);
  const [stdout, setStdout] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        isovalue: 0.5,
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
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Sparkles className="w-4 h-4 text-emerald-400" />
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="NCI">NCI (非共价相互作用 RDG)</option>
            <option value="IGM">IGM (独立梯度模型)</option>
            <option value="mIGM">mIGM (改进独立梯度模型)</option>
            <option value="IGMH">IGMH (Hirshfeld IGM)</option>
            <option value="DORI">DORI (密度重叠区域指示)</option>
          </select>

          <select
            value={outputMode}
            onChange={(e) => setOutputMode(e.target.value as 'scatter' | 'cube')}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="scatter">RDG vs sign(λ₂)ρ 散点图</option>
            <option value="cube">3D 等值面网格 (Cube)</option>
          </select>

          <select
            value={gridQuality}
            onChange={(e) => setGridQuality(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="Coarse">粗糙网格</option>
            <option value="Medium">中等网格</option>
            <option value="Fine">精细网格</option>
          </select>

          {(method === 'IGM' || method === 'IGMH') && (
            <input
              value={fragmentAtoms}
              onChange={(e) => setFragmentAtoms(e.target.value)}
              placeholder="片段1原子 (如 1-3)"
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs font-mono text-slate-200 w-36"
            />
          )}

          <button
            disabled={busy || !inspection}
            onClick={runWeak}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-emerald-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>计算弱相互作用</span>
          </button>
        </div>

        <ExportToolbar
          title={`${inspection?.file_name || 'mol'}_${method}`}
          rows={points}
          rawText={stdout}
        />
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      <div className="grid grid-cols-1 xl:grid-cols-12 gap-4">
        <div className="xl:col-span-7 glass-panel rounded-2xl p-4">
          {outputMode === 'scatter' ? (
            points.length > 0 ? (
              <NciScatterChart points={points} method={method} />
            ) : (
              <div className="h-[360px] flex items-center justify-center text-xs text-slate-500">
                点击「计算弱相互作用」生成 RDG vs sign(λ₂)ρ 交互式散点图
              </div>
            )
          ) : (
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              isosurface={isosurface}
              isoOpacity={isoOpacity}
              onIsoOpacityChange={setIsoOpacity}
              title={`3D ${method} 弱相互作用等值面`}
              heightClass="h-[390px]"
            />
          )}
        </div>

        <div className="xl:col-span-5 glass-panel rounded-2xl p-4 space-y-3">
          <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
            物理判据图例与原始日志
          </h3>
          <div className="grid grid-cols-3 gap-2 text-[11px]">
            <div className="p-2 rounded-lg bg-blue-500/10 border border-blue-500/30 text-blue-300">
              <b>蓝色 (sign &lt; 0)</b>
              <div>强吸引：氢键、卤键</div>
            </div>
            <div className="p-2 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-emerald-300">
              <b>绿色 (sign ≈ 0)</b>
              <div>范德华 / π-π 堆积</div>
            </div>
            <div className="p-2 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300">
              <b>红色 (sign &gt; 0)</b>
              <div>位阻排斥 / 环张力</div>
            </div>
          </div>
          <pre className="h-[245px] overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap">
            {stdout || 'Multiwfn 弱相互作用输出将显示在此处...'}
          </pre>
        </div>
      </div>
    </div>
  );
};
