import React, { useState } from 'react';
import { Box, Loader2, Play, Sliders, TrendingUp } from 'lucide-react';
import { api } from '../api/client';
import type {
  DualIsosurfaceResult,
  LinePoint,
  MoleculeInspection,
  RealspaceFunctionDef,
  Slice2DData,
} from '../types/quantum';
import { Heatmap2DCanvas, type ColormapName } from '../components/Heatmap2DCanvas';
import { Molecule3DCanvas } from '../components/Molecule3DCanvas';
import { LineProfileChart } from '../components/ScientificChart';
import { ExportToolbar } from '../components/ExportToolbar';
import { ResizableSplitPane } from '../components/ResizableSplitPane';

interface Props {
  inspection: MoleculeInspection | null;
  functions: RealspaceFunctionDef[];
}

export const RealSpaceWorkspace: React.FC<Props> = ({ inspection, functions }) => {
  const [funcId, setFuncId] = useState<string>('density');
  const [gridQuality, setGridQuality] = useState<string>('Coarse');
  const [plane, setPlane] = useState<string>('xy');
  const [colormap, setColormap] = useState<ColormapName>('viridis');
  const [isovalue, setIsovalue] = useState<number>(0.05);
  const [isoOpacity, setIsoOpacity] = useState<number>(0.65);
  const [showAtoms, setShowAtoms] = useState(true);
  const [showContours, setShowContours] = useState(true);

  const [cubeId, setCubeId] = useState<string | null>(null);
  const [slice, setSlice] = useState<Slice2DData | null>(null);
  const [isosurface, setIsosurface] = useState<DualIsosurfaceResult | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [durationMs, setDurationMs] = useState<number | null>(null);
  const [atom1, setAtom1] = useState(1);
  const [atom2, setAtom2] = useState(2);
  const [linePoints, setLinePoints] = useState<LinePoint[]>([]);
  const [lineBusy, setLineBusy] = useState(false);

  const activeFunc = functions.find((f) => f.id === funcId);

  const handleComputeLine = async () => {
    if (!inspection) return;
    setLineBusy(true);
    setError(null);
    try {
      const res = await api.calculateLine({
        file_path: inspection.file_path,
        func_id: funcId,
        atom1,
        atom2,
      });
      setLinePoints(res.points);
    } catch (e: any) {
      setError(e.message || '1D 线性质计算失败');
    } finally {
      setLineBusy(false);
    }
  };

  const handleCompute = async () => {
    if (!inspection) return;
    setBusy(true);
    setError(null);
    try {
      const res = await api.computeRealspace({
        file_path: inspection.file_path,
        func_id: funcId,
        grid_quality: gridQuality,
        isovalue,
        plane,
      });
      setCubeId(res.cube_id);
      setSlice(res.slice_2d);
      setIsosurface(res.isosurface);
      setDurationMs(res.duration_ms);
      if (activeFunc?.signed) {
        setColormap('coolwarm');
      }
    } catch (e: any) {
      setError(e.message || '实空间计算失败');
    } finally {
      setBusy(false);
    }
  };

  const handlePlaneOrIndexChange = async (newPlane: string, newIndex?: number) => {
    setPlane(newPlane);
    if (!cubeId) return;
    try {
      const next = await api.getCubeSlice(cubeId, newPlane, newIndex);
      setSlice(next);
    } catch {
      // ignore
    }
  };

  const handleIsoSlider = async (val: number) => {
    setIsovalue(val);
    if (!cubeId) return;
    try {
      const iso = await api.getCubeIsosurface(cubeId, val);
      setIsosurface(iso);
    } catch {
      // ignore
    }
  };

  return (
    <div className="space-y-4">
      {/* Control Strip */}
      <div className="glass-panel rounded-2xl p-4 flex flex-wrap items-end gap-3 justify-between">
        <div className="flex flex-wrap items-end gap-3">
          <div>
            <label className="block text-[11px] text-slate-400 mb-1">实空间函数 (Menu 5)</label>
            <select
              value={funcId}
              onChange={(e) => setFuncId(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100 min-w-[210px]"
            >
              {functions.map((f) => (
                <option key={f.id} value={f.id}>
                  [{f.menu_num}] {f.name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">网格精度</label>
            <select
              value={gridQuality}
              onChange={(e) => setGridQuality(e.target.value)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
            >
              <option value="Coarse">粗糙 (极速)</option>
              <option value="Medium">中等 (推荐)</option>
              <option value="Fine">精细 (慢)</option>
            </select>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">切面方向</label>
            <div className="flex rounded-xl overflow-hidden border border-slate-800 bg-slate-950">
              {['xy', 'xz', 'yz'].map((p) => (
                <button
                  key={p}
                  onClick={() => handlePlaneOrIndexChange(p)}
                  className={`px-3 py-2 text-xs font-mono uppercase cursor-pointer transition ${
                    plane === p
                      ? 'bg-sky-500/25 text-sky-200 font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-[11px] text-slate-400 mb-1">科学色板</label>
            <select
              value={colormap}
              onChange={(e) => setColormap(e.target.value as ColormapName)}
              className="bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-slate-100"
            >
              <option value="viridis">Viridis (经典感知均匀)</option>
              <option value="plasma">Plasma (高对比紫橙)</option>
              <option value="inferno">Inferno (黑金高动态)</option>
              <option value="coolwarm">Coolwarm (正负双极)</option>
              <option value="rdbu">RdBu (红蓝对比)</option>
            </select>
          </div>

          <button
            disabled={busy || !inspection}
            onClick={handleCompute}
            className="px-5 py-2 rounded-xl bg-gradient-to-r from-sky-500 to-cyan-500 hover:from-sky-400 hover:to-cyan-400 text-slate-950 font-bold text-xs flex items-center gap-2 cursor-pointer disabled:opacity-50"
          >
            {busy ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />}
            <span>{busy ? '正在生成三维网格...' : '计算 2D/3D 实空间场'}</span>
          </button>
        </div>

        {durationMs !== null && (
          <div className="text-xs font-mono text-emerald-300">
            已完成 · {(durationMs / 1000).toFixed(2)}s
          </div>
        )}
      </div>

      {activeFunc && (
        <div className="px-4 py-2.5 rounded-xl bg-slate-900/70 border border-slate-800/80 text-xs flex flex-wrap items-center justify-between gap-2">
          <div className="text-slate-300">
            <span className="font-semibold text-sky-300 mr-2">{activeFunc.formula}</span>
            {activeFunc.description}
          </div>
          {slice && (
            <span className="font-mono text-[11px] text-slate-400">
              范围 [{slice.global_min.toExponential(2)}, {slice.global_max.toExponential(2)}] a.u.
            </span>
          )}
        </div>
      )}

      {error && (
        <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/30 text-xs text-rose-300">
          {error}
        </div>
      )}

      {/* Dual View: Left 2D Heatmap, Right 3D Isosurface */}
      <ResizableSplitPane
        storageKey="realspace_workspace"
        defaultSplit={50}
        left={
          <div className="glass-panel rounded-2xl p-4 space-y-3">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-cyan-400" />
                <h3 className="text-xs font-bold text-slate-100">
                  2D 切面分布热图 ({plane.toUpperCase()})
                </h3>
              </div>
              <div className="flex items-center gap-3 text-xs text-slate-300">
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showContours}
                    onChange={(e) => setShowContours(e.target.checked)}
                    className="accent-sky-400"
                  />
                  <span>等高线</span>
                </label>
                <label className="flex items-center gap-1 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={showAtoms}
                    onChange={(e) => setShowAtoms(e.target.checked)}
                    className="accent-sky-400"
                  />
                  <span>原子投影</span>
                </label>
              </div>
            </div>

            {slice ? (
              <>
                <Heatmap2DCanvas
                  slice={slice}
                  colormap={colormap}
                  showAtoms={showAtoms}
                  showContours={showContours}
                />
                <div className="flex items-center gap-3 text-xs">
                  <span className="text-slate-400 shrink-0">
                    切面层 ({slice.slice_index}/{slice.max_index}) ·{' '}
                    {slice.slice_coord_angstrom.toFixed(2)} Å
                  </span>
                  <input
                    type="range"
                    min={0}
                    max={slice.max_index}
                    value={slice.slice_index}
                    onChange={(e) => handlePlaneOrIndexChange(plane, Number(e.target.value))}
                    className="flex-1 accent-sky-400 cursor-pointer"
                  />
                </div>
              </>
            ) : (
              <div className="h-[460px] rounded-xl border border-dashed border-slate-800 flex flex-col items-center justify-center text-slate-500">
                <Box className="w-8 h-8 mb-2 text-slate-600" />
                <p className="text-xs">点击「计算 2D/3D 实空间场」生成交互式热图</p>
              </div>
            )}
          </div>
        }
        right={
          <div className="space-y-3">
            <Molecule3DCanvas
              atoms={inspection?.atoms || []}
              bonds={inspection?.bonds || []}
              isosurface={isosurface}
              isoOpacity={isoOpacity}
              onIsoOpacityChange={setIsoOpacity}
              title={`3D 等值面体渲染 · ±${isovalue.toFixed(3)} a.u.`}
              heightClass="h-[440px]"
            />
            <div className="glass-panel rounded-xl px-4 py-2.5 flex items-center gap-3 text-xs">
              <span className="text-slate-400 shrink-0">3D 等值面阈值</span>
              <input
                type="range"
                min={0.005}
                max={0.35}
                step={0.005}
                value={isovalue}
                onChange={(e) => handleIsoSlider(parseFloat(e.target.value))}
                className="flex-1 accent-cyan-400 cursor-pointer"
              />
              <span className="font-mono text-cyan-300 w-20 text-right">
                ±{isovalue.toFixed(3)}
              </span>
            </div>
          </div>
        }
      />

      {/* 1D Line Profile Section (Menu 3) */}
      <div className="glass-panel rounded-2xl p-4 space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-cyan-400" />
            <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
              1D 键轴线性质分布剖面 (Menu 3)
            </h3>
          </div>
          <div className="flex items-center gap-2 text-xs flex-wrap">
            <span className="text-slate-400">原子1</span>
            <input
              type="number"
              min={1}
              max={Math.max(1, inspection?.atoms.length || 999)}
              value={atom1}
              onChange={(e) => setAtom1(Math.max(1, Number(e.target.value)))}
              className="w-16 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 font-mono text-slate-200"
            />
            <span className="text-slate-400">原子2</span>
            <input
              type="number"
              min={1}
              max={Math.max(1, inspection?.atoms.length || 999)}
              value={atom2}
              onChange={(e) => setAtom2(Math.max(1, Number(e.target.value)))}
              className="w-16 bg-slate-950 border border-slate-800 rounded-lg px-2 py-1 font-mono text-slate-200"
            />
            <button
              disabled={lineBusy || !inspection}
              onClick={handleComputeLine}
              className="px-3.5 py-1.5 rounded-lg bg-cyan-500/20 hover:bg-cyan-500/30 text-cyan-200 border border-cyan-400/35 font-semibold cursor-pointer disabled:opacity-50"
            >
              {lineBusy ? '计算中...' : '提取 1D 线性质曲线'}
            </button>
            <ExportToolbar
              title={`${inspection?.file_name || 'mol'}_line_${funcId}`}
              rows={linePoints}
            />
          </div>
        </div>
        {linePoints.length > 0 ? (
          <LineProfileChart
            points={linePoints}
            title={`原子 ${atom1} — 原子 ${atom2} 沿线 ${activeFunc?.name || funcId} 分布`}
          />
        ) : (
          <div className="py-6 text-center text-xs text-slate-500 border border-dashed border-slate-800 rounded-xl">
            选择起止原子序号后点击「提取 1D 线性质曲线」，自动导出并绘制 1D 物理量曲线
          </div>
        )}
      </div>
    </div>
  );
};
