import React, { useMemo, useState, useEffect } from 'react';
import { ArrowRight, Search, Terminal, X } from 'lucide-react';
import type { MenuCategory, MenuFunctionTemplate, WorkspaceId } from '../types/quantum';
import { NAV_ITEMS } from './Sidebar';

interface CommandPaletteProps {
  open: boolean;
  categories: MenuCategory[];
  onClose: () => void;
  onJumpWorkspace: (ws: WorkspaceId) => void;
  onSelectMenuFunction: (cat: MenuCategory, item: MenuFunctionTemplate) => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({
  open,
  categories,
  onClose,
  onJumpWorkspace,
  onSelectMenuFunction,
}) => {
  const [query, setQuery] = useState('');

  useEffect(() => {
    if (open) setQuery('');
  }, [open]);

  const flatFunctions = useMemo(() => {
    const items: { cat: MenuCategory; fn: MenuFunctionTemplate }[] = [];
    for (const c of categories) {
      for (const f of c.items) {
        items.push({ cat: c, fn: f });
      }
    }
    return items;
  }, [categories]);

  const matchedWorkspaces = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return NAV_ITEMS.slice(0, 6);
    return NAV_ITEMS.filter(
      (n) => n.label.toLowerCase().includes(q) || n.sublabel.toLowerCase().includes(q)
    );
  }, [query]);

  const matchedFunctions = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return flatFunctions.slice(0, 12);
    return flatFunctions
      .filter(
        ({ cat, fn }) =>
          fn.name.toLowerCase().includes(q) ||
          fn.description.toLowerCase().includes(q) ||
          fn.id.toLowerCase().includes(q) ||
          cat.name.toLowerCase().includes(q)
      )
      .slice(0, 18);
  }, [query, flatFunctions]);

  if (!open) return null;

  return (
    <div
      className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-start justify-center pt-20 px-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-2xl rounded-2xl glass-panel border border-sky-500/30 shadow-2xl overflow-hidden"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center gap-3 px-4 py-3.5 border-b border-slate-800">
          <Search className="w-4 h-4 text-sky-400" />
          <input
            autoFocus
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="搜索功能模块或 Multiwfn 菜单指令 (例如: Hirshfeld, ELF, 键级, AIM, NICS, DOS)..."
            className="flex-1 bg-transparent text-sm text-slate-100 placeholder-slate-500 focus:outline-none"
          />
          <button
            onClick={onClose}
            className="p-1 rounded-lg hover:bg-slate-800 text-slate-400 cursor-pointer"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="max-h-[440px] overflow-y-auto p-3 space-y-4">
          {matchedWorkspaces.length > 0 && (
            <div>
              <div className="px-2 pb-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                快速切换工作台
              </div>
              <div className="grid grid-cols-2 gap-1.5">
                {matchedWorkspaces.map((w) => {
                  const Icon = w.icon;
                  return (
                    <button
                      key={w.id}
                      onClick={() => {
                        onJumpWorkspace(w.id);
                        onClose();
                      }}
                      className="flex items-center gap-2.5 px-3 py-2 rounded-xl bg-slate-900/70 hover:bg-sky-500/15 border border-slate-800 hover:border-sky-400/40 text-left transition cursor-pointer"
                    >
                      <Icon className="w-4 h-4 text-sky-400 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-slate-200 truncate">
                          {w.label}
                        </div>
                        <div className="text-[10px] text-slate-500 truncate">
                          {w.sublabel}
                        </div>
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          )}

          {matchedFunctions.length > 0 && (
            <div>
              <div className="px-2 pb-1.5 text-[11px] font-semibold text-slate-500 uppercase tracking-wider">
                Multiwfn 3.8 命令菜单 ({matchedFunctions.length})
              </div>
              <div className="space-y-1">
                {matchedFunctions.map(({ cat, fn }) => (
                  <button
                    key={fn.id}
                    onClick={() => {
                      onSelectMenuFunction(cat, fn);
                      onClose();
                    }}
                    className="w-full flex items-center justify-between gap-3 px-3 py-2 rounded-xl hover:bg-slate-800/80 border border-transparent hover:border-slate-700 text-left transition cursor-pointer"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <Terminal className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                      <div className="min-w-0">
                        <div className="text-xs font-medium text-slate-200 truncate">
                          <span className="text-sky-400 font-mono mr-1.5">[{fn.id}]</span>
                          {fn.name}
                        </div>
                        <div className="text-[11px] text-slate-500 truncate">
                          {cat.name} · {fn.description}
                        </div>
                      </div>
                    </div>
                    <ArrowRight className="w-3.5 h-3.5 text-slate-500 shrink-0" />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
