use axum::{
    body::Body,
    extract::{Multipart, Path as AxumPath, Query, State},
    http::{header, StatusCode},
    response::{IntoResponse, Response},
    routing::{get, post},
    Json, Router,
};
use serde::{Deserialize, Serialize};
use std::env;
use std::fs;
use std::net::SocketAddr;
use std::path::{Path, PathBuf};
use std::sync::Arc;
use tower_http::cors::{Any, CorsLayer};
use tower_http::services::{ServeDir, ServeFile};
use tracing::{info, warn};

use wavecraft_core::commands::{CommandGenerator, REALSPACE_FUNCTIONS};
use wavecraft_core::config::WaveCraftConfig;
use wavecraft_core::cube::{DualIsosurfaceResult, Slice2DData};
use wavecraft_core::engine::MultiwfnEngine;
use wavecraft_core::menu_catalog::build_full_menu_catalog;
use wavecraft_core::parser::{
    build_dos_curve, build_spectrum_curve, parse_aromaticity, parse_bond_orders, parse_cdft_fukui,
    parse_charges, parse_chg_file, parse_critical_points, parse_fuzzy_lidi, parse_line_txt,
    parse_multipole, parse_nci_points, parse_orbital_composition, parse_orbitals,
    parse_spectrum_peaks, parse_thermochemistry, quick_inspect_file,
};

#[derive(Clone)]
struct AppState {
    engine: Arc<MultiwfnEngine>,
}

#[derive(Serialize)]
struct ApiError {
    error: String,
}

fn err_resp(status: StatusCode, msg: impl Into<String>) -> (StatusCode, Json<ApiError>) {
    (status, Json(ApiError { error: msg.into() }))
}

#[derive(Deserialize)]
struct InspectReq {
    file_path: String,
}

#[derive(Deserialize)]
struct ChargeReq {
    file_path: String,
    method: String,
}

#[derive(Deserialize)]
struct ChargeCompareReq {
    file_path: String,
    methods: Vec<String>,
}

#[derive(Deserialize)]
struct BondReq {
    file_path: String,
    method: String,
}

#[derive(Deserialize)]
struct OrbitalCompReq {
    file_path: String,
    orbital_index: usize,
    method: Option<String>,
}

#[derive(Deserialize)]
struct OrbitalCubeReq {
    file_path: String,
    orbital_index: usize,
    grid_quality: Option<String>,
    isovalue: Option<f64>,
}

#[derive(Deserialize)]
struct RealspaceReq {
    file_path: String,
    func_id: String,
    grid_quality: Option<String>,
    isovalue: Option<f64>,
    plane: Option<String>,
    slice_index: Option<usize>,
}

#[derive(Deserialize)]
struct SliceQuery {
    plane: Option<String>,
    index: Option<usize>,
}

#[derive(Deserialize)]
struct IsoQuery {
    isovalue: Option<f64>,
}

#[derive(Deserialize)]
struct DosReq {
    file_path: String,
    fwhm_ev: Option<f64>,
    broadening: Option<String>,
    num_points: Option<usize>,
}

#[derive(Deserialize)]
struct SpectrumReq {
    file_path: String,
    spec_type: String,
    fwhm: Option<f64>,
    broadening: Option<String>,
    num_points: Option<usize>,
}

#[derive(Deserialize)]
struct WeakReq {
    file_path: String,
    method: String,
    grid_quality: Option<String>,
    output_mode: Option<String>,
    fragment_atoms: Option<String>,
    isovalue: Option<f64>,
}

#[derive(Deserialize)]
struct SimpleFileReq {
    file_path: String,
    method: Option<String>,
}

#[derive(Deserialize)]
struct ExportReq {
    file_path: String,
    format: String,
}

#[derive(Deserialize)]
struct ExecuteRawReq {
    file_path: String,
    commands: Vec<String>,
    task_name: Option<String>,
}

#[derive(Deserialize)]
struct LineReq {
    file_path: String,
    func_id: String,
    atom1: usize,
    atom2: usize,
}

#[derive(Deserialize)]
struct DownloadQuery {
    path: String,
}

