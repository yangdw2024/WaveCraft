import React, { useState, useRef, useEffect, useCallback } from 'react';
import { GripVertical, Split, Maximize2, Minimize2, PanelLeft, PanelRight } from 'lucide-react';
import { Tooltip } from './Tooltip';

interface ResizableSplitPaneProps {
  left: React.ReactNode;
  right: React.ReactNode;
  defaultSplit?: number; // e.g. 58 = 58% left, 42% right
  minLeftPercent?: number;
  maxLeftPercent?: number;
  className?: string;
  leftClassName?: string;
  rightClassName?: string;
  storageKey?: string;
  showPresets?: boolean;
}

export const ResizableSplitPane: React.FC<ResizableSplitPaneProps> = ({
  left,
  right,
  defaultSplit = 55,
  minLeftPercent = 20,
  maxLeftPercent = 80,
  className = '',
  leftClassName = '',
  rightClassName = '',
  storageKey,
  showPresets = true,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  // Initialize split ratio from localStorage if available
  const [splitRatio, setSplitRatio] = useState<number>(() => {
    if (storageKey) {
      try {
        const saved = localStorage.getItem(`wavecraft_split_${storageKey}`);
        if (saved) {
          const parsed = parseFloat(saved);
          if (!isNaN(parsed) && parsed >= minLeftPercent && parsed <= maxLeftPercent) {
            return parsed;
          }
        }
      } catch {
        // Ignore localStorage error
      }
    }
    return defaultSplit;
  });

  const [isDragging, setIsDragging] = useState(false);
  const [maximizedPane, setMaximizedPane] = useState<'left' | 'right' | null>(null);

  const updateSplitRatio = useCallback(
    (val: number) => {
      const clamped = Math.max(minLeftPercent, Math.min(maxLeftPercent, val));
      setSplitRatio(clamped);
      if (storageKey) {
        try {
          localStorage.setItem(`wavecraft_split_${storageKey}`, clamped.toFixed(1));
        } catch {
          // Ignore
        }
      }
    },
    [minLeftPercent, maxLeftPercent, storageKey]
  );

  const startDrag = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      setIsDragging(true);

      const onMouseMove = (ev: MouseEvent) => {
        if (!containerRef.current) return;
        const rect = containerRef.current.getBoundingClientRect();
        if (rect.width <= 0) return;
        const offset = ev.clientX - rect.left;
        const percent = (offset / rect.width) * 100;
        updateSplitRatio(percent);
      };

      const onMouseUp = () => {
        setIsDragging(false);
        window.removeEventListener('mousemove', onMouseMove);
        window.removeEventListener('mouseup', onMouseUp);
      };

      window.addEventListener('mousemove', onMouseMove);
      window.addEventListener('mouseup', onMouseUp);
    },
    [updateSplitRatio]
  );

  return (
    <div className={`flex flex-col space-y-2 w-full min-w-0 ${className}`}>
      {/* Top Split Presets & Quick Layout Toolbar */}
      {showPresets && (
        <div className="hidden lg:flex items-center justify-between px-1 text-[11px] text-slate-400">
          <div className="flex items-center gap-1.5 font-mono text-[11px]">
            <Split className="w-3.5 h-3.5 text-cyan-400" />
            <span className="text-slate-400 font-semibold">自适应自由分栏:</span>
            {maximizedPane ? (
              <span className="text-amber-300 font-semibold">
                [ 已最大化展开{maximizedPane === 'left' ? '左侧视口栏' : '右侧数据栏'} ]
              </span>
            ) : (
              <span className="text-cyan-300">
                左 {Math.round(splitRatio)}% : 右 {Math.round(100 - splitRatio)}%
              </span>
            )}
          </div>

          <div className="flex items-center gap-1.5">
            {maximizedPane ? (
              <button
                onClick={() => setMaximizedPane(null)}
                className="px-2.5 py-1 rounded-lg bg-amber-500/20 border border-amber-400/50 text-amber-200 hover:bg-amber-500/30 font-semibold text-[11px] flex items-center gap-1 transition cursor-pointer shadow-sm"
              >
                <Minimize2 className="w-3 h-3" />
                <span>还原双栏分栏</span>
              </button>
            ) : (
              <>
                <div className="flex items-center gap-1 bg-slate-950/80 border border-slate-800 rounded-lg p-0.5">
                  {[
                    { label: '视口主导 (65:35)', val: 65 },
                    { label: '均衡对半 (50:50)', val: 50 },
                    { label: '数据主导 (35:65)', val: 35 },
                  ].map((preset) => (
                    <button
                      key={preset.label}
                      onClick={() => updateSplitRatio(preset.val)}
                      className={`px-2 py-0.5 rounded-md text-[10.5px] font-mono transition cursor-pointer ${
                        Math.abs(splitRatio - preset.val) < 2
                          ? 'bg-cyan-500/25 text-cyan-200 border border-cyan-400/50 font-bold shadow-sm'
                          : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                      }`}
                    >
                      {preset.label}
                    </button>
                  ))}
                </div>

                <div className="flex items-center gap-1">
                  <Tooltip content="仅展开左侧栏为整屏宽度" position="bottom">
                    <button
                      onClick={() => setMaximizedPane('left')}
                      className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
                    >
                      <PanelLeft className="w-3.5 h-3.5" />
                    </button>
                  </Tooltip>
                  <Tooltip content="仅展开右侧栏为整屏宽度" position="bottom">
                    <button
                      onClick={() => setMaximizedPane('right')}
                      className="p-1 rounded-lg bg-slate-900 border border-slate-800 text-slate-400 hover:text-sky-300 transition cursor-pointer"
                    >
                      <PanelRight className="w-3.5 h-3.5" />
                    </button>
                  </Tooltip>
                </div>
              </>
            )}
          </div>
        </div>
      )}

      {/* Main Split Container */}
      <div
        ref={containerRef}
        className={`relative w-full min-w-0 flex flex-col lg:flex-row items-stretch select-none ${
          isDragging ? 'select-none pointer-events-none' : ''
        }`}
      >
        {/* Left Pane */}
        <div
          style={
            maximizedPane === 'left'
              ? { width: '100%', flex: '1 1 100%' }
              : maximizedPane === 'right'
              ? { display: 'none' }
              : {
                  width: `calc(${splitRatio}% - 6px)`,
                  flex: `0 0 calc(${splitRatio}% - 6px)`,
                }
          }
          className={`w-full min-w-0 transition-all ${
            isDragging ? 'transition-none pointer-events-none' : ''
          } ${leftClassName}`}
        >
          {left}
        </div>

        {/* Resizable Divider (Visible on Large screens, only when neither is maximized) */}
        {!maximizedPane && (
          <div
            onMouseDown={startDrag}
            className={`hidden lg:flex items-center justify-center w-3 shrink-0 cursor-col-resize select-none group relative z-10 mx-0.5 ${
              isDragging ? 'bg-cyan-500/30' : 'hover:bg-cyan-500/20'
            } transition-colors rounded-sm`}
            title="按住左右拖拽可自由调整左右视口与数据栏宽度"
          >
            {/* Visual handle pill */}
            <div
              className={`w-1 h-16 rounded-full transition-all flex items-center justify-center ${
                isDragging
                  ? 'bg-cyan-400 shadow-[0_0_10px_rgba(56,189,248,0.9)] scale-y-110'
                  : 'bg-slate-700 group-hover:bg-cyan-400 group-hover:shadow-[0_0_6px_rgba(56,189,248,0.6)]'
              }`}
            >
              <GripVertical className="w-2.5 h-2.5 text-slate-950 opacity-80" />
            </div>
          </div>
        )}

        {/* Right Pane */}
        <div
          style={
            maximizedPane === 'right'
              ? { width: '100%', flex: '1 1 100%' }
              : maximizedPane === 'left'
              ? { display: 'none' }
              : {
                  width: `calc(${100 - splitRatio}% - 6px)`,
                  flex: `0 0 calc(${100 - splitRatio}% - 6px)`,
                }
          }
          className={`w-full min-w-0 transition-all ${
            isDragging ? 'transition-none pointer-events-none' : ''
          } ${rightClassName}`}
        >
          {right}
        </div>
      </div>
    </div>
  );
};
