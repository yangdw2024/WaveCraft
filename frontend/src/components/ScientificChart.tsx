import React, { useMemo, useRef, useState, useEffect } from 'react';
import { Camera, Download, Maximize2, Minimize2, Image as ImageIcon } from 'lucide-react';
import { Tooltip } from './Tooltip';
import type {
  BondOrderEntry,
  ChargeEntry,
  DosCurve,
  LinePoint,
  NciPoint,
  OrbitalInfo,
  SpectrumCurve,
} from '../types/quantum';

function downloadSvg(svgElement: SVGSVGElement | null, filename: string) {
  if (!svgElement) return;
  const svgData = new XMLSerializer().serializeToString(svgElement);
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

function downloadPng(svgElement: SVGSVGElement | null, filename: string, width = 1200, height = 700) {
  if (!svgElement) return;
  const svgData = new XMLSerializer().serializeToString(svgElement);
  const blob = new Blob([svgData], { type: 'image/svg+xml;charset=utf-8' });
  const blobUrl = URL.createObjectURL(blob);
  const canvas = document.createElement('canvas');
  canvas.width = width * 2;
  canvas.height = height * 2;
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    URL.revokeObjectURL(blobUrl);
    return;
  }
  const img = new Image();
  img.onload = () => {
    ctx.fillStyle = '#090e17';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
    URL.revokeObjectURL(blobUrl);
    const url = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  img.onerror = () => {
    URL.revokeObjectURL(blobUrl);
  };
  img.src = blobUrl;
}

// 1. ChargeBarChart: Atom Net Charge Distribution
export const ChargeBarChart: React.FC<{ charges: ChargeEntry[]; method: string }> = ({
  charges,
  method,
}) => {
  if (charges.length === 0) return null;
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) setIsMaximized(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const maxAbs = Math.max(0.2, ...charges.map((c) => Math.abs(c.charge)));
  const w = isMaximized ? 1100 : 680;
  const h = isMaximized ? 560 : 300;
  const padL = 52;
  const padR = 20;
  const padT = 32;
  const padB = 46;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;
  const zeroY = padT + plotH / 2;
  const barSlot = plotW / Math.max(1, charges.length);
  const barW = Math.min(48, barSlot * 0.68);

  return (
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            {method} 原子净电荷柱状分布 (e)
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300">
            {charges.length} 原子 · 极值: ±{maxAbs.toFixed(3)} e
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出出版级矢量 SVG 格式">
            <button
              onClick={() => downloadSvg(svgRef.current, `wavecraft_charges_${method}.svg`)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={() => downloadPng(svgRef.current, `wavecraft_charges_${method}.png`, w, h)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content={isMaximized ? '退出全屏 (Esc)' : '全屏放大图表'}>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
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
                  fontSize={isMaximized ? '12' : '10'}
                  fontFamily="monospace"
                >
                  {c.charge.toFixed(3)}
                </text>
                <text
                  x={cx}
                  y={h - 14}
                  textAnchor="middle"
                  fill="#94a3b8"
                  fontSize={isMaximized ? '12' : '10.5'}
                  fontFamily="monospace"
                >
                  {c.element}
                  {c.index}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

// 2. BondOrderBarChart: Covalent Bond Order Strengths
export const BondOrderBarChart: React.FC<{ bonds: BondOrderEntry[]; method: string }> = ({
  bonds,
  method,
}) => {
  const top = bonds.slice(0, 16);
  if (top.length === 0) return null;
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) setIsMaximized(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const maxBo = Math.max(1.2, ...top.map((b) => Math.abs(b.bond_order)));
  const w = isMaximized ? 1100 : 680;
  const h = isMaximized ? Math.max(450, top.length * 32 + 60) : Math.max(240, top.length * 26 + 56);
  const padL = 128;
  const padR = 65;
  const padT = 32;
  const plotW = w - padL - padR;

  return (
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40 overflow-y-auto'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            {method} 键级强度分布 (Top {top.length})
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300">
            最大键级: {maxBo.toFixed(3)}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出矢量 SVG 格式">
            <button
              onClick={() => downloadSvg(svgRef.current, `wavecraft_bond_orders_${method}.svg`)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={() => downloadPng(svgRef.current, `wavecraft_bond_orders_${method}.png`, w, h)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content={isMaximized ? '退出全屏 (Esc)' : '全屏放大图表'}>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
          {top.map((b, i) => {
            const stepY = isMaximized ? 32 : 26;
            const y = padT + i * stepY;
            const bw = (Math.max(0, b.bond_order) / maxBo) * plotW;
            const color = b.bond_order > 1.75 ? '#a78bfa' : b.bond_order > 1.2 ? '#38bdf8' : '#22d3ee';
            return (
              <g key={`${b.atom1}-${b.atom2}-${i}`}>
                <text x={padL - 10} y={y + 13} textAnchor="end" fill="#cbd5e1" fontSize={isMaximized ? '12' : '11'} fontFamily="monospace">
                  {b.atom1} — {b.atom2}
                </text>
                <rect x={padL} y={y + 2} width={plotW} height={isMaximized ? 18 : 15} rx={4} fill="rgba(30,41,59,0.5)" />
                <rect x={padL} y={y + 2} width={Math.max(3, bw)} height={isMaximized ? 18 : 15} rx={4} fill={color} fillOpacity={0.88} />
                <text x={padL + bw + 8} y={y + 13} fill="#e2e8f0" fontSize={isMaximized ? '11.5' : '10.5'} fontFamily="monospace">
                  {b.bond_order.toFixed(4)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

// 3. OrbitalLadderChart: Frontier MO Energy Ladder
export const OrbitalLadderChart: React.FC<{
  orbitals: OrbitalInfo[];
  selectedOrbital?: number;
  onSelectOrbital?: (idx: number) => void;
}> = ({ orbitals, selectedOrbital, onSelectOrbital }) => {
  if (orbitals.length === 0) return null;
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) setIsMaximized(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const homoIdx = orbitals.reduce((acc, o) => (o.occupancy > 0.01 ? Math.max(acc, o.index) : acc), 0);
  const windowCount = isMaximized ? 12 : 7;
  const windowOrbs = orbitals
    .filter((o) => Math.abs(o.index - homoIdx) <= windowCount && o.energy_ev > -45 && o.energy_ev < 45)
    .sort((a, b) => b.energy_ev - a.energy_ev || b.index - a.index);
  if (windowOrbs.length === 0) return null;

  const w = isMaximized ? 900 : 540;
  const padT = 36;
  const padB = 22;
  const rowStep = isMaximized ? 30 : 24;
  const h = Math.max(340, padT + padB + windowOrbs.length * rowStep);

  return (
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40 overflow-y-auto'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            前线分子轨道能级阶梯 (点击任意轨道剖析成分)
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
            HOMO: #{homoIdx}
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出矢量 SVG 格式">
            <button
              onClick={() => downloadSvg(svgRef.current, `wavecraft_mo_ladder.svg`)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={() => downloadPng(svgRef.current, `wavecraft_mo_ladder.png`, w, h)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content={isMaximized ? '退出全屏 (Esc)' : '全屏放大图表'}>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
          {windowOrbs.map((orb, rowIdx) => {
            const y = padT + rowIdx * rowStep + 10;
            const isOcc = orb.occupancy > 0.01;
            const isSel = selectedOrbital === orb.index;
            const stroke = isSel ? '#facc15' : isOcc ? '#38bdf8' : '#a78bfa';
            const midX1 = isMaximized ? 200 : 130;
            const midX2 = isMaximized ? 560 : 335;
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
                  x1={midX1}
                  y1={y}
                  x2={midX2}
                  y2={y}
                  stroke={stroke}
                  strokeWidth={isSel || orb.label === 'HOMO' || orb.label === 'LUMO' ? 3.2 : 1.8}
                />
                <text x={midX1 - 10} y={y + 4} textAnchor="end" fill="#cbd5e1" fontSize={isMaximized ? '12' : '10.5'} fontFamily="monospace">
                  MO {orb.index} {orb.label ? `(${orb.label})` : ''}
                </text>
                <text x={midX2 + 10} y={y + 4} fill={stroke} fontSize={isMaximized ? '12' : '10.5'} fontFamily="monospace">
                  {orb.energy_ev.toFixed(2)} eV · 电子占据数 {orb.occupancy.toFixed(1)}
                </text>
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
};

// 4. DosChart: Total Density of States (TDOS)
export const DosChart: React.FC<{ curve: DosCurve }> = ({ curve }) => {
  if (!curve.points.length) return null;
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const exportSvg = () => {
    downloadSvg(svgRef.current, `wavecraft_tdos_${curve.broadening}.svg`);
  };

  const exportPng = () => {
    downloadPng(svgRef.current, `wavecraft_tdos_${curve.broadening}.png`, w, h);
  };

  const w = isMaximized ? 1100 : 720;
  const h = isMaximized ? 560 : 340;
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

  const pathD = curve.points
    .map((p, i) => `${i === 0 ? 'M' : 'L'}${xOf(p.energy_ev).toFixed(1)},${yOf(p.tdos).toFixed(1)}`)
    .join(' ');

  const areaD = `${pathD} L${xOf(maxE).toFixed(1)},${padT + plotH} L${xOf(minE).toFixed(1)},${padT + plotH} Z`;

  return (
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            态密度谱图 TDOS ({curve.broadening})
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-sky-300">
            FWHM = {curve.fwhm_ev.toFixed(2)} eV
          </span>
          {curve.homo_energy_ev !== undefined && curve.homo_energy_ev !== null && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-emerald-500/15 text-emerald-300 border border-emerald-500/30">
              HOMO: {curve.homo_energy_ev.toFixed(2)} eV
            </span>
          )}
          {curve.lumo_energy_ev !== undefined && curve.lumo_energy_ev !== null && (
            <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-rose-500/15 text-rose-300 border border-rose-500/30">
              LUMO: {curve.lumo_energy_ev.toFixed(2)} eV
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出出版级矢量 SVG 态密度谱图" title="导出图表" shortcut="[SVG]">
            <button
              onClick={exportSvg}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={exportPng}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip
            content={isMaximized ? "退出全屏模式 (Esc)" : "全屏沉浸高分辨率查看态密度谱图"}
            title="视口模式"
            shortcut="[F]"
          >
            <button
              onClick={() => setIsMaximized((v) => !v)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
          <defs>
            <linearGradient id="tdosFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.45" />
              <stop offset="100%" stopColor="#38bdf8" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[-20, -10, 0, 10, 20].map((ev) => {
            if (ev < minE || ev > maxE) return null;
            const x = xOf(ev);
            return (
              <g key={ev}>
                <line x1={x} y1={padT} x2={x} y2={padT + plotH} stroke="rgba(148,163,184,0.12)" strokeDasharray="3 3" />
                <text x={x} y={padT + plotH + 15} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
                  {ev}
                </text>
              </g>
            );
          })}

          <path d={areaD} fill="url(#tdosFill)" />
          <path d={pathD} fill="none" stroke="#38bdf8" strokeWidth="2.0" />

          {curve.homo_energy_ev !== undefined && curve.homo_energy_ev !== null && (
            <line
              x1={xOf(curve.homo_energy_ev)}
              y1={padT}
              x2={xOf(curve.homo_energy_ev)}
              y2={padT + plotH}
              stroke="#34d399"
              strokeWidth="1.5"
              strokeDasharray="4 2"
            />
          )}

          {/* Axis */}
          <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" />
          <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" />

          <text x={padL + plotW / 2} y={h - 6} textAnchor="middle" fill="#cbd5e1" fontSize="11">
            能量 Energy (eV)
          </text>
          <text
            x={16}
            y={padT + plotH / 2}
            textAnchor="middle"
            fill="#cbd5e1"
            fontSize="11"
            transform={`rotate(-90 16 ${padT + plotH / 2})`}
          >
            态密度 TDOS (states/eV)
          </text>
        </svg>
      </div>
    </div>
  );
};

// 5. SpectrumChart: UV-Vis / IR / Raman Spectrum
export const SpectrumChart: React.FC<{ curve: SpectrumCurve }> = ({ curve }) => {
  const [hovered, setHovered] = useState<number | null>(null);
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  if (!curve || curve.x_values.length === 0) return null;

  const exportSvg = () => {
    downloadSvg(svgRef.current, `wavecraft_spectrum_${curve.spectrum_type || 'spec'}.svg`);
  };

  const exportPng = () => {
    downloadPng(svgRef.current, `wavecraft_spectrum_${curve.spectrum_type || 'spec'}.png`, w, h);
  };

  const w = isMaximized ? 1100 : 720;
  const h = isMaximized ? 560 : 340;
  const padL = 60;
  const padR = 24;
  const padT = 32;
  const padB = 44;
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
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            {curve.spectrum_type || '模拟展宽'} 光谱曲线
          </span>
          <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800/80 text-violet-300">
            {curve.peaks.length} 个特征吸收/振动峰
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出出版级矢量 SVG 光谱图" title="导出图表" shortcut="[SVG]">
            <button
              onClick={exportSvg}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={exportPng}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip
            content={isMaximized ? '退出全屏模式 (Esc)' : '全屏沉浸高分辨率查看光谱图与跃迁棒'}
            title="视口模式"
            shortcut="[F]"
          >
            <button
              onClick={() => setIsMaximized((v) => !v)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
          <defs>
            <linearGradient id="spectFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="#a78bfa" stopOpacity="0.4" />
              <stop offset="100%" stopColor="#a78bfa" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Area fill under curve */}
          <path d={areaPath} fill="url(#spectFill)" />

          {/* Stick peaks */}
          {curve.peaks.map((p, idx) => {
            const sx = xOf(p.x_value);
            const sy = yOf(p.intensity);
            const isHov = hovered === idx;
            return (
              <g
                key={p.index || idx}
                onMouseEnter={() => setHovered(idx)}
                onMouseLeave={() => setHovered(null)}
                className="cursor-pointer"
              >
                <line
                  x1={sx}
                  y1={padT + plotH}
                  x2={sx}
                  y2={Math.max(padT, sy)}
                  stroke={isHov ? '#f43f5e' : '#fb7185'}
                  strokeWidth={isHov ? 2.5 : 1.5}
                />
                <circle cx={sx} cy={Math.max(padT, sy)} r={isHov ? 4 : 2.5} fill={isHov ? '#f43f5e' : '#fb7185'} />
              </g>
            );
          })}

          {/* Broadened envelope curve */}
          <path d={linePath} fill="none" stroke="#c084fc" strokeWidth="2.2" />

          {/* Axes */}
          <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" />
          <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" />

          {/* X ticks */}
          {[0, 0.25, 0.5, 0.75, 1].map((f, i) => {
            const xv = minX + (maxX - minX) * f;
            return (
              <text key={i} x={xOf(xv)} y={padT + plotH + 16} textAnchor="middle" fill="#94a3b8" fontSize="10" fontFamily="monospace">
                {xv.toFixed(1)}
              </text>
            );
          })}

          <text x={padL + plotW / 2} y={h - 6} textAnchor="middle" fill="#cbd5e1" fontSize="11">
            {curve.x_label || '波长 / 波数 (nm / cm⁻¹)'}
          </text>
          <text
            x={16}
            y={padT + plotH / 2}
            textAnchor="middle"
            fill="#cbd5e1"
            fontSize="11"
            transform={`rotate(-90 16 ${padT + plotH / 2})`}
          >
            {curve.y_label || '吸收强度 (Absorbance / Intensity)'}
          </text>
        </svg>
      </div>
    </div>
  );
};

// 6. NciScatterChart: IGMH/RDG 2D Scatter Chart
export const NciScatterChart: React.FC<{ points: NciPoint[]; method: string }> = ({
  points,
  method,
}) => {
  const [customMaxY, setCustomMaxY] = useState<number | 'auto'>('auto');
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const maxPoints = 3000;
  const sampledPoints = useMemo(() => {
    if (points.length <= maxPoints) return points;
    const step = Math.ceil(points.length / maxPoints);
    return points.filter((_, idx) => idx % step === 0);
  }, [points]);

  const exportSvg = () => {
    downloadSvg(svgRef.current, `wavecraft_igmh_scatter_${method}.svg`);
  };

  const exportPng = () => {
    downloadPng(svgRef.current, `wavecraft_igmh_scatter_${method}.png`, w, h);
  };

  const w = isMaximized ? 1100 : 720;
  const h = isMaximized ? 560 : 340;
  const padL = 60;
  const padR = 24;
  const padT = 32;
  const padB = 44;
  const plotW = w - padL - padR;
  const plotH = h - padT - padB;

  const minX = -0.05;
  const maxX = 0.05;
  const maxY = customMaxY === 'auto' ? Math.max(0.6, ...points.map((p) => p.rdg)) : customMaxY;

  const xOf = (x: number) => padL + ((x - minX) / (maxX - minX)) * plotW;
  const yOf = (y: number) => padT + (1 - Math.min(maxY, Math.max(0, y)) / maxY) * plotH;

  return (
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            {method} 弱相互作用二维散点图
          </span>
          <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-slate-800 text-sky-300">
            {points.length} 数据点 · 渲染 {sampledPoints.length} 点
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出矢量 SVG 格式">
            <button
              onClick={exportSvg}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={exportPng}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip
            content={isMaximized ? "退出全屏模式 (Esc)" : "全屏放大散点图"}
            title="视口模式"
            shortcut="[F]"
          >
            <button
              onClick={() => setIsMaximized((v) => !v)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
          {/* Reference lines */}
          <line x1={xOf(0)} y1={padT} x2={xOf(0)} y2={padT + plotH} stroke="#475569" strokeDasharray="3 3" />
          <line x1={padL} y1={padT + plotH} x2={padL + plotW} y2={padT + plotH} stroke="#475569" />
          <line x1={padL} y1={padT} x2={padL} y2={padT + plotH} stroke="#475569" />

          {/* Scatter points with BGR colormap */}
          {sampledPoints.map((p, idx) => {
            const cx = xOf(p.sign_lambda2_rho);
            const cy = yOf(p.rdg);
            let fill = '#10b981'; // Green: vdW
            if (p.sign_lambda2_rho < -0.012) fill = '#0ea5e9'; // Blue: H-bond
            else if (p.sign_lambda2_rho > 0.012) fill = '#f43f5e'; // Red: steric
            return <circle key={idx} cx={cx} cy={cy} r={isMaximized ? 2.5 : 1.75} fill={fill} fillOpacity={0.7} />;
          })}

          <text x={padL + plotW / 2} y={h - 6} textAnchor="middle" fill="#cbd5e1" fontSize="11">
            sign(λ₂)ρ (a.u.)
          </text>
          <text
            x={16}
            y={padT + plotH / 2}
            textAnchor="middle"
            fill="#cbd5e1"
            fontSize="11"
            transform={`rotate(-90 16 ${padT + plotH / 2})`}
          >
            δg_inter / RDG (a.u.)
          </text>
        </svg>
      </div>
    </div>
  );
};

// 7. LineProfileChart: 1D Real Space Density Line Profile
export const LineProfileChart: React.FC<{
  points: LinePoint[];
  title: string;
}> = ({ points, title }) => {
  if (points.length === 0) return null;
  const [isMaximized, setIsMaximized] = useState(false);
  const svgRef = useRef<SVGSVGElement | null>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) setIsMaximized(false);
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const w = isMaximized ? 1100 : 720;
  const h = isMaximized ? 560 : 250;
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
    <div
      className={`glass-panel rounded-2xl p-4 transition-all duration-300 ${
        isMaximized
          ? 'fixed inset-4 z-50 bg-[#070b12]/95 backdrop-blur-2xl flex flex-col justify-between shadow-2xl border border-sky-500/40'
          : 'space-y-3'
      }`}
    >
      <div className="flex items-center justify-between flex-wrap gap-2">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">
            {title} ({points.length} 采样点)
          </span>
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出矢量 SVG 格式">
            <button
              onClick={() => downloadSvg(svgRef.current, `wavecraft_line_profile.svg`)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content="导出高保真位图 PNG 格式">
            <button
              onClick={() => downloadPng(svgRef.current, `wavecraft_line_profile.png`, w, h)}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Camera className="w-3.5 h-3.5" />
            </button>
          </Tooltip>
          <Tooltip content={isMaximized ? '退出全屏 (Esc)' : '全屏放大图表'}>
            <button
              onClick={() => setIsMaximized(!isMaximized)}
              className={`p-1 rounded-lg border transition cursor-pointer ${
                isMaximized
                  ? 'bg-amber-500/20 border-amber-400/40 text-amber-200'
                  : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-sky-300'
              }`}
            >
              {isMaximized ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
            </button>
          </Tooltip>
        </div>
      </div>

      <div className="relative w-full flex items-center justify-center overflow-hidden">
        <svg
          ref={svgRef}
          viewBox={`0 0 ${w} ${h}`}
          className="w-full h-auto rounded-xl bg-[#090e17] border border-slate-800"
        >
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
      </div>
    </div>
  );
};