async fn health_handler(State(state): State<AppState>) -> impl IntoResponse {
    let cfg = state.engine.get_config().await;
    let mwfn_exists = cfg
        .multiwfn_path
        .as_deref()
        .map(|p| Path::new(p).exists())
        .unwrap_or(false);
    Json(serde_json::json!({
        "status": "ok",
        "version": "4.0.0",
        "engine": "WaveCraft Rust Core",
        "multiwfn_found": mwfn_exists,
        "multiwfn_path": cfg.multiwfn_path,
        "examples_dir": cfg.examples_dir,
        "threads": cfg.default_threads,
    }))
}

async fn get_config_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(state.engine.get_config().await)
}

async fn update_config_handler(
    State(state): State<AppState>,
    Json(cfg): Json<WaveCraftConfig>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    state
        .engine
        .update_config(cfg)
        .await
        .map(Json)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))
}

async fn examples_handler(State(state): State<AppState>) -> impl IntoResponse {
    let cfg = state.engine.get_config().await;
    Json(cfg.list_example_files())
}

async fn menu_catalog_handler() -> impl IntoResponse {
    Json(serde_json::json!({
        "categories": build_full_menu_catalog(),
        "realspace_functions": REALSPACE_FUNCTIONS,
    }))
}

async fn list_tasks_handler(State(state): State<AppState>) -> impl IntoResponse {
    Json(state.engine.list_tasks().await)
}

async fn clear_tasks_handler(State(state): State<AppState>) -> impl IntoResponse {
    state.engine.clear_tasks().await;
    Json(serde_json::json!({ "cleared": true }))
}

async fn upload_handler(
    State(state): State<AppState>,
    mut multipart: Multipart,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let cfg = state.engine.get_config().await;
    let upload_dir = PathBuf::from(&cfg.work_dir_root).join("uploads");
    fs::create_dir_all(&upload_dir)
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, format!("创建上传目录失败: {e}")))?;

    while let Some(field) = multipart
        .next_field()
        .await
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, format!("读取上传流失败: {e}")))?
    {
        let raw_name = field
            .file_name()
            .unwrap_or("uploaded.fchk")
            .to_string();
        let clean_name = Path::new(&raw_name)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("uploaded.fchk")
            .to_string();
        let data = field
            .bytes()
            .await
            .map_err(|e| err_resp(StatusCode::BAD_REQUEST, format!("读取文件字节失败: {e}")))?;
        let dest = upload_dir.join(&clean_name);
        fs::write(&dest, &data)
            .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, format!("保存文件失败: {e}")))?;
        let canonical = fs::canonicalize(&dest).unwrap_or(dest);
        return Ok(Json(serde_json::json!({
            "file_path": canonical.to_string_lossy().to_string(),
            "file_name": clean_name,
            "size_bytes": data.len(),
        })));
    }

    Err(err_resp(StatusCode::BAD_REQUEST, "未收到有效文件字段"))
}

async fn inspect_handler(
    State(state): State<AppState>,
    Json(req): Json<InspectReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    state
        .engine
        .inspect_molecule(&req.file_path)
        .await
        .map(Json)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))
}

async fn charges_handler(
    State(state): State<AppState>,
    Json(req): Json<ChargeReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let cmds = CommandGenerator::charge_commands(&req.method)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))?;
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, &format!("电荷分析 ({})", req.method), 300)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let mut charges = Vec::new();
    for gf in &res.generated_files {
        if gf.to_lowercase().ends_with(".chg") {
            if let Ok(c) = fs::read_to_string(gf) {
                charges = parse_chg_file(&c);
                if !charges.is_empty() {
                    break;
                }
            }
        }
    }
    if charges.is_empty() {
        charges = parse_charges(&res.stdout);
    }

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "method": req.method,
        "charges": charges,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn charges_compare_handler(
    State(state): State<AppState>,
    Json(req): Json<ChargeCompareReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let mut series = Vec::new();
    for method in req.methods.into_iter().take(6) {
        let Ok(cmds) = CommandGenerator::charge_commands(&method) else {
            continue;
        };
        if let Ok(res) = state
            .engine
            .run_multiwfn(&req.file_path, &cmds, &format!("电荷对比 ({method})"), 180)
            .await
        {
            let mut charges = Vec::new();
            for gf in &res.generated_files {
                if gf.to_lowercase().ends_with(".chg") {
                    if let Ok(c) = fs::read_to_string(gf) {
                        charges = parse_chg_file(&c);
                        if !charges.is_empty() {
                            break;
                        }
                    }
                }
            }
            if charges.is_empty() {
                charges = parse_charges(&res.stdout);
            }
            series.push(serde_json::json!({
                "method": method,
                "charges": charges,
                "duration_ms": res.duration_ms,
            }));
        }
    }
    Ok(Json(serde_json::json!({ "series": series })))
}

