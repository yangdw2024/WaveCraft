import React, { useState } from 'react';
import { BarChart3, Layers, Link2, Loader2, Play, Zap } from 'lucide-react';
import { api } from '../api/client';
import type {
  BondOrderEntry,
  ChargeEntry,
  MoleculeInspection,
  OrbitalCompositionEntry,
} from '../types/quantum';
import { Molecule3DCanvas } from '../components/Molecule3DCanvas';
import {
  BondOrderBarChart,
  ChargeBarChart,
  OrbitalLadderChart,
} from '../components/ScientificChart';
import { ExportToolbar } from '../components/ExportToolbar';
import { ResizableSplitPane } from '../components/ResizableSplitPane';

const CHARGE_METHODS: { id: string; desc: string }[] = [
  { id: 'ADCH', desc: '原子偶极矩校正 Hirshfeld（物理意义与 ESP 重现极佳，综合推荐）' },
  { id: 'Hirshfeld', desc: '基于自由原子密度比例划分，对基组极不敏感' },
  { id: 'Hirshfeld-I', desc: '迭代自洽 Hirshfeld，改善了经典 Hirshfeld 电荷偏小的问题' },
  { id: 'CM5', desc: 'Charge Model 5，经验参数化改善偶极矩表现' },
  { id: 'Mulliken', desc: '经典基函数布居分析，计算极快但对基组敏感' },
  { id: 'Lowdin', desc: '基于 Lowdin 对称正交化的原子布居电荷' },
  { id: 'SCPA', desc: 'Ros-Schuit 对称化修正 Mulliken 布居' },
  { id: 'VDD', desc: 'Voronoi 变形密度电荷，适合大分子体系' },
  { id: 'Becke', desc: 'Becke 模糊多中心空间划分积分电荷' },
  { id: 'CHELPG', desc: '三维网格静电势拟合电荷，常用于力场参数化' },
  { id: 'MK', desc: 'Merz-Kollmann 分子表面静电势拟合电荷' },
  { id: 'RESP', desc: 'AMBER 标准受限静电势拟合电荷' },
  { id: 'AIM', desc: 'QTAIM Bader 原子盆积分电荷（物理基础最严格）' },
  { id: 'MBIS', desc: '最小基迭代 Stockholder 电荷' },
  { id: 'EEM', desc: '电负性均衡快速经验电荷' },
  { id: 'Gasteiger', desc: 'PEOE 经验轨道电负性电荷' },
];

