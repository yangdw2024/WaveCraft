import type {
  AromaticityResult,
  BondOrderEntry,
  CdftAtomEntry,
  ChargeEntry,
  CriticalPoint,
  DosCurve,
  DualIsosurfaceResult,
  EspSurfaceResult,
  ExampleFileInfo,
  FuzzyResult,
  HealthInfo,
  LinePoint,
  MenuCategory,
  MoleculeInspection,
  MultipoleResult,
  NciPoint,
  OrbitalCompositionEntry,
  OrbitalInfo,
  PlanarityResult,
  RealspaceFunctionDef,
  Slice2DData,
  SpectrumCurve,
  TaskRecord,
  WaveCraftConfig,
  ZmyBatchRow,
} from '../types/quantum';

const BASE = '/api';

async function reqJson<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${url}`, {
    headers: { 'Content-Type': 'application/json', ...(init?.headers || {}) },
    ...init,
  });
  const text = await res.text();
  let data: any;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(text || `HTTP ${res.status}`);
  }
  if (!res.ok) {
    throw new Error(data?.error || `请求失败 (${res.status})`);
  }
  return data as T;
}

export const api = {
  health: () => reqJson<HealthInfo>('/health'),
  getConfig: () => reqJson<WaveCraftConfig>('/config'),
  updateConfig: (cfg: WaveCraftConfig) =>
    reqJson<WaveCraftConfig>('/config', { method: 'POST', body: JSON.stringify(cfg) }),
  listExamples: () => reqJson<ExampleFileInfo[]>('/examples'),
  getMenuCatalog: () =>
    reqJson<{ categories: MenuCategory[]; realspace_functions: RealspaceFunctionDef[] }>(
      '/menu-catalog'
    ),
  listTasks: () => reqJson<TaskRecord[]>('/tasks'),
  clearTasks: () => reqJson<{ cleared: boolean }>('/tasks', { method: 'DELETE' }),

  uploadFile: async (file: File): Promise<{ file_path: string; file_name: string; size_bytes: number }> => {
    const form = new FormData();
    form.append('file', file);
    const res = await fetch(`${BASE}/upload`, { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) throw new Error(data?.error || '文件上传失败');
    return data;
  },

  inspectMolecule: (file_path: string) =>
    reqJson<MoleculeInspection>('/inspect', {
      method: 'POST',
      body: JSON.stringify({ file_path }),
    }),

  calculateCharges: (file_path: string, method: string) =>
    reqJson<{
      task_id: string;
      method: string;
      charges: ChargeEntry[];
      duration_ms: number;
      stdout: string;
    }>('/charges', {
      method: 'POST',
      body: JSON.stringify({ file_path, method }),
    }),

  compareCharges: (file_path: string, methods: string[]) =>
    reqJson<{
      series: { method: string; charges: ChargeEntry[]; duration_ms: number }[];
    }>('/charges/compare', {
      method: 'POST',
      body: JSON.stringify({ file_path, methods }),
    }),

  calculateBondOrders: (file_path: string, method: string) =>
    reqJson<{
      task_id: string;
      method: string;
      bond_orders: BondOrderEntry[];
      duration_ms: number;
      stdout: string;
    }>('/bonds', {
      method: 'POST',
      body: JSON.stringify({ file_path, method }),
    }),

  calculateOrbitalComposition: (file_path: string, orbital_index: number, method: string) =>
    reqJson<{
      task_id: string;
      orbital_index: number;
      method: string;
      compositions: OrbitalCompositionEntry[];
      duration_ms: number;
      stdout: string;
    }>('/orbital/composition', {
      method: 'POST',
      body: JSON.stringify({ file_path, orbital_index, method }),
    }),

  computeOrbitalCube: (
    file_path: string,
    orbital_index: number,
    grid_quality: string,
    isovalue: number
  ) =>
    reqJson<{
      task_id: string;
      cube_id: string;
      cube_path: string;
      duration_ms: number;
      slice_2d: Slice2DData;
      isosurface: DualIsosurfaceResult;
      stdout: string;
    }>('/orbital/cube', {
      method: 'POST',
      body: JSON.stringify({ file_path, orbital_index, grid_quality, isovalue }),
    }),

  computeRealspace: (params: {
    file_path: string;
    func_id: string;
    grid_quality: string;
    isovalue: number;
    plane: string;
  }) =>
    reqJson<{
      task_id: string;
      cube_id: string;
      cube_path: string;
      duration_ms: number;
      slice_2d: Slice2DData;
      isosurface: DualIsosurfaceResult;
      stdout: string;
    }>('/realspace', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  getCubeSlice: (cube_id: string, plane: string, index?: number) => {
    const q = new URLSearchParams({ plane });
    if (index !== undefined) q.set('index', String(index));
    return reqJson<Slice2DData>(`/cube/${cube_id}/slice?${q.toString()}`);
  },

  getCubeIsosurface: (cube_id: string, isovalue: number) =>
    reqJson<DualIsosurfaceResult>(`/cube/${cube_id}/isosurface?isovalue=${isovalue}`),

  calculateDos: (params: {
    file_path: string;
    fwhm_ev: number;
    broadening: string;
    num_points?: number;
  }) =>
    reqJson<{
      curve: DosCurve;
      orbitals: OrbitalInfo[];
      duration_ms: number;
      stdout: string;
    }>('/dos', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  calculateSpectrum: (params: {
    file_path: string;
    spec_type: string;
    fwhm: number;
    broadening: string;
  }) =>
    reqJson<{
      curve: SpectrumCurve;
      thermochemistry: Record<string, any>;
      peak_count: number;
    }>('/spectrum', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  calculateWeakInteraction: (params: {
    file_path: string;
    method: string;
    grid_quality: string;
    output_mode: 'scatter' | 'cube' | 'both';
    fragment_atoms?: string;
    isovalue?: number;
  }) =>
    reqJson<{
      task_id: string;
      method: string;
      mode: string;
      scatter_points: NciPoint[];
      cube_id?: string | null;
      color_cube_id?: string | null;
      slice_2d?: Slice2DData | null;
      isosurface?: DualIsosurfaceResult | null;
      duration_ms: number;
      stdout: string;
    }>('/weak-interaction', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  calculateAim: (file_path: string) =>
    reqJson<{
      task_id: string;
      critical_points: CriticalPoint[];
      duration_ms: number;
      stdout: string;
    }>('/aim', {
      method: 'POST',
      body: JSON.stringify({ file_path }),
    }),

  calculateAromaticity: (file_path: string, method: string) =>
    reqJson<{
      task_id: string;
      method: string;
      aromaticity: AromaticityResult;
      duration_ms: number;
      stdout: string;
    }>('/aromaticity', {
      method: 'POST',
      body: JSON.stringify({ file_path, method }),
    }),

  calculateLine: (params: {
    file_path: string;
    func_id: string;
    atom1: number;
    atom2: number;
  }) =>
    reqJson<{
      task_id: string;
      func_id: string;
      atom1: number;
      atom2: number;
      points: LinePoint[];
      duration_ms: number;
      stdout: string;
    }>('/line', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  calculateFuzzy: (file_path: string, method = 'li_di') =>
    reqJson<{
      task_id: string;
      analysis: string;
      fuzzy: FuzzyResult;
      duration_ms: number;
      stdout: string;
    }>('/fuzzy', {
      method: 'POST',
      body: JSON.stringify({ file_path, method }),
    }),

  calculateCdft: (file_path: string, method = 'ow_fukui') =>
    reqJson<{
      task_id: string;
      mode: string;
      entries: CdftAtomEntry[];
      duration_ms: number;
      stdout: string;
    }>('/cdft', {
      method: 'POST',
      body: JSON.stringify({ file_path, method }),
    }),

  calculateMultipole: (file_path: string) =>
    reqJson<{
      task_id: string;
      multipole: MultipoleResult;
      duration_ms: number;
      stdout: string;
    }>('/multipole', {
      method: 'POST',
      body: JSON.stringify({ file_path }),
    }),

  calculatePlanarity: (file_path: string, heavy_only = true) =>
    reqJson<{
      task_id: string;
      heavy_only: boolean;
      planarity: PlanarityResult;
      duration_ms: number;
      stdout: string;
    }>('/planarity', {
      method: 'POST',
      body: JSON.stringify({ file_path, heavy_only }),
    }),

  calculateEspSurface: (file_path: string, grid_spacing = 0.25) =>
    reqJson<{
      task_id: string;
      grid_spacing: number;
      esp: EspSurfaceResult;
      duration_ms: number;
      stdout: string;
    }>('/esp-surface', {
      method: 'POST',
      body: JSON.stringify({ file_path, grid_spacing }),
    }),

  runZmyBatchWorkflow: (params: {
    file_paths: string[];
    include_mpp?: boolean;
    include_esp?: boolean;
    esp_grid_spacing?: number;
  }) =>
    reqJson<{
      count: number;
      rows: ZmyBatchRow[];
    }>('/workflow/zmy-batch', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  exportStructure: (file_path: string, format: string) =>
    reqJson<{
      task_id: string;
      filename: string;
      exported_path: string;
      size_bytes: number;
      preview: string;
      duration_ms: number;
    }>('/export', {
      method: 'POST',
      body: JSON.stringify({ file_path, format }),
    }),

  executeRaw: (file_path: string, commands: string[], task_name?: string) =>
    reqJson<{
      task_id: string;
      duration_ms: number;
      stdout: string;
      stderr: string;
      generated_files: string[];
      cube_id?: string | null;
      charges: ChargeEntry[];
      bond_orders: BondOrderEntry[];
      slice_2d?: Slice2DData | null;
      isosurface?: DualIsosurfaceResult | null;
    }>('/execute-raw', {
      method: 'POST',
      body: JSON.stringify({ file_path, commands, task_name }),
    }),

  exportSave: (params: {
    file_path: string;
    target_dir?: string;
    task_id?: string;
    points?: NciPoint[];
    mesh?: any;
    report_markdown?: string;
    export_csv?: boolean;
    export_obj?: boolean;
    export_cubes?: boolean;
    export_report?: boolean;
    export_log?: boolean;
    log_content?: string;
  }) =>
    reqJson<{
      ok: boolean;
      target_dir: string;
      files_written: string[];
      count: number;
      message: string;
    }>('/export-save', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  searchSobko: (query: string, top_k?: number) =>
    reqJson<{
      query: string;
      count: number;
      results: Array<{
        chunk_id: string;
        title: string;
        text: string;
        canonical_url?: string;
      }>;
    }>('/sobko/search', {
      method: 'POST',
      body: JSON.stringify({ query, top_k }),
    }),

  agentChat: (params: {
    prompt: string;
    file_path?: string;
    api_url?: string;
    api_key?: string;
    model?: string;
  }) =>
    reqJson<{
      answer: string;
      report_markdown: string;
      steps: Array<{
        type: string;
        title: string;
        detail: string;
      }>;
      model_used: string;
    }>('/agent/chat', {
      method: 'POST',
      body: JSON.stringify(params),
    }),

  downloadUrl: (path: string) => `${BASE}/download?path=${encodeURIComponent(path)}`,
};
