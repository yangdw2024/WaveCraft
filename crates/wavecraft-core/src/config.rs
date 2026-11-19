use serde::{Deserialize, Serialize};
use std::env;
use std::fs;
use std::path::{Path, PathBuf};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WaveCraftConfig {
    pub multiwfn_path: Option<String>,
    pub examples_dir: Option<String>,
    pub default_threads: usize,
    pub work_dir_root: String,
    pub recent_files: Vec<String>,
    pub theme: String,
    pub language: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ExampleFileInfo {
    pub name: String,
    pub path: String,
    pub relative_path: String,
    pub category: String,
    pub extension: String,
    pub size_bytes: u64,
}

impl Default for WaveCraftConfig {
    fn default() -> Self {
        Self {
            multiwfn_path: Self::detect_multiwfn_path(),
            examples_dir: Self::detect_examples_dir(),
            default_threads: 8,
            work_dir_root: Self::default_work_dir_root(),
            recent_files: Vec::new(),
            theme: "quantum-obsidian".to_string(),
            language: "zh-CN".to_string(),
        }
    }
}

impl WaveCraftConfig {
    pub fn default_work_dir_root() -> String {
        let dir = env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join("workspace_runs");
        let _ = fs::create_dir_all(&dir);
        dir.to_string_lossy().to_string()
    }

    pub fn config_file_path() -> PathBuf {
        env::current_dir()
            .unwrap_or_else(|_| PathBuf::from("."))
            .join("config")
            .join("wavecraft_config.json")
    }

    pub fn load_or_create() -> Self {
        let path = Self::config_file_path();
        if path.exists() {
            if let Ok(content) = fs::read_to_string(&path) {
                if let Ok(mut cfg) = serde_json::from_str::<WaveCraftConfig>(&content) {
                    if cfg.multiwfn_path.as_ref().map_or(true, |p| !Path::new(p).exists()) {
                        cfg.multiwfn_path = Self::detect_multiwfn_path();
                    }
                    if cfg.examples_dir.as_ref().map_or(true, |p| !Path::new(p).exists()) {
                        cfg.examples_dir = Self::detect_examples_dir();
                    }
                    if cfg.work_dir_root.trim().is_empty() {
                        cfg.work_dir_root = Self::default_work_dir_root();
                    }
                    let _ = fs::create_dir_all(&cfg.work_dir_root);
                    return cfg;
                }
            }
        }
        let cfg = Self::default();
        let _ = cfg.save();
        cfg
    }

    pub fn save(&self) -> Result<(), String> {
        let path = Self::config_file_path();
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|e| format!("无法创建配置目录: {e}"))?;
        }
        let json =
            serde_json::to_string_pretty(self).map_err(|e| format!("序列化配置失败: {e}"))?;
        fs::write(&path, json).map_err(|e| format!("写入配置失败: {e}"))?;
        Ok(())
    }

    pub fn detect_multiwfn_path() -> Option<String> {
        let mut candidates: Vec<PathBuf> = Vec::new();
        if let Ok(env_path) = env::var("Multiwfnpath") {
            if !env_path.trim().is_empty() {
                candidates.push(PathBuf::from(env_path));
            }
        }
        if let Ok(exe_dir) = env::current_exe() {
            if let Some(dir) = exe_dir.parent() {
                candidates.push(dir.join("Multiwfn.exe"));
                candidates.push(dir.join("Multiwfn_3.8_bin_Win64").join("Multiwfn.exe"));
            }
        }
        if let Ok(cwd) = env::current_dir() {
            candidates.push(cwd.join("Multiwfn_3.8_bin_Win64").join("Multiwfn.exe"));
            if let Some(parent) = cwd.parent() {
                candidates.push(parent.join("Multiwfn_3.8_bin_Win64").join("Multiwfn.exe"));
            }
        }
        candidates.push(PathBuf::from(
            r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\Multiwfn.exe",
        ));

        for candidate in candidates {
            if candidate.exists() && candidate.is_file() {
                return Some(
                    fs::canonicalize(&candidate)
                        .unwrap_or(candidate)
                        .to_string_lossy()
                        .to_string(),
                );
            }
        }
        None
    }

    pub fn detect_examples_dir() -> Option<String> {
        if let Some(mwfn_path) = Self::detect_multiwfn_path() {
            if let Some(parent) = Path::new(&mwfn_path).parent() {
                let examples = parent.join("examples");
                if examples.exists() && examples.is_dir() {
                    return Some(examples.to_string_lossy().to_string());
                }
            }
        }
        let fallback = PathBuf::from(r"D:\Multiwfn\Multiwfn_3.8_bin_Win64\examples");
        if fallback.exists() {
            return Some(fallback.to_string_lossy().to_string());
        }
        None
    }

    pub fn add_recent_file(&mut self, file_path: &str) {
        self.recent_files.retain(|x| x != file_path);
        self.recent_files.insert(0, file_path.to_string());
        if self.recent_files.len() > 16 {
            self.recent_files.truncate(16);
        }
    }

    pub fn list_example_files(&self) -> Vec<ExampleFileInfo> {
        let Some(dir) = &self.examples_dir else {
            return Vec::new();
        };
        let root = Path::new(dir);
        if !root.exists() {
            return Vec::new();
        }
        let supported_exts = [
            "fch", "fchk", "wfn", "wfx", "mwfn", "molden", "pdb", "xyz", "cub", "cube", "out",
            "log", "gjf", "com", "mol", "cml",
        ];
        let mut items = Vec::new();
        collect_examples(root, root, 0, &supported_exts, &mut items);

        // Prioritize featured root molecules and spectroscopy/excited examples
        items.sort_by(|a, b| {
            let a_prio = example_priority(&a.relative_path);
            let b_prio = example_priority(&b.relative_path);
            a_prio
                .cmp(&b_prio)
                .then_with(|| a.relative_path.cmp(&b.relative_path))
        });
        items
    }
}