export const ChargeAnalysisWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
}> = ({ inspection }) => {
  const [method, setMethod] = useState('ADCH');
  const [charges, setCharges] = useState<ChargeEntry[]>([]);
  const [compareSeries, setCompareSeries] = useState<
    { method: string; charges: ChargeEntry[]; duration_ms: number }[]
  >([]);
  const [busy, setBusy] = useState(false);
  const [stdout, setStdout] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  const methodMeta = CHARGE_METHODS.find((m) => m.id === method);

  const runCharge = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateCharges(inspection.file_path, method);
      setCharges(res.charges);
      setStdout(res.stdout);
      setDurationMs(res.duration_ms);
    } catch (e: any) {
      setError(e.message || '电荷计算失败');
    } finally {
      setBusy(false);
    }
  };

  const runCompare = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.compareCharges(inspection.file_path, [
        'Mulliken',
        'Hirshfeld',
        'ADCH',
        'CM5',
      ]);
      setCompareSeries(res.series);
      if (res.series.length > 0) {
        const adch = res.series.find((s) => s.method === 'ADCH') || res.series[0];
        setCharges(adch.charges);
      }
    } catch (e: any) {
      setError(e.message || '多方法对比失败');
    } finally {
      setBusy(false);
    }
  };

  const totalCharge = charges.reduce((s, c) => s + c.charge, 0);

  return (
    <div className="space-y-4">
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Zap className="w-4 h-4 text-sky-400" />
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 min-w-[180px]"
          >
            {CHARGE_METHODS.map((m) => (
              <option key={m.id} value={m.id}>
                {m.id} 电荷
              </option>
            ))}
          </select>

          <button
            disabled={busy || !inspection}
            onClick={runCharge}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>计算 {method} 电荷</span>
          </button>

          <button
            disabled={busy || !inspection}
            onClick={runCompare}
            className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-sky-200 border border-slate-700 text-xs font-medium flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            <BarChart3 className="w-3.5 h-3.5" />
            <span>四模型横向对比 (Mulliken/Hirshfeld/ADCH/CM5)</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          {durationMs !== null && (
            <span className="text-xs font-mono text-emerald-300">
              {(durationMs / 1000).toFixed(2)}s · ∑q = {totalCharge.toFixed(4)}
            </span>
          )}
          <ExportToolbar
            title={`${inspection?.file_name || 'mol'}_${method}_charges`}
            rows={charges}
            rawText={stdout}
          />
        </div>
      </div>

      {methodMeta && (
        <div className="px-4 py-2 rounded-xl bg-slate-900/70 border border-slate-800 text-xs text-slate-300">
          <span className="text-sky-300 font-semibold mr-2">{method}:</span>
          {methodMeta.desc}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      <ResizableSplitPane
        storageKey="charge_workspace"
        defaultSplit={52}
        left={
          <div className="space-y-4">
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              charges={charges}
              title={`3D 静电电荷着色模型 (${method})`}
              heightClass="h-[460px]"
            />
          </div>
        }
        right={
          <div className="space-y-4">
            <div className="glass-panel rounded-2xl p-4">
              {charges.length > 0 ? (
                <ChargeBarChart charges={charges} method={method} />
              ) : (
                <div className="h-[300px] flex items-center justify-center text-xs text-slate-500">
                  点击「计算电荷」生成交互式柱状图与 3D 电荷映射
                </div>
              )}
            </div>

            {/* Data Table */}
            <div className="glass-panel rounded-2xl p-4">
              <div className="max-h-[210px] overflow-y-auto rounded-xl border border-slate-800">
                <table className="w-full text-xs font-mono">
                  <thead className="bg-slate-900 text-slate-400 sticky top-0">
                    <tr>
                      <th className="py-2 px-3 text-left">原子</th>
                      <th className="py-2 px-3 text-right">{method} 电荷 (e)</th>
                      {compareSeries
                        .filter((s) => s.method !== method)
                        .map((s) => (
                          <th key={s.method} className="py-2 px-3 text-right">
                            {s.method}
                          </th>
                        ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {charges.map((c) => (
                      <tr key={c.index} className="hover:bg-slate-800/40">
                        <td className="py-1.5 px-3 text-slate-200">
                          {c.index} ({c.element})
                        </td>
                        <td
                          className={`py-1.5 px-3 text-right font-semibold ${
                            c.charge >= 0 ? 'text-sky-300' : 'text-rose-300'
                          }`}
                        >
                          {c.charge >= 0 ? '+' : ''}
                          {c.charge.toFixed(5)}
                        </td>
                        {compareSeries
                          .filter((s) => s.method !== method)
                          .map((s) => {
                            const match = s.charges.find((x) => x.index === c.index);
                            return (
                              <td key={s.method} className="py-1.5 px-3 text-right text-slate-300">
                                {match ? match.charge.toFixed(4) : '—'}
                              </td>
                            );
                          })}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        }
      />
    </div>
  );
};

const BOND_METHODS = [
  'Mayer 键级',
  'Wiberg 键级 (Lowdin 基)',
  'Fuzzy 键级 (FBO)',
  'Laplacian 键级 (LBO)',
  'Mulliken 键级',
  'IBSI 本征键强指数',
  '占据扰动 Mayer 键级',
];

export const BondOrderWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
}> = ({ inspection }) => {
  const [method, setMethod] = useState('Mayer 键级');
  const [bonds, setBonds] = useState<BondOrderEntry[]>([]);
  const [busy, setBusy] = useState(false);
  const [stdout, setStdout] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  const runBonds = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateBondOrders(inspection.file_path, method);
      setBonds(res.bond_orders);
      setStdout(res.stdout);
      setDurationMs(res.duration_ms);
    } catch (e: any) {
      setError(e.message || '键级计算失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Link2 className="w-4 h-4 text-cyan-400" />
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 min-w-[220px]"
          >
            {BOND_METHODS.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
          <button
            disabled={busy || !inspection}
            onClick={runBonds}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-cyan-500 to-sky-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>计算键级</span>
          </button>
        </div>

        <div className="flex items-center gap-3">
          {durationMs !== null && (
            <span className="text-xs font-mono text-emerald-300">
              {(durationMs / 1000).toFixed(2)}s · {bonds.length} 对成键
            </span>
          )}
          <ExportToolbar
            title={`${inspection?.file_name || 'mol'}_bond_orders`}
            rows={bonds}
            rawText={stdout}
          />
        </div>
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      <ResizableSplitPane
        storageKey="bond_order_workspace"
        defaultSplit={52}
        left={
          <div className="space-y-4">
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              bondOrders={bonds}
              title={`3D 键级强弱可视化 (${method})`}
              heightClass="h-[460px]"
            />
          </div>
        }
        right={
          <div className="space-y-4">
            <div className="glass-panel rounded-2xl p-4">
              {bonds.length > 0 ? (
                <BondOrderBarChart bonds={bonds} method={method} />
              ) : (
                <div className="h-[260px] flex items-center justify-center text-xs text-slate-500">
                  点击「计算键级」解析化学键级矩阵
                </div>
              )}
            </div>

            <div className="glass-panel rounded-2xl p-4">
              <div className="max-h-[200px] overflow-y-auto rounded-xl border border-slate-800">
                <table className="w-full text-xs font-mono">
                  <thead className="bg-slate-900 text-slate-400 sticky top-0">
                    <tr>
                      <th className="py-2 px-3 text-left">原子 1</th>
                      <th className="py-2 px-3 text-left">原子 2</th>
                      <th className="py-2 px-3 text-right">键级值</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {bonds.map((b, i) => (
                      <tr key={i} className="hover:bg-slate-800/40">
                        <td className="py-1.5 px-3 text-slate-200">{b.atom1}</td>
                        <td className="py-1.5 px-3 text-slate-200">{b.atom2}</td>
                        <td className="py-1.5 px-3 text-right text-cyan-300 font-semibold">
                          {b.bond_order.toFixed(5)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        }
      />
    </div>
  );
};

export const OrbitalAnalysisWorkspace: React.FC<{
  inspection: MoleculeInspection | null;
}> = ({ inspection }) => {
  const [orbitalIdx, setOrbitalIdx] = useState<number>(
    inspection?.summary?.homo_index || 1
  );
  const [method, setMethod] = useState('Hirshfeld');
  const [comps, setComps] = useState<OrbitalCompositionEntry[]>([]);
  const [stdout, setStdout] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  React.useEffect(() => {
    if (inspection?.summary?.homo_index) {
      setOrbitalIdx(inspection.summary.homo_index);
    }
  }, [inspection?.file_path, inspection?.summary?.homo_index]);

  const runComp = async (idx?: number) => {
    if (!inspection) return;
    const target = idx ?? orbitalIdx;
    setOrbitalIdx(target);
    setBusy(true);
    setError(null);
    try {
      const res = await api.calculateOrbitalComposition(
        inspection.file_path,
        target,
        method
      );
      setComps(res.compositions);
      setStdout(res.stdout);
    } catch (e: any) {
      setError(e.message || '轨道成分分析失败');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex flex-wrap items-center gap-3">
          <Layers className="w-4 h-4 text-violet-400" />
          <div className="flex items-center gap-2 text-xs">
            <span className="text-slate-400">轨道序号</span>
            <input
              type="number"
              min={1}
              max={Math.max(1, inspection?.orbitals.length || 999)}
              value={orbitalIdx}
              onChange={(e) => setOrbitalIdx(Math.max(1, Number(e.target.value)))}
              className="w-20 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 font-mono text-slate-100"
            />
          </div>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-1.5 text-xs text-slate-100"
          >
            <option value="Hirshfeld">Hirshfeld 划分 (基组无关推荐)</option>
            <option value="Becke">Becke 划分</option>
            <option value="Mulliken">Mulliken 划分</option>
            <option value="SCPA">SCPA 划分</option>
          </select>
          <button
            disabled={busy || !inspection}
            onClick={() => runComp()}
            className="px-4 py-2 rounded-xl bg-gradient-to-r from-violet-500 to-sky-500 text-slate-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Play className="w-3.5 h-3.5" />}
            <span>剖析 MO #{orbitalIdx} 成分</span>
          </button>
        </div>

        <ExportToolbar
          title={`${inspection?.file_name || 'mol'}_MO${orbitalIdx}_composition`}
          rows={comps}
          rawText={stdout}
        />
      </div>

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      <ResizableSplitPane
        storageKey="orbital_composition"
        defaultSplit={50}
        left={
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <OrbitalLadderChart
              orbitals={inspection?.orbitals || []}
              selectedOrbital={orbitalIdx}
              onSelectOrbital={(idx) => runComp(idx)}
            />
          </div>
        }
        right={
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
              原子轨道成分贡献 (MO #{orbitalIdx} · {method})
            </h3>

            {comps.length > 0 ? (
              <div className="space-y-2 max-h-[340px] overflow-y-auto pr-1">
                {comps.map((c) => (
                  <div key={c.atom_index} className="space-y-1">
                    <div className="flex justify-between text-xs font-mono">
                      <span className="text-slate-200">
                        原子 {c.atom_index} ({c.element})
                      </span>
                      <span className="text-violet-300 font-semibold">
                        {c.percentage.toFixed(2)}%
                      </span>
                    </div>
                    <div className="h-2 rounded-full bg-slate-900 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-violet-500 to-sky-400"
                        style={{ width: `${Math.min(100, c.percentage)}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <pre className="h-[300px] overflow-auto rounded-xl bg-slate-950 border border-slate-800 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap">
                {stdout || '在左侧点击任意能级条或点击「剖析成分」查看轨道原子贡献详情'}
              </pre>
            )}
          </div>
        }
      />
    </div>
  );
};
