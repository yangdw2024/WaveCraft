use chrono::Utc;
use encoding_rs::GBK;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Stdio;
use std::sync::Arc;
use std::time::{Duration, Instant};
use tokio::io::AsyncWriteExt;
use tokio::process::Command;
use tokio::sync::RwLock;
use uuid::Uuid;

use crate::commands::CommandGenerator;
use crate::config::WaveCraftConfig;
use crate::cube::CubeData;
use crate::parser::{
    compute_bonds, compute_formula, enrich_homo_lumo, parse_orbitals, parse_wfn_info,
    parse_xyz_text, quick_inspect_file, Atom3D, BondLink, OrbitalInfo, WavefunctionSummary,
};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum TaskStatus {
    Running,
    Completed,
    Failed,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TaskRecord {
    pub id: String,
    pub name: String,
    pub input_file: String,
    pub commands: Vec<String>,
    pub status: TaskStatus,
    pub started_at: String,
    pub completed_at: Option<String>,
    pub duration_ms: Option<u128>,
    pub error: Option<String>,
    pub generated_files: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CalculationResult {
    pub task_id: String,
    pub duration_ms: u128,
    pub stdout: String,
    pub stderr: String,
    pub run_dir: String,
    pub generated_files: Vec<String>,
    pub cube_id: Option<String>,
    pub cube_path: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MoleculeInspection {
    pub file_path: String,
    pub file_name: String,
    pub extension: String,
    pub file_size: u64,
    pub atoms: Vec<Atom3D>,
    pub bonds: Vec<BondLink>,
    pub summary: WavefunctionSummary,
    pub orbitals: Vec<OrbitalInfo>,
    pub raw_output: String,
}

pub struct MultiwfnEngine {
    pub config: RwLock<WaveCraftConfig>,
    pub tasks: RwLock<Vec<TaskRecord>>,
    pub cube_cache: RwLock<HashMap<String, Arc<CubeData>>>,
}

impl MultiwfnEngine {
    pub fn new(config: WaveCraftConfig) -> Self {
        Self {
            config: RwLock::new(config),
            tasks: RwLock::new(Vec::new()),
            cube_cache: RwLock::new(HashMap::new()),
        }
    }

    pub async fn get_config(&self) -> WaveCraftConfig {
        self.config.read().await.clone()
    }

    pub async fn update_config(&self, mut new_cfg: WaveCraftConfig) -> Result<WaveCraftConfig, String> {
        if new_cfg.work_dir_root.trim().is_empty() {
            new_cfg.work_dir_root = WaveCraftConfig::default_work_dir_root();
        }
        let _ = fs::create_dir_all(&new_cfg.work_dir_root);
        new_cfg.save()?;
        let mut guard = self.config.write().await;
        *guard = new_cfg.clone();
        Ok(new_cfg)
    }

    pub async fn list_tasks(&self) -> Vec<TaskRecord> {
        self.tasks.read().await.clone()
    }

    pub async fn clear_tasks(&self) {
        self.tasks.write().await.clear();
    }

    pub async fn cache_cube(&self, cube_id: String, cube: CubeData) -> Arc<CubeData> {
        let arc = Arc::new(cube);
        let mut cache = self.cube_cache.write().await;
        if cache.len() > 24 {
            if let Some(oldest_key) = cache.keys().next().cloned() {
                cache.remove(&oldest_key);
            }
        }
        cache.insert(cube_id, arc.clone());
        arc
    }

    pub async fn get_cached_cube(&self, cube_id: &str) -> Option<Arc<CubeData>> {
        self.cube_cache.read().await.get(cube_id).cloned()
    }

    pub async fn inspect_molecule(&self, file_path: &str) -> Result<MoleculeInspection, String> {
        let path = Path::new(file_path);
        if !path.exists() {
            return Err(format!("文件不存在: {file_path}"));
        }

        let file_name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or(file_path)
            .to_string();
        let extension = path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_lowercase();
        let file_size = fs::metadata(path).map(|m| m.len()).unwrap_or(0);

        {
            let mut cfg = self.config.write().await;
            cfg.add_recent_file(file_path);
            let _ = cfg.save();
        }

        let (mut atoms, mut summary, mut orbitals) = quick_inspect_file(path);
        let mut raw_output = String::new();

        // For wavefunction formats (not plain gaussian .out/.log or .gjf), call Multiwfn to get exact orbitals & XYZ
        let is_wfn_binary_or_rich = matches!(
            extension.as_str(),
            "fch" | "fchk" | "wfn" | "wfx" | "mwfn" | "molden" | "pdb" | "xyz" | "gjf"
        );
        if is_wfn_binary_or_rich {
            if let Ok(res) = self
                .run_multiwfn(
                    file_path,
                    &CommandGenerator::wfn_inspect_and_xyz(),
                    &format!("解析波函数: {file_name}"),
                    60,
                )
                .await
            {
                raw_output = res.stdout.clone();
                let parsed_summary = parse_wfn_info(&res.stdout);
                merge_summary(&mut summary, parsed_summary);

                let parsed_orbitals = parse_orbitals(&res.stdout);
                if !parsed_orbitals.is_empty() {
                    orbitals = parsed_orbitals;
                    enrich_homo_lumo(&mut summary, &orbitals);
                }

                let xyz_path = Path::new(&res.run_dir).join("wavecraft_geom.xyz");
                if xyz_path.exists() {
                    if let Ok(xyz_content) = fs::read_to_string(&xyz_path) {
                        let parsed_atoms = parse_xyz_text(&xyz_content);
                        if !parsed_atoms.is_empty() {
                            atoms = parsed_atoms;
                        }
                    }
                }
            }
        }

        if summary.formula.is_none() && !atoms.is_empty() {
            summary.formula = Some(compute_formula(&atoms));
        }
        if summary.num_atoms.is_none() && !atoms.is_empty() {
            summary.num_atoms = Some(atoms.len());
        }

        let bonds = compute_bonds(&atoms);

        Ok(MoleculeInspection {
            file_path: file_path.to_string(),
            file_name,
            extension,
            file_size,
            atoms,
            bonds,
            summary,
            orbitals,
            raw_output,
        })
    }

    pub async fn run_multiwfn(
        &self,
        input_file: &str,
        commands: &[String],
        task_name: &str,
        timeout_secs: u64,
    ) -> Result<CalculationResult, String> {
        let cfg = self.config.read().await.clone();
        let mwfn_path = cfg
            .multiwfn_path
            .as_deref()
            .filter(|p| Path::new(p).exists())
            .ok_or_else(|| {
                "未找到 Multiwfn.exe，请在系统设置中配置正确路径或设置 Multiwfnpath 环境变量"
                    .to_string()
            })?;

        if !Path::new(input_file).exists() {
            return Err(format!("输入文件不存在: {input_file}"));
        }

        let task_id = Uuid::new_v4().to_string()[..8].to_string();
        let run_dir = PathBuf::from(&cfg.work_dir_root).join(format!("run_{task_id}"));
        fs::create_dir_all(&run_dir).map_err(|e| format!("无法创建计算工作目录: {e}"))?;

        // Copy Multiwfn settings.ini with isilent=1 so CLI runs never block on Dislin GUI popups
        if let Some(mwfn_parent) = Path::new(mwfn_path).parent() {
            let src_ini = mwfn_parent.join("settings.ini");
            if src_ini.exists() {
                if let Ok(ini_text) = fs::read_to_string(&src_ini) {
                    let silent_ini = ini_text.replace("isilent= 0", "isilent= 1");
                    let _ = fs::write(run_dir.join("settings.ini"), silent_ini);
                }
            }
        }

        let started_at = Utc::now().to_rfc3339();
        let task_record = TaskRecord {
            id: task_id.clone(),
            name: task_name.to_string(),
            input_file: input_file.to_string(),
            commands: commands.to_vec(),
            status: TaskStatus::Running,
            started_at,
            completed_at: None,
            duration_ms: None,
            error: None,
            generated_files: Vec::new(),
        };
        {
            let mut list = self.tasks.write().await;
            list.insert(0, task_record);
            if list.len() > 100 {
                list.truncate(100);
            }
        }

        let start = Instant::now();
        let mut cmd = Command::new(mwfn_path);
        cmd.arg(input_file)
            .current_dir(&run_dir)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped());

        #[cfg(windows)]
        {
            const CREATE_NO_WINDOW: u32 = 0x0800_0000;
            cmd.creation_flags(CREATE_NO_WINDOW);
        }

        let mut child = cmd.spawn().map_err(|e| {
            let msg = format!("启动 Multiwfn.exe 失败: {e}");
            msg
        })?;

        let joined = format!("{}\n", commands.join("\n"));
        let (encoded, _, _) = GBK.encode(&joined);
        if let Some(mut stdin) = child.stdin.take() {
            let _ = stdin.write_all(&encoded).await;
            let _ = stdin.flush().await;
            drop(stdin);
        }

        let wait_res =
            tokio::time::timeout(Duration::from_secs(timeout_secs), child.wait_with_output())
                .await;

        let duration_ms = start.elapsed().as_millis();

        let output = match wait_res {
            Ok(Ok(out)) => out,
            Ok(Err(e)) => {
                let err_msg = format!("等待 Multiwfn 进程失败: {e}");
                self.finish_task_failed(&task_id, duration_ms, &err_msg)
                    .await;
                return Err(err_msg);
            }
            Err(_) => {
                let err_msg = format!("Multiwfn 计算超时（超过 {timeout_secs} 秒）");
                self.finish_task_failed(&task_id, duration_ms, &err_msg)
                    .await;
                return Err(err_msg);
            }
        };

        let (stdout_cow, _, _) = GBK.decode(&output.stdout);
        let (stderr_cow, _, _) = GBK.decode(&output.stderr);
        let stdout = stdout_cow.into_owned();
        let stderr = stderr_cow.into_owned();

        if !output.status.success() {
            let code = output.status.code().unwrap_or(-1);
            let tail: String = stdout
                .lines()
                .rev()
                .take(15)
                .collect::<Vec<_>>()
                .into_iter()
                .rev()
                .collect::<Vec<_>>()
                .join("\n");
            let err_msg = format!("Multiwfn 非零退出码 ({code}): {stderr}\n{tail}");
            self.finish_task_failed(&task_id, duration_ms, &err_msg)
                .await;
            return Err(err_msg);
        }

        let mut generated_files = Vec::new();
        let mut cube_path: Option<String> = None;
        if let Ok(entries) = fs::read_dir(&run_dir) {
            for entry in entries.flatten() {
                let p = entry.path();
                if p.is_file() {
                    let s = p.to_string_lossy().to_string();
                    let lower = s.to_lowercase();
                    if lower.ends_with(".cub") || lower.ends_with(".cube") {
                        cube_path = Some(s.clone());
                    }
                    generated_files.push(s);
                }
            }
        }

        let mut cube_id: Option<String> = None;
        if let Some(ref cpath) = cube_path {
            if let Ok(cube) = CubeData::from_file(cpath) {
                let cid = format!("cube_{task_id}");
                self.cache_cube(cid.clone(), cube).await;
                cube_id = Some(cid);
            }
        }

        self.finish_task_ok(&task_id, duration_ms, generated_files.clone())
            .await;

        Ok(CalculationResult {
            task_id,
            duration_ms,
            stdout,
            stderr,
            run_dir: run_dir.to_string_lossy().to_string(),
            generated_files,
            cube_id,
            cube_path,
        })
    }

    async fn finish_task_ok(&self, task_id: &str, duration_ms: u128, files: Vec<String>) {
        let mut list = self.tasks.write().await;
        if let Some(t) = list.iter_mut().find(|x| x.id == task_id) {
            t.status = TaskStatus::Completed;
            t.completed_at = Some(Utc::now().to_rfc3339());
            t.duration_ms = Some(duration_ms);
            t.generated_files = files;
        }
    }

    async fn finish_task_failed(&self, task_id: &str, duration_ms: u128, err: &str) {
        let mut list = self.tasks.write().await;
        if let Some(t) = list.iter_mut().find(|x| x.id == task_id) {
            t.status = TaskStatus::Failed;
            t.completed_at = Some(Utc::now().to_rfc3339());
            t.duration_ms = Some(duration_ms);
            t.error = Some(err.to_string());
        }
    }
}

fn merge_summary(dst: &mut WavefunctionSummary, src: WavefunctionSummary) {
    if src.formula.is_some() {
        dst.formula = src.formula;
    }
    if src.total_energy_hartree.is_some() {
        dst.total_energy_hartree = src.total_energy_hartree;
    }
    if src.virial_ratio.is_some() {
        dst.virial_ratio = src.virial_ratio;
    }
    if src.num_electrons.is_some() {
        dst.num_electrons = src.num_electrons;
    }
    if src.alpha_electrons.is_some() {
        dst.alpha_electrons = src.alpha_electrons;
    }
    if src.beta_electrons.is_some() {
        dst.beta_electrons = src.beta_electrons;
    }
    if src.num_basis_functions.is_some() {
        dst.num_basis_functions = src.num_basis_functions;
    }
    if src.num_gtfs.is_some() {
        dst.num_gtfs = src.num_gtfs;
    }
    if src.num_atoms.is_some() {
        dst.num_atoms = src.num_atoms;
    }
    if src.net_charge.is_some() {
        dst.net_charge = src.net_charge;
    }
    if src.multiplicity.is_some() {
        dst.multiplicity = src.multiplicity;
    }
    if src.molecular_weight.is_some() {
        dst.molecular_weight = src.molecular_weight;
    }
    if src.point_group.is_some() {
        dst.point_group = src.point_group;
    }
    if src.wavefunction_type.is_some() {
        dst.wavefunction_type = src.wavefunction_type;
    }
    if src.occ_start.is_some() {
        dst.occ_start = src.occ_start;
    }
    if src.occ_end.is_some() {
        dst.occ_end = src.occ_end;
    }
    if src.title.is_some() {
        dst.title = src.title;
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[tokio::test]
    async fn test_real_multiwfn_ch3cl_pipeline() {
        let example_path = r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\examples\CH3Cl.fchk";
        let mwfn_path = r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\Multiwfn.exe";
        if !Path::new(example_path).exists() || !Path::new(mwfn_path).exists() {
            return;
        }
        let mut cfg = WaveCraftConfig::default();
        cfg.multiwfn_path = Some(mwfn_path.to_string());
        let engine = MultiwfnEngine::new(cfg);

        let insp = engine
            .inspect_molecule(example_path)
            .await
            .expect("inspect CH3Cl.fchk should succeed");
        assert_eq!(insp.atoms.len(), 5);
        assert_eq!(insp.bonds.len(), 4);
        assert_eq!(insp.orbitals.len(), 40);
        assert!(insp.summary.homo_lumo_gap_ev.is_some());

        let chg_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::charge_commands("ADCH").unwrap(),
                "test_adch",
                60,
            )
            .await
            .expect("ADCH charge calculation should succeed");
        let chg_file = chg_res
            .generated_files
            .iter()
            .find(|f| f.to_lowercase().ends_with(".chg"))
            .expect("ADCH should write .chg file");
        let charges = crate::parser::parse_chg_file(&fs::read_to_string(chg_file).unwrap());
        assert_eq!(charges.len(), 5);

        let orb_comp_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::orbital_composition_commands(13, "Hirshfeld"),
                "test_hirshfeld_orb_comp",
                60,
            )
            .await
            .expect("Hirshfeld orbital composition should succeed");
        let comps = crate::parser::parse_orbital_composition(&orb_comp_res.stdout);
        assert_eq!(comps.len(), 5);

        let aim_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::aim_topology_commands(),
                "test_aim",
                60,
            )
            .await
            .expect("AIM topology should succeed");
        let cps_file = aim_res
            .generated_files
            .iter()
            .find(|f| f.to_lowercase().ends_with("cps.txt"))
            .expect("AIM should produce CPs.txt");
        let cps = crate::parser::parse_critical_points(
            &aim_res.stdout,
            Some(&fs::read_to_string(cps_file).unwrap()),
            None,
        );
        assert!(cps.len() >= 5);

        let nci_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::weak_interaction_commands("NCI", "Coarse", "scatter", None),
                "test_nci_scatter",
                60,
            )
            .await
            .expect("NCI scatter should succeed");
        let nci_file = nci_res
            .generated_files
            .iter()
            .find(|f| f.to_lowercase().ends_with("output.txt"))
            .expect("NCI should produce output.txt");
        let nci_pts = crate::parser::parse_nci_points(&fs::read_to_string(nci_file).unwrap(), 1000);
        assert!(!nci_pts.is_empty());

        let (exp_cmds, exp_name) = CommandGenerator::export_commands("xyz").unwrap();
        let exp_res = engine
            .run_multiwfn(example_path, &exp_cmds, "test_export_xyz", 60)
            .await
            .expect("Export xyz should succeed");
        assert!(Path::new(&exp_res.run_dir).join(exp_name).exists());

        let uv_file = r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\examples\spectra\indigo_TD-B3LYP_water.out";
        if Path::new(uv_file).exists() {
            let peaks = crate::parser::parse_spectrum_peaks(
                &fs::read_to_string(uv_file).unwrap(),
                "UV-Vis",
            );
            assert!(!peaks.is_empty());
            let curve = crate::parser::build_spectrum_curve(&peaks, "UV-Vis", 20.0, "Gaussian", 200);
            assert_eq!(curve.x_values.len(), 200);
        }

        let ir_file = r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\examples\spectra\NH3BF3_freq.out";
        if Path::new(ir_file).exists() {
            let peaks = crate::parser::parse_spectrum_peaks(
                &fs::read_to_string(ir_file).unwrap(),
                "IR",
            );
            assert!(!peaks.is_empty());
            let curve = crate::parser::build_spectrum_curve(&peaks, "IR", 25.0, "Gaussian", 200);
            assert_eq!(curve.x_values.len(), 200);
        }

        let dos_curve = crate::parser::build_dos_curve(&insp.orbitals, 0.6, "Gaussian", 250);
        assert_eq!(dos_curve.points.len(), 250);
        assert!(dos_curve.gap_ev.is_some());

        let examples = engine.get_config().await.list_example_files();
        assert!(
            examples.iter().any(|e| e.name == "NH3BF3_freq.out"),
            "NH3BF3_freq.out should be included in listed examples"
        );
        assert!(
            examples.iter().any(|e| e.name == "indigo_TD-B3LYP_water.out"),
            "indigo_TD-B3LYP_water.out should be included in listed examples"
        );

        // Verify new Line (Menu 3), Fuzzy (Menu 15), CDFT (Menu 22), Multipole (Menu 300-5), and full catalog
        let line_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::line_commands("density", 1, 5).unwrap(),
                "test_line",
                60,
            )
            .await
            .expect("Line profile should succeed");
        let line_file = line_res
            .generated_files
            .iter()
            .find(|f| f.to_lowercase().ends_with("line.txt"))
            .expect("Line should produce *line.txt");
        let line_pts = crate::parser::parse_line_txt(&fs::read_to_string(line_file).unwrap());
        assert!(!line_pts.is_empty());

        let fuzzy_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::fuzzy_commands("li_di"),
                "test_fuzzy",
                60,
            )
            .await
            .expect("Fuzzy LI/DI should succeed");
        let fuzzy = crate::parser::parse_fuzzy_lidi(&fuzzy_res.stdout);
        assert_eq!(fuzzy.li_entries.len(), 5);

        let cdft_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::cdft_commands("ow_fukui"),
                "test_cdft",
                60,
            )
            .await
            .expect("CDFT OW Fukui should succeed");
        assert!(!cdft_res.stdout.is_empty());

        let mp_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::multipole_commands(),
                "test_multipole",
                60,
            )
            .await
            .expect("Multipole should succeed");
        assert!(!mp_res.stdout.is_empty());

        let catalog = crate::menu_catalog::build_full_menu_catalog();
        assert!(catalog.len() >= 25, "Catalog should cover all major Multiwfn menus");

        let cube_res = engine
            .run_multiwfn(
                example_path,
                &CommandGenerator::realspace_cube_commands("density", "Coarse").unwrap(),
                "test_density_cube",
                60,
            )
            .await
            .expect("Density cube generation should succeed");
        let cid = cube_res.cube_id.expect("cube_id must be cached");
        let cube = engine.get_cached_cube(&cid).await.expect("cube in cache");
        let iso = cube.extract_dual_isosurface(0.05);
        assert!(iso.positive.triangle_count > 100);
    }
}
