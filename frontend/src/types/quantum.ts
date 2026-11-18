export type WorkspaceId =
  | 'file-hub'
  | 'structure-orbital'
  | 'realspace'
  | 'charges'
  | 'bonds'
  | 'orbitals'
  | 'dos'
  | 'spectrum'
  | 'weak-interaction'
  | 'advanced'
  | 'menu-explorer';

export interface HealthInfo {
  status: string;
  version: string;
  engine: string;
  multiwfn_found: boolean;
  multiwfn_path: string | null;
  examples_dir: string | null;
  threads: number;
}

export interface WaveCraftConfig {
  multiwfn_path: string | null;
  examples_dir: string | null;
  default_threads: number;
  work_dir_root: string;
  recent_files: string[];
  theme: string;
  language: string;
}

export interface ExampleFileInfo {
  name: string;
  path: string;
  relative_path: string;
  category: string;
  extension: string;
  size_bytes: number;
}

export interface Atom3D {
  index: number;
  symbol: string;
  atomic_number: number;
  x: number;
  y: number;
  z: number;
  color: string;
  covalent_radius: number;
  vdw_radius: number;
  charge?: number | null;
}

export interface BondLink {
  atom1: number;
  atom2: number;
  symbol1: string;
  symbol2: string;
  length: number;
  order: number;
}

export interface WavefunctionSummary {
  formula?: string | null;
  total_energy_hartree?: number | null;
  virial_ratio?: number | null;
  num_electrons?: number | null;
  alpha_electrons?: number | null;
  beta_electrons?: number | null;
  num_basis_functions?: number | null;
  num_gtfs?: number | null;
  num_atoms?: number | null;
  net_charge?: number | null;
  multiplicity?: number | null;
  dipole_moment?: number | null;
  molecular_weight?: number | null;
  point_group?: string | null;
  wavefunction_type?: string | null;
  occ_start?: number | null;
  occ_end?: number | null;
  homo_index?: number | null;
  lumo_index?: number | null;
  homo_energy_ev?: number | null;
  lumo_energy_ev?: number | null;
  homo_lumo_gap_ev?: number | null;
  title?: string | null;
}

export interface OrbitalInfo {
  index: number;
  energy_hartree: number;
  energy_ev: number;
  occupancy: number;
  spin_type: string;
  label?: string | null;
}

export interface MoleculeInspection {
  file_path: string;
  file_name: string;
  extension: string;
  file_size: number;
  atoms: Atom3D[];
  bonds: BondLink[];
  summary: WavefunctionSummary;
  orbitals: OrbitalInfo[];
  raw_output: string;
}

export interface ChargeEntry {
  index: number;
  element: string;
  charge: number;
}

export interface BondOrderEntry {
  atom1_index: number;
  atom2_index: number;
  atom1: string;
  atom2: string;
  bond_order: number;
}

export interface OrbitalCompositionEntry {
  atom_index: number;
  element: string;
  percentage: number;
}

export interface CubeMetadata {
  title: string;
  comment: string;
  dimensions: [number, number, number];
  origin_angstrom: [number, number, number];
  bounds_angstrom: [[number, number], [number, number], [number, number]];
  min_value: number;
  max_value: number;
  atom_count: number;
  voxel_count: number;
}

export interface ProjectedAtom2D {
  index: number;
  symbol: string;
  u: number;
  v: number;
  dist_to_plane: number;
}

export interface Slice2DData {
  plane: string;
  slice_index: number;
  max_index: number;
  slice_coord_angstrom: number;
  width: number;
  height: number;
  extent: [number, number, number, number];
  u_label: string;
  v_label: string;
  values: number[];
  slice_min: number;
  slice_max: number;
  global_min: number;
  global_max: number;
  projected_atoms: ProjectedAtom2D[];
}

export interface IsosurfaceMesh {
  positions: number[];
  normals: number[];
  colors?: number[];
  indices: number[];
  vertex_count: number;
  triangle_count: number;
}

export interface DualIsosurfaceResult {
  isovalue: number;
  has_negative: boolean;
  positive: IsosurfaceMesh;
  negative?: IsosurfaceMesh | null;
  metadata: CubeMetadata;
  color_scale?: string;
  color_range?: [number, number];
}

export interface DosPoint {
  energy_ev: number;
  tdos: number;
  occupied_dos: number;
  virtual_dos: number;
}

