use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RealspaceFunctionDef {
    pub id: &'static str,
    pub menu_num: u32,
    pub name: &'static str,
    pub formula: &'static str,
    pub description: &'static str,
    pub signed: bool,
}

pub const REALSPACE_FUNCTIONS: &[RealspaceFunctionDef] = &[
    RealspaceFunctionDef {
        id: "density",
        menu_num: 1,
        name: "电子密度 ρ(r)",
        formula: "ρ(r)",
        description: "三维空间电子概率分布，是 AIM 拓扑分析、原子电荷划分及静电势计算的基础物理量。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "gradient_norm",
        menu_num: 2,
        name: "密度梯度模 |∇ρ(r)|",
        formula: "|∇ρ(r)|",
        description: "电子密度空间变化速率，可用于识别原子壳层结构与成键区域边界。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "laplacian",
        menu_num: 3,
        name: "密度拉普拉斯 ∇²ρ(r)",
        formula: "∇²ρ(r)",
        description: "负值表示电子局部聚集（共价键、孤对电子），正值表示电子耗竭（闭壳层作用）。",
        signed: true,
    },
    RealspaceFunctionDef {
        id: "elf",
        menu_num: 9,
        name: "电子定域化函数 ELF",
        formula: "ELF(r) ∈ [0, 1]",
        description: "Becke-Edgecombe 定域化指标，越接近 1 表示电子定域越强（共价键、孤对电子、壳层）。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "lol",
        menu_num: 10,
        name: "局部轨道定位函数 LOL",
        formula: "LOL(r) ∈ [0, 1]",
        description: "基于动能密度的轨道定域化指标，在划分原子壳层与共价区域时图像通常更锐利。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "esp",
        menu_num: 12,
        name: "总静电势 ESP",
        formula: "V_tot(r)",
        description: "核电荷正电势与电子云负电势的叠加，直接反映亲核/亲电反应活性位点与非共价识别。",
        signed: true,
    },
    RealspaceFunctionDef {
        id: "rdg",
        menu_num: 13,
        name: "约化密度梯度 RDG",
        formula: "s(r) = |∇ρ| / [2(3π²)^(1/3) ρ^(4/3)]",
        description: "NCI 弱相互作用可视化核心物理量，在氢键/范德华相互作用区域呈现特征低值尖峰。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "sign_lambda2_rho",
        menu_num: 15,
        name: "sign(λ₂)ρ(r)",
        formula: "sign(λ₂)·ρ(r)",
        description: "以密度 Hessian 第二特征值符号区分弱相互作用性质：负值吸引（氢键），正值排斥（位阻）。",
        signed: true,
    },
    RealspaceFunctionDef {
        id: "ked_k",
        menu_num: 6,
        name: "Hamiltonian 动能密度 K(r)",
        formula: "K(r)",
        description: "共价成键区域通常具有负的 K(r) 或显著正的 |V|/G 特征，用于 Cremer-Kraka 成键判据。",
        signed: true,
    },
    RealspaceFunctionDef {
        id: "ked_g",
        menu_num: 7,
        name: "Lagrange 动能密度 G(r)",
        formula: "G(r) ≥ 0",
        description: "恒非负的局部动能密度，常与势能密度 V(r) 配合表征化学键的共价性与离子性。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "alie",
        menu_num: 18,
        name: "平均局部电离能 ALIE",
        formula: "Ī(r)",
        description: "衡量空间各处电离一个电子所需平均能量，极小值点精准对应亲电进攻最活跃位点。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "iri",
        menu_num: 24,
        name: "相互作用区域指示函数 IRI",
        formula: "IRI(r) = |∇ρ| / ρ^a",
        description: "Lu & Chen 提出的新一代实空间指标，可在同一等值面上同时揭示化学键与弱相互作用。",
        signed: false,
    },
    RealspaceFunctionDef {
        id: "spin_density",
        menu_num: 5,
        name: "自旋密度 ρ_α - ρ_β",
        formula: "ρ_s(r)",
        description: "仅适用于开壳层体系（UHF/UKS/ROHF），揭示未成对单电子的空间自旋极化分布。",
        signed: true,
    },
    RealspaceFunctionDef {
        id: "info_entropy",
        menu_num: 11,
        name: "局部信息熵",
        formula: "S_L(r)",
        description: "电子密度分布的信息论测度，用于研究电子离域与芳香性特征。",
        signed: false,
    },
];

