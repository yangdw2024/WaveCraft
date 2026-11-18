import React from 'react';
import {
  Activity,
  Atom,
  Bot,
  Box,
  Compass,
  DownloadCloud,
  FolderKanban,
  GitMerge,
  Layers,
  Link2,
  Sparkles,
  Server,
  Terminal,
  Waves,
  Zap,
} from 'lucide-react';
import type { WorkspaceId } from '../types/quantum';

interface NavItem {
  id: WorkspaceId;
  label: string;
  sublabel: string;
  icon: React.FC<{ className?: string }>;
  badge?: string;
}

export const NAV_ITEMS: NavItem[] = [
  { id: 'file-hub', label: '波函数中心', sublabel: '文件库 · 引擎配置', icon: FolderKanban },
  { id: 'structure-orbital', label: '3D 结构与轨道', sublabel: '几何测量 · MO 等值面', icon: Atom },
  { id: 'realspace', label: '实空间分析', sublabel: '2D 热图 · 3D 体渲染', icon: Box, badge: '14' },
  { id: 'charges', label: '原子电荷', sublabel: '16 种布居与对比', icon: Zap, badge: '16' },
  { id: 'bonds', label: '键级分析', sublabel: 'Mayer · Wiberg · Fuzzy', icon: Link2 },
  { id: 'orbitals', label: '轨道成分', sublabel: '能级阶梯 · 原子贡献', icon: Layers },
  { id: 'dos', label: 'DOS 态密度', sublabel: 'TDOS · HOMO/LUMO', icon: Activity },
  { id: 'spectrum', label: '光谱分析', sublabel: 'IR · Raman · UV-Vis', icon: Waves },
  { id: 'weak-interaction', label: '弱相互作用', sublabel: 'NCI · IGM · DORI', icon: Sparkles },
  { id: 'ai-agent', label: 'AI 量子智能体', sublabel: '文献复刻 · 自动报告', icon: Bot, badge: 'AI' },
  { id: 'linux-server', label: 'Linux 智算中心', sublabel: '远程超算 · SSH · 文件同步', icon: Server, badge: 'SSH' },
  { id: 'export-hub', label: '导出与归档', sublabel: '同目录导出 · OBJ · 报告', icon: DownloadCloud },
  { id: 'advanced', label: '高级量子工具', sublabel: 'AIM · 芳香性 · 格式导出', icon: GitMerge },
  { id: 'menu-explorer', label: '全功能菜单', sublabel: 'Multiwfn 指令控制台', icon: Terminal },
];

interface SidebarProps {
  active: WorkspaceId;
  onSelect: (id: WorkspaceId) => void;
  runningTasksCount: number;
  totalTasksCount: number;
}

export const Sidebar: React.FC<SidebarProps> = ({
  active,
  onSelect,
  runningTasksCount,
  totalTasksCount,
}) => {
  return (
    <aside className="w-60 shrink-0 border-r border-slate-800/80 bg-[#080c14]/90 flex flex-col justify-between py-3 px-2.5 overflow-y-auto">
      <div className="space-y-1">
        <div className="px-2.5 pb-1.5 flex items-center justify-between text-[11px] font-semibold uppercase tracking-wider text-slate-500">
          <span>分析工作台</span>
          <Compass className="w-3.5 h-3.5 text-slate-600" />
        </div>
        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = active === item.id;
          return (
            <button
              key={item.id}
              onClick={() => onSelect(item.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-left transition cursor-pointer group ${
                isActive
                  ? 'bg-gradient-to-r from-sky-500/20 to-cyan-500/10 border border-sky-400/35 text-slate-100 shadow-[0_0_20px_rgba(14,165,233,0.12)]'
                  : 'border border-transparent text-slate-400 hover:bg-slate-800/50 hover:text-slate-200'
              }`}
            >
              <div
                className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 transition ${
                  isActive
                    ? 'bg-sky-500/20 text-sky-300'
                    : 'bg-slate-900/90 text-slate-500 group-hover:text-sky-400'
                }`}
              >
                <Icon className="w-4 h-4" />
              </div>
              <div className="min-w-0 flex-1">
                <div className="flex items-center justify-between gap-1">
                  <span className="text-xs font-semibold truncate">{item.label}</span>
                  {item.badge && (
                    <span
                      className={`text-[10px] px-1.5 py-0.2 rounded-full font-mono ${
                        isActive
                          ? 'bg-sky-400/20 text-sky-200'
                          : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {item.badge}
                    </span>
                  )}
                </div>
                <div className="text-[10.5px] text-slate-500 truncate mt-0.5">
                  {item.sublabel}
                </div>
              </div>
            </button>
          );
        })}
      </div>

      {/* Bottom Task Telemetry */}
      <div className="mt-4 pt-3 border-t border-slate-800/80 px-2">
        <div
          onClick={() => onSelect('menu-explorer')}
          className="cursor-pointer rounded-xl bg-slate-900/80 border border-slate-800/90 p-2.5 hover:border-sky-500/30 transition"
        >
          <div className="flex items-center justify-between text-xs">
            <span className="text-slate-400 font-medium">计算任务队列</span>
            <span
              className={`px-1.5 py-0.5 rounded text-[10px] font-mono ${
                runningTasksCount > 0
                  ? 'bg-sky-500/20 text-sky-300 animate-pulse'
                  : 'bg-slate-800 text-slate-400'
              }`}
            >
              {runningTasksCount > 0 ? `${runningTasksCount} 运行中` : `${totalTasksCount} 已记录`}
            </span>
          </div>
          <div className="text-[10.5px] text-slate-500 mt-1">
            Rust Tokio 异步进程池 · GBK 自动转码
          </div>
        </div>
      </div>
    </aside>
  );
};