export interface DosCurve {
  points: DosPoint[];
  homo_energy_ev?: number | null;
  lumo_energy_ev?: number | null;
  gap_ev?: number | null;
  fwhm_ev: number;
  broadening: string;
}

export interface SpectrumPeak {
  index: number;
  x_value: number;
  energy_ev?: number | null;
  wavelength_nm?: number | null;
  intensity: number;
  label: string;
}

export interface SpectrumCurve {
  x_values: number[];
  y_values: number[];
  peaks: SpectrumPeak[];
  x_label: string;
  y_label: string;
  spectrum_type: string;
}

export interface CriticalPoint {
  index: number;
  cp_type_code: number;
  cp_type_label: string;
  x: number;
  y: number;
  z: number;
  rho?: number | null;
  laplacian?: number | null;
  elf?: number | null;
}

export interface NciPoint {
  x: number;
  y: number;
  z: number;
  sign_lambda2_rho: number;
  rdg: number;
  dg_intra?: number | null;
  dg_total?: number | null;
}

export interface AromaticityResult {
  nics_values: number[];
  flu?: number | null;
  homa?: number | null;
  bird?: number | null;
  mci?: number | null;
  pdi?: number | null;
  shannon_index?: number | null;
}

export interface RealspaceFunctionDef {
  id: string;
  menu_num: number;
  name: string;
  formula: string;
  description: string;
  signed: boolean;
}

export interface MenuParam {
  key: string;
  name: string;
  param_type: 'int' | 'float' | 'select' | 'text';
  default_value: string;
  options: string[];
  description: string;
}

export interface MenuFunctionTemplate {
  id: string;
  main_id: string;
  sub_id: string;
  name: string;
  description: string;
  result_type: string;
  params: MenuParam[];
  command_template: string[];
}

export interface MenuCategory {
  id: string;
  name: string;
  description: string;
  icon: string;
  items: MenuFunctionTemplate[];
}

export interface TaskRecord {
  id: string;
  name: string;
  input_file: string;
  commands: string[];
  status: 'running' | 'completed' | 'failed';
  started_at: string;
  completed_at?: string | null;
  duration_ms?: number | null;
  error?: string | null;
  generated_files: string[];
}

export interface LinePoint {
  x_angstrom: number;
  y_angstrom: number;
  z_angstrom: number;
  dist_angstrom: number;
  value: number;
}

export interface FuzzyLiEntry {
  index: number;
  element: string;
  localization_index: number;
}

export interface FuzzyResult {
  li_entries: FuzzyLiEntry[];
  di_matrix: number[][];
}

export interface MultipoleResult {
  dipole_debye?: number | null;
  dipole_xyz_debye?: [number, number, number] | null;
  spatial_extent_r2?: number | null;
  quadrupole_xx_yy_zz?: [number, number, number] | null;
}

export interface CdftAtomEntry {
  index: number;
  element: string;
  f_minus?: number | null;
  f_plus?: number | null;
  f_zero?: number | null;
  dual_descriptor?: number | null;
}

export interface AtomDeviation {
  atom_index: number;
  element: string;
  deviation_angstrom: number;
}

export interface PlanarityResult {
  mpp_angstrom?: number | null;
  sdp_angstrom?: number | null;
  max_positive_angstrom?: number | null;
  max_negative_angstrom?: number | null;
  atom_deviations: AtomDeviation[];
}

export interface EspSurfaceResult {
  volume_angstrom3?: number | null;
  density_g_cm3?: number | null;
  vs_min_kcal?: number | null;
  vs_max_kcal?: number | null;
  overall_area_angstrom2?: number | null;
  positive_area_angstrom2?: number | null;
  negative_area_angstrom2?: number | null;
  sigma2_tot_kcal2?: number | null;
  sigma2_pos_kcal2?: number | null;
  sigma2_neg_kcal2?: number | null;
  balance_nu?: number | null;
  internal_charge_sep_pi_kcal?: number | null;
  mpi_ev?: number | null;
  mpi_kcal?: number | null;
  nonpolar_area_pct?: number | null;
  polar_area_pct?: number | null;
}

export interface ZmyBatchRow {
  name: string;
  file_path: string;
  atom_count: number;
  homo_ev?: number | null;
  lumo_ev?: number | null;
  gap_ev?: number | null;
  dipole_debye?: number | null;
  mpp_angstrom?: number | null;
  sdp_angstrom?: number | null;
  esp?: EspSurfaceResult | null;
}