pub struct CommandGenerator;

impl CommandGenerator {
    pub fn grid_code(grid_quality: &str) -> &'static str {
        let lower = grid_quality.trim().to_lowercase();
        match lower.as_str() {
            "coarse" | "low" | "1" | "粗糙" => "1",
            "medium" | "2" | "中等" | "中" => "2",
            "fine" | "high" | "3" | "精细" => "3",
            "ultra" | "ultrafine" | "ultra fine" | "4" | "超精细" => "4",
            _ => "1",
        }
    }

    pub fn wfn_inspect_and_xyz() -> Vec<String> {
        vec![
            "6".into(),
            "3".into(),
            "-1".into(),
            "100".into(),
            "2".into(),
            "2".into(),
            "wavecraft_geom.xyz".into(),
            "0".into(),
            "q".into(),
        ]
    }

    pub fn charge_commands(method: &str) -> Result<Vec<String>, String> {
        let cmds: Vec<&str> = match method {
            "Hirshfeld" => vec!["7", "1", "1", "y", "0", "q"],
            "VDD" => vec!["7", "2", "1", "y", "0", "q"],
            "Mulliken" => vec!["7", "5", "1", "y", "0", "0", "q"],
            "Lowdin" => vec!["7", "6", "lowdin_pop.txt", "y", "0", "q"],
            "SCPA" => vec!["7", "7", "y", "0", "q"],
            "Becke" => vec!["7", "10", "0", "y", "0", "q"],
            "ADCH" => vec!["7", "11", "1", "y", "0", "q"],
            "CHELPG" => vec!["7", "12", "1", "y", "0", "0", "q"],
            "MK" => vec!["7", "13", "1", "y", "0", "0", "q"],
            // AIM basin charges via Menu 17 -> 1 (electron density basins) -> 1 -> 2 (integrate & print charges)
            "AIM" => vec!["17", "1", "1", "1", "2", "0", "-10", "q"],
            "Hirshfeld-I" => vec!["7", "15", "1", "1", "y", "0", "q"],
            "CM5" => vec!["7", "16", "1", "y", "0", "q"],
            "EEM" => vec!["7", "17", "g", "0", "y", "-1", "0", "q"],
            "RESP" => vec!["7", "18", "1", "y", "0", "0", "q"],
            "Gasteiger" => vec!["7", "19", "y", "0", "q"],
            "MBIS" => vec!["7", "20", "1", "y", "0", "q"],
            other => return Err(format!("不支持的电荷计算方法: {other}")),
        };
        Ok(cmds.into_iter().map(String::from).collect())
    }

    pub fn bond_order_commands(method: &str) -> Result<Vec<String>, String> {
        let lower = method.to_lowercase();
        let cmds: Vec<&str> = if lower.contains("mayer") && lower.contains("occ") {
            vec!["9", "6", "n", "0", "q"]
        } else if lower.contains("mayer") {
            vec!["9", "1", "n", "0", "q"]
        } else if lower.contains("wiberg") {
            vec!["9", "3", "n", "0", "q"]
        } else if lower.contains("mulliken") {
            vec!["9", "4", "n", "0", "q"]
        } else if lower.contains("fuzzy") || lower.contains("模糊") {
            vec!["9", "7", "n", "0", "q"]
        } else if lower.contains("laplacian") || lower.contains("拉普拉斯") {
            vec!["9", "8", "n", "0", "q"]
        } else if lower.contains("ibsi") {
            vec!["9", "10", "n", "0", "q"]
        } else if lower.contains("av1245") {
            vec!["9", "11", "n", "0", "q"]
        } else if lower.contains("multicenter") || lower.contains("多中心") {
            vec!["9", "2", "0", "q"]
        } else if lower.contains("nao") {
            vec!["9", "9", "n", "0", "q"]
        } else {
            return Err(format!("不支持的键级方法: {method}"));
        };
        Ok(cmds.into_iter().map(String::from).collect())
    }

    pub fn realspace_cube_commands(func_id: &str, grid_quality: &str) -> Result<Vec<String>, String> {
        let menu_num = if let Ok(n) = func_id.parse::<u32>() {
            n
        } else {
            REALSPACE_FUNCTIONS
                .iter()
                .find(|f| {
                    f.id.eq_ignore_ascii_case(func_id)
                        || f.name.eq_ignore_ascii_case(func_id)
                })
                .map(|f| f.menu_num)
                .ok_or_else(|| format!("未知实空间函数: {func_id}"))?
        };
        let grid = Self::grid_code(grid_quality);
        Ok(vec![
            "5".into(),
            menu_num.to_string(),
            grid.into(),
            "2".into(),
            "0".into(),
            "q".into(),
        ])
    }

    pub fn orbital_cube_commands(orbital_index: usize, grid_quality: &str) -> Vec<String> {
        let grid = Self::grid_code(grid_quality);
        vec![
            "5".into(),
            "4".into(),
            orbital_index.to_string(),
            grid.into(),
            "2".into(),
            "0".into(),
            "q".into(),
        ]
    }

    pub fn orbital_composition_commands(orbital_index: usize, method: &str) -> Vec<String> {
        match method.to_lowercase().as_str() {
            "hirshfeld" => vec![
                "8".into(),
                "8".into(),
                "1".into(),
                orbital_index.to_string(),
                "0".into(),
                "-10".into(),
                "q".into(),
            ],
            "becke" => vec![
                "8".into(),
                "9".into(),
                orbital_index.to_string(),
                "0".into(),
                "-10".into(),
                "q".into(),
            ],
            "scpa" => vec![
                "8".into(),
                "3".into(),
                orbital_index.to_string(),
                "0".into(),
                "-10".into(),
                "q".into(),
            ],
            "nao" => vec![
                "8".into(),
                "7".into(),
                orbital_index.to_string(),
                "0".into(),
                "-10".into(),
                "q".into(),
            ],
            "stout-politzer" | "sp" => vec![
                "8".into(),
                "2".into(),
                orbital_index.to_string(),
                "0".into(),
                "-10".into(),
                "q".into(),
            ],
            _ => vec![
                "8".into(),
                "1".into(),
                orbital_index.to_string(),
                "0".into(),
                "-10".into(),
                "q".into(),
            ],
        }
    }

    pub fn aim_topology_commands() -> Vec<String> {
        vec![
            "2".into(),
            "2".into(),
            "3".into(),
            "7".into(),
            "0".into(),
            "-4".into(),
            "4".into(),
            "0".into(),
            "-10".into(),
            "q".into(),
        ]
    }

    pub fn weak_interaction_commands(
        method: &str,
        grid_quality: &str,
        output_mode: &str,
        fragment_atoms: Option<&str>,
    ) -> Vec<String> {
        let submenu = match method.to_uppercase().as_str() {
            "NCI" => "1",
            "IGM" => "2",
            "MIGM" => "3",
            "IGMH" => "4",
            "DORI" => "5",
            "ARDG" => "6",
            "HIRSHFELD" => "7",
            _ => "1",
        };
        let grid = Self::grid_code(grid_quality);
        if submenu == "7" {
            return vec![
                "20".into(),
                "7".into(),
                "1".into(),
                grid.into(),
                "".into(),
                "".into(),
                "0".into(),
                "0".into(),
                "q".into(),
            ];
        }
        let out_choice = if output_mode.eq_ignore_ascii_case("cube") {
            "1"
        } else {
            "2"
        };
        let mut cmds = vec!["20".to_string(), submenu.to_string()];
        if let Some(frag) = fragment_atoms {
            let trimmed = frag.trim();
            if !trimmed.is_empty() && (submenu == "2" || submenu == "4") {
                cmds.extend(["1".into(), trimmed.into(), "0".into(), "1".into()]);
            } else {
                cmds.push("1".into());
            }
        } else {
            cmds.push("1".into());
        }
        cmds.extend([
            grid.into(),
            out_choice.into(),
            "0".into(),
            "0".into(),
            "q".into(),
        ]);
        cmds
    }

    pub fn aromaticity_commands(method: &str) -> Vec<String> {
        let lower = method.to_lowercase();
        if lower.contains("homa") {
            vec!["25".into(), "6".into(), "".into(), "0".into(), "q".into()]
        } else if lower.contains("flu") {
            vec!["25".into(), "9".into(), "".into(), "0".into(), "q".into()]
        } else if lower.contains("shannon") {
            vec!["25".into(), "7".into(), "0".into(), "q".into()]
        } else if lower.contains("pdi") {
            vec!["25".into(), "8".into(), "".into(), "0".into(), "q".into()]
        } else {
            vec!["25".into(), "1".into(), "0".into(), "q".into()]
        }
    }

    pub fn export_commands(format: &str) -> Result<(Vec<String>, String), String> {
        let (fmt_num, ext) = match format.trim().to_lowercase().as_str() {
            "pdb" => ("1", "pdb"),
            "xyz" => ("2", "xyz"),
            "chg" => ("3", "chg"),
            "wfx" => ("4", "wfx"),
            "wfn" => ("5", "wfn"),
            "molden" => ("6", "molden"),
            "fch" | "fchk" => ("7", "fch"),
            "47" => ("8", "47"),
            "mwfn" => ("32", "mwfn"),
            other => return Err(format!("不支持导出格式: {other}")),
        };
        let filename = format!("wavecraft_export.{ext}");
        let cmds = vec![
            "100".into(),
            "2".into(),
            fmt_num.into(),
            filename.clone(),
            "0".into(),
            "q".into(),
        ];
        Ok((cmds, filename))
    }

    pub fn line_commands(func_id: &str, atom1: usize, atom2: usize) -> Result<Vec<String>, String> {
        let menu_num = if let Ok(n) = func_id.parse::<u32>() {
            n
        } else {
            REALSPACE_FUNCTIONS
                .iter()
                .find(|f| {
                    f.id.eq_ignore_ascii_case(func_id)
                        || f.name.eq_ignore_ascii_case(func_id)
                })
                .map(|f| f.menu_num)
                .ok_or_else(|| format!("未知实空间函数: {func_id}"))?
        };
        Ok(vec![
            "3".into(),
            menu_num.to_string(),
            "1".into(),
            format!("{atom1},{atom2}"),
            "2".into(),
            "0".into(),
            "q".into(),
        ])
    }

    pub fn fuzzy_commands(analysis: &str) -> Vec<String> {
        match analysis.to_lowercase().as_str() {
            "multipole" => vec!["15".into(), "2".into(), "0".into(), "q".into()],
            "pdi" => vec!["15".into(), "5".into(), "0".into(), "q".into()],
            "flu" => vec!["15".into(), "6".into(), "0".into(), "q".into()],
            "polar" | "c6" => vec!["15".into(), "13".into(), "0".into(), "q".into()],
            _ => vec!["15".into(), "4".into(), "n".into(), "0".into(), "q".into()], // LI & DI
        }
    }

    pub fn cdft_commands(mode: &str) -> Vec<String> {
        let sub = match mode.to_lowercase().as_str() {
            "superdeloc" => "8",
            _ => "6", // condensed OW Fukui & dual descriptor
        };
        vec!["22".into(), sub.into(), "0".into(), "q".into()]
    }

    pub fn multipole_commands() -> Vec<String> {
        vec!["300".into(), "5".into(), "0".into(), "q".into()]
    }
}
