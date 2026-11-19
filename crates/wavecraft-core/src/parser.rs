use regex::Regex;
use serde::{Deserialize, Serialize};
use std::collections::BTreeMap;
use std::fs;
use std::path::Path;

use crate::cube::{CubeData, BOHR_TO_ANGSTROM};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Atom3D {
    pub index: usize,
    pub symbol: String,
    pub atomic_number: u8,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub color: String,
    pub covalent_radius: f64,
    pub vdw_radius: f64,
    pub charge: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BondLink {
    pub atom1: usize,
    pub atom2: usize,
    pub symbol1: String,
    pub symbol2: String,
    pub length: f64,
    pub order: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct WavefunctionSummary {
    pub formula: Option<String>,
    pub total_energy_hartree: Option<f64>,
    pub virial_ratio: Option<f64>,
    pub num_electrons: Option<f64>,
    pub alpha_electrons: Option<f64>,
    pub beta_electrons: Option<f64>,
    pub num_basis_functions: Option<usize>,
    pub num_gtfs: Option<usize>,
    pub num_atoms: Option<usize>,
    pub net_charge: Option<f64>,
    pub multiplicity: Option<usize>,
    pub dipole_moment: Option<f64>,
    pub molecular_weight: Option<f64>,
    pub point_group: Option<String>,
    pub wavefunction_type: Option<String>,
    pub occ_start: Option<usize>,
    pub occ_end: Option<usize>,
    pub homo_index: Option<usize>,
    pub lumo_index: Option<usize>,
    pub homo_energy_ev: Option<f64>,
    pub lumo_energy_ev: Option<f64>,
    pub homo_lumo_gap_ev: Option<f64>,
    pub title: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrbitalInfo {
    pub index: usize,
    pub energy_hartree: f64,
    pub energy_ev: f64,
    pub occupancy: f64,
    pub spin_type: String,
    pub label: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChargeEntry {
    pub index: usize,
    pub element: String,
    pub charge: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BondOrderEntry {
    pub atom1_index: usize,
    pub atom2_index: usize,
    pub atom1: String,
    pub atom2: String,
    pub bond_order: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrbitalCompositionEntry {
    pub atom_index: usize,
    pub element: String,
    pub percentage: f64,
    pub s_pct: Option<f64>,
    pub p_pct: Option<f64>,
    pub d_pct: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DosPoint {
    pub energy_ev: f64,
    pub tdos: f64,
    pub occupied_dos: f64,
    pub virtual_dos: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DosCurve {
    pub points: Vec<DosPoint>,
    pub homo_energy_ev: Option<f64>,
    pub lumo_energy_ev: Option<f64>,
    pub gap_ev: Option<f64>,
    pub fwhm_ev: f64,
    pub broadening: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpectrumPeak {
    pub index: usize,
    pub x_value: f64, // cm^-1 for IR/Raman/VCD/ROA, eV or nm for UV-Vis/ECD, ppm for NMR
    pub energy_ev: Option<f64>,
    pub wavelength_nm: Option<f64>,
    pub intensity: f64,
    pub label: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SpectrumCurve {
    pub x_values: Vec<f64>,
    pub y_values: Vec<f64>,
    pub peaks: Vec<SpectrumPeak>,
    pub x_label: String,
    pub y_label: String,
    pub spectrum_type: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CriticalPoint {
    pub index: usize,
    pub cp_type_code: i32, // 1=(3,-3) NCP, 2=(3,-1) BCP, 3=(3,+1) RCP, 4=(3,+3) CCP
    pub cp_type_label: String,
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub rho: Option<f64>,
    pub laplacian: Option<f64>,
    pub elf: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NciPoint {
    pub x: f64,
    pub y: f64,
    pub z: f64,
    pub sign_lambda2_rho: f64,
    pub rdg: f64,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dg_intra: Option<f64>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub dg_total: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AromaticityResult {
    pub nics_values: Vec<f64>,
    pub flu: Option<f64>,
    pub homa: Option<f64>,
    pub bird: Option<f64>,
    pub mci: Option<f64>,
    pub pdi: Option<f64>,
    pub shannon_index: Option<f64>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct ThermochemistryInfo {
    pub zero_point_energy: Option<f64>,
    pub thermal_energy: Option<f64>,
    pub enthalpy: Option<f64>,
    pub gibbs_free_energy: Option<f64>,
    pub entropy: Option<f64>,
    pub heat_capacity: Option<f64>,
    pub temperature: Option<f64>,
    pub frequencies: Vec<f64>,
}

pub struct ElementMeta {
    pub z: u8,
    pub symbol: &'static str,
    pub name_zh: &'static str,
    pub color: &'static str,
    pub covalent_radius: f64,
    pub vdw_radius: f64,
}

const ELEMENTS: &[ElementMeta] = &[
    ElementMeta { z: 0, symbol: "Bq", name_zh: "虚原子", color: "#94a3b8", covalent_radius: 0.30, vdw_radius: 1.00 },
    ElementMeta { z: 1, symbol: "H", name_zh: "氢", color: "#f8fafc", covalent_radius: 0.31, vdw_radius: 1.20 },
    ElementMeta { z: 2, symbol: "He", name_zh: "氦", color: "#67e8f9", covalent_radius: 0.28, vdw_radius: 1.40 },
    ElementMeta { z: 3, symbol: "Li", name_zh: "锂", color: "#c084fc", covalent_radius: 1.28, vdw_radius: 1.82 },
    ElementMeta { z: 4, symbol: "Be", name_zh: "铍", color: "#84cc16", covalent_radius: 0.96, vdw_radius: 1.53 },
    ElementMeta { z: 5, symbol: "B", name_zh: "硼", color: "#fda4af", covalent_radius: 0.84, vdw_radius: 1.92 },
    ElementMeta { z: 6, symbol: "C", name_zh: "碳", color: "#64748b", covalent_radius: 0.76, vdw_radius: 1.70 },
    ElementMeta { z: 7, symbol: "N", name_zh: "氮", color: "#3b82f6", covalent_radius: 0.71, vdw_radius: 1.55 },
    ElementMeta { z: 8, symbol: "O", name_zh: "氧", color: "#ef4444", covalent_radius: 0.66, vdw_radius: 1.52 },
    ElementMeta { z: 9, symbol: "F", name_zh: "氟", color: "#22c55e", covalent_radius: 0.57, vdw_radius: 1.47 },
    ElementMeta { z: 10, symbol: "Ne", name_zh: "氖", color: "#38bdf8", covalent_radius: 0.58, vdw_radius: 1.54 },
    ElementMeta { z: 11, symbol: "Na", name_zh: "钠", color: "#a855f7", covalent_radius: 1.66, vdw_radius: 2.27 },
    ElementMeta { z: 12, symbol: "Mg", name_zh: "镁", color: "#4ade80", covalent_radius: 1.41, vdw_radius: 1.73 },
    ElementMeta { z: 13, symbol: "Al", name_zh: "铝", color: "#94a3b8", covalent_radius: 1.21, vdw_radius: 1.84 },
    ElementMeta { z: 14, symbol: "Si", name_zh: "硅", color: "#fbbf24", covalent_radius: 1.11, vdw_radius: 2.10 },
    ElementMeta { z: 15, symbol: "P", name_zh: "磷", color: "#f97316", covalent_radius: 1.07, vdw_radius: 1.80 },
    ElementMeta { z: 16, symbol: "S", name_zh: "硫", color: "#eab308", covalent_radius: 1.05, vdw_radius: 1.80 },
    ElementMeta { z: 17, symbol: "Cl", name_zh: "氯", color: "#10b981", covalent_radius: 1.02, vdw_radius: 1.75 },
    ElementMeta { z: 18, symbol: "Ar", name_zh: "氩", color: "#22d3ee", covalent_radius: 1.06, vdw_radius: 1.88 },
    ElementMeta { z: 19, symbol: "K", name_zh: "钾", color: "#9333ea", covalent_radius: 2.03, vdw_radius: 2.75 },
    ElementMeta { z: 20, symbol: "Ca", name_zh: "钙", color: "#16a34a", covalent_radius: 1.76, vdw_radius: 2.31 },
    ElementMeta { z: 21, symbol: "Sc", name_zh: "钪", color: "#cbd5e1", covalent_radius: 1.70, vdw_radius: 2.11 },
    ElementMeta { z: 22, symbol: "Ti", name_zh: "钛", color: "#94a3b8", covalent_radius: 1.60, vdw_radius: 2.00 },
    ElementMeta { z: 23, symbol: "V", name_zh: "钒", color: "#94a3b8", covalent_radius: 1.53, vdw_radius: 2.00 },
    ElementMeta { z: 24, symbol: "Cr", name_zh: "铬", color: "#60a5fa", covalent_radius: 1.39, vdw_radius: 2.00 },
    ElementMeta { z: 25, symbol: "Mn", name_zh: "锰", color: "#c084fc", covalent_radius: 1.39, vdw_radius: 2.00 },
    ElementMeta { z: 26, symbol: "Fe", name_zh: "铁", color: "#ea580c", covalent_radius: 1.32, vdw_radius: 2.00 },
    ElementMeta { z: 27, symbol: "Co", name_zh: "钴", color: "#f472b6", covalent_radius: 1.26, vdw_radius: 2.00 },
    ElementMeta { z: 28, symbol: "Ni", name_zh: "镍", color: "#22c55e", covalent_radius: 1.24, vdw_radius: 1.63 },
    ElementMeta { z: 29, symbol: "Cu", name_zh: "铜", color: "#d97706", covalent_radius: 1.32, vdw_radius: 1.40 },
    ElementMeta { z: 30, symbol: "Zn", name_zh: "锌", color: "#64748b", covalent_radius: 1.22, vdw_radius: 1.39 },
    ElementMeta { z: 31, symbol: "Ga", name_zh: "镓", color: "#a16207", covalent_radius: 1.22, vdw_radius: 1.87 },
    ElementMeta { z: 32, symbol: "Ge", name_zh: "锗", color: "#0d9488", covalent_radius: 1.20, vdw_radius: 2.11 },
    ElementMeta { z: 33, symbol: "As", name_zh: "砷", color: "#a855f7", covalent_radius: 1.19, vdw_radius: 1.85 },
    ElementMeta { z: 34, symbol: "Se", name_zh: "硒", color: "#f59e0b", covalent_radius: 1.20, vdw_radius: 1.90 },
    ElementMeta { z: 35, symbol: "Br", name_zh: "溴", color: "#b91c1c", covalent_radius: 1.20, vdw_radius: 1.85 },
    ElementMeta { z: 36, symbol: "Kr", name_zh: "氪", color: "#38bdf8", covalent_radius: 1.16, vdw_radius: 2.02 },
    ElementMeta { z: 44, symbol: "Ru", name_zh: "钌", color: "#06b6d4", covalent_radius: 1.46, vdw_radius: 2.05 },
    ElementMeta { z: 45, symbol: "Rh", name_zh: "铑", color: "#0891b2", covalent_radius: 1.42, vdw_radius: 2.00 },
    ElementMeta { z: 46, symbol: "Pd", name_zh: "钯", color: "#0e7490", covalent_radius: 1.39, vdw_radius: 1.63 },
    ElementMeta { z: 47, symbol: "Ag", name_zh: "银", color: "#cbd5e1", covalent_radius: 1.45, vdw_radius: 1.72 },
    ElementMeta { z: 53, symbol: "I", name_zh: "碘", color: "#7e22ce", covalent_radius: 1.39, vdw_radius: 1.98 },
    ElementMeta { z: 54, symbol: "Xe", name_zh: "氙", color: "#0284c7", covalent_radius: 1.40, vdw_radius: 2.16 },
    ElementMeta { z: 75, symbol: "Re", name_zh: "铼", color: "#38bdf8", covalent_radius: 1.51, vdw_radius: 2.05 },
    ElementMeta { z: 78, symbol: "Pt", name_zh: "铂", color: "#cbd5e1", covalent_radius: 1.36, vdw_radius: 1.75 },
    ElementMeta { z: 79, symbol: "Au", name_zh: "金", color: "#facc15", covalent_radius: 1.36, vdw_radius: 1.66 },
];

pub fn element_by_z(z: u8) -> &'static ElementMeta {
    ELEMENTS
        .iter()
        .find(|e| e.z == z)
        .unwrap_or(&ELEMENTS[0])
}

pub fn element_by_symbol(sym: &str) -> &'static ElementMeta {
    let clean = sym.trim();
    ELEMENTS
        .iter()
        .find(|e| e.symbol.eq_ignore_ascii_case(clean))
        .unwrap_or(&ELEMENTS[0])
}

pub fn atomic_symbol(z: u8) -> &'static str {
    element_by_z(z).symbol
}

pub fn make_atom(index: usize, symbol_or_z: &str, x: f64, y: f64, z: f64) -> Atom3D {
    let meta = if let Ok(zn) = symbol_or_z.trim().parse::<u8>() {
        element_by_z(zn)
    } else {
        element_by_symbol(symbol_or_z)
    };
    let sym = if meta.z == 0 && !symbol_or_z.trim().is_empty() {
        symbol_or_z.trim().to_string()
    } else {
        meta.symbol.to_string()
    };
    Atom3D {
        index,
        symbol: sym,
        atomic_number: meta.z,
        x,
        y,
        z,
        color: meta.color.to_string(),
        covalent_radius: meta.covalent_radius,
        vdw_radius: meta.vdw_radius,
        charge: None,
    }
}

pub fn compute_bonds(atoms: &[Atom3D]) -> Vec<BondLink> {
    let mut bonds = Vec::new();
    let n = atoms.len();
    for i in 0..n {
        for j in (i + 1)..n {
            let a = &atoms[i];
            let b = &atoms[j];
            let dx = a.x - b.x;
            let dy = a.y - b.y;
            let dz = a.z - b.z;
            let dist = (dx * dx + dy * dy + dz * dz).sqrt();
            let threshold = 1.25 * (a.covalent_radius + b.covalent_radius);
            if dist > 0.35 && dist <= threshold {
                let order = if dist < 0.85 * (a.covalent_radius + b.covalent_radius) {
                    2.0
                } else {
                    1.0
                };
                bonds.push(BondLink {
                    atom1: a.index,
                    atom2: b.index,
                    symbol1: a.symbol.clone(),
                    symbol2: b.symbol.clone(),
                    length: (dist * 10000.0).round() / 10000.0,
                    order,
                });
            }
        }
    }
    bonds
}

pub fn compute_formula(atoms: &[Atom3D]) -> String {
    if atoms.is_empty() {
        return String::new();
    }
    let mut counts: BTreeMap<String, usize> = BTreeMap::new();
    for a in atoms {
        *counts.entry(a.symbol.clone()).or_insert(0) += 1;
    }
    // Hill system: C first, then H, then alphabetical
    let mut parts = Vec::new();
    if let Some(c) = counts.remove("C") {
        parts.push(if c == 1 {
            "C".to_string()
        } else {
            format!("C{c}")
        });
        if let Some(h) = counts.remove("H") {
            parts.push(if h == 1 {
                "H".to_string()
            } else {
                format!("H{h}")
            });
        }
    }
    for (sym, cnt) in counts {
        parts.push(if cnt == 1 {
            sym
        } else {
            format!("{sym}{cnt}")
        });
    }
    parts.join("")
}

pub fn parse_xyz_text(text: &str) -> Vec<Atom3D> {
    let mut atoms = Vec::new();
    let lines: Vec<&str> = text.lines().collect();
    if lines.len() >= 3 {
        if let Ok(natoms) = lines[0].trim().parse::<usize>() {
            for (idx, line) in lines.iter().skip(2).take(natoms).enumerate() {
                let parts: Vec<&str> = line.split_whitespace().collect();
                if parts.len() >= 4 {
                    if let (Ok(x), Ok(y), Ok(z)) = (
                        parts[1].parse::<f64>(),
                        parts[2].parse::<f64>(),
                        parts[3].parse::<f64>(),
                    ) {
                        atoms.push(make_atom(idx + 1, parts[0], x, y, z));
                    }
                }
            }
            if !atoms.is_empty() {
                return atoms;
            }
        }
    }

    // Fallback generic "Elem X Y Z" line match
    let re = Regex::new(r"^\s*([A-Za-z]{1,3})\s+([-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?)\s+([-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?)\s+([-+]?\d*\.?\d+(?:[eEdD][-+]?\d+)?)\s*$").unwrap();
    for line in lines {
        if let Some(caps) = re.captures(line) {
            let sym = &caps[1];
            let x = caps[2].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            let y = caps[3].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            let z = caps[4].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            atoms.push(make_atom(atoms.len() + 1, sym, x, y, z));
        }
    }
    atoms
}

/// Fast direct parser for .fch/.fchk/.xyz/.pdb/.cub files so UI can display 3D geometry immediately.
pub fn quick_inspect_file(path: &Path) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let ext = path
        .extension()
        .and_then(|e| e.to_str())
        .unwrap_or("")
        .to_lowercase();
    let Ok(content) = fs::read_to_string(path) else {
        return (Vec::new(), WavefunctionSummary::default(), Vec::new());
    };

    match ext.as_str() {
        "xyz" => {
            let atoms = parse_xyz_text(&content);
            let mut summary = WavefunctionSummary::default();
            summary.num_atoms = Some(atoms.len());
            summary.formula = Some(compute_formula(&atoms));
            (atoms, summary, Vec::new())
        }
        "cub" | "cube" => {
            if let Ok(cube) = CubeData::parse(&content) {
                let atoms: Vec<Atom3D> = cube
                    .atoms
                    .iter()
                    .map(|a| make_atom(a.index, &a.symbol, a.x, a.y, a.z))
                    .collect();
                let mut summary = WavefunctionSummary::default();
                summary.num_atoms = Some(atoms.len());
                summary.formula = Some(compute_formula(&atoms));
                summary.title = Some(cube.title);
                return (atoms, summary, Vec::new());
            }
            (Vec::new(), WavefunctionSummary::default(), Vec::new())
        }
        "pdb" => {
            let mut atoms = Vec::new();
            for line in content.lines() {
                if line.starts_with("ATOM  ") || line.starts_with("HETATM") {
                    if line.len() >= 54 {
                        let x = line[30..38].trim().parse::<f64>().unwrap_or(0.0);
                        let y = line[38..46].trim().parse::<f64>().unwrap_or(0.0);
                        let z = line[46..54].trim().parse::<f64>().unwrap_or(0.0);
                        let elem = if line.len() >= 78 && !line[76..78].trim().is_empty() {
                            line[76..78].trim()
                        } else {
                            let atom_name = line[12..16].trim();
                            atom_name.trim_start_matches(|c: char| c.is_ascii_digit())
                        };
                        let sym = elem.chars().take(2).collect::<String>();
                        atoms.push(make_atom(atoms.len() + 1, &sym, x, y, z));
                    }
                }
            }
            let mut summary = WavefunctionSummary::default();
            summary.num_atoms = Some(atoms.len());
            summary.formula = Some(compute_formula(&atoms));
            (atoms, summary, Vec::new())
        }
        "fch" | "fchk" => parse_fchk_direct(&content),
        "wfn" => parse_wfn_direct(&content),
        "wfx" => parse_wfx_direct(&content),
        "gjf" | "com" => parse_gjf_direct(&content),
        "out" | "log" => parse_gaussian_log_direct(&content),
        "molden" => parse_molden_direct(&content),
        _ => (Vec::new(), WavefunctionSummary::default(), Vec::new()),
    }
}

fn parse_wfn_direct(content: &str) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let mut summary = WavefunctionSummary::default();
    let lines: Vec<&str> = content.lines().collect();
    if let Some(first) = lines.first() {
        let t = first.trim();
        if !t.is_empty() {
            summary.title = Some(t.to_string());
        }
    }

    const BOHR_TO_ANGSTROM: f64 = 0.52917721092;
    let mut atoms = Vec::new();
    let mut orbitals = Vec::new();

    let re_atom = Regex::new(
        r"^\s*([A-Za-z]{1,2})\s+\d+\s+\(CENTRE\s+\d+\)\s+([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s+([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s+([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s+CHARGE\s*=\s*([-+]?\d+\.?\d*)",
    )
    .unwrap();

    let re_mo = Regex::new(
        r"^\s*MO\s+(\d+)\s+OCC\s+NO\s*=\s*([-+]?\d+\.?\d*)\s+ORB\.\s*ENERGY\s*=\s*([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)",
    )
    .unwrap();

    for line in &lines {
        if line.contains("MOL ORBITALS") && line.contains("NUCLEI") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            for i in 0..parts.len() {
                if parts[i] == "NUCLEI" && i > 0 {
                    summary.num_atoms = parts[i - 1].parse().ok();
                } else if parts[i] == "PRIMITIVES" && i > 0 {
                    summary.num_basis_functions = parts[i - 1].parse().ok();
                }
            }
        } else if let Some(caps) = re_atom.captures(line) {
            let sym = &caps[1];
            let x_bohr = caps[2].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            let y_bohr = caps[3].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            let z_bohr = caps[4].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            let x = x_bohr * BOHR_TO_ANGSTROM;
            let y = y_bohr * BOHR_TO_ANGSTROM;
            let z = z_bohr * BOHR_TO_ANGSTROM;
            let mut atom = make_atom(atoms.len() + 1, sym, x, y, z);
            if let Ok(chg) = caps[5].parse::<f64>() {
                atom.charge = Some(chg);
            }
            atoms.push(atom);
        } else if let Some(caps) = re_mo.captures(line) {
            let idx = caps[1].parse::<usize>().unwrap_or(orbitals.len() + 1);
            let occ = caps[2].parse::<f64>().unwrap_or(0.0);
            let energy_au = caps[3].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
            let energy_ev = energy_au * 27.211386245988;
            orbitals.push(OrbitalInfo {
                index: idx,
                energy_hartree: energy_au,
                energy_ev,
                occupancy: occ,
                spin_type: "Alpha".to_string(),
                label: None,
            });
        }
    }

    if !orbitals.is_empty() {
        enrich_homo_lumo(&mut summary, &orbitals);
    }
    summary.num_atoms = Some(atoms.len());
    summary.formula = Some(compute_formula(&atoms));

    (atoms, summary, orbitals)
}

fn parse_wfx_direct(content: &str) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let mut summary = WavefunctionSummary::default();
    const BOHR_TO_ANGSTROM: f64 = 0.52917721092;

    let extract_tag = |tag: &str| -> Option<String> {
        let open = format!("<{tag}>");
        let close = format!("</{tag}>");
        if let Some(start) = content.find(&open) {
            if let Some(end) = content[start..].find(&close) {
                return Some(content[start + open.len()..start + end].trim().to_string());
            }
        }
        None
    };

    if let Some(t) = extract_tag("Title") {
        summary.title = Some(t);
    }
    if let Some(s) = extract_tag("Number of Nuclei").and_then(|s| s.parse().ok()) {
        summary.num_atoms = Some(s);
    }
    if let Some(s) = extract_tag("Number of Electrons").and_then(|s| s.parse().ok()) {
        summary.num_electrons = Some(s);
    }
    if let Some(s) = extract_tag("Number of Alpha Electrons").and_then(|s| s.parse().ok()) {
        summary.alpha_electrons = Some(s);
    }
    if let Some(s) = extract_tag("Number of Beta Electrons").and_then(|s| s.parse().ok()) {
        summary.beta_electrons = Some(s);
    }
    if let Some(s) = extract_tag("Total Energy").and_then(|s| s.parse().ok()) {
        summary.total_energy_hartree = Some(s);
    }

    let mut names = Vec::new();
    if let Some(n_text) = extract_tag("Nuclear Names") {
        for tok in n_text.split_whitespace() {
            let sym = tok.trim_end_matches(|c: char| c.is_ascii_digit());
            names.push(sym.to_string());
        }
    }

    let mut coords_bohr = Vec::new();
    if let Some(c_text) = extract_tag("Nuclear Cartesian Coordinates") {
        for tok in c_text.split_whitespace() {
            if let Ok(v) = tok.parse::<f64>() {
                coords_bohr.push(v);
            }
        }
    }

    let mut atoms = Vec::new();
    let num = names.len().min(coords_bohr.len() / 3);
    for i in 0..num {
        let sym = &names[i];
        let x = coords_bohr[i * 3] * BOHR_TO_ANGSTROM;
        let y = coords_bohr[i * 3 + 1] * BOHR_TO_ANGSTROM;
        let z = coords_bohr[i * 3 + 2] * BOHR_TO_ANGSTROM;
        atoms.push(make_atom(i + 1, sym, x, y, z));
    }

    summary.num_atoms = Some(atoms.len());
    summary.formula = Some(compute_formula(&atoms));

    (atoms, summary, Vec::new())
}

fn parse_gjf_direct(content: &str) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let mut summary = WavefunctionSummary::default();
    let lines: Vec<&str> = content.lines().collect();

    let re_charge_mult = Regex::new(r"^\s*([-+]?\d+)\s+(\d+)\s*$").unwrap();
    let re_geom = Regex::new(
        r"^\s*([A-Za-z]{1,2})\s+([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s+([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s+([-+]?\d+\.?\d*(?:[eEdD][-+]?\d+)?)\s*$",
    )
    .unwrap();

    let mut found_cm = false;
    let mut atoms = Vec::new();

    for line in lines {
        let trimmed = line.trim();
        if !found_cm {
            if let Some(caps) = re_charge_mult.captures(trimmed) {
                summary.net_charge = caps[1].parse().ok();
                summary.multiplicity = caps[2].parse().ok();
                found_cm = true;
            }
        } else {
            if trimmed.is_empty() {
                if !atoms.is_empty() {
                    break;
                }
                continue;
            }
            if let Some(caps) = re_geom.captures(trimmed) {
                let sym = &caps[1];
                let x = caps[2].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
                let y = caps[3].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
                let z = caps[4].replace(['d', 'D'], "e").parse::<f64>().unwrap_or(0.0);
                atoms.push(make_atom(atoms.len() + 1, sym, x, y, z));
            } else if !atoms.is_empty() {
                break;
            }
        }
    }

    summary.num_atoms = Some(atoms.len());
    summary.formula = Some(compute_formula(&atoms));

    (atoms, summary, Vec::new())
}

fn parse_gaussian_log_direct(
    content: &str,
) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let mut summary = WavefunctionSummary::default();
    let lines: Vec<&str> = content.lines().collect();

    let mut last_orient_start: Option<usize> = None;
    for (idx, line) in lines.iter().enumerate() {
        if line.contains("Standard orientation:") || line.contains("Input orientation:") {
            last_orient_start = Some(idx);
        }
        if line.contains("SCF Done:") {
            if let Some(idx_eq) = line.find('=') {
                let rest = line[idx_eq + 1..].trim();
                if let Some(val_str) = rest.split_whitespace().next() {
                    if let Ok(v) = val_str.parse::<f64>() {
                        summary.total_energy_hartree = Some(v);
                    }
                }
            }
        }
        if line.contains("alpha electrons") && line.contains("beta electrons") {
            let parts: Vec<&str> = line.split_whitespace().collect();
            for i in 0..parts.len() {
                if parts[i] == "alpha" && i > 0 {
                    summary.alpha_electrons = parts[i - 1].parse().ok();
                } else if parts[i] == "beta" && i > 0 {
                    summary.beta_electrons = parts[i - 1].parse().ok();
                }
            }
            if let (Some(a), Some(b)) = (summary.alpha_electrons, summary.beta_electrons) {
                summary.num_electrons = Some(a + b);
            }
        }
    }

    let mut atoms = Vec::new();
    if let Some(start_idx) = last_orient_start {
        let mut i = start_idx + 1;
        let mut dash_count = 0;
        while i < lines.len() {
            let l = lines[i].trim();
            if l.starts_with("---") {
                dash_count += 1;
                if dash_count == 2 {
                    i += 1;
                    break;
                }
            }
            i += 1;
        }

        while i < lines.len() {
            let l = lines[i].trim();
            if l.starts_with("---") {
                break;
            }
            let parts: Vec<&str> = l.split_whitespace().collect();
            if parts.len() >= 6 {
                if let (Ok(zn), Ok(x), Ok(y), Ok(z)) = (
                    parts[1].parse::<u8>(),
                    parts[3].parse::<f64>(),
                    parts[4].parse::<f64>(),
                    parts[5].parse::<f64>(),
                ) {
                    let sym = atomic_symbol(zn);
                    atoms.push(make_atom(atoms.len() + 1, sym, x, y, z));
                }
            }
            i += 1;
        }
    }

    summary.num_atoms = Some(atoms.len());
    summary.formula = Some(compute_formula(&atoms));

    (atoms, summary, Vec::new())
}

fn parse_molden_direct(content: &str) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let mut summary = WavefunctionSummary::default();
    const BOHR_TO_ANGSTROM: f64 = 0.52917721092;
    let lines: Vec<&str> = content.lines().collect();

    let mut in_atoms = false;
    let mut is_au = true;
    let mut atoms = Vec::new();

    for line in lines {
        let trimmed = line.trim();
        if trimmed.starts_with("[Atoms]") || trimmed.starts_with("[ATOMS]") {
            in_atoms = true;
            is_au = trimmed.to_uppercase().contains("AU");
            continue;
        }
        if in_atoms {
            if trimmed.starts_with('[') {
                break;
            }
            let parts: Vec<&str> = trimmed.split_whitespace().collect();
            if parts.len() >= 6 {
                let sym = parts[0];
                let scale = if is_au { BOHR_TO_ANGSTROM } else { 1.0 };
                if let (Ok(x), Ok(y), Ok(z)) = (
                    parts[3].parse::<f64>(),
                    parts[4].parse::<f64>(),
                    parts[5].parse::<f64>(),
                ) {
                    atoms.push(make_atom(atoms.len() + 1, sym, x * scale, y * scale, z * scale));
                }
            }
        }
    }

    summary.num_atoms = Some(atoms.len());
    summary.formula = Some(compute_formula(&atoms));

    (atoms, summary, Vec::new())
}

fn parse_fchk_direct(content: &str) -> (Vec<Atom3D>, WavefunctionSummary, Vec<OrbitalInfo>) {
    let mut summary = WavefunctionSummary::default();
    let lines: Vec<&str> = content.lines().collect();
    if let Some(first) = lines.first() {
        let t = first.trim();
        if !t.is_empty() {
            summary.title = Some(t.to_string());
        }
    }

    let mut atomic_numbers: Vec<u8> = Vec::new();
    let mut coords_bohr: Vec<f64> = Vec::new();
    let mut alpha_energies: Vec<f64> = Vec::new();

    let mut i = 0;
    while i < lines.len() {
        let line = lines[i];
        if line.starts_with("Number of atoms") {
            summary.num_atoms = line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Charge ") {
            summary.net_charge = line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Multiplicity ") {
            summary.multiplicity = line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Number of electrons ") {
            summary.num_electrons = line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Number of alpha electrons ") {
            summary.alpha_electrons = line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Number of beta electrons ") {
            summary.beta_electrons = line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Number of basis functions ") {
            summary.num_basis_functions =
                line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Total Energy ") {
            summary.total_energy_hartree =
                line.split_whitespace().last().and_then(|s| s.parse().ok());
        } else if line.starts_with("Atomic numbers ") {
            let count: usize = line.split_whitespace().last().and_then(|s| s.parse().ok()).unwrap_or(0);
            i += 1;
            while i < lines.len() && atomic_numbers.len() < count {
                for tok in lines[i].split_whitespace() {
                    if let Ok(z) = tok.parse::<u8>() {
                        atomic_numbers.push(z);
                    }
                }
                if atomic_numbers.len() >= count {
                    break;
                }
                i += 1;
            }
        } else if line.starts_with("Current cartesian coordinates ") {
            let count: usize = line.split_whitespace().last().and_then(|s| s.parse().ok()).unwrap_or(0);
            i += 1;
            while i < lines.len() && coords_bohr.len() < count {
                for tok in lines[i].split_whitespace() {
                    if let Ok(v) = tok.parse::<f64>() {
                        coords_bohr.push(v);
                    }
                }
                if coords_bohr.len() >= count {
                    break;
                }
                i += 1;
            }
        } else if line.starts_with("Alpha Orbital Energies ") {
            let count: usize = line.split_whitespace().last().and_then(|s| s.parse().ok()).unwrap_or(0);
            i += 1;
            while i < lines.len() && alpha_energies.len() < count {
                for tok in lines[i].split_whitespace() {
                    if let Ok(v) = tok.parse::<f64>() {
                        alpha_energies.push(v);
                    }
                }
                if alpha_energies.len() >= count {
                    break;
                }
                i += 1;
            }
        }
        i += 1;
    }

    let mut atoms = Vec::new();
    for (idx, z) in atomic_numbers.iter().enumerate() {
        let base = idx * 3;
        if base + 2 < coords_bohr.len() {
            let x = coords_bohr[base] * BOHR_TO_ANGSTROM;
            let y = coords_bohr[base + 1] * BOHR_TO_ANGSTROM;
            let zc = coords_bohr[base + 2] * BOHR_TO_ANGSTROM;
            atoms.push(make_atom(idx + 1, &z.to_string(), x, y, zc));
        }
    }
    if !atoms.is_empty() {
        summary.formula = Some(compute_formula(&atoms));
        summary.num_atoms = Some(atoms.len());
    }

    let n_occ = summary.alpha_electrons.unwrap_or(0.0).round() as usize;
    let mut orbitals = Vec::new();
    if !alpha_energies.is_empty() {
        for (idx, &eh) in alpha_energies.iter().enumerate() {
            let orb_num = idx + 1;
            let e_ev = eh * 27.211386245988;
            let occ = if orb_num <= n_occ { 2.0 } else { 0.0 };
            let label = tag_orbital_label(orb_num, n_occ);
            orbitals.push(OrbitalInfo {
                index: orb_num,
                energy_hartree: eh,
                energy_ev: e_ev,
                occupancy: occ,
                spin_type: "A+B".to_string(),
                label,
            });
        }
        enrich_homo_lumo(&mut summary, &orbitals);
    }

    (atoms, summary, orbitals)
}

fn tag_orbital_label(orb_num: usize, homo_idx: usize) -> Option<String> {
    if homo_idx == 0 {
        return None;
    }
    if orb_num == homo_idx {
        Some("HOMO".to_string())
    } else if orb_num + 1 == homo_idx {
        Some("HOMO-1".to_string())
    } else if orb_num + 2 == homo_idx {
        Some("HOMO-2".to_string())
    } else if orb_num == homo_idx + 1 {
        Some("LUMO".to_string())
    } else if orb_num == homo_idx + 2 {
        Some("LUMO+1".to_string())
    } else if orb_num == homo_idx + 3 {
        Some("LUMO+2".to_string())
    } else {
        None
    }
}

pub fn enrich_homo_lumo(summary: &mut WavefunctionSummary, orbitals: &[OrbitalInfo]) {
    let mut last_occ: Option<&OrbitalInfo> = None;
    let mut first_vir: Option<&OrbitalInfo> = None;
    for orb in orbitals {
        if orb.occupancy > 0.01 {
            last_occ = Some(orb);
        } else if first_vir.is_none() {
            first_vir = Some(orb);
        }
    }
    if let Some(h) = last_occ {
        summary.homo_index = Some(h.index);
        summary.homo_energy_ev = Some((h.energy_ev * 10000.0).round() / 10000.0);
    }
    if let Some(l) = first_vir {
        summary.lumo_index = Some(l.index);
        summary.lumo_energy_ev = Some((l.energy_ev * 10000.0).round() / 10000.0);
    }
    if let (Some(he), Some(le)) = (summary.homo_energy_ev, summary.lumo_energy_ev) {
        summary.homo_lumo_gap_ev = Some(((le - he) * 10000.0).round() / 10000.0);
    }
}

pub fn parse_wfn_info(output: &str) -> WavefunctionSummary {
    let mut info = WavefunctionSummary::default();

    let cap_f64 = |pat: &str| -> Option<f64> {
        Regex::new(pat)
            .ok()?
            .captures(output)?
            .get(1)?
            .as_str()
            .trim()
            .parse::<f64>()
            .ok()
    };
    let cap_usize = |pat: &str| -> Option<usize> {
        Regex::new(pat)
            .ok()?
            .captures(output)?
            .get(1)?
            .as_str()
            .trim()
            .parse::<usize>()
            .ok()
    };
    let cap_str = |pat: &str| -> Option<String> {
        Some(
            Regex::new(pat)
                .ok()?
                .captures(output)?
                .get(1)?
                .as_str()
                .trim()
                .to_string(),
        )
    };

    info.total_energy_hartree = cap_f64(r"(?i)Total energy\s*[:=]\s*([-+\d.Ee]+)");
    info.virial_ratio = cap_f64(r"(?i)Virial ratio\s*[:=]\s*([-+\d.Ee]+)");
    info.num_electrons = cap_f64(r"(?i)Total/Alpha/Beta electrons:\s*([\d.]+)");
    info.alpha_electrons = cap_f64(r"(?i)Total/Alpha/Beta electrons:\s*[\d.]+\s+([\d.]+)");
    info.beta_electrons = cap_f64(r"(?i)Total/Alpha/Beta electrons:\s*[\d.]+\s+[\d.]+\s+([\d.]+)");
    info.num_basis_functions = cap_usize(r"(?i)Basis functions:\s*(\d+)");
    info.num_gtfs = cap_usize(r"(?i)GTFs:\s*(\d+)");
    info.num_atoms = cap_usize(r"(?i)Atoms:\s*(\d+)");
    info.net_charge = cap_f64(r"(?i)Net charge:\s*([-+\d.]+)");
    info.multiplicity = cap_usize(r"(?i)Expected multiplicity:\s*(\d+)");
    info.molecular_weight = cap_f64(r"(?i)Molecule weight:\s*([\d.]+)");
    info.point_group = cap_str(r"(?i)Point group:\s*(\S+)");
    info.formula = cap_str(r"(?i)Formula:\s*(.+?)\s{2,}Total atoms");
    if info.formula.is_none() {
        info.formula = cap_str(r"(?i)Formula:\s*(\S+(?:\s+\S+)*)");
    }
    info.title = cap_str(r"(?i)Title line of this file:\s*(.+)");

    if let Some(caps) = Regex::new(r"(?i)Orbitals from\s+(\d+)\s+to\s+(\d+)\s+are occupied")
        .unwrap()
        .captures(output)
    {
        info.occ_start = caps[1].parse().ok();
        info.occ_end = caps[2].parse().ok();
    }

    if output.to_lowercase().contains("restricted single-determinant") {
        info.wavefunction_type = Some("RHF/RKS".to_string());
    } else if output.to_lowercase().contains("unrestricted single-determinant") {
        info.wavefunction_type = Some("UHF/UKS".to_string());
    } else if output.to_lowercase().contains("restricted open-shell") {
        info.wavefunction_type = Some("ROHF/ROKS".to_string());
    }

    info
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LinePoint {
    pub x_angstrom: f64,
    pub y_angstrom: f64,
    pub z_angstrom: f64,
    pub dist_angstrom: f64,
    pub value: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzyLiEntry {
    pub index: usize,
    pub element: String,
    pub localization_index: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct FuzzyResult {
    pub li_entries: Vec<FuzzyLiEntry>,
    pub di_matrix: Vec<Vec<f64>>,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct MultipoleResult {
    pub dipole_debye: Option<f64>,
    pub dipole_xyz_debye: Option<[f64; 3]>,
    pub spatial_extent_r2: Option<f64>,
    pub quadrupole_xx_yy_zz: Option<[f64; 3]>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CdftAtomEntry {
    pub index: usize,
    pub element: String,
    pub f_minus: Option<f64>,
    pub f_plus: Option<f64>,
    pub f_zero: Option<f64>,
    pub dual_descriptor: Option<f64>,
}

pub fn parse_line_txt(content: &str) -> Vec<LinePoint> {
    let mut pts = Vec::new();
    let mut origin: Option<[f64; 3]> = None;
    for line in content.lines() {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 5 {
            if let (Ok(xb), Ok(yb), Ok(zb), Ok(db), Ok(val)) = (
                parts[0].parse::<f64>(),
                parts[1].parse::<f64>(),
                parts[2].parse::<f64>(),
                parts[3].parse::<f64>(),
                parts[4].parse::<f64>(),
            ) {
                let _ = origin.get_or_insert([xb, yb, zb]);
                pts.push(LinePoint {
                    x_angstrom: xb * BOHR_TO_ANGSTROM,
                    y_angstrom: yb * BOHR_TO_ANGSTROM,
                    z_angstrom: zb * BOHR_TO_ANGSTROM,
                    dist_angstrom: db * BOHR_TO_ANGSTROM,
                    value: val,
                });
                continue;
            }
        }
        if parts.len() >= 4 {
            if let (Ok(xb), Ok(yb), Ok(zb), Ok(val)) = (
                parts[0].parse::<f64>(),
                parts[1].parse::<f64>(),
                parts[2].parse::<f64>(),
                parts[3].parse::<f64>(),
            ) {
                let o = origin.get_or_insert([xb, yb, zb]);
                let dist_b = ((xb - o[0]).powi(2) + (yb - o[1]).powi(2) + (zb - o[2]).powi(2)).sqrt();
                pts.push(LinePoint {
                    x_angstrom: xb * BOHR_TO_ANGSTROM,
                    y_angstrom: yb * BOHR_TO_ANGSTROM,
                    z_angstrom: zb * BOHR_TO_ANGSTROM,
                    dist_angstrom: dist_b * BOHR_TO_ANGSTROM,
                    value: val,
                });
            }
        }
    }
    if pts.len() > 400 {
        let step = (pts.len() / 350).max(1);
        pts = pts.into_iter().step_by(step).collect();
    }
    pts
}

pub fn parse_fuzzy_lidi(output: &str) -> FuzzyResult {
    let mut res = FuzzyResult::default();
    if let Some(idx) = output.find("Localization index:") {
        let slice = &output[idx..];
        let end = slice.find("Total delocalization").unwrap_or(slice.len().min(1500));
        let re = Regex::new(r"(\d+)\(([A-Za-z]+)\s*\):\s*([-+\d.]+)").unwrap();
        for caps in re.captures_iter(&slice[..end]) {
            if let (Ok(i), Ok(v)) = (caps[1].parse::<usize>(), caps[3].parse::<f64>()) {
                res.li_entries.push(FuzzyLiEntry {
                    index: i,
                    element: caps[2].trim().to_string(),
                    localization_index: v,
                });
            }
        }
    }
    if let Some(idx) = output.find("Total delocalization index matrix") {
        let slice = &output[idx..];
        for line in slice.lines().skip(2) {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 2 && parts[0].parse::<usize>().is_ok() {
                let row: Vec<f64> = parts[1..]
                    .iter()
                    .filter_map(|s| s.parse::<f64>().ok())
                    .collect();
                if !row.is_empty() {
                    res.di_matrix.push(row);
                }
            } else if !res.di_matrix.is_empty() && line.trim().is_empty() {
                break;
            }
        }
    }
    res
}

pub fn parse_multipole(output: &str) -> MultipoleResult {
    let mut res = MultipoleResult::default();
    if let Some(caps) = Regex::new(r"(?i)Magnitude of dipole moment:\s*[-+\d.]+\s*a\.u\.\s*([-+\d.]+)\s*Debye")
        .unwrap()
        .captures(output)
    {
        res.dipole_debye = caps[1].parse::<f64>().ok();
    } else if let Some(caps) = Regex::new(r"(?i)Norm of dipole moment:\s*[-+\d.]+\s*a\.u\.\s*([-+\d.]+)\s*Debye")
        .unwrap()
        .captures(output)
    {
        res.dipole_debye = caps[1].parse::<f64>().ok();
    }
    if let Some(caps) = Regex::new(r"(?i)Electronic spatial extent\s*<R\^2>:\s*([-+\d.Ee]+)")
        .unwrap()
        .captures(output)
    {
        res.spatial_extent_r2 = caps[1].parse::<f64>().ok();
    }
    res
}

pub fn parse_cdft_fukui(output: &str) -> Vec<CdftAtomEntry> {
    let mut entries = Vec::new();
    let re = Regex::new(
        r"^\s*(\d+)\(([A-Za-z]+)\s*\)\s+([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)\s+([-+\d.]+)",
    )
    .unwrap();
    for line in output.lines() {
        if let Some(caps) = re.captures(line) {
            if let Ok(idx) = caps[1].parse::<usize>() {
                entries.push(CdftAtomEntry {
                    index: idx,
                    element: caps[2].trim().to_string(),
                    f_minus: caps[3].parse::<f64>().ok(),
                    f_plus: caps[4].parse::<f64>().ok(),
                    f_zero: caps[5].parse::<f64>().ok(),
                    dual_descriptor: caps[6].parse::<f64>().ok(),
                });
            }
        }
    }
    entries
}

pub fn parse_orbitals(output: &str) -> Vec<OrbitalInfo> {
    let re = Regex::new(
        r"Orb:\s*(\d+)\s+Ene\(au/eV\):\s*([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+Occ:\s*([-+\d.Ee]+)\s+Type:\s*(\S+)",
    )
    .unwrap();

    let mut raw: Vec<OrbitalInfo> = Vec::new();
    for caps in re.captures_iter(output) {
        let index = caps[1].parse::<usize>().unwrap_or(0);
        let energy_hartree = caps[2].parse::<f64>().unwrap_or(0.0);
        let energy_ev = caps[3].parse::<f64>().unwrap_or(0.0);
        let occupancy = caps[4].parse::<f64>().unwrap_or(0.0);
        let spin_type = caps[5].trim().to_string();
        if index > 0 {
            raw.push(OrbitalInfo {
                index,
                energy_hartree,
                energy_ev,
                occupancy,
                spin_type,
                label: None,
            });
        }
    }

    // Deduplicate by index + spin_type
    let mut dedup: Vec<OrbitalInfo> = Vec::new();
    for item in raw {
        if !dedup
            .iter()
            .any(|x| x.index == item.index && x.spin_type == item.spin_type)
        {
            dedup.push(item);
        }
    }

    let homo_idx = dedup
        .iter()
        .filter(|o| o.occupancy > 0.01)
        .map(|o| o.index)
        .max()
        .unwrap_or(0);

    for orb in &mut dedup {
        orb.label = tag_orbital_label(orb.index, homo_idx);
    }
    dedup
}

pub fn parse_charges(output: &str) -> Vec<ChargeEntry> {
    let patterns = [
        Regex::new(r"(?i)Atom\s+(\d+)\(([A-Za-z]+)\s*\).*?Net charge:\s*([-+\d.]+)").unwrap(),
        Regex::new(r"(?i)Atom\s+(\d+)\(([A-Za-z]+)\s*\).*?Atomic charge:\s*([-+\d.]+)").unwrap(),
        Regex::new(r"(?m)^\s*Atom\s+(\d+)\(([A-Za-z]+)\s*\):\s+([-+\d.]+)").unwrap(),
        Regex::new(r"(?i)(?:Hirshfeld|ADCH|CM5|CHELPG|MK|RESP|MBIS|Becke|Gasteiger|AIM)\s+(?:atomic\s+)?charge\s+of\s+atom\s+(\d+)\(([A-Za-z]+)\s*\)\s+is\s+([-+\d.]+)").unwrap(),
        Regex::new(r"(?m)^\s*(\d+)\(([A-Za-z]+)\s*\)\s+([-+\d.]+)\s*$").unwrap(),
        Regex::new(r"(?m)^\s*(\d+)\s+([A-Za-z]{1,3})\s+([-+\d.]+)\s*$").unwrap(),
    ];

    for pat in &patterns {
        let mut found: BTreeMap<usize, ChargeEntry> = BTreeMap::new();
        for caps in pat.captures_iter(output) {
            if let (Ok(idx), Ok(val)) = (caps[1].parse::<usize>(), caps[3].parse::<f64>()) {
                if val.abs() <= 50.0 {
                    found.insert(
                        idx,
                        ChargeEntry {
                            index: idx,
                            element: caps[2].trim().to_string(),
                            charge: val,
                        },
                    );
                }
            }
        }
        if !found.is_empty() {
            return found.into_values().collect();
        }
    }
    Vec::new()
}

pub fn parse_chg_file(content: &str) -> Vec<ChargeEntry> {
    let mut res = Vec::new();
    for (i, line) in content.lines().enumerate() {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 5 {
            // Standard Multiwfn .chg format: Elem X Y Z Charge
            if let Ok(chg) = parts[4].parse::<f64>() {
                res.push(ChargeEntry {
                    index: i + 1,
                    element: parts[0].to_string(),
                    charge: chg,
                });
                continue;
            }
        }
        if parts.len() >= 3 {
            if let (Ok(idx), Ok(chg)) = (parts[0].parse::<usize>(), parts[2].parse::<f64>()) {
                res.push(ChargeEntry {
                    index: idx,
                    element: parts[1].to_string(),
                    charge: chg,
                });
            }
        }
    }
    res
}

pub fn parse_bond_orders(output: &str) -> Vec<BondOrderEntry> {
    let mut entries = Vec::new();

    // Multiwfn standard: #    1:         1(C )    2(H )    0.93327430
    let re1 = Regex::new(
        r"#\s*\d+:\s*(\d+)\(([A-Za-z]+)\s*\)\s+(\d+)\(([A-Za-z]+)\s*\)\s+([-+\d.]+)",
    )
    .unwrap();
    for caps in re1.captures_iter(output) {
        if let (Ok(a1), Ok(a2), Ok(bo)) = (
            caps[1].parse::<usize>(),
            caps[3].parse::<usize>(),
            caps[5].parse::<f64>(),
        ) {
            entries.push(BondOrderEntry {
                atom1_index: a1,
                atom2_index: a2,
                atom1: format!("{}({})", a1, caps[2].trim()),
                atom2: format!("{}({})", a2, caps[4].trim()),
                bond_order: bo,
            });
        }
    }

    if entries.is_empty() {
        let re2 = Regex::new(
            r"(?i)bond order\s+between\s+atom\s+(\d+)\s+and\s+(\d+).*?:\s*([-+\d.]+)",
        )
        .unwrap();
        for caps in re2.captures_iter(output) {
            if let (Ok(a1), Ok(a2), Ok(bo)) = (
                caps[1].parse::<usize>(),
                caps[2].parse::<usize>(),
                caps[3].parse::<f64>(),
            ) {
                entries.push(BondOrderEntry {
                    atom1_index: a1,
                    atom2_index: a2,
                    atom1: format!("Atom {a1}"),
                    atom2: format!("Atom {a2}"),
                    bond_order: bo,
                });
            }
        }
    }

    entries.sort_by(|a, b| {
        b.bond_order
            .partial_cmp(&a.bond_order)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    entries
}

pub fn parse_orbital_composition(output: &str) -> Vec<OrbitalCompositionEntry> {
    let mut items = Vec::new();
    // Matches lines like: " Atom     1(C ) :    52.34 %   s: 12.3%   p: 40.0%" or "   1(C ) :   52.34%"
    let re = Regex::new(r"(?m)^\s*(?:Atom\s+)?(\d+)\(([A-Za-z]+)\s*\)\s*[: ]\s*([\d.]+)\s*%").unwrap();
    for caps in re.captures_iter(output) {
        if let (Ok(idx), Ok(pct)) = (caps[1].parse::<usize>(), caps[3].parse::<f64>()) {
            items.push(OrbitalCompositionEntry {
                atom_index: idx,
                element: caps[2].trim().to_string(),
                percentage: pct,
                s_pct: None,
                p_pct: None,
                d_pct: None,
            });
        }
    }
    items.sort_by(|a, b| {
        b.percentage
            .partial_cmp(&a.percentage)
            .unwrap_or(std::cmp::Ordering::Equal)
    });
    items
}

pub fn parse_critical_points(
    output: &str,
    cps_txt: Option<&str>,
    cpprop_txt: Option<&str>,
) -> Vec<CriticalPoint> {
    let mut cps = Vec::new();
    let label_for = |code: i32| -> &'static str {
        match code {
            1 => "(3,-3) 核临界点 NCP",
            2 => "(3,-1) 键临界点 BCP",
            3 => "(3,+1) 环临界点 RCP",
            4 => "(3,+3) 笼临界点 CCP",
            _ => "临界点 CP",
        }
    };

    if let Some(txt) = cps_txt {
        for line in txt.lines().skip(1) {
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() >= 5 {
                if let (Ok(idx), Ok(xb), Ok(yb), Ok(zb), Ok(code)) = (
                    parts[0].parse::<usize>(),
                    parts[1].parse::<f64>(),
                    parts[2].parse::<f64>(),
                    parts[3].parse::<f64>(),
                    parts[4].parse::<i32>(),
                ) {
                    cps.push(CriticalPoint {
                        index: idx,
                        cp_type_code: code,
                        cp_type_label: label_for(code).to_string(),
                        x: xb * BOHR_TO_ANGSTROM,
                        y: yb * BOHR_TO_ANGSTROM,
                        z: zb * BOHR_TO_ANGSTROM,
                        rho: None,
                        laplacian: None,
                        elf: None,
                    });
                }
            }
        }
    }

    if let Some(prop_txt) = cpprop_txt {
        // Parse density & Laplacian per CP from CPprop.txt
        let block_re = Regex::new(r"(?i)CP\s+(\d+).*?Density of all electrons:\s*([-+\d.Ee]+).*?Laplacian of electron density:\s*([-+\d.Ee]+)").unwrap();
        let norm_text = prop_txt.replace('\r', "");
        for block in norm_text.split("----------------") {
            if let Some(caps) = Regex::new(r"CP\s+(\d+)").unwrap().captures(block) {
                if let Ok(idx) = caps[1].parse::<usize>() {
                    let rho = Regex::new(r"Density of all electrons:\s*([-+\d.Ee]+)")
                        .unwrap()
                        .captures(block)
                        .and_then(|c| c[1].parse::<f64>().ok());
                    let lap = Regex::new(r"Laplacian of electron density:\s*([-+\d.Ee]+)")
                        .unwrap()
                        .captures(block)
                        .and_then(|c| c[1].parse::<f64>().ok());
                    let elf = Regex::new(r"Electron localization function \(ELF\):\s*([-+\d.Ee]+)")
                        .unwrap()
                        .captures(block)
                        .and_then(|c| c[1].parse::<f64>().ok());
                    if let Some(cp) = cps.iter_mut().find(|c| c.index == idx) {
                        cp.rho = rho;
                        cp.laplacian = lap;
                        cp.elf = elf;
                    }
                }
            }
        }
        let _ = block_re;
    }

    if cps.is_empty() {
        let re = Regex::new(
            r"(?i)CP\s*#?\s*(\d+).*?([-+\d.Ee]+)\s+([-+\d.Ee]+)\s+([-+\d.Ee]+)",
        )
        .unwrap();
        for caps in re.captures_iter(output) {
            if let (Ok(idx), Ok(x), Ok(y), Ok(z)) = (
                caps[1].parse::<usize>(),
                caps[2].parse::<f64>(),
                caps[3].parse::<f64>(),
                caps[4].parse::<f64>(),
            ) {
                cps.push(CriticalPoint {
                    index: idx,
                    cp_type_code: 2,
                    cp_type_label: label_for(2).to_string(),
                    x: x * BOHR_TO_ANGSTROM,
                    y: y * BOHR_TO_ANGSTROM,
                    z: z * BOHR_TO_ANGSTROM,
                    rho: None,
                    laplacian: None,
                    elf: None,
                });
            }
        }
    }

    cps
}

pub fn parse_nci_points(content: &str, max_points: usize) -> Vec<NciPoint> {
    let mut pts = Vec::new();
    let mut is_igm_format = false;
    for line in content.lines() {
        let parts: Vec<&str> = line.split_whitespace().collect();
        if parts.len() >= 5 {
            if let (Ok(x), Ok(y), Ok(z), Ok(sign_rho), Ok(rdg)) = (
                parts[0].parse::<f64>(),
                parts[1].parse::<f64>(),
                parts[2].parse::<f64>(),
                parts[3].parse::<f64>(),
                parts[4].parse::<f64>(),
            ) {
                if rdg.is_finite() && sign_rho.is_finite() && rdg <= 3.0 {
                    pts.push(NciPoint {
                        x: x * BOHR_TO_ANGSTROM,
                        y: y * BOHR_TO_ANGSTROM,
                        z: z * BOHR_TO_ANGSTROM,
                        sign_lambda2_rho: sign_rho,
                        rdg,
                        dg_intra: None,
                        dg_total: None,
                    });
                }
            }
        } else if parts.len() == 4 {
            // IGM / IGMH output.txt: dg_inter, dg_intra, dg_total, sign(lambda2)rho
            if let (Ok(dg_inter), Ok(dg_intra), Ok(dg_total), Ok(sign_rho)) = (
                parts[0].parse::<f64>(),
                parts[1].parse::<f64>(),
                parts[2].parse::<f64>(),
                parts[3].parse::<f64>(),
            ) {
                is_igm_format = true;
                if dg_inter.is_finite()
                    && sign_rho.is_finite()
                    && sign_rho.abs() <= 0.08
                    && dg_inter > 1e-6
                {
                    pts.push(NciPoint {
                        x: 0.0,
                        y: 0.0,
                        z: 0.0,
                        sign_lambda2_rho: sign_rho,
                        rdg: dg_inter,
                        dg_intra: Some(dg_intra),
                        dg_total: Some(dg_total),
                    });
                }
            }
        }
    }

    if pts.len() > max_points && max_points > 0 {
        if is_igm_format {
            // For IGM/IGMH, prioritize strong intermolecular interaction spikes
            pts.sort_by(|a, b| {
                b.rdg
                    .partial_cmp(&a.rdg)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
            let top_count = (max_points * 75) / 100;
            let mut sampled = Vec::with_capacity(max_points);
            sampled.extend_from_slice(&pts[..top_count.min(pts.len())]);
            let rest = &pts[top_count.min(pts.len())..];
            let remaining = max_points.saturating_sub(sampled.len());
            if !rest.is_empty() && remaining > 0 {
                let step = (rest.len() / remaining).max(1);
                for p in rest.iter().step_by(step).take(remaining) {
                    sampled.push(p.clone());
                }
            }
            return sampled;
        } else {
            // For NCI/RDG, keep low-RDG spikes preferentially
            pts.sort_by(|a, b| {
                a.rdg
                    .partial_cmp(&b.rdg)
                    .unwrap_or(std::cmp::Ordering::Equal)
            });
            let low_count = (max_points * 7) / 10;
            let mut sampled = Vec::with_capacity(max_points);
            sampled.extend_from_slice(&pts[..low_count.min(pts.len())]);
            let rest = &pts[low_count.min(pts.len())..];
            let remaining = max_points.saturating_sub(sampled.len());
            if !rest.is_empty() && remaining > 0 {
                let step = (rest.len() / remaining).max(1);
                for p in rest.iter().step_by(step).take(remaining) {
                    sampled.push(p.clone());
                }
            }
            return sampled;
        }
    }
    pts
}

pub fn parse_aromaticity(output: &str) -> AromaticityResult {
    let mut res = AromaticityResult::default();
    let nics_re = Regex::new(r"(?i)NICS(?:\(\d+\))?(?:_ZZ)?\s*[:=]\s*([-+\d.]+)").unwrap();
    for caps in nics_re.captures_iter(output) {
        if let Ok(v) = caps[1].parse::<f64>() {
            res.nics_values.push(v);
        }
    }
    let cap_one = |pat: &str| -> Option<f64> {
        Regex::new(pat)
            .ok()?
            .captures(output)?
            .get(1)?
            .as_str()
            .parse::<f64>()
            .ok()
    };
    res.flu = cap_one(r"(?i)FLU(?:-pi)?\s*[:=]\s*([-+\d.]+)");
    res.homa = cap_one(r"(?i)HOMA[cr]?\s*(?:value|index)?\s*[:=]\s*([-+\d.]+)");
    res.bird = cap_one(r"(?i)Bird\s+index\s*[:=]\s*([-+\d.]+)");
    res.mci = cap_one(r"(?i)MCI\s*[:=]\s*([-+\d.]+)");
    res.pdi = cap_one(r"(?i)PDI\s*[:=]\s*([-+\d.]+)");
    res.shannon_index = cap_one(r"(?i)Shannon\s+aromaticity\s+index\s*[:=]\s*([-+\d.]+)");
    res
}

pub fn parse_spectrum_peaks(text: &str, spec_type: &str) -> Vec<SpectrumPeak> {
    let mut peaks = Vec::new();
    let st_upper = spec_type.to_uppercase();

    // 1. Gaussian TDDFT excited states: Excited State   1:   Singlet-A      3.8763 eV  319.85 nm  f=0.3541
    let exc_re = Regex::new(
        r"(?i)Excited\s+State\s+(\d+)\s*:.*?([-+\d.Ee]+)\s+eV\s+([-+\d.Ee]+)\s+nm\s+f=([-+\d.Ee]+)",
    )
    .unwrap();
    if st_upper.contains("UV") || st_upper.contains("ECD") || exc_re.is_match(text) {
        for caps in exc_re.captures_iter(text) {
            if let (Ok(idx), Ok(ev), Ok(nm), Ok(f)) = (
                caps[1].parse::<usize>(),
                caps[2].parse::<f64>(),
                caps[3].parse::<f64>(),
                caps[4].parse::<f64>(),
            ) {
                peaks.push(SpectrumPeak {
                    index: idx,
                    x_value: nm,
                    energy_ev: Some(ev),
                    wavelength_nm: Some(nm),
                    intensity: f,
                    label: format!("S{idx} ({nm:.1} nm, f={f:.4})"),
                });
            }
        }
        if !peaks.is_empty() {
            return peaks;
        }
    }

    // 2. Gaussian Frequency / IR / Raman blocks
    if st_upper.contains("IR") || st_upper.contains("RAMAN") || st_upper.contains("VCD") {
        let mut freqs = Vec::new();
        let mut ir_ints = Vec::new();
        let mut raman_acts = Vec::new();
        for line in text.lines() {
            let trimmed = line.trim();
            if trimmed.starts_with("Frequencies --") {
                for tok in trimmed["Frequencies --".len()..].split_whitespace() {
                    if let Ok(v) = tok.parse::<f64>() {
                        freqs.push(v);
                    }
                }
            } else if trimmed.starts_with("IR Inten    --") {
                for tok in trimmed["IR Inten    --".len()..].split_whitespace() {
                    if let Ok(v) = tok.parse::<f64>() {
                        ir_ints.push(v);
                    }
                }
            } else if trimmed.starts_with("Raman Activ --") {
                for tok in trimmed["Raman Activ --".len()..].split_whitespace() {
                    if let Ok(v) = tok.parse::<f64>() {
                        raman_acts.push(v);
                    }
                }
            }
        }
        for (idx, &freq) in freqs.iter().enumerate() {
            let inten = if st_upper.contains("RAMAN") {
                raman_acts
                    .get(idx)
                    .copied()
                    .or_else(|| ir_ints.get(idx).copied())
                    .unwrap_or(1.0)
            } else {
                ir_ints.get(idx).copied().unwrap_or(1.0)
            };
            peaks.push(SpectrumPeak {
                index: idx + 1,
                x_value: freq,
                energy_ev: None,
                wavelength_nm: None,
                intensity: inten,
                label: format!("Mode {} ({freq:.1} cm⁻¹)", idx + 1),
            });
        }
        if !peaks.is_empty() {
            return peaks;
        }
    }

    // 3. Generic 2-column or 4-column Multiwfn table (skip raw Gaussian logs that aren't tables)
    let is_gaussian_log = text.contains("Entering Link 1") || text.contains("Gaussian, Inc.");
    if !is_gaussian_log {
        for line in text.lines() {
            let t = line.trim();
            if t.is_empty() || t.starts_with('#') || t.starts_with('!') {
                continue;
            }
            let parts: Vec<&str> = t.split_whitespace().collect();
            if parts.len() == 2 {
                if let (Ok(x), Ok(y)) = (parts[0].parse::<f64>(), parts[1].parse::<f64>()) {
                    if x >= 0.0 {
                        let idx = peaks.len() + 1;
                        peaks.push(SpectrumPeak {
                            index: idx,
                            x_value: x,
                            energy_ev: None,
                            wavelength_nm: None,
                            intensity: y,
                            label: format!("Peak {idx}"),
                        });
                    }
                }
            } else if parts.len() >= 4 {
                if let (Ok(idx), Ok(ev), Ok(nm), Ok(inten)) = (
                    parts[0].parse::<usize>(),
                    parts[1].parse::<f64>(),
                    parts[2].parse::<f64>(),
                    parts[3].parse::<f64>(),
                ) {
                    peaks.push(SpectrumPeak {
                        index: idx,
                        x_value: nm,
                        energy_ev: Some(ev),
                        wavelength_nm: Some(nm),
                        intensity: inten,
                        label: format!("State {idx}"),
                    });
                }
            }
        }
    }

    peaks
}

pub fn build_dos_curve(
    orbitals: &[OrbitalInfo],
    fwhm_ev: f64,
    broadening: &str,
    num_points: usize,
) -> DosCurve {
    let fwhm = fwhm_ev.max(0.05);
    let sigma = fwhm / 2.354_820_045;
    let gamma = fwhm * 0.5;
    let is_lorentz = broadening.eq_ignore_ascii_case("lorentzian");

    let mut min_e = -28.0f64;
    let mut max_e = 15.0f64;
    if !orbitals.is_empty() {
        let window: Vec<f64> = orbitals
            .iter()
            .map(|o| o.energy_ev)
            .filter(|&e| e > -45.0 && e < 35.0)
            .collect();
        if let (Some(&lo), Some(&hi)) = (
            window.iter().min_by(|a, b| a.partial_cmp(b).unwrap()),
            window.iter().max_by(|a, b| a.partial_cmp(b).unwrap()),
        ) {
            min_e = (lo - 4.0).max(-45.0);
            max_e = (hi + 4.0).min(35.0);
        }
    }

    let n = num_points.clamp(120, 1200);
    let step = (max_e - min_e) / (n - 1) as f64;
    let mut points = Vec::with_capacity(n);

    for k in 0..n {
        let e = min_e + k as f64 * step;
        let mut occ_sum = 0.0;
        let mut vir_sum = 0.0;
        for orb in orbitals {
            if orb.energy_ev < min_e - 8.0 || orb.energy_ev > max_e + 8.0 {
                continue;
            }
            let de = e - orb.energy_ev;
            let val = if is_lorentz {
                (gamma / std::f64::consts::PI) / (de * de + gamma * gamma)
            } else {
                let norm = 1.0 / (sigma * (2.0 * std::f64::consts::PI).sqrt());
                norm * (-0.5 * (de / sigma).powi(2)).exp()
            };
            if orb.occupancy > 0.01 {
                occ_sum += val;
            } else {
                vir_sum += val;
            }
        }
        points.push(DosPoint {
            energy_ev: (e * 1000.0).round() / 1000.0,
            tdos: occ_sum + vir_sum,
            occupied_dos: occ_sum,
            virtual_dos: vir_sum,
        });
    }

    let mut summary = WavefunctionSummary::default();
    enrich_homo_lumo(&mut summary, orbitals);

    DosCurve {
        points,
        homo_energy_ev: summary.homo_energy_ev,
        lumo_energy_ev: summary.lumo_energy_ev,
        gap_ev: summary.homo_lumo_gap_ev,
        fwhm_ev: fwhm,
        broadening: if is_lorentz {
            "Lorentzian".to_string()
        } else {
            "Gaussian".to_string()
        },
    }
}

pub fn build_spectrum_curve(
    peaks: &[SpectrumPeak],
    spec_type: &str,
    fwhm: f64,
    broadening: &str,
    num_points: usize,
) -> SpectrumCurve {
    let st_upper = spec_type.to_uppercase();
    let is_ir_like = st_upper.contains("IR") || st_upper.contains("RAMAN") || st_upper.contains("VCD");
    let default_fwhm = if is_ir_like { 25.0 } else { 18.0 };
    let w = if fwhm > 0.0 { fwhm } else { default_fwhm };
    let sigma = w / 2.354_820_045;
    let gamma = w * 0.5;
    let is_lorentz = broadening.eq_ignore_ascii_case("lorentzian");

    let (x_min, x_max) = if peaks.is_empty() {
        if is_ir_like {
            (400.0, 4000.0)
        } else {
            (180.0, 750.0)
        }
    } else {
        let min_p = peaks
            .iter()
            .map(|p| p.x_value)
            .fold(f64::INFINITY, f64::min);
        let max_p = peaks
            .iter()
            .map(|p| p.x_value)
            .fold(f64::NEG_INFINITY, f64::max);
        let pad = ((max_p - min_p) * 0.15).max(w * 4.0);
        ((min_p - pad).max(0.0), max_p + pad)
    };

    let n = num_points.clamp(120, 1200);
    let step = (x_max - x_min).max(1.0) / (n - 1) as f64;
    let mut x_values = Vec::with_capacity(n);
    let mut y_values = Vec::with_capacity(n);

    for k in 0..n {
        let x = x_min + k as f64 * step;
        let mut y = 0.0;
        for peak in peaks {
            let dx = x - peak.x_value;
            let kernel = if is_lorentz {
                (gamma * gamma) / (dx * dx + gamma * gamma)
            } else {
                (-0.5 * (dx / sigma).powi(2)).exp()
            };
            y += peak.intensity * kernel;
        }
        x_values.push((x * 100.0).round() / 100.0);
        y_values.push(y);
    }

    let (x_label, y_label) = if is_ir_like {
        ("波数 (cm⁻¹)".to_string(), "相对强度".to_string())
    } else if st_upper.contains("NMR") {
        ("化学位移 (ppm)".to_string(), "信号强度".to_string())
    } else {
        ("波长 (nm)".to_string(), "摩尔吸光系数 / 振子强度".to_string())
    };

    SpectrumCurve {
        x_values,
        y_values,
        peaks: peaks.to_vec(),
        x_label,
        y_label,
        spectrum_type: spec_type.to_string(),
    }
}

pub fn parse_thermochemistry(output: &str) -> ThermochemistryInfo {
    let mut info = ThermochemistryInfo::default();
    let cap_f = |pat: &str| -> Option<f64> {
        Regex::new(pat)
            .ok()?
            .captures(output)?
            .get(1)?
            .as_str()
            .parse::<f64>()
            .ok()
    };
    info.zero_point_energy = cap_f(r"(?i)Zero-point correction=\s*([-+\d.Ee]+)");
    info.thermal_energy = cap_f(r"(?i)Thermal correction to Energy=\s*([-+\d.Ee]+)");
    info.enthalpy = cap_f(r"(?i)Thermal correction to Enthalpy=\s*([-+\d.Ee]+)");
    info.gibbs_free_energy = cap_f(r"(?i)Thermal correction to Gibbs Free Energy=\s*([-+\d.Ee]+)");
    for line in output.lines() {
        let t = line.trim();
        if t.starts_with("Frequencies --") {
            for tok in t["Frequencies --".len()..].split_whitespace() {
                if let Ok(v) = tok.parse::<f64>() {
                    info.frequencies.push(v);
                }
            }
        }
    }
    info
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct AtomDeviation {
    pub atom_index: usize,
    pub element: String,
    pub deviation_angstrom: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct PlanarityResult {
    pub mpp_angstrom: Option<f64>,
    pub sdp_angstrom: Option<f64>,
    pub max_positive_angstrom: Option<f64>,
    pub max_negative_angstrom: Option<f64>,
    pub atom_deviations: Vec<AtomDeviation>,
}

pub fn parse_mpp_planarity(stdout: &str) -> PlanarityResult {
    let mut res = PlanarityResult::default();
    let re_mpp = Regex::new(r"Molecular planarity parameter \(MPP\) is\s+([-+\d.]+)").unwrap();
    let re_sdp = Regex::new(r"Span of deviation from plane \(SDP\) is\s+([-+\d.]+)").unwrap();
    let re_pos = Regex::new(r"Maximal positive deviation.*?:\s+([-+\d.]+)").unwrap();
    let re_neg = Regex::new(r"Maximal negative deviation.*?:\s+([-+\d.]+)").unwrap();
    let re_atom = Regex::new(
        r"Deviation of atom\s+(\d+)\(\s*([A-Za-z]+)\s*\)\s+to the plane:\s+([-+\d.]+)",
    )
    .unwrap();

    if let Some(c) = re_mpp.captures(stdout) {
        res.mpp_angstrom = c[1].parse().ok();
    }
    if let Some(c) = re_sdp.captures(stdout) {
        res.sdp_angstrom = c[1].parse().ok();
    }
    if let Some(c) = re_pos.captures(stdout) {
        res.max_positive_angstrom = c[1].parse().ok();
    }
    if let Some(c) = re_neg.captures(stdout) {
        res.max_negative_angstrom = c[1].parse().ok();
    }
    for cap in re_atom.captures_iter(stdout) {
        if let (Ok(idx), Ok(dev)) = (cap[1].parse::<usize>(), cap[3].parse::<f64>()) {
            res.atom_deviations.push(AtomDeviation {
                atom_index: idx,
                element: cap[2].trim().to_string(),
                deviation_angstrom: dev,
            });
        }
    }
    res
}

#[derive(Debug, Clone, Serialize, Deserialize, Default)]
pub struct EspSurfaceResult {
    pub volume_angstrom3: Option<f64>,
    pub density_g_cm3: Option<f64>,
    pub vs_min_kcal: Option<f64>,
    pub vs_max_kcal: Option<f64>,
    pub overall_area_angstrom2: Option<f64>,
    pub positive_area_angstrom2: Option<f64>,
    pub negative_area_angstrom2: Option<f64>,
    pub sigma2_tot_kcal2: Option<f64>,
    pub sigma2_pos_kcal2: Option<f64>,
    pub sigma2_neg_kcal2: Option<f64>,
    pub balance_nu: Option<f64>,
    pub internal_charge_sep_pi_kcal: Option<f64>,
    pub mpi_ev: Option<f64>,
    pub mpi_kcal: Option<f64>,
    pub nonpolar_area_pct: Option<f64>,
    pub polar_area_pct: Option<f64>,
}

pub fn parse_esp_surface(stdout: &str) -> EspSurfaceResult {
    let mut res = EspSurfaceResult::default();
    let cap_num = |pat: &str| -> Option<f64> {
        Regex::new(pat)
            .ok()?
            .captures(stdout)?
            .get(1)?
            .as_str()
            .parse::<f64>()
            .ok()
    };
    res.volume_angstrom3 = cap_num(r"Volume:\s+[-+\d.]+\s+Bohr\^3\s+\(\s*([-+\d.]+)\s+Angstrom\^3\)");
    res.density_g_cm3 = cap_num(r"Estimated density according to mass and volume.*?:\s+([-+\d.]+)");
    res.vs_min_kcal = cap_num(r"Minimal value:\s+([-+\d.]+)\s+kcal/mol");
    res.vs_max_kcal = cap_num(r"Maximal value:\s+([-+\d.]+)\s+kcal/mol");
    res.overall_area_angstrom2 = cap_num(r"Overall surface area:\s+[-+\d.]+\s+Bohr\^2\s+\(\s*([-+\d.]+)\s+Angstrom\^2\)");
    res.positive_area_angstrom2 = cap_num(r"Positive surface area:\s+[-+\d.]+\s+Bohr\^2\s+\(\s*([-+\d.]+)\s+Angstrom\^2\)");
    res.negative_area_angstrom2 = cap_num(r"Negative surface area:\s+[-+\d.]+\s+Bohr\^2\s+\(\s*([-+\d.]+)\s+Angstrom\^2\)");
    res.sigma2_tot_kcal2 = cap_num(r"Overall variance \(sigma\^2_tot\):\s+[-+\d.]+\s+a\.u\.\^2\s+\(\s*([-+\d.]+)\s+\(kcal/mol\)\^2\)");
    res.sigma2_pos_kcal2 = cap_num(r"Positive variance:\s+[-+\d.]+\s+a\.u\.\^2\s+\(\s*([-+\d.]+)\s+\(kcal/mol\)\^2\)");
    res.sigma2_neg_kcal2 = cap_num(r"Negative variance:\s+[-+\d.]+\s+a\.u\.\^2\s+\(\s*([-+\d.]+)\s+\(kcal/mol\)\^2\)");
    res.balance_nu = cap_num(r"Balance of charges \(nu\):\s+([-+\d.]+)");
    res.internal_charge_sep_pi_kcal = cap_num(r"Internal charge separation \(Pi\):\s+[-+\d.]+\s+a\.u\.\s+\(\s*([-+\d.]+)\s+kcal/mol\)");
    res.mpi_ev = cap_num(r"Molecular polarity index \(MPI\):\s+([-+\d.]+)\s+eV");
    res.mpi_kcal = cap_num(r"Molecular polarity index \(MPI\):\s+[-+\d.]+\s+eV\s+\(\s*([-+\d.]+)\s+kcal/mol\)");
    res.nonpolar_area_pct = cap_num(r"Nonpolar surface area.*?Angstrom\^2\s+\(\s*([-+\d.]+)\s*%\)");
    res.polar_area_pct = cap_num(r"Polar surface area.*?Angstrom\^2\s+\(\s*([-+\d.]+)\s*%\)");
    res
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_orbitals_and_gap() {
        let sample = r#"
 Orb:    12 Ene(au/eV):  -0.296447   -8.0667 Occ: 2.000000 Type:A+B
 Orb:    13 Ene(au/eV):  -0.296447   -8.0667 Occ: 2.000000 Type:A+B
 Orb:    14 Ene(au/eV):   0.025820    0.7026 Occ: 0.000000 Type:A+B
"#;
        let orbs = parse_orbitals(sample);
        assert_eq!(orbs.len(), 3);
        assert_eq!(orbs[1].label.as_deref(), Some("HOMO"));
        assert_eq!(orbs[2].label.as_deref(), Some("LUMO"));
        let mut summary = WavefunctionSummary::default();
        enrich_homo_lumo(&mut summary, &orbs);
        assert!((summary.homo_lumo_gap_ev.unwrap() - 8.7693).abs() < 1e-3);
    }
}
