import React, { useCallback, useEffect, useRef, useState } from 'react';
import { api } from './api/client';
import type {
  ExampleFileInfo,
  HealthInfo,
  MenuCategory,
  MenuFunctionTemplate,
  MoleculeInspection,
  RealspaceFunctionDef,
  TaskRecord,
  WaveCraftConfig,
  WorkspaceId,
} from './types/quantum';
import { TopBar } from './components/TopBar';
import { Sidebar } from './components/Sidebar';
import { PanelLeftOpen } from 'lucide-react';
import { CommandPalette } from './components/CommandPalette';
import { FileHubWorkspace } from './workspaces/FileHubWorkspace';
import { StructureOrbitalWorkspace } from './workspaces/StructureOrbitalWorkspace';
import { RealSpaceWorkspace } from './workspaces/RealSpaceWorkspace';
import {
  BondOrderWorkspace,
  ChargeAnalysisWorkspace,
  OrbitalAnalysisWorkspace,
} from './workspaces/ChargeBondOrbitalsWorkspaces';
import {
  DosWorkspace,
  SpectrumWorkspace,
  WeakInteractionWorkspace,
} from './workspaces/DosSpectrumWeakWorkspaces';
import {
  AdvancedToolsWorkspace,
  FunctionMenuWorkspace,
} from './workspaces/AdvancedAndMenuWorkspaces';
import { AiAgentWorkspace } from './workspaces/AiAgentWorkspace';
import { ExportHubWorkspace } from './workspaces/ExportHubWorkspace';
import { LinuxServerWorkspace } from './workspaces/LinuxServerWorkspace';