async fn bonds_handler(
    State(state): State<AppState>,
    Json(req): Json<BondReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let cmds = CommandGenerator::bond_order_commands(&req.method)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))?;
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, &format!("键级分析 ({})", req.method), 300)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let bond_orders = parse_bond_orders(&res.stdout);
    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "method": req.method,
        "bond_orders": bond_orders,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn orbital_comp_handler(
    State(state): State<AppState>,
    Json(req): Json<OrbitalCompReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let method = req.method.unwrap_or_else(|| "Mulliken".to_string());
    let cmds = CommandGenerator::orbital_composition_commands(req.orbital_index, &method);
    let res = state
        .engine
        .run_multiwfn(
            &req.file_path,
            &cmds,
            &format!("轨道 #{} 成分 ({})", req.orbital_index, method),
            120,
        )
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;
    let compositions = parse_orbital_composition(&res.stdout);
    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "orbital_index": req.orbital_index,
        "method": method,
        "compositions": compositions,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn orbital_cube_handler(
    State(state): State<AppState>,
    Json(req): Json<OrbitalCubeReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let grid = req.grid_quality.unwrap_or_else(|| "Coarse".to_string());
    let iso = req.isovalue.unwrap_or(0.03);
    let cmds = CommandGenerator::orbital_cube_commands(req.orbital_index, &grid);
    let res = state
        .engine
        .run_multiwfn(
            &req.file_path,
            &cmds,
            &format!("分子轨道 #{} Cube ({})", req.orbital_index, grid),
            600,
        )
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let Some(cube_id) = res.cube_id.clone() else {
        return Err(err_resp(
            StatusCode::INTERNAL_SERVER_ERROR,
            "Multiwfn 未生成轨道 Cube 文件",
        ));
    };
    let cube = state
        .engine
        .get_cached_cube(&cube_id)
        .await
        .ok_or_else(|| err_resp(StatusCode::INTERNAL_SERVER_ERROR, "Cube 缓存未命中"))?;
    let slice_2d = cube.extract_slice("xy", None);
    let isosurface = cube.extract_dual_isosurface(iso);

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "cube_id": cube_id,
        "cube_path": res.cube_path,
        "duration_ms": res.duration_ms,
        "slice_2d": slice_2d,
        "isosurface": isosurface,
        "stdout": res.stdout,
    })))
}

async fn realspace_handler(
    State(state): State<AppState>,
    Json(req): Json<RealspaceReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let grid = req.grid_quality.unwrap_or_else(|| "Coarse".to_string());
    let iso = req.isovalue.unwrap_or(0.05);
    let plane = req.plane.unwrap_or_else(|| "xy".to_string());
    let cmds = CommandGenerator::realspace_cube_commands(&req.func_id, &grid)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))?;
    let res = state
        .engine
        .run_multiwfn(
            &req.file_path,
            &cmds,
            &format!("实空间函数 {} ({})", req.func_id, grid),
            600,
        )
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let Some(cube_id) = res.cube_id.clone() else {
        return Err(err_resp(
            StatusCode::INTERNAL_SERVER_ERROR,
            "Multiwfn 未生成实空间 Cube 文件",
        ));
    };
    let cube = state
        .engine
        .get_cached_cube(&cube_id)
        .await
        .ok_or_else(|| err_resp(StatusCode::INTERNAL_SERVER_ERROR, "Cube 缓存未命中"))?;
    let slice_2d = cube.extract_slice(&plane, req.slice_index);
    let isosurface = cube.extract_dual_isosurface(iso);

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "cube_id": cube_id,
        "cube_path": res.cube_path,
        "duration_ms": res.duration_ms,
        "slice_2d": slice_2d,
        "isosurface": isosurface,
        "stdout": res.stdout,
    })))
}

