import React, { useState, useRef, useEffect } from 'react';
import {
  Copy,
  Check,
  Maximize2,
  Minimize2,
  Trash2,
  GripHorizontal,
  Terminal,
} from 'lucide-react';
import { Tooltip } from './Tooltip';

interface ExpandableConsoleProps {
  title?: string;
  content: string;
  placeholder?: string;
  initialHeight?: number;
  minHeight?: number;
  maxHeight?: number;
  className?: string;
  actions?: React.ReactNode;
  onClear?: () => void;
  headerBadge?: React.ReactNode;
  icon?: React.ReactNode;
}

export const ExpandableConsole: React.FC<ExpandableConsoleProps> = ({
  title,
  content,
  placeholder = '暂无输出...',
  initialHeight = 240,
  minHeight = 140,
  maxHeight = 1000,
  className = '',
  actions,
  onClear,
  headerBadge,
  icon,
}) => {
  const [height, setHeight] = useState<number>(initialHeight);
  const [isMaximized, setIsMaximized] = useState(false);
  const [copied, setCopied] = useState(false);
  const [isDragging, setIsDragging] = useState(false);

  const startYRef = useRef(0);
  const startHRef = useRef(0);
  const preRef = useRef<HTMLPreElement>(null);

  // Auto-scroll to bottom when new content arrives
  useEffect(() => {
    if (preRef.current) {
      preRef.current.scrollTop = preRef.current.scrollHeight;
    }
  }, [content]);

  // Handle ESC to exit fullscreen
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isMaximized) {
        setIsMaximized(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isMaximized]);

  const copyContent = async () => {
    if (!content) return;
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const startDrag = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
    startYRef.current = e.clientY;
    startHRef.current = height;

    const onMouseMove = (ev: MouseEvent) => {
      const delta = ev.clientY - startYRef.current;
      const nextH = Math.max(minHeight, Math.min(maxHeight, startHRef.current + delta));
      setHeight(nextH);
    };

    const onMouseUp = () => {
      setIsDragging(false);
      window.removeEventListener('mousemove', onMouseMove);
      window.removeEventListener('mouseup', onMouseUp);
    };

    window.addEventListener('mousemove', onMouseMove);
    window.addEventListener('mouseup', onMouseUp);
  };

  const contentElement = (
    <pre
      ref={preRef}
      style={isMaximized ? undefined : { height: `${height}px` }}
      className={`w-full overflow-auto rounded-xl bg-slate-950 border border-slate-800/80 p-3 text-[11px] font-mono text-slate-300 whitespace-pre-wrap leading-relaxed select-text ${
        isMaximized ? 'flex-1 min-h-0' : ''
      }`}
    >
      {content || <span className="text-slate-600 italic">{placeholder}</span>}
    </pre>
  );

  if (isMaximized) {
    return (
      <div className="fixed inset-4 z-[9999] rounded-2xl bg-slate-950/95 border border-cyan-500/50 shadow-2xl p-4 flex flex-col backdrop-blur-2xl">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div className="flex items-center gap-2">
            {icon || <Terminal className="w-4 h-4 text-cyan-400" />}
            <span className="text-sm font-bold text-slate-100">{title || '控制台全屏查看'}</span>
            {headerBadge}
          </div>
          <div className="flex items-center gap-2">
            {actions}
            <button
              onClick={copyContent}
              className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-xs text-slate-300 hover:text-white flex items-center gap-1 cursor-pointer transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? '已复制' : '复制内容'}</span>
            </button>
            {onClear && (
              <button
                onClick={onClear}
                className="px-2.5 py-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-rose-500/40 text-xs text-slate-300 hover:text-rose-300 flex items-center gap-1 cursor-pointer transition"
              >
                <Trash2 className="w-3.5 h-3.5" />
                <span>清空</span>
              </button>
            )}
            <button
              onClick={() => setIsMaximized(false)}
              className="px-3 py-1 rounded-lg bg-cyan-500/20 border border-cyan-400/40 hover:bg-cyan-500/30 text-xs font-semibold text-cyan-200 flex items-center gap-1 cursor-pointer transition"
            >
              <Minimize2 className="w-3.5 h-3.5 text-cyan-300" />
              <span>还原窗口 (Esc)</span>
            </button>
          </div>
        </div>

        <div className="flex-1 min-h-0 pt-3 flex flex-col">
          {contentElement}
        </div>
      </div>
    );
  }

  return (
    <div className={`space-y-1.5 flex flex-col ${className}`}>
      {title && (
        <div className="flex items-center justify-between flex-wrap gap-2 mb-1">
          <div className="flex items-center gap-1.5">
            {icon || <Terminal className="w-3.5 h-3.5 text-cyan-400" />}
            <span className="text-xs font-bold text-slate-300 uppercase tracking-wider">{title}</span>
            {headerBadge}
          </div>

          <div className="flex items-center gap-1">
            {/* Quick Height Presets */}
            <div className="hidden sm:flex items-center gap-1 mr-1">
              {[
                { label: '紧凑', h: 180 },
                { label: '标准', h: 320 },
                { label: '宽屏', h: 520 },
                { label: '巨幕', h: 750 },
              ].map((p) => (
                <button
                  key={p.label}
                  onClick={() => setHeight(p.h)}
                  className={`px-1.5 py-0.5 rounded text-[10px] font-mono cursor-pointer transition ${
                    height === p.h
                      ? 'bg-cyan-500/20 text-cyan-200 border border-cyan-400/50'
                      : 'bg-slate-900 text-slate-500 border border-slate-800 hover:text-slate-300'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>

            {actions}

            <Tooltip content="复制控制台全部输出">
              <button
                onClick={copyContent}
                className="p-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-slate-700 text-slate-400 hover:text-slate-200 cursor-pointer transition"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </Tooltip>

            {onClear && (
              <Tooltip content="清空控制台日志">
                <button
                  onClick={onClear}
                  className="p-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-rose-500/40 text-slate-400 hover:text-rose-300 cursor-pointer transition"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                </button>
              </Tooltip>
            )}

            <Tooltip content="全屏最大化显示控制台 (按 Esc 还原)">
              <button
                onClick={() => setIsMaximized(true)}
                className="p-1 rounded-lg bg-slate-900 border border-slate-800 hover:border-cyan-500/40 text-slate-400 hover:text-cyan-300 cursor-pointer transition"
              >
                <Maximize2 className="w-3.5 h-3.5" />
              </button>
            </Tooltip>
          </div>
        </div>
      )}

      {/* Main Console Box */}
      {contentElement}

      {/* Draggable Height Resizer Bar */}
      <div
        onMouseDown={startDrag}
        className={`w-full h-2.5 flex items-center justify-center cursor-row-resize rounded-md transition select-none group ${
          isDragging ? 'bg-cyan-500/40' : 'hover:bg-cyan-500/20'
        }`}
        title="按住上下拖拽可自由调节窗口高度"
      >
        <div className="w-12 h-1 rounded-full bg-slate-700 group-hover:bg-cyan-400 transition" />
      </div>
    </div>
  );
};
