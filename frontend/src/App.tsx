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

export function App() {
  const [activeWorkspace, setActiveWorkspace] = useState<WorkspaceId>('file-hub');
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
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);

  const mainRef = useRef<HTMLElement>(null);
  const runningTasksCount = tasks.filter((t) => t.status === 'running').length;

  useEffect(() => {
    mainRef.current?.scrollTo({ top: 0 });
  }, [activeWorkspace]);

  return (
    <div className="h-screen w-screen flex flex-col bg-[#06090f] text-slate-100 quantum-grid-bg overflow-hidden">
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

      <div className="flex-1 flex min-h-0 overflow-hidden">
        <Sidebar
          active={activeWorkspace}
          onSelect={setActiveWorkspace}
          runningTasksCount={runningTasksCount}
          totalTasksCount={tasks.length}
        />

        <main ref={mainRef} className="flex-1 min-w-0 overflow-y-auto p-5">
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

          {activeWorkspace === 'file-hub' && (
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
          )}

          {activeWorkspace === 'structure-orbital' && (
            <StructureOrbitalWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'realspace' && (
            <RealSpaceWorkspace
              inspection={inspection}
              functions={realspaceFunctions}
            />
          )}

          {activeWorkspace === 'charges' && (
            <ChargeAnalysisWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'bonds' && (
            <BondOrderWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'orbitals' && (
            <OrbitalAnalysisWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'dos' && (
            <DosWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'spectrum' && (
            <SpectrumWorkspace
              inspection={inspection}
              examples={examples}
              onSelectFile={loadFile}
            />
          )}

          {activeWorkspace === 'weak-interaction' && (
            <WeakInteractionWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'advanced' && (
            <AdvancedToolsWorkspace inspection={inspection} />
          )}

          {activeWorkspace === 'menu-explorer' && (
            <FunctionMenuWorkspace
              inspection={inspection}
              categories={categories}
              tasks={tasks}
              selectedTemplate={selectedMenuTemplate}
              onSelectTemplate={setSelectedMenuTemplate}
              onRefreshTasks={refreshTasks}
            />
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