async fn cube_slice_handler(
    State(state): State<AppState>,
    AxumPath(cube_id): AxumPath<String>,
    Query(q): Query<SliceQuery>,
) -> Result<Json<Slice2DData>, (StatusCode, Json<ApiError>)> {
    let cube = state
        .engine
        .get_cached_cube(&cube_id)
        .await
        .ok_or_else(|| err_resp(StatusCode::NOT_FOUND, "Cube 缓存不存在或已过期"))?;
    let plane = q.plane.unwrap_or_else(|| "xy".to_string());
    Ok(Json(cube.extract_slice(&plane, q.index)))
}

async fn cube_isosurface_handler(
    State(state): State<AppState>,
    AxumPath(cube_id): AxumPath<String>,
    Query(q): Query<IsoQuery>,
) -> Result<Json<DualIsosurfaceResult>, (StatusCode, Json<ApiError>)> {
    let cube = state
        .engine
        .get_cached_cube(&cube_id)
        .await
        .ok_or_else(|| err_resp(StatusCode::NOT_FOUND, "Cube 缓存不存在或已过期"))?;
    let iso = q.isovalue.unwrap_or(0.03);
    Ok(Json(cube.extract_dual_isosurface(iso)))
}

async fn dos_handler(
    State(state): State<AppState>,
    Json(req): Json<DosReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let fwhm = req.fwhm_ev.unwrap_or(0.6);
    let broadening = req.broadening.unwrap_or_else(|| "Gaussian".to_string());
    let num_points = req.num_points.unwrap_or(400);

    let mut orbitals = Vec::new();
    let mut stdout = String::new();
    let mut duration_ms = 0u128;

    let (_, _, quick_orbs) = quick_inspect_file(Path::new(&req.file_path));
    if !quick_orbs.is_empty() {
        orbitals = quick_orbs;
    }

    if orbitals.is_empty() {
        let cmds = vec!["6".into(), "3".into(), "-1".into(), "q".into()];
        let res = state
            .engine
            .run_multiwfn(&req.file_path, &cmds, "DOS 轨道能级提取", 120)
            .await
            .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;
        orbitals = parse_orbitals(&res.stdout);
        stdout = res.stdout;
        duration_ms = res.duration_ms;
    }

    let curve = build_dos_curve(&orbitals, fwhm, &broadening, num_points);
    Ok(Json(serde_json::json!({
        "curve": curve,
        "orbitals": orbitals,
        "duration_ms": duration_ms,
        "stdout": stdout,
    })))
}

async fn spectrum_handler(
    State(_state): State<AppState>,
    Json(req): Json<SpectrumReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let fwhm = req.fwhm.unwrap_or(0.0);
    let broadening = req.broadening.unwrap_or_else(|| "Gaussian".to_string());
    let num_points = req.num_points.unwrap_or(450);

    let content = fs::read_to_string(&req.file_path)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, format!("读取光谱输入文件失败: {e}")))?;

    let peaks = parse_spectrum_peaks(&content, &req.spec_type);
    let thermo = parse_thermochemistry(&content);
    let curve = build_spectrum_curve(&peaks, &req.spec_type, fwhm, &broadening, num_points);

    Ok(Json(serde_json::json!({
        "curve": curve,
        "thermochemistry": thermo,
        "peak_count": peaks.len(),
    })))
}

