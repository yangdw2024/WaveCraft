import React, { useEffect, useState } from 'react';
import { Boxes, Loader2, Sparkles } from 'lucide-react';
import { api } from '../api/client';
import type { DualIsosurfaceResult, MoleculeInspection } from '../types/quantum';
import { Molecule3DCanvas } from '../components/Molecule3DCanvas';
import { ExportToolbar } from '../components/ExportToolbar';
import { ResizableSplitPane } from '../components/ResizableSplitPane';

interface Props {
  inspection: MoleculeInspection | null;
}

export const StructureOrbitalWorkspace: React.FC<Props> = ({ inspection }) => {
  const [orbitalIdx, setOrbitalIdx] = useState<number>(1);
  const [gridQuality, setGridQuality] = useState<string>('Coarse');
  const [isovalue, setIsovalue] = useState<number>(0.03);
  const [isoOpacity, setIsoOpacity] = useState<number>(0.68);
  const [cubeId, setCubeId] = useState<string | null>(null);
  const [isosurface, setIsosurface] = useState<DualIsosurfaceResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);

  useEffect(() => {
    if (inspection?.summary?.homo_index) {
      setOrbitalIdx(inspection.summary.homo_index);
    } else {
      setOrbitalIdx(1);
    }
    setCubeId(null);
    setIsosurface(null);
    setError(null);
  }, [inspection?.file_path]);

  const runOrbitalCube = async (targetOrb?: number) => {
    if (!inspection) return;
    const orb = targetOrb ?? orbitalIdx;
    setOrbitalIdx(orb);
    setBusy(true);
    setError(null);
    try {
      const res = await api.computeOrbitalCube(
        inspection.file_path,
        orb,
        gridQuality,
        isovalue
      );
      setCubeId(res.cube_id);
      setIsosurface(res.isosurface);
      setDurationMs(res.duration_ms);
    } catch (e: any) {
      setError(e.message || '计算轨道等值面失败');
    } finally {
      setBusy(false);
    }
  };

  const handleIsoChange = async (newIso: number) => {
    setIsovalue(newIso);
    if (!cubeId) return;
    try {
      const updated = await api.getCubeIsosurface(cubeId, newIso);
      setIsosurface(updated);
    } catch {
      // ignore transient slider errors
    }
  };

  const homo = inspection?.summary?.homo_index;
  const lumo = inspection?.summary?.lumo_index;
  const selectedOrbInfo = inspection?.orbitals.find((o) => o.index === orbitalIdx);

  return (
    <ResizableSplitPane
      storageKey="structure_orbital"
      defaultSplit={62}
      left={
        <div className="space-y-4">
          <Molecule3DCanvas
            atoms={inspection?.atoms || []}
            bonds={inspection?.bonds || []}
            isosurface={isosurface}
            isoOpacity={isoOpacity}
            onIsoOpacityChange={setIsoOpacity}
            title={
              isosurface
                ? `3D 分子轨道 #${orbitalIdx} 等值面 (±${isovalue.toFixed(3)} a.u.)`
                : '3D 分子结构交互测量视口'
            }
            heightClass="h-[540px]"
          />

          {/* Bond Lengths Summary Table */}
          <div className="glass-panel rounded-2xl p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                共价键几何参数表 ({inspection?.bonds.length || 0})
              </h3>
              <ExportToolbar
                title={`${inspection?.file_name || 'molecule'}_geometry`}
                rows={inspection?.bonds.map((b) => ({
                  原子1: `${b.symbol1}${b.atom1}`,
                  原子2: `${b.symbol2}${b.atom2}`,
                  键长_Angstrom: b.length,
                  推测键级: b.order,
                }))}
              />
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-5 gap-2 max-h-40 overflow-y-auto">
              {(inspection?.bonds || []).map((b, i) => (
                <div
                  key={i}
                  className="px-2.5 py-2 rounded-xl bg-slate-900/70 border border-slate-800 text-xs flex items-center justify-between"
                >
                  <span className="text-slate-300 font-mono">
                    {b.symbol1}
                    {b.atom1}—{b.symbol2}
                    {b.atom2}
                  </span>
                  <span className="text-sky-300 font-mono font-semibold">
                    {b.length.toFixed(3)} Å
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      }
      right={
        <div className="space-y-4">
          <div className="glass-panel rounded-2xl p-4 space-y-3.5">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Boxes className="w-4 h-4 text-sky-400" />
                <h3 className="text-sm font-bold text-slate-100">
                  3D 分子轨道等值面引擎
                </h3>
              </div>
              {durationMs !== null && (
                <span className="text-[11px] font-mono text-emerald-400">
                  {(durationMs / 1000).toFixed(2)}s
                </span>
              )}
            </div>

            <p className="text-xs text-slate-400 leading-relaxed">
              调用 Multiwfn <code className="text-sky-300">菜单 5 → 4</code> 导出轨道三维网格，并由 Rust Marching Cubes 实时提取正负双相（蓝/红）等值面。
            </p>

            {/* Quick Frontier Orbital Buttons */}
            {homo && (
              <div className="grid grid-cols-4 gap-1.5">
                {[
                  { label: 'HOMO-1', idx: Math.max(1, homo - 1) },
                  { label: 'HOMO', idx: homo },
                  { label: 'LUMO', idx: lumo || homo + 1 },
                  { label: 'LUMO+1', idx: (lumo || homo + 1) + 1 },
                ].map((btn) => (
                  <button
                    key={btn.label}
                    disabled={busy || !inspection}
                    onClick={() => runOrbitalCube(btn.idx)}
                    className={`py-1.5 rounded-lg text-[11px] font-semibold border transition cursor-pointer ${
                      orbitalIdx === btn.idx
                        ? 'bg-sky-500/25 border-sky-400 text-sky-200'
                        : 'bg-slate-900 border-slate-800 text-slate-300 hover:border-sky-500/40'
                    }`}
                  >
                    {btn.label} (#{btn.idx})
                  </button>
                ))}
              </div>
            )}

            <div className="grid grid-cols-2 gap-2.5">
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">轨道序号</label>
                <input
                  type="number"
                  min={1}
                  max={Math.max(1, inspection?.orbitals.length || 999)}
                  value={orbitalIdx}
                  onChange={(e) => setOrbitalIdx(Math.max(1, Number(e.target.value)))}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-1.5 text-xs font-mono text-slate-200"
                />
              </div>
              <div>
                <label className="block text-[11px] text-slate-400 mb-1">网格精度</label>
                <select
                  value={gridQuality}
                  onChange={(e) => setGridQuality(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-800 rounded-lg px-2 py-1.5 text-xs text-slate-200"
                >
                  <option value="Coarse">粗糙 (极速预览)</option>
                  <option value="Medium">中等 (推荐平衡)</option>
                  <option value="Fine">精细 (发表级)</option>
                </select>
              </div>
            </div>

            {selectedOrbInfo && (
              <div className="px-3 py-2 rounded-xl bg-slate-900/80 border border-slate-800 text-xs flex items-center justify-between font-mono">
                <span className="text-slate-400">
                  MO #{selectedOrbInfo.index} {selectedOrbInfo.label || ''}
                </span>
                <span className="text-cyan-300">
                  {selectedOrbInfo.energy_ev.toFixed(3)} eV (Occ {selectedOrbInfo.occupancy})
                </span>
              </div>
            )}

            <div>
              <div className="flex justify-between text-[11px] text-slate-400 mb-1">
                <span>等值面阈值 (Isovalue)</span>
                <span className="font-mono text-sky-300">±{isovalue.toFixed(3)} a.u.</span>
              </div>
              <input
                type="range"
                min={0.005}
                max={0.12}
                step={0.005}
                value={isovalue}
                onChange={(e) => handleIsoChange(parseFloat(e.target.value))}
                className="w-full accent-sky-400 cursor-pointer"
              />
            </div>

            <button
              disabled={busy || !inspection}
              onClick={() => runOrbitalCube()}
              className="w-full py-2.5 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 hover:from-sky-400 hover:to-cyan-400 text-slate-950 font-bold text-xs flex items-center justify-center gap-2 transition cursor-pointer disabled:opacity-50"
            >
              {busy ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Sparkles className="w-4 h-4" />
              )}
              <span>{busy ? '正在生成三维轨道网格...' : '计算并渲染 3D 分子轨道'}</span>
            </button>

            {error && (
              <div className="p-2.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
                {error}
              </div>
            )}
          </div>

          {/* Atom Coordinates Table */}
          <div className="glass-panel rounded-2xl p-4">
            <h3 className="text-xs font-bold text-slate-200 uppercase tracking-wider mb-2.5">
              笛卡尔原子坐标 (Å)
            </h3>
            <div className="max-h-[250px] overflow-y-auto rounded-xl border border-slate-800/80">
              <table className="w-full text-xs font-mono">
                <thead className="bg-slate-900/90 text-slate-400 sticky top-0">
                  <tr>
                    <th className="py-1.5 px-2 text-left">#</th>
                    <th className="py-1.5 px-2 text-left">元素</th>
                    <th className="py-1.5 px-2 text-right">X</th>
                    <th className="py-1.5 px-2 text-right">Y</th>
                    <th className="py-1.5 px-2 text-right">Z</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60">
                  {(inspection?.atoms || []).map((a) => (
                    <tr key={a.index} className="hover:bg-slate-800/40">
                      <td className="py-1 px-2 text-slate-400">{a.index}</td>
                      <td className="py-1 px-2 font-semibold text-sky-300">{a.symbol}</td>
                      <td className="py-1 px-2 text-right">{a.x.toFixed(4)}</td>
                      <td className="py-1 px-2 text-right">{a.y.toFixed(4)}</td>
                      <td className="py-1 px-2 text-right">{a.z.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      }
    />
  );
};
