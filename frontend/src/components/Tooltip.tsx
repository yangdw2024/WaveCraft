import React, { useState, useRef } from 'react';

export interface TooltipProps {
  content: React.ReactNode;
  title?: string;
  shortcut?: string;
  position?: 'top' | 'bottom' | 'left' | 'right';
  delayMs?: number;
  children: React.ReactNode;
  className?: string;
}

export const Tooltip: React.FC<TooltipProps> = ({
  content,
  title,
  shortcut,
  position = 'top',
  delayMs = 120,
  children,
  className = '',
}) => {
  const [visible, setVisible] = useState(false);
  const timerRef = useRef<number | null>(null);

  const showTooltip = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      setVisible(true);
    }, delayMs);
  };

  const hideTooltip = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setVisible(false);
  };

  const positionClasses = {
    top: 'bottom-full left-1/2 -translate-x-1/2 mb-2',
    bottom: 'top-full left-1/2 -translate-x-1/2 mt-2',
    left: 'right-full top-1/2 -translate-y-1/2 mr-2',
    right: 'left-full top-1/2 -translate-y-1/2 ml-2',
  }[position];

  const arrowClasses = {
    top: 'top-full left-1/2 -translate-x-1/2 border-t-slate-800 border-l-transparent border-r-transparent border-b-transparent',
    bottom: 'bottom-full left-1/2 -translate-x-1/2 border-b-slate-800 border-l-transparent border-r-transparent border-t-transparent',
    left: 'left-full top-1/2 -translate-y-1/2 border-l-slate-800 border-t-transparent border-b-transparent border-r-transparent',
    right: 'right-full top-1/2 -translate-y-1/2 border-r-slate-800 border-t-transparent border-b-transparent border-l-transparent',
  }[position];

  return (
    <div
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {visible && (
        <div
          className={`absolute z-50 pointer-events-none transition-all duration-150 transform scale-100 opacity-100 ${positionClasses}`}
        >
          <div className="bg-slate-900/95 backdrop-blur-md border border-slate-700/80 rounded-xl px-2.5 py-1.5 shadow-2xl shadow-black/60 max-w-xs whitespace-normal text-left">
            {title && (
              <div className="text-[11px] font-bold text-sky-300 flex items-center justify-between gap-2 mb-0.5">
                <span>{title}</span>
                {shortcut && (
                  <span className="px-1 py-0.2 rounded bg-slate-800 text-slate-300 font-mono text-[9px] border border-slate-700">
                    {shortcut}
                  </span>
                )}
              </div>
            )}
            <div className="text-[11px] text-slate-200 leading-tight">
              {content}
            </div>
            {!title && shortcut && (
              <div className="mt-1 flex justify-end">
                <span className="px-1 py-0.2 rounded bg-slate-800 text-slate-400 font-mono text-[9px] border border-slate-700">
                  {shortcut}
                </span>
              </div>
            )}
          </div>
          {/* Arrow */}
          <div
            className={`absolute w-0 h-0 border-4 ${arrowClasses}`}
          />
        </div>
      )}
    </div>
  );
};