async fn weak_interaction_handler(
    State(state): State<AppState>,
    Json(req): Json<WeakReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let grid = req.grid_quality.unwrap_or_else(|| "Coarse".to_string());
    let mode = req.output_mode.unwrap_or_else(|| "scatter".to_string());
    let iso = req.isovalue.unwrap_or(0.5);
    let cmds = CommandGenerator::weak_interaction_commands(
        &req.method,
        &grid,
        &mode,
        req.fragment_atoms.as_deref(),
    );

    let res = state
        .engine
        .run_multiwfn(
            &req.file_path,
            &cmds,
            &format!("弱相互作用 {} ({})", req.method, mode),
            600,
        )
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let mut scatter_points = Vec::new();
    for gf in &res.generated_files {
        let lower = gf.to_lowercase();
        if lower.ends_with("output.txt") {
            if let Ok(txt) = fs::read_to_string(gf) {
                scatter_points = parse_nci_points(&txt, 8000);
                break;
            }
        }
    }

    let mut slice_2d = None;
    let mut isosurface = None;
    if let Some(ref cid) = res.cube_id {
        if let Some(cube) = state.engine.get_cached_cube(cid).await {
            slice_2d = Some(cube.extract_slice("xy", None));
            isosurface = Some(cube.extract_dual_isosurface(iso));
        }
    }

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "method": req.method,
        "mode": mode,
        "scatter_points": scatter_points,
        "cube_id": res.cube_id,
        "slice_2d": slice_2d,
        "isosurface": isosurface,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn aim_handler(
    State(state): State<AppState>,
    Json(req): Json<SimpleFileReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let cmds = CommandGenerator::aim_topology_commands();
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, "AIM 临界点拓扑分析", 300)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let mut cps_txt: Option<String> = None;
    let mut cpprop_txt: Option<String> = None;
    for gf in &res.generated_files {
        let fname = Path::new(gf)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("")
            .to_lowercase();
        if fname == "cps.txt" {
            cps_txt = fs::read_to_string(gf).ok();
        } else if fname.ends_with("cpprop.txt") {
            cpprop_txt = fs::read_to_string(gf).ok();
        }
    }

    let critical_points =
        parse_critical_points(&res.stdout, cps_txt.as_deref(), cpprop_txt.as_deref());

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "critical_points": critical_points,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn aromaticity_handler(
    State(state): State<AppState>,
    Json(req): Json<SimpleFileReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let method = req.method.unwrap_or_else(|| "Shannon".to_string());
    let cmds = CommandGenerator::aromaticity_commands(&method);
    let res = state
        .engine
        .run_multiwfn(
            &req.file_path,
            &cmds,
            &format!("芳香性分析 ({method})"),
            180,
        )
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;
    let aromaticity = parse_aromaticity(&res.stdout);
    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "method": method,
        "aromaticity": aromaticity,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn export_handler(
    State(state): State<AppState>,
    Json(req): Json<ExportReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let (cmds, filename) = CommandGenerator::export_commands(&req.format)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))?;
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, &format!("导出格式 ({})", req.format), 120)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let target = Path::new(&res.run_dir).join(&filename);
    let size_bytes = fs::metadata(&target).map(|m| m.len()).unwrap_or(0);
    let preview = fs::read_to_string(&target)
        .map(|s| s.chars().take(6000).collect::<String>())
        .unwrap_or_default();

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "filename": filename,
        "exported_path": target.to_string_lossy().to_string(),
        "size_bytes": size_bytes,
        "preview": preview,
        "duration_ms": res.duration_ms,
    })))
}

async fn execute_raw_handler(
    State(state): State<AppState>,
    Json(req): Json<ExecuteRawReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let name = req.task_name.unwrap_or_else(|| "自定义 Multiwfn 指令".to_string());
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &req.commands, &name, 600)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let charges = parse_charges(&res.stdout);
    let bond_orders = parse_bond_orders(&res.stdout);
    let mut slice_2d = None;
    let mut isosurface = None;
    if let Some(ref cid) = res.cube_id {
        if let Some(cube) = state.engine.get_cached_cube(cid).await {
            slice_2d = Some(cube.extract_slice("xy", None));
            isosurface = Some(cube.extract_dual_isosurface(0.03));
        }
    }

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
        "stderr": res.stderr,
        "generated_files": res.generated_files,
        "cube_id": res.cube_id,
        "charges": charges,
        "bond_orders": bond_orders,
        "slice_2d": slice_2d,
        "isosurface": isosurface,
    })))
}

