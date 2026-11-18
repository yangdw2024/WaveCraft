import React, { useEffect, useRef, useState } from 'react';
import { Camera, Download, Maximize2, Minimize2 } from 'lucide-react';
import { Tooltip } from './Tooltip';
import type { Slice2DData } from '../types/quantum';

export type ColormapName = 'viridis' | 'plasma' | 'inferno' | 'coolwarm' | 'rdbu';

interface Heatmap2DCanvasProps {
  slice: Slice2DData | null;
  colormap: ColormapName;
  showAtoms?: boolean;
  showContours?: boolean;
}

function lerp(a: number, b: number, t: number): number {
  return a + (b - a) * t;
}

function sampleStops(stops: [number, number, number][], t: number): [number, number, number] {
  const clamped = Math.max(0, Math.min(1, t));
  const scaled = clamped * (stops.length - 1);
  const idx = Math.floor(scaled);
  const frac = scaled - idx;
  const c0 = stops[idx];
  const c1 = stops[Math.min(stops.length - 1, idx + 1)];
  return [
    Math.round(lerp(c0[0], c1[0], frac)),
    Math.round(lerp(c0[1], c1[1], frac)),
    Math.round(lerp(c0[2], c1[2], frac)),
  ];
}

const PALETTES: Record<ColormapName, [number, number, number][]> = {
  viridis: [
    [68, 1, 84],
    [59, 82, 139],
    [33, 145, 140],
    [94, 201, 98],
    [253, 231, 37],
  ],
  plasma: [
    [13, 8, 135],
    [126, 3, 168],
    [204, 71, 120],
    [248, 149, 64],
    [240, 249, 33],
  ],
  inferno: [
    [0, 0, 4],
    [87, 16, 110],
    [188, 55, 84],
    [249, 142, 9],
    [252, 255, 164],
  ],
  coolwarm: [
    [59, 76, 192],
    [141, 176, 254],
    [221, 221, 221],
    [244, 154, 123],
    [180, 4, 38],
  ],
  rdbu: [
    [103, 0, 31],
    [214, 96, 77],
    [247, 247, 247],
    [67, 147, 195],
    [5, 48, 97],
  ],
};