export function App() {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>('file-hub');
  const [visitedWorkspaces, setVisitedWorkspaces] = useState<Set<WorkspaceId>>(
    () => new Set<WorkspaceId>(['file-hub', 'weak-interaction'])
  );

  useEffect(() => {
    setVisitedWorkspaces((prev) => {
      if (prev.has(activeWorkspace)) return prev;
      const next = new Set(prev);
      next.add(activeWorkspace);
      return next;
    });
  }, [activeWorkspace]);
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [config, setConfig] = useState<WaveCraftConfig | null>(null);
  const [examples, setExamples] = useState<ExampleFileInfo[]>([]);
  const [categories, setCategories] = useState<MenuCategory[]>([]);
  const [realspaceFunctions, setRealspaceFunctions] = useState<RealspaceFunctionDef[]>([]);
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [inspection, setInspection] = useState<MoleculeInspection | null>(null);
  const [loading, setLoading] = useState(false);
  const [globalError, setGlobalError] = useState<string | null>(null);
  const [paletteOpen, setPaletteOpen] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [selectedMenuTemplate, setSelectedMenuTemplate] =
    useState<MenuFunctionTemplate | null>(null);

  const refreshTasks = useCallback(async () => {
    try {
      const list = await api.listTasks();
      setTasks(list);
    } catch {
      // ignore
    }
  }, []);

  const loadFile = useCallback(
    async (filePath: string) => {
      setLoading(true);
      setGlobalError(null);
      try {
        const res = await api.inspectMolecule(filePath);
        setInspection(res);
        const updatedCfg = await api.getConfig();
        setConfig(updatedCfg);
        await refreshTasks();
      } catch (e: any) {
        setGlobalError(e.message || `加载文件失败: ${filePath}`);
      } finally {
        setLoading(false);
      }
    },
    [refreshTasks]
  );

  const handleUploadFile = useCallback(
    async (file: File) => {
      setLoading(true);
      setGlobalError(null);
      try {
        const uploaded = await api.uploadFile(file);
        await loadFile(uploaded.file_path);
      } catch (e: any) {
        setGlobalError(e.message || '上传失败');
        setLoading(false);
      }
    },
    [loadFile]
  );

  const handleSaveConfig = useCallback(async (newCfg: WaveCraftConfig) => {
    const saved = await api.updateConfig(newCfg);
    setConfig(saved);
    const h = await api.health();
    setHealth(h);
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const [h, cfg, exList, catalog, taskList] = await Promise.all([
          api.health(),
          api.getConfig(),
          api.listExamples(),
          api.getMenuCatalog(),
          api.listTasks(),
        ]);
        setHealth(h);
        setConfig(cfg);
        setExamples(exList);
        setCategories(catalog.categories);
        setRealspaceFunctions(catalog.realspace_functions);
        setTasks(taskList);

        // Auto-load CH3Cl.fchk or first example for instant out-of-box 3D experience
        const defaultEx =
          exList.find((e) => e.name.toLowerCase() === 'ch3cl.fchk') ||
          exList.find((e) => e.name.toLowerCase() === 'benzene.fch') ||
          exList[0];
        if (defaultEx) {
          await loadFile(defaultEx.path);
        }
      } catch (e: any) {
        setGlobalError(
          e.message || '无法连接 WaveCraft Rust 核心后端，请确认服务已启动'
        );
      }
    })();
  }, [loadFile]);

  // Ctrl+K shortcut
  useEffect(() => {
    const onKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        setPaletteOpen((v) => !v);
      }
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'b') {
        e.preventDefault();
        setSidebarCollapsed((v) => !v);
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const mainRef = useRef<HTMLElement>(null);
  const runningTasksCount = tasks.filter((t) => t.status === 'running').length;

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0 });
    // Notify 3D viewports to adapt and center squarely when tab switches
    window.dispatchEvent(new CustomEvent('wavecraft-workspace-switch'));
  }, [activeWorkspace]);

  return (
    <div className="h-screen w-screen flex flex-col bg-[#06090f] text-slate-100 quantum-grid-bg overflow-hidden relative">
      <TopBar
        health={health}
        inspection={inspection}
        examples={examples}
        loading={loading}
        onSelectFile={loadFile}
        onUploadFile={handleUploadFile}
        onOpenPalette={() => setPaletteOpen(true)}
        onJumpToFileHub={() => setActiveWorkspace('file-hub')}
      />

      <div className="flex-1 flex min-h-0 overflow-hidden relative">
        <Sidebar
          active={activeWorkspace}
          onSelect={setActiveWorkspace}
          runningTasksCount={runningTasksCount}
          totalTasksCount={tasks.length}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed((v) => !v)}
        />

        {sidebarCollapsed && (
          <button
            onClick={() => setSidebarCollapsed(false)}
            className="absolute left-3 top-3 z-30 px-3 py-1.5 rounded-xl bg-slate-900/90 border border-sky-400/50 text-sky-200 shadow-2xl backdrop-blur-md flex items-center gap-1.5 text-xs font-semibold hover:bg-slate-800 transition cursor-pointer hover:border-sky-300 animate-in fade-in slide-in-from-left duration-200"
            title="展开侧边导航 (Ctrl+B)"
          >
            <PanelLeftOpen className="w-4 h-4 text-sky-400" />
            <span className="text-[11px]">展开导航</span>
          </button>
        )}

        <main ref={mainRef} className="flex-1 min-w-0 overflow-y-auto p-5 transition-all">
          {globalError && (
            <div className="mb-4 px-4 py-3 rounded-xl bg-rose-500/10 border border-rose-500/35 text-xs text-rose-200 flex items-center justify-between">
              <span>{globalError}</span>
              <button
                onClick={() => setGlobalError(null)}
                className="text-rose-300 hover:text-white underline cursor-pointer"
              >
                关闭
              </button>
            </div>
          )}

          {visitedWorkspaces.has('file-hub') && (
            <div style={{ display: activeWorkspace === 'file-hub' ? 'block' : 'none' }}>
              <FileHubWorkspace
                health={health}
                config={config}
                examples={examples}
                inspection={inspection}
                loading={loading}
                onSelectFile={loadFile}
                onUploadFile={handleUploadFile}
                onSaveConfig={handleSaveConfig}
              />
            </div>
          )}

          {visitedWorkspaces.has('structure-orbital') && (
            <div style={{ display: activeWorkspace === 'structure-orbital' ? 'block' : 'none' }}>
              <StructureOrbitalWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('realspace') && (
            <div style={{ display: activeWorkspace === 'realspace' ? 'block' : 'none' }}>
              <RealSpaceWorkspace
                inspection={inspection}
                functions={realspaceFunctions}
              />
            </div>
          )}

          {visitedWorkspaces.has('charges') && (
            <div style={{ display: activeWorkspace === 'charges' ? 'block' : 'none' }}>
              <ChargeAnalysisWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('bonds') && (
            <div style={{ display: activeWorkspace === 'bonds' ? 'block' : 'none' }}>
              <BondOrderWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('orbitals') && (
            <div style={{ display: activeWorkspace === 'orbitals' ? 'block' : 'none' }}>
              <OrbitalAnalysisWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('dos') && (
            <div style={{ display: activeWorkspace === 'dos' ? 'block' : 'none' }}>
              <DosWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('spectrum') && (
            <div style={{ display: activeWorkspace === 'spectrum' ? 'block' : 'none' }}>
              <SpectrumWorkspace
                inspection={inspection}
                examples={examples}
                onSelectFile={loadFile}
              />
            </div>
          )}

          {visitedWorkspaces.has('weak-interaction') && (
            <div style={{ display: activeWorkspace === 'weak-interaction' ? 'block' : 'none' }}>
              <WeakInteractionWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('ai-agent') && (
            <div style={{ display: activeWorkspace === 'ai-agent' ? 'block' : 'none' }}>
              <AiAgentWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('export-hub') && (
            <div style={{ display: activeWorkspace === 'export-hub' ? 'block' : 'none' }}>
              <ExportHubWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('linux-server') && (
            <div style={{ display: activeWorkspace === 'linux-server' ? 'block' : 'none' }}>
              <LinuxServerWorkspace
                inspection={inspection}
                onSelectFile={loadFile}
              />
            </div>
          )}

          {visitedWorkspaces.has('advanced') && (
            <div style={{ display: activeWorkspace === 'advanced' ? 'block' : 'none' }}>
              <AdvancedToolsWorkspace inspection={inspection} />
            </div>
          )}

          {visitedWorkspaces.has('menu-explorer') && (
            <div style={{ display: activeWorkspace === 'menu-explorer' ? 'block' : 'none' }}>
              <FunctionMenuWorkspace
                inspection={inspection}
                categories={categories}
                tasks={tasks}
                selectedTemplate={selectedMenuTemplate}
                onSelectTemplate={setSelectedMenuTemplate}
                onRefreshTasks={refreshTasks}
              />
            </div>
          )}
        </main>
      </div>

      <CommandPalette
        open={paletteOpen}
        categories={categories}
        onClose={() => setPaletteOpen(false)}
        onJumpWorkspace={(ws) => setActiveWorkspace(ws)}
        onSelectMenuFunction={(_cat, item) => {
          setSelectedMenuTemplate(item);
          setActiveWorkspace('menu-explorer');
        }}
      />
    </div>
  );
}

export default App;