fn example_priority(rel: &str) -> u8 {
    let lower = rel.to_lowercase();
    if lower == "ch3cl.fchk"
        || lower == "benzene.fch"
        || lower == "h2o.fch"
        || lower == "oxirane.fchk"
        || lower == "co.fch"
    {
        return 0;
    }
    if !lower.contains('\\') && !lower.contains('/') {
        return 1;
    }
    if lower.starts_with("spectra") || lower.starts_with("excit") {
        return 2;
    }
    3
}

fn collect_examples(
    root: &Path,
    current: &Path,
    depth: usize,
    supported_exts: &[&str],
    out: &mut Vec<ExampleFileInfo>,
) {
    if depth > 2 || out.len() >= 1000 {
        return;
    }
    let Ok(entries) = fs::read_dir(current) else {
        return;
    };
    let mut dirs = Vec::new();
    let mut files = Vec::new();
    for entry in entries.flatten() {
        let path = entry.path();
        if path.is_dir() {
            dirs.push(path);
        } else if path.is_file() {
            files.push((path, entry.metadata().map(|m| m.len()).unwrap_or(0)));
        }
    }

    for (path, size_bytes) in files {
        let ext = path
            .extension()
            .and_then(|e| e.to_str())
            .unwrap_or("")
            .to_lowercase();
        if !supported_exts.contains(&ext.as_str()) {
            continue;
        }
        let rel = path
            .strip_prefix(root)
            .unwrap_or(&path)
            .to_string_lossy()
            .replace('\\', "/");
        let category = if let Some((first, _)) = rel.split_once('/') {
            first.to_string()
        } else {
            "基础波函数".to_string()
        };
        let name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("")
            .to_string();
        out.push(ExampleFileInfo {
            name,
            path: path.to_string_lossy().to_string(),
            relative_path: rel,
            category,
            extension: ext,
            size_bytes,
        });
    }

    dirs.sort_by(|a, b| {
        let an = a.file_name().and_then(|n| n.to_str()).unwrap_or("").to_lowercase();
        let bn = b.file_name().and_then(|n| n.to_str()).unwrap_or("").to_lowercase();
        let prio = |n: &str| -> u8 {
            if n == "spectra" || n == "excit" || n == "dos" {
                0
            } else {
                1
            }
        };
        prio(&an).cmp(&prio(&bn)).then_with(|| an.cmp(&bn))
    });

    for path in dirs {
        let folder_name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("")
            .to_lowercase();
        if folder_name == "atomwfn" || folder_name == "scripts" || folder_name == "wfntmp" {
            continue;
        }
        collect_examples(root, &path, depth + 1, supported_exts, out);
    }
}