export const Heatmap2DCanvas: React.FC<Heatmap2DCanvasProps> = ({
  slice,
  colormap,
  showAtoms = true,
  showContours = true,
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [hoverInfo, setHoverInfo] = useState<{
    u: number;
    v: number;
    value: number;
  } | null>(null);
  const [isMaximized, setIsMaximized] = useState(false);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const exportPng = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const url = canvas.toDataURL('image/png');
    const a = document.createElement('a');
    a.href = url;
    a.download = `wavecraft_2d_slice_${colormap}.png`;
    a.click();
  };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !slice || slice.width < 2 || slice.height < 2) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const padL = 54;
    const padR = 72;
    const padT = 22;
    const padB = 42;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = '#090e17';
    ctx.fillRect(0, 0, W, H);

    // Value range (symmetric if signed or coolwarm/rdbu with negative values)
    let vmin = slice.slice_min;
    let vmax = slice.slice_max;
    if (vmax <= vmin) {
      vmax = vmin + 1e-6;
    }
    const isDiverging = (colormap === 'coolwarm' || colormap === 'rdbu') && vmin < 0 && vmax > 0;
    if (isDiverging) {
      const m = Math.max(Math.abs(vmin), Math.abs(vmax));
      vmin = -m;
      vmax = m;
    }

    // Offscreen bilinear image
    const imgData = ctx.createImageData(plotW, plotH);
    const stops = PALETTES[colormap];
    const sw = slice.width;
    const sh = slice.height;
    const vals = slice.values;

    for (let py = 0; py < plotH; py++) {
      // Flip Y so mathematical v_max is at top
      const fy = ((plotH - 1 - py) / Math.max(1, plotH - 1)) * (sh - 1);
      const y0 = Math.floor(fy);
      const y1 = Math.min(sh - 1, y0 + 1);
      const ty = fy - y0;

      for (let px = 0; px < plotW; px++) {
        const fx = (px / Math.max(1, plotW - 1)) * (sw - 1);
        const x0 = Math.floor(fx);
        const x1 = Math.min(sw - 1, x0 + 1);
        const tx = fx - x0;

        const v00 = vals[y0 * sw + x0] ?? 0;
        const v10 = vals[y0 * sw + x1] ?? 0;
        const v01 = vals[y1 * sw + x0] ?? 0;
        const v11 = vals[y1 * sw + x1] ?? 0;
        const v = lerp(lerp(v00, v10, tx), lerp(v01, v11, tx), ty);

        const norm = (v - vmin) / (vmax - vmin);
        const [r, g, b] = sampleStops(stops, norm);
        const off = (py * plotW + px) * 4;
        imgData.data[off] = r;
        imgData.data[off + 1] = g;
        imgData.data[off + 2] = b;
        imgData.data[off + 3] = 255;
      }
    }
    ctx.putImageData(imgData, padL, padT);

    // Optional contour lines via marching squares threshold crossings
    if (showContours) {
      const levels = 8;
      ctx.fillStyle = 'rgba(255,255,255,0.22)';
      for (let py = 1; py < plotH - 1; py++) {
        for (let px = 1; px < plotW - 1; px++) {
          const fy = ((plotH - 1 - py) / Math.max(1, plotH - 1)) * (sh - 1);
          const fx = (px / Math.max(1, plotW - 1)) * (sw - 1);
          const ix = Math.round(fx);
          const iy = Math.round(fy);
          const ix2 = Math.min(sw - 1, ix + 1);
          const iy2 = Math.min(sh - 1, iy + 1);
          const b0 = Math.floor(((vals[iy * sw + ix] - vmin) / (vmax - vmin)) * levels);
          const b1 = Math.floor(((vals[iy * sw + ix2] - vmin) / (vmax - vmin)) * levels);
          const b2 = Math.floor(((vals[iy2 * sw + ix] - vmin) / (vmax - vmin)) * levels);
          if (b0 !== b1 || b0 !== b2) {
            ctx.fillRect(padL + px, padT + py, 1, 1);
          }
        }
      }
    }

    // Plot border
    ctx.strokeStyle = 'rgba(148, 163, 184, 0.35)';
    ctx.lineWidth = 1;
    ctx.strokeRect(padL, padT, plotW, plotH);

    // Projected Atoms (with automatic label stagger when multiple atoms share similar 2D projections)
    const [uMin, uMax, vMin, vMax] = slice.extent;
    if (showAtoms && uMax > uMin && vMax > vMin) {
      const placedLabels: { x: number; y: number }[] = [];
      for (const a of slice.projected_atoms) {
        const px = padL + ((a.u - uMin) / (uMax - uMin)) * plotW;
        const py = padT + (1 - (a.v - vMin) / (vMax - vMin)) * plotH;
        if (px < padL || px > padL + plotW || py < padT || py > padT + plotH) continue;
        const close = a.dist_to_plane < 0.8;
        ctx.beginPath();
        ctx.arc(px, py, close ? 5 : 3.2, 0, Math.PI * 2);
        ctx.fillStyle = close ? 'rgba(248, 250, 252, 0.95)' : 'rgba(203, 213, 225, 0.45)';
        ctx.fill();
        ctx.strokeStyle = '#0f172a';
        ctx.lineWidth = 1.2;
        ctx.stroke();

        let lx = px + 7;
        let ly = py - 5;
        for (const prev of placedLabels) {
          if (Math.abs(lx - prev.x) < 34 && Math.abs(ly - prev.y) < 13) {
            ly += 14;
          }
        }
        placedLabels.push({ x: lx, y: ly });

        ctx.font = 'bold 11px ui-monospace, SFMono-Regular, monospace';
        ctx.fillStyle = close ? '#f8fafc' : 'rgba(226, 232, 240, 0.72)';
        ctx.fillText(`${a.symbol}${a.index}`, lx, ly);
      }
    }

    // Axes ticks
    ctx.fillStyle = '#94a3b8';
    ctx.font = '11px ui-monospace, monospace';
    ctx.textAlign = 'center';
    for (let i = 0; i <= 4; i++) {
      const f = i / 4;
      const uVal = lerp(uMin, uMax, f);
      const px = padL + f * plotW;
      ctx.fillText(uVal.toFixed(1), px, padT + plotH + 16);
    }
    ctx.fillStyle = '#cbd5e1';
    ctx.fillText(slice.u_label, padL + plotW / 2, padT + plotH + 34);

    ctx.textAlign = 'right';
    ctx.fillStyle = '#94a3b8';
    for (let i = 0; i <= 4; i++) {
      const f = i / 4;
      const vVal = lerp(vMin, vMax, f);
      const py = padT + (1 - f) * plotH;
      ctx.fillText(vVal.toFixed(1), padL - 7, py + 4);
    }

    // Colorbar
    const cbX = padL + plotW + 14;
    const cbW = 12;
    for (let py = 0; py < plotH; py++) {
      const norm = 1 - py / Math.max(1, plotH - 1);
      const [r, g, b] = sampleStops(stops, norm);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(cbX, padT + py, cbW, 1);
    }
    ctx.strokeStyle = 'rgba(148,163,184,0.4)';
    ctx.strokeRect(cbX, padT, cbW, plotH);

    ctx.textAlign = 'left';
    ctx.fillStyle = '#cbd5e1';
    ctx.font = '10px ui-monospace, monospace';
    ctx.fillText(vmax.toExponential(1), cbX + cbW + 4, padT + 9);
    ctx.fillText(((vmax + vmin) * 0.5).toExponential(1), cbX + cbW + 4, padT + plotH / 2 + 3);
    ctx.fillText(vmin.toExponential(1), cbX + cbW + 4, padT + plotH);
  }, [slice, colormap, showAtoms, showContours, isMaximized]);

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas || !slice) return;
    const rect = canvas.getBoundingClientRect();
    const sx = (e.clientX - rect.left) * (canvas.width / rect.width);
    const sy = (e.clientY - rect.top) * (canvas.height / rect.height);
    const padL = 54;
    const padR = 72;
    const padT = 22;
    const padB = 42;
    const plotW = canvas.width - padL - padR;
    const plotH = canvas.height - padT - padB;
    if (sx < padL || sx > padL + plotW || sy < padT || sy > padT + plotH) {
      setHoverInfo(null);
      return;
    }
    const fx = (sx - padL) / plotW;
    const fy = 1 - (sy - padT) / plotH;
    const [uMin, uMax, vMin, vMax] = slice.extent;
    const u = lerp(uMin, uMax, fx);
    const v = lerp(vMin, vMax, fy);
    const ix = Math.min(slice.width - 1, Math.max(0, Math.round(fx * (slice.width - 1))));
    const iy = Math.min(slice.height - 1, Math.max(0, Math.round(fy * (slice.height - 1))));
    const val = slice.values[iy * slice.width + ix] ?? 0;
    setHoverInfo({ u, v, value: val });
  };

  return (
    <div
      className={
        isMaximized
          ? 'fixed inset-0 z-50 bg-[#070b12] p-6 flex flex-col items-center justify-center backdrop-blur-2xl'
          : 'relative w-full space-y-2'
      }
    >
      <div className="w-full flex items-center justify-between gap-2 px-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-slate-200">2D 实空间切面热力图</span>
          {slice && (
            <span className="text-[11px] font-mono px-2 py-0.5 rounded bg-slate-800 text-slate-400">
              {slice.width} × {slice.height} 网格 · 色标: {colormap}
            </span>
          )}
        </div>

        <div className="flex items-center gap-1.5">
          <Tooltip content="导出当前 2D 实空间切面为高分辨率 PNG 图像" title="导出图像" shortcut="[PNG]">
            <button
              onClick={exportPng}
              className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
            >
              <Download className="w-3.5 h-3.5" />
            </button>
          </Tooltip>

          <Tooltip
            content={isMaximized ? '退出全屏模式' : '全屏沉浸高分辨率查看 2D 切面图'}
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

      <div className="relative w-full flex flex-col items-center justify-center">
        <canvas
          ref={canvasRef}
          width={isMaximized ? 960 : 680}
          height={isMaximized ? 620 : 460}
          onMouseMove={handleMouseMove}
          onMouseLeave={() => setHoverInfo(null)}
          className="w-full h-auto rounded-xl border border-slate-800 bg-[#090e17]"
        />
        {hoverInfo && (
          <div className="mt-2 w-full px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-700/80 text-xs font-mono text-slate-200 flex items-center justify-between">
            <span>
              坐标: ({hoverInfo.u.toFixed(3)}, {hoverInfo.v.toFixed(3)}) Å
            </span>
            <span className="text-sky-300 font-semibold">
              f(r) = {hoverInfo.value.toExponential(4)} a.u.
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