async fn line_handler(
    State(state): State<AppState>,
    Json(req): Json<LineReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let cmds = CommandGenerator::line_commands(&req.func_id, req.atom1, req.atom2)
        .map_err(|e| err_resp(StatusCode::BAD_REQUEST, e))?;
    let res = state
        .engine
        .run_multiwfn(
            &req.file_path,
            &cmds,
            &format!("线性质剖面 {} ({}-{})", req.func_id, req.atom1, req.atom2),
            120,
        )
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;

    let mut points = Vec::new();
    for gf in &res.generated_files {
        if gf.to_lowercase().ends_with("line.txt") {
            if let Ok(c) = fs::read_to_string(gf) {
                points = parse_line_txt(&c);
                break;
            }
        }
    }

    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "func_id": req.func_id,
        "atom1": req.atom1,
        "atom2": req.atom2,
        "points": points,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn fuzzy_handler(
    State(state): State<AppState>,
    Json(req): Json<SimpleFileReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let analysis = req.method.unwrap_or_else(|| "li_di".to_string());
    let cmds = CommandGenerator::fuzzy_commands(&analysis);
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, &format!("Fuzzy 原子空间 ({analysis})"), 180)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;
    let fuzzy = parse_fuzzy_lidi(&res.stdout);
    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "analysis": analysis,
        "fuzzy": fuzzy,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn cdft_handler(
    State(state): State<AppState>,
    Json(req): Json<SimpleFileReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let mode = req.method.unwrap_or_else(|| "ow_fukui".to_string());
    let cmds = CommandGenerator::cdft_commands(&mode);
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, &format!("概念 DFT ({mode})"), 120)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;
    let entries = parse_cdft_fukui(&res.stdout);
    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "mode": mode,
        "entries": entries,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn multipole_handler(
    State(state): State<AppState>,
    Json(req): Json<SimpleFileReq>,
) -> Result<impl IntoResponse, (StatusCode, Json<ApiError>)> {
    let cmds = CommandGenerator::multipole_commands();
    let res = state
        .engine
        .run_multiwfn(&req.file_path, &cmds, "电偶极/多极矩与 <R^2>", 120)
        .await
        .map_err(|e| err_resp(StatusCode::INTERNAL_SERVER_ERROR, e))?;
    let multipole = parse_multipole(&res.stdout);
    Ok(Json(serde_json::json!({
        "task_id": res.task_id,
        "multipole": multipole,
        "duration_ms": res.duration_ms,
        "stdout": res.stdout,
    })))
}

async fn download_handler(Query(q): Query<DownloadQuery>) -> impl IntoResponse {
    let path = PathBuf::from(&q.path);
    if !path.exists() || !path.is_file() {
        return Response::builder()
            .status(StatusCode::NOT_FOUND)
            .body(Body::from("File not found"))
            .unwrap();
    }
    let fname = path
        .file_name()
        .and_then(|n| n.to_str())
        .unwrap_or("download.txt")
        .to_string();
    match fs::read(&path) {
        Ok(bytes) => Response::builder()
            .status(StatusCode::OK)
            .header(header::CONTENT_TYPE, "application/octet-stream")
            .header(
                header::CONTENT_DISPOSITION,
                format!("attachment; filename=\"{fname}\""),
            )
            .body(Body::from(bytes))
            .unwrap(),
        Err(e) => Response::builder()
            .status(StatusCode::INTERNAL_SERVER_ERROR)
            .body(Body::from(format!("Read error: {e}")))
            .unwrap(),
    }
}

fn find_frontend_dist() -> Option<PathBuf> {
    let mut candidates = Vec::new();
    if let Ok(cwd) = env::current_dir() {
        candidates.push(cwd.join("frontend").join("dist"));
    }
    if let Ok(exe) = env::current_exe() {
        if let Some(dir) = exe.parent() {
            candidates.push(dir.join("frontend").join("dist"));
            candidates.push(dir.join("dist"));
        }
    }
    candidates.into_iter().find(|p| p.join("index.html").exists())
}

fn launch_desktop_browser(url: &str) {
    #[cfg(windows)]
    {
        let edge_candidates = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        ];
        for edge in edge_candidates {
            if Path::new(edge).exists() {
                if std::process::Command::new(edge)
                    .arg(format!("--app={url}"))
                    .arg("--window-size=1600,980")
                    .spawn()
                    .is_ok()
                {
                    return;
                }
            }
        }
        let _ = std::process::Command::new("cmd")
            .args(["/C", "start", "", url])
            .spawn();
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt()
        .with_env_filter(
            env::var("RUST_LOG").unwrap_or_else(|_| "wavecraft_app=info,wavecraft_core=info".into()),
        )
        .init();

    let args: Vec<String> = env::args().collect();
    let no_open = args.iter().any(|a| a == "--no-open");
    let mut port: u16 = 18420;
    for window in args.windows(2) {
        if window[0] == "--port" {
            if let Ok(p) = window[1].parse::<u16>() {
                port = p;
            }
        }
    }

    let cfg = WaveCraftConfig::load_or_create();
    info!("WaveCraft v4.0 Core 启动中...");
    info!("Multiwfn 路径: {:?}", cfg.multiwfn_path);
    info!("示例目录: {:?}", cfg.examples_dir);

    let engine = Arc::new(MultiwfnEngine::new(cfg));
    let state = AppState { engine };

    let cors = CorsLayer::new()
        .allow_origin(Any)
        .allow_methods(Any)
        .allow_headers(Any);

    let api_routes = Router::new()
        .route("/health", get(health_handler))
        .route("/config", get(get_config_handler).post(update_config_handler))
        .route("/examples", get(examples_handler))
        .route("/menu-catalog", get(menu_catalog_handler))
        .route("/tasks", get(list_tasks_handler).delete(clear_tasks_handler))
        .route("/upload", post(upload_handler))
        .route("/inspect", post(inspect_handler))
        .route("/charges", post(charges_handler))
        .route("/charges/compare", post(charges_compare_handler))
        .route("/bonds", post(bonds_handler))
        .route("/orbital/composition", post(orbital_comp_handler))
        .route("/orbital/cube", post(orbital_cube_handler))
        .route("/realspace", post(realspace_handler))
        .route("/cube/{cube_id}/slice", get(cube_slice_handler))
        .route("/cube/{cube_id}/isosurface", get(cube_isosurface_handler))
        .route("/dos", post(dos_handler))
        .route("/spectrum", post(spectrum_handler))
        .route("/weak-interaction", post(weak_interaction_handler))
        .route("/aim", post(aim_handler))
        .route("/aromaticity", post(aromaticity_handler))
        .route("/line", post(line_handler))
        .route("/fuzzy", post(fuzzy_handler))
        .route("/cdft", post(cdft_handler))
        .route("/multipole", post(multipole_handler))
        .route("/export", post(export_handler))
        .route("/execute-raw", post(execute_raw_handler))
        .route("/download", get(download_handler));

    let mut app = Router::new().nest("/api", api_routes).with_state(state);

    if let Some(dist_dir) = find_frontend_dist() {
        info!("托管静态前端目录: {:?}", dist_dir);
        let index_file = dist_dir.join("index.html");
        let serve = ServeDir::new(dist_dir).not_found_service(ServeFile::new(index_file));
        app = app.fallback_service(serve);
    } else {
        warn!("未检测到 frontend/dist，仅启动 API 模式 (请先执行前端构建或使用 Vite 开发服务器)");
    }

    let app = app.layer(cors);
    let addr = SocketAddr::from(([127, 0, 0, 1], port));
    let url = format!("http://127.0.0.1:{port}");
    info!("WaveCraft 服务监听于 {url}");

    let listener = tokio::net::TcpListener::bind(addr)
        .await
        .expect("绑定本地端口失败");

    if !no_open {
        let launch_url = url.clone();
        tokio::spawn(async move {
            tokio::time::sleep(std::time::Duration::from_millis(350)).await;
            launch_desktop_browser(&launch_url);
        });
    }

    axum::serve(listener, app)
        .await
        .expect("WaveCraft HTTP 服务运行失败");
}
