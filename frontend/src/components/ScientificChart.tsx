import React, { useMemo, useRef, useState } from 'react';
import { Camera, Download, Maximize2, Minimize2 } from 'lucide-react';
import type {
  BondOrderEntry,
  ChargeEntry,
  DosCurve,
  LinePoint,
  NciPoint,
  OrbitalInfo,
  SpectrumCurve,
} from '../types/quantum';

export const ChargeBarChart: React.FC<{ charges: ChargeEntry[]; method: string }> = ({
  charges,
  method,
}) => {
  if (charges.length === 0) return null;
  const maxAbs = Math.max(0.2, ...charges.map((c) => Math.abs(c.charge)));
  const w = 680;
  const h = 300;
  const padL = 52;
  const padR = 20;
  const padT = 32;
  const padB = 46;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const zeroY = padT + plotH / 2;
  const barSlot = plotW / Math.max(1, charges.length);
  const barW = Math.min(36, barSlot * 0.68);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800">
      <text x={padL} y={19} fill="#cbd5e1" fontSize="12" fontWeight="600">
        {method} 原子净电荷分布 (e)
      </text>
      <line x1={padL} y1={zeroY} x2={w - padR} y2={zeroY} stroke="#475569" strokeDasharray="4 3" />
      {[-maxAbs, -maxAbs / 2, 0, maxAbs / 2, maxAbs].map((val, i) => {
        const y = zeroY - (val / maxAbs) * (plotH / 2);
        return (
          <g key={i}>
            <line x1={padL} y1={y} x2={w - padR} y2={y} stroke="rgba(148,163,184,0.08)" />
            <text x={padL - 8} y={y + 4} textAnchor="end" fill="#94a3b8" fontSize="10" fontFamily="monospace">
              {val.toFixed(2)}
            </text>
          </g>
        );
      })}

      {charges.map((c, idx) => {
        const cx = padL + idx * barSlot + barSlot / 2;
        const bh = (Math.abs(c.charge) / maxAbs) * (plotH / 2);
        const y = c.charge >= 0 ? zeroY - bh : zeroY;
        const fill = c.charge >= 0 ? '#38bdf8' : '#f43f5e';
        return (
          <g key={c.index}>
            <rect
              x={cx - barW / 2}
              y={y}
              width={barW}
              height={Math.max(2, bh)}
              rx={4}
              fill={fill}
              fillOpacity={0.85}
            />
            <text
              x={cx}
              y={c.charge >= 0 ? y - 5 : y + bh + 12}
              textAnchor="middle"
              fill="#e2e8f0"
              fontSize="10"
              fontFamily="monospace"
            >
              {c.charge.toFixed(3)}
            </text>
            <text
              x={cx}
              y={h - 14}
              textAnchor="middle"
              fill="#94a3b8"
              fontSize="10.5"
              fontFamily="monospace"
            >
              {c.element}
              {c.index}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export const BondOrderBarChart: React.FC<{ bonds: BondOrderEntry[]; method: string }> = ({
  bonds,
  method,
}) => {
  const top = bonds.slice(0, 14);
  if (top.length === 0) return null;
  const maxBo = Math.max(1.2, ...top.map((b) => Math.abs(b.bond_order)));
  const w = 680;
  const h = Math.max(240, top.length * 26 + 56);
  const padL = 128;
  const padR = 65;
  const padT = 32;
  const plotW = w - padL - padR;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800">
      <text x={20} y={20} fill="#cbd5e1" fontSize="12" fontWeight="600">
        {method} 键级强度分布 (Top {top.length})
      </text>
      {top.map((b, i) => {
        const y = padT + i * 26;
        const bw = (Math.max(0, b.bond_order) / maxBo) * plotW;
        const color = b.bond_order > 1.75 ? '#a78bfa' : b.bond_order > 1.2 ? '#38bdf8' : '#22d3ee';
        return (
          <g key={`${b.atom1}-${b.atom2}-${i}`}>
            <text x={padL - 10} y={y + 13} textAnchor="end" fill="#cbd5e1" fontSize="11" fontFamily="monospace">
              {b.atom1} — {b.atom2}
            </text>
            <rect x={padL} y={y + 2} width={plotW} height={15} rx={4} fill="rgba(30,41,59,0.5)" />
            <rect x={padL} y={y + 2} width={Math.max(3, bw)} height={15} rx={4} fill={color} fillOpacity={0.88} />
            <text x={padL + bw + 8} y={y + 13} fill="#e2e8f0" fontSize="10.5" fontFamily="monospace">
              {b.bond_order.toFixed(4)}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export const OrbitalLadderChart: React.FC<{
  orbitals: OrbitalInfo[];
  selectedOrbital?: number;
  onSelectOrbital?: (idx: number) => void;
}> = ({ orbitals, selectedOrbital, onSelectOrbital }) => {
  if (orbitals.length === 0) return null;
  const homoIdx = orbitals.reduce((acc, o) => (o.occupancy > 0.01 ? Math.max(acc, o.index) : acc), 0);
  const window = orbitals
    .filter((o) => Math.abs(o.index - homoIdx) <= 6 && o.energy_ev > -45 && o.energy_ev < 45)
    .sort((a, b) => b.energy_ev - a.energy_ev || b.index - a.index);
  if (window.length === 0) return null;

  const w = 540;
  const padT = 36;
  const padB = 22;
  const rowStep = 24;
  const h = Math.max(340, padT + padB + window.length * rowStep);

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800">
      <text x={18} y={20} fill="#cbd5e1" fontSize="12" fontWeight="600">
        前线分子轨道能级阶梯 (点击任意轨道剖析成分)
      </text>
      {window.map((orb, rowIdx) => {
        const y = padT + rowIdx * rowStep + 10;
        const isOcc = orb.occupancy > 0.01;
        const isSel = selectedOrbital === orb.index;
        const stroke = isSel ? '#facc15' : isOcc ? '#38bdf8' : '#a78bfa';
        return (
          <g
            key={`${orb.index}-${orb.spin_type}`}
            onClick={() => onSelectOrbital?.(orb.index)}
            className="cursor-pointer"
          >
            {orb.label === 'LUMO' && (
              <line
                x1={24}
                y1={y + rowStep * 0.5}
                x2={w - 24}
                y2={y + rowStep * 0.5}
                stroke="rgba(148,163,184,0.22)"
                strokeDasharray="4 4"
              />
            )}
            <line
              x1={130}
              y1={y}
              x2={335}
              y2={y}
              stroke={stroke}
              strokeWidth={isSel || orb.label === 'HOMO' || orb.label === 'LUMO' ? 3 : 1.8}
            />
            <text x={120} y={y + 4} textAnchor="end" fill="#cbd5e1" fontSize="10.5" fontFamily="monospace">
              MO {orb.index} {orb.label ? `(${orb.label})` : ''}
            </text>
            <text x={345} y={y + 4} fill={stroke} fontSize="10.5" fontFamily="monospace">
              {orb.energy_ev.toFixed(2)} eV · Occ {orb.occupancy.toFixed(1)}
            </text>
          </g>
        );
      })}
    </svg>
  );
};

export const DosChart: React.FC<{ curve: DosCurve }> = ({ curve }) => {
  if (!curve.points.length) return null;
  const w = 720;
  const h = 340;
  const padL = 56;
  const padR = 24;
  const padT = 34;
  const padB = 42;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const minE = curve.points[0].energy_ev;
  const maxE = curve.points[curve.points.length - 1].energy_ev;
  const maxD = Math.max(0.1, ...curve.points.map((p) => p.tdos));

  const xOf = (e: number) => padL + ((e - minE) / Math.max(1e-6, maxE - minE)) * plotW;
  const yOf = (d: number) => padT + (1 - d / maxD) * plotH;

  const pathOf = (pick: (p: DosCurve['points'][0]) => number) =>
    curve.points
      .map((p, i) => `${i === 0 ? 'M' : 'L'}${xOf(p.energy_ev).toFixed(1)},${yOf(pick(p)).toFixed(1)}`)
      .join(' ');

  const tdosPath = pathOf((p) => p.tdos);
  const occArea =
    `${pathOf((p) => p.occupied_dos)} L${xOf(maxE).toFixed(1)},${(padT + plotH).toFixed(1)} L${xOf(minE).toFixed(1)},${(padT + plotH).toFixed(1)} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800">
      <text x={padL} y={20} fill="#cbd5e1" fontSize="12" fontWeight="600">
        态密度谱图 TDOS ({curve.broadening}, FWHM = {curve.fwhm_ev.toFixed(2)} eV)
      </text>

      <path d={occArea} fill="rgba(56, 189, 248, 0.16)" />
      <path d={tdosPath} fill="none" stroke="#38bdf8" strokeWidth="2.2" />
      <path d={pathOf((p) => p.virtual_dos)} fill="none" stroke="#a78bfa" strokeWidth="1.5" strokeDasharray="4 3" />

      {curve.homo_energy_ev !== undefined && curve.homo_energy_ev !== null && (
        <g>
          <line
            x1={xOf(curve.homo_energy_ev)}
            y1={padT}
            x2={xOf(curve.homo_energy_ev)}
            y2={padT + plotH}
            stroke="#22c55e"
            strokeDasharray="5 3"
          />
          <text x={xOf(curve.homo_energy_ev) - 4} y={padT + 12} textAnchor="end" fill="#4ade80" fontSize="10.5" fontFamily="monospace">
            HOMO ({curve.homo_energy_ev.toFixed(2)} eV)
          </text>
        </g>
      )}

      {curve.lumo_energy_ev !== undefined && curve.lumo_energy_ev !== null && (
        <g>
          <line
            x1={xOf(curve.lumo_energy_ev)}
            y1={padT}
            x2={xOf(curve.lumo_energy_ev)}
            y2={padT + plotH}
            stroke="#f43f5e"
            strokeDasharray="5 3"
          />
          <text x={xOf(curve.lumo_energy_ev) + 4} y={padT + 26} textAnchor="start" fill="#fb7185" fontSize="10.5" fontFamily="monospace">
            LUMO ({curve.lumo_energy_ev.toFixed(2)} eV)
          </text>
        </g>
      )}

      <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" />
      <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" />
      {[0, 0.25, 0.5, 0.75, 1].map((f, i) => {
        const ev = minE + (maxE - minE) * f;
        return (
          <text key={i} x={xOf(ev)} y={padT + plotH + 17} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
            {ev.toFixed(1)}
          </text>
        );
      })}
      <text x={padL + plotW / 2} y={h - 6} textAnchor="middle" fill="#cbd5e1" fontSize="11">
        轨道能量 (eV)
      </text>
    </svg>
  );
};

export const SpectrumChart: React.FC<{ curve: SpectrumCurve }> = ({ curve }) => {
  const [hovered, setHovered] = useState<number | null>(null);
  if (curve.x_values.length === 0) return null;

  const w = 720;
  const h = 340;
  const padL = 56;
  const padR = 24;
  const padT = 34;
  const padB = 42;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const minX = curve.x_values[0];
  const maxX = curve.x_values[curve.x_values.length - 1];
  const maxY = Math.max(1e-5, ...curve.y_values, ...curve.peaks.map((p) => p.intensity));

  const xOf = (x: number) => padL + ((x - minX) / Math.max(1e-6, maxX - minX)) * plotW;
  const yOf = (y: number) => padT + (1 - Math.max(0, y) / maxY) * plotH;

  const linePath = curve.x_values
    .map((x, i) => `${i === 0 ? 'M' : 'L'}${xOf(x).toFixed(1)},${yOf(curve.y_values[i]).toFixed(1)}`)
    .join(' ');
  const areaPath = `${linePath} L${xOf(maxX).toFixed(1)},${(padT + plotH).toFixed(1)} L${xOf(minX).toFixed(1)},${(padT + plotH).toFixed(1)} Z`;

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800">
      <text x={padL} y={20} fill="#cbd5e1" fontSize="12" fontWeight="600">
        {curve.spectrum_type} 模拟展宽谱图 ({curve.peaks.length} 个特征峰)
      </text>
      <path d={areaPath} fill="rgba(168, 85, 247, 0.16)" />
      <path d={linePath} fill="none" stroke="#c084fc" strokeWidth="2.2" />

      {curve.peaks.map((p, idx) => {
        const px = xOf(p.x_value);
        const py = yOf(p.intensity);
        const active = hovered === idx;
        return (
          <g
            key={p.index}
            onMouseEnter={() => setHovered(idx)}
            onMouseLeave={() => setHovered(null)}
            className="cursor-pointer"
          >
            <line
              x1={px}
              y1={padT + plotH}
              x2={px}
              y2={py}
              stroke={active ? '#facc15' : 'rgba(56, 189, 248, 0.55)'}
              strokeWidth={active ? 2.5 : 1.3}
            />
            {active && (
              <text x={Math.min(w - 130, Math.max(padL + 10, px))} y={Math.max(padT + 14, py - 6)} fill="#fde047" fontSize="10.5" fontFamily="monospace">
                {p.label}
              </text>
            )}
          </g>
        );
      })}

      <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" />
      <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" />
      {[0, 0.25, 0.5, 0.75, 1].map((f, i) => {
        const xv = minX + (maxX - minX) * f;
        return (
          <text key={i} x={xOf(xv)} y={padT + plotH + 17} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
            {xv.toFixed(0)}
          </text>
        );
      })}
      <text x={padL + plotW / 2} y={h - 6} textAnchor="middle" fill="#cbd5e1" fontSize="11">
        {curve.x_label}
      </text>
    </svg>
  );
};

function getBgrScatterColor(s: number): string {
  // Continuous Multiwfn / gnuplot BGR color mapping:
  // s = sign(lambda2) * rho
  // <= -0.04: Royal Blue (Strong attractive, H-bonds)
  // -0.02: Cyan
  // 0.00: Emerald Green (vdW, pi-pi stacking)
  // +0.012: Amber Yellow
  // >= +0.02: Bright Red (Steric clash, ring strain)
  if (s <= -0.04) return '#2563eb';
  if (s < -0.015) {
    const t = (s - -0.04) / 0.025;
    const r = Math.round(37 + (6 - 37) * t);
    const g = Math.round(99 + (182 - 99) * t);
    const b = Math.round(235 + (212 - 235) * t);
    return `rgb(${r},${g},${b})`;
  }
  if (s < 0.0) {
    const t = (s - -0.015) / 0.015;
    const r = Math.round(6 + (34 - 6) * t);
    const g = Math.round(182 + (197 - 182) * t);
    const b = Math.round(212 + (94 - 212) * t);
    return `rgb(${r},${g},${b})`;
  }
  if (s < 0.012) {
    const t = s / 0.012;
    const r = Math.round(34 + (234 - 34) * t);
    const g = Math.round(197 + (179 - 197) * t);
    const b = Math.round(94 + (8 - 94) * t);
    return `rgb(${r},${g},${b})`;
  }
  if (s < 0.022) {
    const t = (s - 0.012) / 0.01;
    const r = Math.round(234 + (239 - 234) * t);
    const g = Math.round(179 + (68 - 179) * t);
    const b = Math.round(8 + (68 - 8) * t);
    return `rgb(${r},${g},${b})`;
  }
  return '#ef4444';
}

export const NciScatterChart: React.FC<{ points: NciPoint[]; method: string }> = ({
  points,
  method,
}) => {
  const [customMaxY, setCustomMaxY] = useState<number | 'auto'>('auto');
  const [isMaximized, setIsMaximized] = useState(false);
  const [hoveredPoint, setHoveredPoint] = useState<NciPoint | null>(null);
  const [mousePos, setMousePos] = useState<{ x: number; y: number } | null>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);

  if (points.length === 0) return null;

  const isIgm = method.includes('IGM');

  // Compute real data maxima
  const realMaxY = useMemo(() => {
    let m = 0;
    for (const p of points) {
      if (p.rdg > m) m = p.rdg;
    }
    return m;
  }, [points]);

  // Dynamic scientific Y-axis ceiling:
  // For IGMH, dg_inter max is typically ~0.025-0.038 a.u. Defaulting to ~0.035-0.040 gives full resolution!
  const activeMaxY = useMemo(() => {
    if (typeof customMaxY === 'number') return customMaxY;
    if (isIgm) {
      const target = Math.max(0.025, realMaxY * 1.15);
      return Math.ceil(target * 100) / 100;
    }
    return Math.max(1.5, Math.ceil(realMaxY * 1.1));
  }, [customMaxY, isIgm, realMaxY]);

  const w = isMaximized ? 1100 : 720;
  const h = isMaximized ? 640 : 380;
  const padL = 68;
  const padR = 28;
  const padT = 38;
  const padB = 48;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const minX = -0.05;
  const maxX = 0.05;

  const xOf = (s: number) => padL + ((Math.max(minX, Math.min(maxX, s)) - minX) / (maxX - minX)) * plotW;
  const yOf = (r: number) => padT + (1 - Math.max(0, Math.min(activeMaxY, r)) / activeMaxY) * plotH;

  const yTicks = useMemo(() => {
    return [0, activeMaxY * 0.25, activeMaxY * 0.5, activeMaxY * 0.75, activeMaxY];
  }, [activeMaxY]);

  const exportSvg = () => {
    if (!svgRef.current) return;
    const svgData = new XMLSerializer().serializeToString(svgRef.current);
    const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `wavecraft_${method}_scatter.svg`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div
      className={
        isMaximized
          ? 'fixed inset-0 z-50 bg-[#070b12] p-6 flex flex-col items-center justify-center backdrop-blur-xl'
          : 'relative rounded-2xl bg-[#090e17] border border-slate-800 p-3 space-y-2'
      }
    >
      {/* Chart Header & Controls */}
      <div className="flex items-center justify-between gap-2 flex-wrap px-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            {method} {isIgm ? '分子间独立梯度模型 (IGMH)' : '非共价相互作用 (NCI)'} 散点图
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
            {points.length.toLocaleString()} 采样点 · Y峰值: {realMaxY.toFixed(4)} a.u.
          </span>
        </div>

        <div className="flex items-center gap-1.5 flex-wrap">
          {/* Y Range Selector */}
          <div className="flex items-center bg-slate-900 border border-slate-800 rounded-lg p-0.5 text-[10px] font-mono">
            <span className="text-slate-500 px-1.5">Y量程:</span>
            <button
              onClick={() => setCustomMaxY('auto')}
              className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                customMaxY === 'auto'
                  ? 'bg-sky-500/20 text-sky-300 font-bold'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
              title="自动自适应最优显示区间"
            >
              自动 ({activeMaxY.toFixed(activeMaxY < 0.1 ? 3 : 2)})
            </button>
            {isIgm ? (
              <>
                <button
                  onClick={() => setCustomMaxY(0.04)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    customMaxY === 0.04
                      ? 'bg-sky-500/20 text-sky-300 font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="IGMH 经典标准量程 (0 ~ 0.04 a.u.)"
                >
                  0.04 (标准)
                </button>
                <button
                  onClick={() => setCustomMaxY(0.08)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    customMaxY === 0.08
                      ? 'bg-sky-500/20 text-sky-300 font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  0.08
                </button>
                <button
                  onClick={() => setCustomMaxY(2.0)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    customMaxY === 2.0
                      ? 'bg-sky-500/20 text-sky-300 font-bold'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                  title="全尺度 RDG 范围"
                >
                  2.0 (全景)
                </button>
              </>
            ) : (
              <>
                <button
                  onClick={() => setCustomMaxY(1.0)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    customMaxY === 1.0 ? 'bg-sky-500/20 text-sky-300' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  1.0
                </button>
                <button
                  onClick={() => setCustomMaxY(2.0)}
                  className={`px-1.5 py-0.5 rounded transition cursor-pointer ${
                    customMaxY === 2.0 ? 'bg-sky-500/20 text-sky-300' : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  2.0 (标准)
                </button>
              </>
            )}
          </div>

          <button
            onClick={exportSvg}
            className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            title="导出出版级矢量 SVG 图表"
          >
            <Download className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={() => setIsMaximized((v) => !v)}
            className={`p-1 rounded-lg border transition cursor-pointer ${
              isMaximized
                ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
            }`}
            title={isMaximized ? '退出全屏' : '全屏最大化'}
          >
            {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
          </button>
        </div>
      </div>

      {/* SVG Canvas */}
      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl select-none"
          onMouseMove={(e) => {
            const rect = e.currentTarget.getBoundingClientRect();
            const svgX = ((e.clientX - rect.left) / rect.width) * w;
            const svgY = ((e.clientY - rect.top) / rect.height) * h;
            setMousePos({ x: svgX, y: svgY });

            // Find closest point within threshold
            if (svgX >= padL && svgX <= padL + plotW && svgY >= padT && svgY <= padT + plotH) {
              const invS = minX + ((svgX - padL) / plotW) * (maxX - minX);
              const invY = (1 - (svgY - padT) / plotH) * activeMaxY;
              let best: NciPoint | null = null;
              let bestDist = Infinity;
              for (const p of points) {
                const dx = (p.sign_lambda2_rho - invS) / (maxX - minX);
                const dy = (p.rdg - invY) / activeMaxY;
                const d = dx * dx + dy * dy;
                if (d < bestDist && d < 0.003) {
                  bestDist = d;
                  best = p;
                }
              }
              setHoveredPoint(best);
            } else {
              setHoveredPoint(null);
            }
          }}
          onMouseLeave={() => {
            setHoveredPoint(null);
            setMousePos(null);
          }}
        >
          {/* Background grid */}
          <rect x={padL} y={padT} width={plotW} height={plotH} fill="#060a10" rx={6} />

          {/* Zero reference vertical line */}
          <line
            x1={xOf(0)}
            y1={padT}
            x2={xOf(0)}
            y2={padT + plotH}
            stroke="#334155"
            strokeWidth="1.2"
            strokeDasharray="4 3"
          />

          {/* Horizontal Grid lines */}
          {yTicks.map((val, idx) => {
            const y = yOf(val);
            return (
              <g key={idx}>
                <line
                  x1={padL}
                  y1={y}
                  x2={padL + plotW}
                  y2={y}
                  stroke="rgba(51, 65, 85, 0.45)"
                  strokeDasharray="3 3"
                />
                <text
                  x={padL - 10}
                  y={y + 4}
                  textAnchor="end"
                  fill="#94a3b8"
                  fontSize="10"
                  fontFamily="monospace"
                >
                  {val.toFixed(val < 0.1 ? 3 : 2)}
                </text>
              </g>
            );
          })}

          {/* Scatter points rendered with smooth continuous BGR colors */}
          {points.map((p, i) => {
            const s = p.sign_lambda2_rho;
            const fill = getBgrScatterColor(s);
            const cx = xOf(s);
            const cy = yOf(p.rdg);
            return (
              <circle
                key={i}
                cx={cx}
                cy={cy}
                r={1.75}
                fill={fill}
                fillOpacity={0.72}
              />
            );
          })}

          {/* Coordinate axes */}
          <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" strokeWidth="1.2" />
          <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" strokeWidth="1.2" />

          {/* X ticks */}
          {[-0.05, -0.025, 0, 0.025, 0.05].map((v, i) => (
            <g key={i}>
              <line x1={xOf(v)} y1={padT + plotH} x2={xOf(v)} y2={padT + plotH + 5} stroke="#475569" />
              <text
                x={xOf(v)}
                y={padT + plotH + 18}
                textAnchor="middle"
                fill="#94a3b8"
                fontSize="10"
                fontFamily="monospace"
              >
                {v.toFixed(3)}
              </text>
            </g>
          ))}

          {/* X Axis Label */}
          <text x={padL + plotW / 2} y={h - 10} textAnchor="middle" fill="#cbd5e1" fontSize="11" fontWeight="500">
            sign(λ₂)ρ (a.u.) · 蓝色: 强吸引(氢键) | 绿色: 范德华/π-π堆积 | 红色: 位阻排斥
          </text>

          {/* Y Axis Label */}
          <text
            x={16}
            y={padT + plotH / 2}
            textAnchor="middle"
            transform={`rotate(-90 16 ${padT + plotH / 2})`}
            fill="#cbd5e1"
            fontSize="11"
            fontWeight="500"
          >
            {isIgm ? 'δg_inter (分子间弱相互作用强度, a.u.)' : 'RDG (折减密度梯度, a.u.)'}
          </text>

          {/* Hover highlight indicator */}
          {hoveredPoint && (
            <g>
              <circle
                cx={xOf(hoveredPoint.sign_lambda2_rho)}
                cy={yOf(hoveredPoint.rdg)}
                r={5}
                fill="none"
                stroke="#facc15"
                strokeWidth="2"
              />
            </g>
          )}
        </svg>

        {/* Hover Point Tooltip */}
        {hoveredPoint && mousePos && (
          <div
            className="pointer-events-none absolute px-2.5 py-1.5 rounded-lg bg-slate-950/90 border border-slate-700 text-[11px] font-mono shadow-2xl backdrop-blur text-slate-200 z-20"
            style={{
              left: Math.min(w - 180, Math.max(20, mousePos.x + 12)),
              top: Math.max(10, mousePos.y - 48),
            }}
          >
            <div className="font-semibold text-cyan-300">
              sign(λ₂)ρ = {hoveredPoint.sign_lambda2_rho.toFixed(4)} a.u.
            </div>
            <div className="text-slate-300">
              {isIgm ? 'δg_inter' : 'RDG'} = {hoveredPoint.rdg.toFixed(4)} a.u.
            </div>
            <div className="text-[10px] text-slate-400">
              {hoveredPoint.sign_lambda2_rho < -0.015
                ? '强相互作用 (强吸引/氢键)'
                : hoveredPoint.sign_lambda2_rho > 0.015
                  ? '空间位阻排斥 (环张力/碰撞)'
                  : '弱相互作用 (范德华 / π-π 堆积)'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export const LineProfileChart: React.FC<{
  points: LinePoint[];
  title: string;
}> = ({ points, title }) => {
  if (points.length === 0) return null;
  const w = 720;
  const h = 250;
  const padL = 62;
  const padR = 24;
  const padT = 30;
  const padB = 38;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const minX = points[0].dist_angstrom;
  const maxX = points[points.length - 1].dist_angstrom;
  const minY = Math.min(...points.map((p) => p.value));
  const maxY = Math.max(...points.map((p) => p.value));
  const spanY = Math.max(1e-9, maxY - minY);

  const xOf = (x: number) => padL + ((x - minX) / Math.max(1e-6, maxX - minX)) * plotW;
  const yOf = (y: number) => padT + (1 - (y - minY) / spanY) * plotH;

  const linePath = points
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${xOf(p.dist_angstrom).toFixed(1)},${yOf(p.value).toFixed(1)}`)
    .join(' ');

  return (
    <svg viewBox={`0 0 ${w} ${h}`} className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800">
      <text x={padL} y={19} fill="#cbd5e1" fontSize="12" fontWeight="600">
        {title} ({points.length} 采样点)
      </text>
      <path d={linePath} fill="none" stroke="#22d3ee" strokeWidth="2.2" />
      <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" />
      <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" />
      {[0, 0.25, 0.5, 0.75, 1].map((f, i) => {
        const xv = minX + (maxX - minX) * f;
        return (
          <text key={i} x={xOf(xv)} y={padT + plotH + 15} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
            {xv.toFixed(2)}
          </text>
        );
      })}
      <text x={padL - 8} y={padT + 8} textAnchor="end" fill="#94a3b8" fontSize="10" fontFamily="monospace">
        {maxY.toExponential(1)}
      </text>
      <text x={padL - 8} y={padT + plotH} textAnchor="end" fill="#94a3b8" fontSize="10" fontFamily="monospace">
        {minY.toExponential(1)}
      </text>
      <text x={padL + plotW / 2} y={h - 6} textAnchor="middle" fill="#cbd5e1" fontSize="11">
        沿键轴路径距离 (Å)
      </text>
    </svg>
  );
};
