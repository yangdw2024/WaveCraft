import React, { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';

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
  delayMs = 100,
  children,
  className = '',
}) => {
  const [visible, setVisible] = useState(false);
  const [coords, setCoords] = useState<{
    top: number;
    left: number;
    placement: 'top' | 'bottom';
  } | null>(null);

  const triggerRef = useRef<HTMLDivElement>(null);
  const timerRef = useRef<number | null>(null);

  const updatePosition = () => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    
    // Automatically flip to bottom if too close to top of viewport
    const preferBottom = position === 'bottom' || rect.top < 85;
    const top = preferBottom ? rect.bottom + 8 : rect.top - 8;

    // Horizontally center over trigger, clamping to viewport margins (8px - window width)
    let left = rect.left + rect.width / 2;
    left = Math.max(140, Math.min(window.innerWidth - 140, left));

    setCoords({
      top,
      left,
      placement: preferBottom ? 'bottom' : 'top',
    });
  };

  const showTooltip = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    timerRef.current = window.setTimeout(() => {
      updatePosition();
      setVisible(true);
    }, delayMs);
  };

  const hideTooltip = () => {
    if (timerRef.current) clearTimeout(timerRef.current);
    setVisible(false);
  };

  useEffect(() => {
    if (visible) {
      const handleScrollOrResize = () => updatePosition();
      window.addEventListener('scroll', handleScrollOrResize, true);
      window.addEventListener('resize', handleScrollOrResize);
      return () => {
        window.removeEventListener('scroll', handleScrollOrResize, true);
        window.removeEventListener('resize', handleScrollOrResize);
      };
    }
  }, [visible]);

  return (
    <div
      ref={triggerRef}
      className={`relative inline-flex items-center ${className}`}
      onMouseEnter={showTooltip}
      onMouseLeave={hideTooltip}
      onFocus={showTooltip}
      onBlur={hideTooltip}
    >
      {children}
      {visible &&
        coords &&
        createPortal(
          <div
            style={{
              position: 'fixed',
              top: coords.top,
              left: coords.left,
              transform: coords.placement === 'top' ? 'translate(-50%, -100%)' : 'translate(-50%, 0)',
              zIndex: 99999,
            }}
            className="pointer-events-none transition-opacity duration-150 animate-in fade-in zoom-in-95 duration-100 w-max max-w-sm"
          >
            <div className="bg-slate-900/98 backdrop-blur-xl border border-sky-500/40 rounded-xl px-3 py-2 shadow-[0_12px_40px_rgba(0,0,0,0.85)] text-left text-xs">
              {title && (
                <div className="text-[11px] font-bold text-sky-300 flex items-center justify-between gap-3 mb-1 border-b border-slate-800/80 pb-0.5">
                  <span className="whitespace-nowrap">{title}</span>
                  {shortcut && (
                    <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-300 font-mono text-[9px] border border-slate-700 whitespace-nowrap">
                      {shortcut}
                    </span>
                  )}
                </div>
              )}
              <div className="text-[11px] text-slate-200 leading-normal">
                {content}
              </div>
              {!title && shortcut && (
                <div className="mt-1 flex justify-end">
                  <span className="px-1.5 py-0.2 rounded bg-slate-800 text-slate-400 font-mono text-[9px] border border-slate-700 whitespace-nowrap">
                    {shortcut}
                  </span>
                </div>
              )}
            </div>
            {/* Small Pointer Triangle */}
            <div
              style={{
                left: '50%',
                transform: 'translateX(-50%)',
              }}
              className={`absolute w-0 h-0 border-4 ${
                coords.placement === 'top'
                  ? 'top-full border-t-sky-500/40 border-l-transparent border-r-transparent border-b-transparent'
                  : 'bottom-full border-b-sky-500/40 border-l-transparent border-r-transparent border-t-transparent'
              }`}
            />
          </div>,
          document.body
        )}
    </div>
  );
};
