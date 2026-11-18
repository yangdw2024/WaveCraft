use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

pub const BOHR_TO_ANGSTROM: f64 = 0.529_177_210_903;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CubeAtom {
    pub index: usize,
    pub atomic_number: u8,
    pub symbol: String,
    pub charge: f64,
    pub x: f64,
    pub y: f64,
    pub z: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CubeMetadata {
    pub title: String,
    pub comment: String,
    pub dimensions: [usize; 3],
    pub origin_angstrom: [f64; 3],
    pub step_angstrom: [[f64; 3]; 3],
    pub bounds_angstrom: [[f64; 2]; 3],
    pub min_value: f64,
    pub max_value: f64,
    pub atom_count: usize,
    pub voxel_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ProjectedAtom2D {
    pub index: usize,
    pub symbol: String,
    pub u: f64,
    pub v: f64,
    pub dist_to_plane: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Slice2DData {
    pub plane: String,
    pub slice_index: usize,
    pub max_index: usize,
    pub slice_coord_angstrom: f64,
    pub width: usize,
    pub height: usize,
    pub extent: [f64; 4], // [u_min, u_max, v_min, v_max]
    pub u_label: String,
    pub v_label: String,
    pub values: Vec<f32>,
    pub slice_min: f64,
    pub slice_max: f64,
    pub global_min: f64,
    pub global_max: f64,
    pub projected_atoms: Vec<ProjectedAtom2D>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IsosurfaceMesh {
    pub positions: Vec<f32>,
    pub normals: Vec<f32>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub colors: Option<Vec<f32>>,
    pub indices: Vec<u32>,
    pub vertex_count: usize,
    pub triangle_count: usize,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DualIsosurfaceResult {
    pub isovalue: f64,
    pub has_negative: bool,
    pub positive: IsosurfaceMesh,
    pub negative: Option<IsosurfaceMesh>,
    pub metadata: CubeMetadata,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub color_scale: Option<String>,
    #[serde(default, skip_serializing_if = "Option::is_none")]
    pub color_range: Option<[f64; 2]>,
}

#[derive(Debug, Clone)]
pub struct CubeData {
    pub title: String,
    pub comment: String,
    pub dims: [usize; 3],
    pub origin: [f64; 3],     // Angstrom
    pub axes: [[f64; 3]; 3],  // Angstrom per step
    pub atoms: Vec<CubeAtom>, // Coordinates in Angstrom
    pub values: Vec<f32>,     // Row-major (ix, iy, iz) where iz is fastest
    pub min_value: f64,
    pub max_value: f64,
}

pub fn bgr_color_map(val: f64) -> [f32; 3] {
    // Multiwfn & VMD BGR colormap for sign(lambda2)rho
    // Blue (attractive, <= -0.04) -> Green (van der Waals, ~0.0) -> Red (steric, >= 0.02)
    if val <= -0.04 {
        [0.05, 0.25, 0.95]
    } else if val < 0.0 {
        let t = ((val + 0.04) / 0.04) as f32; // 0.0 at -0.04, 1.0 at 0.0
        let r = 0.05 * (1.0 - t) + 0.05 * t;
        let g = 0.25 * (1.0 - t) + 0.85 * t;
        let b = 0.95 * (1.0 - t) + 0.15 * t;
        [r, g, b]
    } else if val < 0.02 {
        let t = (val / 0.02) as f32; // 0.0 at 0.0, 1.0 at 0.02
        let r = 0.05 * (1.0 - t) + 0.95 * t;
        let g = 0.85 * (1.0 - t) + 0.15 * t;
        let b = 0.15 * (1.0 - t) + 0.12 * t;
        [r, g, b]
    } else {
        [0.95, 0.12, 0.12]
    }
}

pub fn bwr_color_map(val: f64) -> [f32; 3] {
    // Blue-White-Red colormap for ESP (-25 to +25 kcal/mol)
    let clamped = val.clamp(-25.0, 25.0);
    if clamped < 0.0 {
        let t = ((clamped + 25.0) / 25.0) as f32; // 0.0 at -25, 1.0 at 0
        let r = 0.10 * (1.0 - t) + 0.95 * t;
        let g = 0.30 * (1.0 - t) + 0.95 * t;
        let b = 0.95 * (1.0 - t) + 0.95 * t;
        [r, g, b]
    } else {
        let t = (clamped / 25.0) as f32; // 0.0 at 0, 1.0 at +25
        let r = 0.95 * (1.0 - t) + 0.95 * t;
        let g = 0.95 * (1.0 - t) + 0.18 * t;
        let b = 0.95 * (1.0 - t) + 0.18 * t;
        [r, g, b]
    }
}

impl CubeData {
    pub fn from_file(path: impl AsRef<Path>) -> Result<Self, String> {
        let content = fs::read_to_string(path.as_ref())
            .map_err(|e| format!("无法读取 Cube 文件: {e}"))?;
        Self::parse(&content)
    }

    pub fn parse(content: &str) -> Result<Self, String> {
        let mut lines = content.lines();
        let title = lines.next().unwrap_or("").trim().to_string();
        let comment = lines.next().unwrap_or("").trim().to_string();

        let line3 = lines.next().ok_or("Cube 文件第 3 行缺失")?;
        let p3: Vec<&str> = line3.split_whitespace().collect();
        if p3.len() < 4 {
            return Err("Cube 文件头原子行格式无效".to_string());
        }
        let natoms_raw: i64 = p3[0].parse().map_err(|_| "Cube 原子数无效")?;
        let has_mo_header = natoms_raw < 0;
        let natoms = natoms_raw.unsigned_abs() as usize;

        let mut origin_raw = [
            p3[1].parse::<f64>().unwrap_or(0.0),
            p3[2].parse::<f64>().unwrap_or(0.0),
            p3[3].parse::<f64>().unwrap_or(0.0),
        ];

        let mut dims = [0usize; 3];
        let mut axes = [[0.0f64; 3]; 3];
        let mut unit_in_angstrom = false;

        for i in 0..3 {
            let line = lines.next().ok_or("Cube 文件网格轴行缺失")?;
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 4 {
                return Err("Cube 网格轴定义无效".to_string());
            }
            let n_raw: i64 = parts[0].parse().map_err(|_| "Cube 网格维数无效")?;
            if i == 0 && n_raw < 0 {
                unit_in_angstrom = true;
            }
            dims[i] = n_raw.unsigned_abs() as usize;
            let scale = if unit_in_angstrom {
                1.0
            } else {
                BOHR_TO_ANGSTROM
            };
            axes[i] = [
                parts[1].parse::<f64>().unwrap_or(0.0) * scale,
                parts[2].parse::<f64>().unwrap_or(0.0) * scale,
                parts[3].parse::<f64>().unwrap_or(0.0) * scale,
            ];
        }

        let scale = if unit_in_angstrom {
            1.0
        } else {
            BOHR_TO_ANGSTROM
        };
        for v in &mut origin_raw {
            *v *= scale;
        }

        let mut atoms = Vec::with_capacity(natoms);
        for idx in 0..natoms {
            let line = lines.next().ok_or("Cube 文件原子坐标行不足")?;
            let parts: Vec<&str> = line.split_whitespace().collect();
            if parts.len() < 5 {
                continue;
            }
            let z: u8 = parts[0].parse::<i64>().unwrap_or(0).clamp(0, 118) as u8;
            let charge: f64 = parts[1].parse().unwrap_or(z as f64);
            let x = parts[2].parse::<f64>().unwrap_or(0.0) * scale;
            let y = parts[3].parse::<f64>().unwrap_or(0.0) * scale;
            let z_coord = parts[4].parse::<f64>().unwrap_or(0.0) * scale;
            atoms.push(CubeAtom {
                index: idx + 1,
                atomic_number: z,
                symbol: crate::parser::atomic_symbol(z).to_string(),
                charge,
                x,
                y,
                z: z_coord,
            });
        }

        let expected = dims[0] * dims[1] * dims[2];
        if expected == 0 {
            return Err("Cube 网格尺寸不能为 0".to_string());
        }

        let mut remaining_tokens = Vec::with_capacity(expected + 16);
        for line in lines {
            for tok in line.split_whitespace() {
                remaining_tokens.push(tok);
            }
        }

        let mut token_offset = 0usize;
        if has_mo_header && !remaining_tokens.is_empty() {
            if let Ok(nmo) = remaining_tokens[0].parse::<usize>() {
                token_offset = (1 + nmo).min(remaining_tokens.len());
            }
        }

        let mut values = Vec::with_capacity(expected);
        let mut min_val = f64::INFINITY;
        let mut max_val = f64::NEG_INFINITY;

        for tok in &remaining_tokens[token_offset..] {
            if values.len() >= expected {
                break;
            }
            if let Ok(v) = tok.parse::<f64>() {
                if v < min_val {
                    min_val = v;
                }
                if v > max_val {
                    max_val = v;
                }
                values.push(v as f32);
            }
        }

        if values.len() < expected {
            values.resize(expected, 0.0);
        }
        if !min_val.is_finite() {
            min_val = 0.0;
            max_val = 0.0;
        }

        Ok(Self {
            title,
            comment,
            dims,
            origin: origin_raw,
            axes,
            atoms,
            values,
            min_value: min_val,
            max_value: max_val,
        })
    }

    #[inline]
    pub fn get(&self, ix: usize, iy: usize, iz: usize) -> f32 {
        let ny = self.dims[1];
        let nz = self.dims[2];
        self.values[(ix * ny + iy) * nz + iz]
    }

    pub fn to_cube_format(&self) -> String {
        let mut out = String::new();
        out.push_str(&format!("{}\n", if self.title.is_empty() { "WaveCraft Cube Export" } else { &self.title }));
        out.push_str(&format!("{}\n", if self.comment.is_empty() { "Generated by WaveCraft Core" } else { &self.comment }));
        out.push_str(&format!("{:5} {:12.6} {:12.6} {:12.6}\n", self.atoms.len(), self.origin[0], self.origin[1], self.origin[2]));
        out.push_str(&format!("{:5} {:12.6} {:12.6} {:12.6}\n", self.dims[0], self.axes[0][0], self.axes[0][1], self.axes[0][2]));
        out.push_str(&format!("{:5} {:12.6} {:12.6} {:12.6}\n", self.dims[1], self.axes[1][0], self.axes[1][1], self.axes[1][2]));
        out.push_str(&format!("{:5} {:12.6} {:12.6} {:12.6}\n", self.dims[2], self.axes[2][0], self.axes[2][1], self.axes[2][2]));
        for a in &self.atoms {
            out.push_str(&format!("{:5} {:12.6} {:12.6} {:12.6} {:12.6}\n", a.atomic_number, a.charge, a.x, a.y, a.z));
        }
        let mut count = 0;
        for val in &self.values {
            out.push_str(&format!(" {:13.5E}", val));
            count += 1;
            if count % 6 == 0 {
                out.push('\n');
            }
        }
        if count % 6 != 0 {
            out.push('\n');
        }
        out
    }

    #[inline]
    pub fn voxel_pos(&self, ix: f64, iy: f64, iz: f64) -> [f64; 3] {
        [
            self.origin[0] + ix * self.axes[0][0] + iy * self.axes[1][0] + iz * self.axes[2][0],
            self.origin[1] + ix * self.axes[0][1] + iy * self.axes[1][1] + iz * self.axes[2][1],
            self.origin[2] + ix * self.axes[0][2] + iy * self.axes[1][2] + iz * self.axes[2][2],
        ]
    }

    pub fn metadata(&self) -> CubeMetadata {
        let p0 = self.voxel_pos(0.0, 0.0, 0.0);
        let p1 = self.voxel_pos(
            (self.dims[0].saturating_sub(1)) as f64,
            (self.dims[1].saturating_sub(1)) as f64,
            (self.dims[2].saturating_sub(1)) as f64,
        );
        CubeMetadata {
            title: self.title.clone(),
            comment: self.comment.clone(),
            dimensions: self.dims,
            origin_angstrom: self.origin,
            step_angstrom: self.axes,
            bounds_angstrom: [
                [p0[0].min(p1[0]), p0[0].max(p1[0])],
                [p0[1].min(p1[1]), p0[1].max(p1[1])],
                [p0[2].min(p1[2]), p0[2].max(p1[2])],
            ],
            min_value: self.min_value,
            max_value: self.max_value,
            atom_count: self.atoms.len(),
            voxel_count: self.values.len(),
        }
    }

    pub fn extract_slice(&self, plane: &str, index: Option<usize>) -> Slice2DData {
        let [nx, ny, nz] = self.dims;
        let p0 = self.voxel_pos(0.0, 0.0, 0.0);
        let p_max = self.voxel_pos(
            (nx.saturating_sub(1)) as f64,
            (ny.saturating_sub(1)) as f64,
            (nz.saturating_sub(1)) as f64,
        );

        let plane_lower = plane.to_lowercase();
        let (width, height, max_idx, slice_idx, slice_coord, extent, u_label, v_label, values) =
            match plane_lower.as_str() {
                "xz" => {
                    let max_i = ny.saturating_sub(1);
                    let iy = index.unwrap_or(ny / 2).min(max_i);
                    let mut vals = Vec::with_capacity(nx * nz);
                    for iz in 0..nz {
                        for ix in 0..nx {
                            vals.push(self.get(ix, iy, iz));
                        }
                    }
                    let coord = self.voxel_pos(0.0, iy as f64, 0.0)[1];
                    (
                        nx,
                        nz,
                        max_i,
                        iy,
                        coord,
                        [p0[0], p_max[0], p0[2], p_max[2]],
                        "X (Å)".to_string(),
                        "Z (Å)".to_string(),
                        vals,
                    )
                }
                "yz" => {
                    let max_i = nx.saturating_sub(1);
                    let ix = index.unwrap_or(nx / 2).min(max_i);
                    let mut vals = Vec::with_capacity(ny * nz);
                    for iz in 0..nz {
                        for iy in 0..ny {
                            vals.push(self.get(ix, iy, iz));
                        }
                    }
                    let coord = self.voxel_pos(ix as f64, 0.0, 0.0)[0];
                    (
                        ny,
                        nz,
                        max_i,
                        ix,
                        coord,
                        [p0[1], p_max[1], p0[2], p_max[2]],
                        "Y (Å)".to_string(),
                        "Z (Å)".to_string(),
                        vals,
                    )
                }
                _ => {
                    let max_i = nz.saturating_sub(1);
                    let iz = index.unwrap_or(nz / 2).min(max_i);
                    let mut vals = Vec::with_capacity(nx * ny);
                    for iy in 0..ny {
                        for ix in 0..nx {
                            vals.push(self.get(ix, iy, iz));
                        }
                    }
                    let coord = self.voxel_pos(0.0, 0.0, iz as f64)[2];
                    (
                        nx,
                        ny,
                        max_i,
                        iz,
                        coord,
                        [p0[0], p_max[0], p0[1], p_max[1]],
                        "X (Å)".to_string(),
                        "Y (Å)".to_string(),
                        vals,
                    )
                }
            };

        let mut slice_min = f64::INFINITY;
        let mut slice_max = f64::NEG_INFINITY;
        for &v in &values {
            let vf = v as f64;
            if vf < slice_min {
                slice_min = vf;
            }
            if vf > slice_max {
                slice_max = vf;
            }
        }
        if !slice_min.is_finite() {
            slice_min = 0.0;
            slice_max = 0.0;
        }

        let projected_atoms = self
            .atoms
            .iter()
            .map(|a| {
                let (u, v, dist) = match plane_lower.as_str() {
                    "xz" => (a.x, a.z, (a.y - slice_coord).abs()),
                    "yz" => (a.y, a.z, (a.x - slice_coord).abs()),
                    _ => (a.x, a.y, (a.z - slice_coord).abs()),
                };
                ProjectedAtom2D {
                    index: a.index,
                    symbol: a.symbol.clone(),
                    u,
                    v,
                    dist_to_plane: dist,
                }
            })
            .collect();

        Slice2DData {
            plane: if plane_lower == "xz" || plane_lower == "yz" {
                plane_lower
            } else {
                "xy".to_string()
            },
            slice_index: slice_idx,
            max_index: max_idx,
            slice_coord_angstrom: slice_coord,
            width,
            height,
            extent,
            u_label,
            v_label,
            values,
            slice_min,
            slice_max,
            global_min: self.min_value,
            global_max: self.max_value,
            projected_atoms,
        }
    }

    pub fn sample_at(&self, x: f64, y: f64, z: f64) -> f64 {
        let dx = x - self.origin[0];
        let dy = y - self.origin[1];
        let dz = z - self.origin[2];

        let step_x = self.axes[0][0];
        let step_y = self.axes[1][1];
        let step_z = self.axes[2][2];
        if step_x.abs() < 1e-12 || step_y.abs() < 1e-12 || step_z.abs() < 1e-12 {
            return 0.0;
        }

        let gx = (dx / step_x).clamp(0.0, (self.dims[0].saturating_sub(1)) as f64);
        let gy = (dy / step_y).clamp(0.0, (self.dims[1].saturating_sub(1)) as f64);
        let gz = (dz / step_z).clamp(0.0, (self.dims[2].saturating_sub(1)) as f64);

        let x0 = (gx.floor() as usize).min(self.dims[0] - 1);
        let x1 = (x0 + 1).min(self.dims[0] - 1);
        let fx = (gx - x0 as f64) as f32;

        let y0 = (gy.floor() as usize).min(self.dims[1] - 1);
        let y1 = (y0 + 1).min(self.dims[1] - 1);
        let fy = (gy - y0 as f64) as f32;

        let z0 = (gz.floor() as usize).min(self.dims[2] - 1);
        let z1 = (z0 + 1).min(self.dims[2] - 1);
        let fz = (gz - z0 as f64) as f32;

        let c000 = self.get(x0, y0, z0);
        let c100 = self.get(x1, y0, z0);
        let c010 = self.get(x0, y1, z0);
        let c110 = self.get(x1, y1, z0);
        let c001 = self.get(x0, y0, z1);
        let c101 = self.get(x1, y0, z1);
        let c011 = self.get(x0, y1, z1);
        let c111 = self.get(x1, y1, z1);

        let c00 = c000 * (1.0 - fx) + c100 * fx;
        let c10 = c010 * (1.0 - fx) + c110 * fx;
        let c01 = c001 * (1.0 - fx) + c101 * fx;
        let c11 = c011 * (1.0 - fx) + c111 * fx;

        let c0 = c00 * (1.0 - fy) + c10 * fy;
        let c1 = c01 * (1.0 - fy) + c11 * fy;

        (c0 * (1.0 - fz) + c1 * fz) as f64
    }

    pub fn extract_dual_isosurface(&self, isovalue: f64) -> DualIsosurfaceResult {
        self.extract_mapped_isosurface(isovalue, None, "dual")
    }

    pub fn extract_mapped_isosurface(
        &self,
        isovalue: f64,
        color_cube: Option<&CubeData>,
        color_mode: &str,
    ) -> DualIsosurfaceResult {
        let iso = isovalue.abs().max(1e-6);
        let positive = self.marching_cubes(iso as f32, false, color_cube, Some(color_mode));
        let has_negative = color_cube.is_none() && self.min_value <= -iso;
        let negative = if has_negative {
            let neg_mesh = self.marching_cubes(iso as f32, true, None, None);
            if neg_mesh.triangle_count > 0 {
                Some(neg_mesh)
            } else {
                None
            }
        } else {
            None
        };

        let (scale_str, range_val) = if color_cube.is_some() {
            if color_mode.eq_ignore_ascii_case("bwr") {
                (Some("bwr".to_string()), Some([-25.0, 25.0]))
            } else {
                (Some("bgr".to_string()), Some([-0.04, 0.02]))
            }
        } else {
            (None, None)
        };

        DualIsosurfaceResult {
            isovalue: iso,
            has_negative: negative.is_some(),
            positive,
            negative,
            metadata: self.metadata(),
            color_scale: scale_str,
            color_range: range_val,
        }
    }

    fn gradient_at(&self, ix: usize, iy: usize, iz: usize) -> [f32; 3] {
        let [nx, ny, nz] = self.dims;
        let gx = if ix > 0 && ix + 1 < nx {
            (self.get(ix + 1, iy, iz) - self.get(ix - 1, iy, iz)) * 0.5
        } else if ix + 1 < nx {
            self.get(ix + 1, iy, iz) - self.get(ix, iy, iz)
        } else if ix > 0 {
            self.get(ix, iy, iz) - self.get(ix - 1, iy, iz)
        } else {
            0.0
        };
        let gy = if iy > 0 && iy + 1 < ny {
            (self.get(ix, iy + 1, iz) - self.get(ix, iy - 1, iz)) * 0.5
        } else if iy + 1 < ny {
            self.get(ix, iy + 1, iz) - self.get(ix, iy, iz)
        } else if iy > 0 {
            self.get(ix, iy, iz) - self.get(ix, iy - 1, iz)
        } else {
            0.0
        };
        let gz = if iz > 0 && iz + 1 < nz {
            (self.get(ix, iy, iz + 1) - self.get(ix, iy, iz - 1)) * 0.5
        } else if iz + 1 < nz {
            self.get(ix, iy, iz + 1) - self.get(ix, iy, iz)
        } else if iz > 0 {
            self.get(ix, iy, iz) - self.get(ix, iy, iz - 1)
        } else {
            0.0
        };
        // Normal points outward (towards smaller magnitude)
        [-gx, -gy, -gz]
    }

    fn marching_cubes(
        &self,
        isovalue: f32,
        negate: bool,
        color_cube: Option<&CubeData>,
        color_mode: Option<&str>,
    ) -> IsosurfaceMesh {
        let [nx, ny, nz] = self.dims;
        if nx < 2 || ny < 2 || nz < 2 {
            return IsosurfaceMesh {
                positions: Vec::new(),
                normals: Vec::new(),
                colors: None,
                indices: Vec::new(),
                vertex_count: 0,
                triangle_count: 0,
            };
        }

        // Stride down large grids (> 160 on any axis) for ultra-responsive WebGL meshes
        let max_dim = nx.max(ny).max(nz);
        let stride = if max_dim > 160 { 2usize } else { 1usize };

        let mut positions: Vec<f32> = Vec::new();
        let mut normals: Vec<f32> = Vec::new();
        let mut colors: Vec<f32> = Vec::new();
        let mut indices: Vec<u32> = Vec::new();

        // Corner offsets in (ix, iy, iz) following Paul Bourke convention
        const CORNER_OFFSETS: [[usize; 3]; 8] = [
            [0, 0, 0],
            [1, 0, 0],
            [1, 1, 0],
            [0, 1, 0],
            [0, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 1, 1],
        ];

        const EDGE_CONN: [[usize; 2]; 12] = [
            [0, 1],
            [1, 2],
            [2, 3],
            [3, 0],
            [4, 5],
            [5, 6],
            [6, 7],
            [7, 4],
            [0, 4],
            [1, 5],
            [2, 6],
            [3, 7],
        ];

        let sign = if negate { -1.0f32 } else { 1.0f32 };

        let mut ix = 0;
        while ix + stride < nx {
            let mut iy = 0;
            while iy + stride < ny {
                let mut iz = 0;
                while iz + stride < nz {
                    let mut vals = [0.0f32; 8];
                    let mut cube_index = 0usize;

                    for c in 0..8 {
                        let gx = ix + CORNER_OFFSETS[c][0] * stride;
                        let gy = iy + CORNER_OFFSETS[c][1] * stride;
                        let gz = iz + CORNER_OFFSETS[c][2] * stride;
                        let v = self.get(gx, gy, gz) * sign;
                        vals[c] = v;
                        if v < isovalue {
                            cube_index |= 1 << c;
                        }
                    }

                    let edges = EDGE_TABLE[cube_index];
                    if edges == 0 {
                        iz += stride;
                        continue;
                    }

                    let mut c_pos = [[0.0f32; 3]; 8];
                    let mut c_norm = [[0.0f32; 3]; 8];
                    for c in 0..8 {
                        let gx = ix + CORNER_OFFSETS[c][0] * stride;
                        let gy = iy + CORNER_OFFSETS[c][1] * stride;
                        let gz = iz + CORNER_OFFSETS[c][2] * stride;
                        let wp = self.voxel_pos(gx as f64, gy as f64, gz as f64);
                        c_pos[c] = [wp[0] as f32, wp[1] as f32, wp[2] as f32];
                        let g = self.gradient_at(gx, gy, gz);
                        c_norm[c] = [g[0] * sign, g[1] * sign, g[2] * sign];
                    }

                    let mut vert_list = [[0.0f32; 3]; 12];
                    let mut norm_list = [[0.0f32; 3]; 12];

                    for e in 0..12 {
                        if (edges & (1 << e)) != 0 {
                            let c1 = EDGE_CONN[e][0];
                            let c2 = EDGE_CONN[e][1];
                            let v1 = vals[c1];
                            let v2 = vals[c2];
                            let mu = if (v2 - v1).abs() < 1e-12 {
                                0.5
                            } else {
                                ((isovalue - v1) / (v2 - v1)).clamp(0.0, 1.0)
                            };
                            for k in 0..3 {
                                vert_list[e][k] =
                                    c_pos[c1][k] + mu * (c_pos[c2][k] - c_pos[c1][k]);
                                norm_list[e][k] =
                                    c_norm[c1][k] + mu * (c_norm[c2][k] - c_norm[c1][k]);
                            }
                            let nlen = (norm_list[e][0] * norm_list[e][0]
                                + norm_list[e][1] * norm_list[e][1]
                                + norm_list[e][2] * norm_list[e][2])
                                .sqrt();
                            if nlen > 1e-12 {
                                norm_list[e][0] /= nlen;
                                norm_list[e][1] /= nlen;
                                norm_list[e][2] /= nlen;
                            } else {
                                norm_list[e] = [0.0, 0.0, 1.0];
                            }
                        }
                    }

                    let tri_row = &TRI_TABLE[cube_index];
                    let mut t = 0;
                    while t + 2 < 16 && tri_row[t] != -1 {
                        let e0 = tri_row[t] as usize;
                        let e1 = tri_row[t + 1] as usize;
                        let e2 = tri_row[t + 2] as usize;

                        let base = (positions.len() / 3) as u32;
                        for &ei in &[e0, e1, e2] {
                            positions.extend_from_slice(&vert_list[ei]);
                            normals.extend_from_slice(&norm_list[ei]);
                            if let Some(cc) = color_cube {
                                let val = cc.sample_at(
                                    vert_list[ei][0] as f64,
                                    vert_list[ei][1] as f64,
                                    vert_list[ei][2] as f64,
                                );
                                let rgb = match color_mode {
                                    Some("bwr") => bwr_color_map(val),
                                    _ => bgr_color_map(val),
                                };
                                colors.extend_from_slice(&rgb);
                            }
                        }
                        indices.push(base);
                        indices.push(base + 1);
                        indices.push(base + 2);

                        t += 3;
                    }

                    iz += stride;
                }
                iy += stride;
            }
            ix += stride;
        }

        let vertex_count = positions.len() / 3;
        let triangle_count = indices.len() / 3;

        IsosurfaceMesh {
            positions,
            normals,
            colors: if color_cube.is_some() { Some(colors) } else { None },
            indices,
            vertex_count,
            triangle_count,
        }
    }
}

#[rustfmt::skip]
const EDGE_TABLE: [u16; 256] = [
    0x0, 0x109, 0x203, 0x30a, 0x406, 0x50f, 0x605, 0x70c,
    0x80c, 0x905, 0xa0f, 0xb06, 0xc0a, 0xd03, 0xe09, 0xf00,
    0x190, 0x99, 0x393, 0x29a, 0x596, 0x49f, 0x795, 0x69c,
    0x99c, 0x895, 0xb9f, 0xa96, 0xd9a, 0xc93, 0xf99, 0xe90,
    0x230, 0x339, 0x33, 0x13a, 0x636, 0x73f, 0x435, 0x53c,
    0xa3c, 0xb35, 0x83f, 0x936, 0xe3a, 0xf33, 0xc39, 0xd30,
    0x3a0, 0x2a9, 0x1a3, 0xaa, 0x7a6, 0x6af, 0x5a5, 0x4ac,
    0xbac, 0xaa5, 0x9af, 0x8a6, 0xfaa, 0xea3, 0xda9, 0xca0,
    0x460, 0x569, 0x663, 0x76a, 0x66, 0x16f, 0x265, 0x36c,
    0xc6c, 0xd65, 0xe6f, 0xf66, 0x86a, 0x963, 0xa69, 0xb60,
    0x5f0, 0x4f9, 0x7f3, 0x6fa, 0x1f6, 0xff, 0x3f5, 0x2fc,
    0xdfc, 0xcf5, 0xfff, 0xef6, 0x9fa, 0x8f3, 0xbf9, 0xaf0,
    0x650, 0x759, 0x453, 0x55a, 0x256, 0x35f, 0x55, 0x15c,
    0xe5c, 0xf55, 0xc5f, 0xd56, 0xa5a, 0xb53, 0x859, 0x950,
    0x7c0, 0x6c9, 0x5c3, 0x4ca, 0x3c6, 0x2cf, 0x1c5, 0xcc,
    0xfcc, 0xec5, 0xdcf, 0xcc6, 0xbca, 0xac3, 0x9c9, 0x8c0,
    0x8c0, 0x9c9, 0xac3, 0xbca, 0xcc6, 0xdcf, 0xec5, 0xfcc,
    0xcc, 0x1c5, 0x2cf, 0x3c6, 0x4ca, 0x5c3, 0x6c9, 0x7c0,
    0x950, 0x859, 0xb53, 0xa5a, 0xd56, 0xc5f, 0xf55, 0xe5c,
    0x15c, 0x55, 0x35f, 0x256, 0x55a, 0x453, 0x759, 0x650,
    0xaf0, 0xbf9, 0x8f3, 0x9fa, 0xef6, 0xfff, 0xcf5, 0xdfc,
    0x2fc, 0x3f5, 0xff, 0x1f6, 0x6fa, 0x7f3, 0x4f9, 0x5f0,
    0xb60, 0xa69, 0x963, 0x86a, 0xf66, 0xe6f, 0xd65, 0xc6c,
    0x36c, 0x265, 0x16f, 0x66, 0x76a, 0x663, 0x569, 0x460,
    0xca0, 0xda9, 0xea3, 0xfaa, 0x8a6, 0x9af, 0xaa5, 0xbac,
    0x4ac, 0x5a5, 0x6af, 0x7a6, 0xaa, 0x1a3, 0x2a9, 0x3a0,
    0xd30, 0xc39, 0xf33, 0xe3a, 0x936, 0x83f, 0xb35, 0xa3c,
    0x53c, 0x435, 0x73f, 0x636, 0x13a, 0x33, 0x339, 0x230,
    0xe90, 0xf99, 0xc93, 0xd9a, 0xa96, 0xb9f, 0x895, 0x99c,
    0x69c, 0x795, 0x49f, 0x596, 0x29a, 0x393, 0x99, 0x190,
    0xf00, 0xe09, 0xd03, 0xc0a, 0xb06, 0xa0f, 0x905, 0x80c,
    0x70c, 0x605, 0x50f, 0x406, 0x30a, 0x203, 0x109, 0x0,
];

#[rustfmt::skip]
const TRI_TABLE: [[i8; 16]; 256] = [
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 1, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 8, 3, 9, 8, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 3, 1, 2, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [9, 2, 10, 0, 2, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [2, 8, 3, 2, 10, 8, 10, 9, 8, -1, -1, -1, -1, -1, -1, -1],
    [3, 11, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 11, 2, 8, 11, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 9, 0, 2, 3, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 11, 2, 1, 9, 11, 9, 8, 11, -1, -1, -1, -1, -1, -1, -1],
    [3, 10, 1, 11, 10, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 10, 1, 0, 8, 10, 8, 11, 10, -1, -1, -1, -1, -1, -1, -1],
    [3, 9, 0, 3, 11, 9, 11, 10, 9, -1, -1, -1, -1, -1, -1, -1],
    [9, 8, 10, 10, 8, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 7, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 3, 0, 7, 3, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 1, 9, 8, 4, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 1, 9, 4, 7, 1, 7, 3, 1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 10, 8, 4, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [3, 4, 7, 3, 0, 4, 1, 2, 10, -1, -1, -1, -1, -1, -1, -1],
    [9, 2, 10, 9, 0, 2, 8, 4, 7, -1, -1, -1, -1, -1, -1, -1],
    [2, 10, 9, 2, 9, 7, 2, 7, 3, 7, 9, 4, -1, -1, -1, -1],
    [8, 4, 7, 3, 11, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [11, 4, 7, 11, 2, 4, 2, 0, 4, -1, -1, -1, -1, -1, -1, -1],
    [9, 0, 1, 8, 4, 7, 2, 3, 11, -1, -1, -1, -1, -1, -1, -1],
    [4, 7, 11, 9, 4, 11, 9, 11, 2, 9, 2, 1, -1, -1, -1, -1],
    [3, 10, 1, 3, 11, 10, 7, 8, 4, -1, -1, -1, -1, -1, -1, -1],
    [1, 11, 10, 1, 4, 11, 1, 0, 4, 7, 11, 4, -1, -1, -1, -1],
    [4, 7, 8, 9, 0, 11, 9, 11, 10, 11, 0, 3, -1, -1, -1, -1],
    [4, 7, 11, 4, 11, 9, 9, 11, 10, -1, -1, -1, -1, -1, -1, -1],
    [9, 5, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [9, 5, 4, 0, 8, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 5, 4, 1, 5, 0, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [8, 5, 4, 8, 3, 5, 3, 1, 5, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 10, 9, 5, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [3, 0, 8, 1, 2, 10, 4, 9, 5, -1, -1, -1, -1, -1, -1, -1],
    [5, 2, 10, 5, 4, 2, 4, 0, 2, -1, -1, -1, -1, -1, -1, -1],
    [2, 10, 5, 3, 2, 5, 3, 5, 4, 3, 4, 8, -1, -1, -1, -1],
    [9, 5, 4, 2, 3, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 11, 2, 0, 8, 11, 4, 9, 5, -1, -1, -1, -1, -1, -1, -1],
    [0, 5, 4, 0, 1, 5, 2, 3, 11, -1, -1, -1, -1, -1, -1, -1],
    [2, 1, 5, 2, 5, 8, 2, 8, 11, 4, 8, 5, -1, -1, -1, -1],
    [10, 3, 11, 10, 1, 3, 9, 5, 4, -1, -1, -1, -1, -1, -1, -1],
    [4, 9, 5, 0, 8, 1, 8, 10, 1, 8, 11, 10, -1, -1, -1, -1],
    [5, 4, 0, 5, 0, 11, 5, 11, 10, 11, 0, 3, -1, -1, -1, -1],
    [5, 4, 8, 5, 8, 10, 10, 8, 11, -1, -1, -1, -1, -1, -1, -1],
    [9, 7, 8, 5, 7, 9, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [9, 3, 0, 9, 5, 3, 5, 7, 3, -1, -1, -1, -1, -1, -1, -1],
    [0, 7, 8, 0, 1, 7, 1, 5, 7, -1, -1, -1, -1, -1, -1, -1],
    [1, 5, 3, 3, 5, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [9, 7, 8, 9, 5, 7, 10, 1, 2, -1, -1, -1, -1, -1, -1, -1],
    [10, 1, 2, 9, 5, 0, 5, 3, 0, 5, 7, 3, -1, -1, -1, -1],
    [8, 0, 2, 8, 2, 5, 8, 5, 7, 10, 5, 2, -1, -1, -1, -1],
    [2, 10, 5, 2, 5, 3, 3, 5, 7, -1, -1, -1, -1, -1, -1, -1],
    [7, 9, 5, 7, 8, 9, 3, 11, 2, -1, -1, -1, -1, -1, -1, -1],
    [9, 5, 7, 9, 7, 2, 9, 2, 0, 2, 7, 11, -1, -1, -1, -1],
    [2, 3, 11, 0, 1, 8, 1, 7, 8, 1, 5, 7, -1, -1, -1, -1],
    [11, 2, 1, 11, 1, 7, 7, 1, 5, -1, -1, -1, -1, -1, -1, -1],
    [9, 5, 8, 8, 5, 7, 10, 1, 3, 10, 3, 11, -1, -1, -1, -1],
    [5, 7, 0, 5, 0, 9, 7, 11, 0, 1, 0, 10, 11, 10, 0, -1],
    [11, 10, 0, 11, 0, 3, 10, 5, 0, 8, 0, 7, 5, 7, 0, -1],
    [11, 10, 5, 7, 11, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [10, 6, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 3, 5, 10, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [9, 0, 1, 5, 10, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 8, 3, 1, 9, 8, 5, 10, 6, -1, -1, -1, -1, -1, -1, -1],
    [1, 6, 5, 2, 6, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 6, 5, 1, 2, 6, 3, 0, 8, -1, -1, -1, -1, -1, -1, -1],
    [9, 6, 5, 9, 0, 6, 0, 2, 6, -1, -1, -1, -1, -1, -1, -1],
    [5, 9, 8, 5, 8, 2, 5, 2, 6, 3, 2, 8, -1, -1, -1, -1],
    [2, 3, 11, 10, 6, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [11, 0, 8, 11, 2, 0, 10, 6, 5, -1, -1, -1, -1, -1, -1, -1],
    [0, 1, 9, 2, 3, 11, 5, 10, 6, -1, -1, -1, -1, -1, -1, -1],
    [5, 10, 6, 1, 9, 2, 9, 11, 2, 9, 8, 11, -1, -1, -1, -1],
    [6, 3, 11, 6, 5, 3, 5, 1, 3, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 11, 0, 11, 5, 0, 5, 1, 5, 11, 6, -1, -1, -1, -1],
    [3, 11, 6, 0, 3, 6, 0, 6, 5, 0, 5, 9, -1, -1, -1, -1],
    [6, 5, 9, 6, 9, 11, 11, 9, 8, -1, -1, -1, -1, -1, -1, -1],
    [5, 10, 6, 4, 7, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 3, 0, 4, 7, 3, 6, 5, 10, -1, -1, -1, -1, -1, -1, -1],
    [1, 9, 0, 5, 10, 6, 8, 4, 7, -1, -1, -1, -1, -1, -1, -1],
    [10, 6, 5, 1, 9, 7, 1, 7, 3, 7, 9, 4, -1, -1, -1, -1],
    [6, 1, 2, 6, 5, 1, 4, 7, 8, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 5, 5, 2, 6, 3, 0, 4, 3, 4, 7, -1, -1, -1, -1],
    [8, 4, 7, 9, 0, 5, 0, 6, 5, 0, 2, 6, -1, -1, -1, -1],
    [7, 3, 9, 7, 9, 4, 3, 2, 9, 5, 9, 6, 2, 6, 9, -1],
    [3, 11, 2, 7, 8, 4, 10, 6, 5, -1, -1, -1, -1, -1, -1, -1],
    [5, 10, 6, 4, 7, 2, 4, 2, 0, 2, 7, 11, -1, -1, -1, -1],
    [0, 1, 9, 4, 7, 8, 2, 3, 11, 5, 10, 6, -1, -1, -1, -1],
    [9, 2, 1, 9, 11, 2, 9, 4, 11, 7, 11, 4, 5, 10, 6, -1],
    [8, 4, 7, 3, 11, 5, 3, 5, 1, 5, 11, 6, -1, -1, -1, -1],
    [5, 1, 11, 5, 11, 6, 1, 0, 11, 7, 11, 4, 0, 4, 11, -1],
    [0, 5, 9, 0, 6, 5, 0, 3, 6, 11, 6, 3, 8, 4, 7, -1],
    [6, 5, 9, 6, 9, 11, 4, 7, 9, 7, 11, 9, -1, -1, -1, -1],
    [10, 4, 9, 6, 4, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 10, 6, 4, 9, 10, 0, 8, 3, -1, -1, -1, -1, -1, -1, -1],
    [10, 0, 1, 10, 6, 0, 6, 4, 0, -1, -1, -1, -1, -1, -1, -1],
    [8, 3, 1, 8, 1, 6, 8, 6, 4, 6, 1, 10, -1, -1, -1, -1],
    [1, 4, 9, 1, 2, 4, 2, 6, 4, -1, -1, -1, -1, -1, -1, -1],
    [3, 0, 8, 1, 2, 9, 2, 4, 9, 2, 6, 4, -1, -1, -1, -1],
    [0, 2, 4, 4, 2, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [8, 3, 2, 8, 2, 4, 4, 2, 6, -1, -1, -1, -1, -1, -1, -1],
    [10, 4, 9, 10, 6, 4, 11, 2, 3, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 2, 2, 8, 11, 4, 9, 10, 4, 10, 6, -1, -1, -1, -1],
    [3, 11, 2, 0, 1, 6, 0, 6, 4, 6, 1, 10, -1, -1, -1, -1],
    [6, 4, 1, 6, 1, 10, 4, 8, 1, 2, 1, 11, 8, 11, 1, -1],
    [9, 6, 4, 9, 3, 6, 9, 1, 3, 11, 6, 3, -1, -1, -1, -1],
    [8, 11, 1, 8, 1, 0, 11, 6, 1, 9, 1, 4, 6, 4, 1, -1],
    [3, 11, 6, 3, 6, 0, 0, 6, 4, -1, -1, -1, -1, -1, -1, -1],
    [6, 4, 8, 11, 6, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [7, 10, 6, 7, 8, 10, 8, 9, 10, -1, -1, -1, -1, -1, -1, -1],
    [0, 7, 3, 0, 10, 7, 0, 9, 10, 6, 7, 10, -1, -1, -1, -1],
    [10, 6, 7, 1, 10, 7, 1, 7, 8, 1, 8, 0, -1, -1, -1, -1],
    [10, 6, 7, 10, 7, 1, 1, 7, 3, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 6, 1, 6, 8, 1, 8, 9, 8, 6, 7, -1, -1, -1, -1],
    [2, 6, 9, 2, 9, 1, 6, 7, 9, 0, 9, 3, 7, 3, 9, -1],
    [7, 8, 0, 7, 0, 6, 6, 0, 2, -1, -1, -1, -1, -1, -1, -1],
    [7, 3, 2, 6, 7, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [2, 3, 11, 10, 6, 8, 10, 8, 9, 8, 6, 7, -1, -1, -1, -1],
    [2, 0, 7, 2, 7, 11, 0, 9, 7, 6, 7, 10, 9, 10, 7, -1],
    [1, 8, 0, 1, 7, 8, 1, 10, 7, 6, 7, 10, 2, 3, 11, -1],
    [11, 2, 1, 11, 1, 7, 10, 6, 1, 6, 7, 1, -1, -1, -1, -1],
    [8, 9, 6, 8, 6, 7, 9, 1, 6, 11, 6, 3, 1, 3, 6, -1],
    [0, 9, 1, 11, 6, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [7, 8, 0, 7, 0, 6, 3, 11, 0, 11, 6, 0, -1, -1, -1, -1],
    [7, 11, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [7, 6, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [3, 0, 8, 11, 7, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 1, 9, 11, 7, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [8, 1, 9, 8, 3, 1, 11, 7, 6, -1, -1, -1, -1, -1, -1, -1],
    [10, 1, 2, 6, 11, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 10, 3, 0, 8, 6, 11, 7, -1, -1, -1, -1, -1, -1, -1],
    [2, 9, 0, 2, 10, 9, 6, 11, 7, -1, -1, -1, -1, -1, -1, -1],
    [6, 11, 7, 2, 10, 3, 10, 8, 3, 10, 9, 8, -1, -1, -1, -1],
    [7, 2, 3, 6, 2, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [7, 0, 8, 7, 6, 0, 6, 2, 0, -1, -1, -1, -1, -1, -1, -1],
    [2, 7, 6, 2, 3, 7, 0, 1, 9, -1, -1, -1, -1, -1, -1, -1],
    [1, 6, 2, 1, 8, 6, 1, 9, 8, 8, 7, 6, -1, -1, -1, -1],
    [10, 7, 6, 10, 1, 7, 1, 3, 7, -1, -1, -1, -1, -1, -1, -1],
    [10, 7, 6, 1, 7, 10, 1, 8, 7, 1, 0, 8, -1, -1, -1, -1],
    [0, 3, 7, 0, 7, 10, 0, 10, 9, 6, 10, 7, -1, -1, -1, -1],
    [7, 6, 10, 7, 10, 8, 8, 10, 9, -1, -1, -1, -1, -1, -1, -1],
    [6, 8, 4, 11, 8, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [3, 6, 11, 3, 0, 6, 0, 4, 6, -1, -1, -1, -1, -1, -1, -1],
    [8, 6, 11, 8, 4, 6, 9, 0, 1, -1, -1, -1, -1, -1, -1, -1],
    [9, 4, 6, 9, 6, 3, 9, 3, 1, 11, 3, 6, -1, -1, -1, -1],
    [6, 8, 4, 6, 11, 8, 2, 10, 1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 10, 3, 0, 11, 0, 6, 11, 0, 4, 6, -1, -1, -1, -1],
    [4, 11, 8, 4, 6, 11, 0, 2, 9, 2, 10, 9, -1, -1, -1, -1],
    [10, 9, 3, 10, 3, 2, 9, 4, 3, 11, 3, 6, 4, 6, 3, -1],
    [8, 2, 3, 8, 4, 2, 4, 6, 2, -1, -1, -1, -1, -1, -1, -1],
    [0, 4, 2, 4, 6, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 9, 0, 2, 3, 4, 2, 4, 6, 4, 3, 8, -1, -1, -1, -1],
    [1, 9, 4, 1, 4, 2, 2, 4, 6, -1, -1, -1, -1, -1, -1, -1],
    [8, 1, 3, 8, 6, 1, 8, 4, 6, 6, 10, 1, -1, -1, -1, -1],
    [10, 1, 0, 10, 0, 6, 6, 0, 4, -1, -1, -1, -1, -1, -1, -1],
    [4, 6, 3, 4, 3, 8, 6, 10, 3, 0, 3, 9, 10, 9, 3, -1],
    [10, 9, 4, 6, 10, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 9, 5, 7, 6, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 3, 4, 9, 5, 11, 7, 6, -1, -1, -1, -1, -1, -1, -1],
    [5, 0, 1, 5, 4, 0, 7, 6, 11, -1, -1, -1, -1, -1, -1, -1],
    [11, 7, 6, 8, 3, 4, 3, 5, 4, 3, 1, 5, -1, -1, -1, -1],
    [9, 5, 4, 10, 1, 2, 7, 6, 11, -1, -1, -1, -1, -1, -1, -1],
    [6, 11, 7, 1, 2, 10, 0, 8, 3, 4, 9, 5, -1, -1, -1, -1],
    [7, 6, 11, 5, 4, 10, 4, 2, 10, 4, 0, 2, -1, -1, -1, -1],
    [3, 4, 8, 3, 5, 4, 3, 2, 5, 10, 5, 2, 11, 7, 6, -1],
    [7, 2, 3, 7, 6, 2, 5, 4, 9, -1, -1, -1, -1, -1, -1, -1],
    [9, 5, 4, 0, 8, 6, 0, 6, 2, 6, 8, 7, -1, -1, -1, -1],
    [3, 6, 2, 3, 7, 6, 1, 5, 0, 5, 4, 0, -1, -1, -1, -1],
    [6, 2, 8, 6, 8, 7, 2, 1, 8, 4, 8, 5, 1, 5, 8, -1],
    [9, 5, 4, 10, 1, 6, 1, 7, 6, 1, 3, 7, -1, -1, -1, -1],
    [1, 6, 10, 1, 7, 6, 1, 0, 7, 8, 7, 0, 9, 5, 4, -1],
    [4, 0, 10, 4, 10, 5, 0, 3, 10, 6, 10, 7, 3, 7, 10, -1],
    [7, 6, 10, 7, 10, 8, 5, 4, 10, 4, 8, 10, -1, -1, -1, -1],
    [6, 9, 5, 6, 11, 9, 11, 8, 9, -1, -1, -1, -1, -1, -1, -1],
    [3, 6, 11, 0, 6, 3, 0, 5, 6, 0, 9, 5, -1, -1, -1, -1],
    [0, 11, 8, 0, 5, 11, 0, 1, 5, 5, 6, 11, -1, -1, -1, -1],
    [6, 11, 3, 6, 3, 5, 5, 3, 1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 10, 9, 5, 11, 9, 11, 8, 11, 5, 6, -1, -1, -1, -1],
    [0, 11, 3, 0, 6, 11, 0, 9, 6, 5, 6, 9, 1, 2, 10, -1],
    [11, 8, 5, 11, 5, 6, 8, 0, 5, 10, 5, 2, 0, 2, 5, -1],
    [6, 11, 3, 6, 3, 5, 2, 10, 3, 10, 5, 3, -1, -1, -1, -1],
    [5, 8, 9, 5, 2, 8, 5, 6, 2, 3, 8, 2, -1, -1, -1, -1],
    [9, 5, 6, 9, 6, 0, 0, 6, 2, -1, -1, -1, -1, -1, -1, -1],
    [1, 5, 8, 1, 8, 0, 5, 6, 8, 3, 8, 2, 6, 2, 8, -1],
    [1, 5, 6, 2, 1, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 3, 6, 1, 6, 10, 3, 8, 6, 5, 6, 9, 8, 9, 6, -1],
    [10, 1, 0, 10, 0, 6, 9, 5, 0, 5, 6, 0, -1, -1, -1, -1],
    [0, 3, 8, 5, 6, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [10, 5, 6, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [11, 5, 10, 7, 5, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [11, 5, 10, 11, 7, 5, 8, 3, 0, -1, -1, -1, -1, -1, -1, -1],
    [5, 11, 7, 5, 10, 11, 1, 9, 0, -1, -1, -1, -1, -1, -1, -1],
    [10, 7, 5, 10, 11, 7, 9, 8, 1, 8, 3, 1, -1, -1, -1, -1],
    [11, 1, 2, 11, 7, 1, 7, 5, 1, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 3, 1, 2, 7, 1, 7, 5, 7, 2, 11, -1, -1, -1, -1],
    [9, 7, 5, 9, 2, 7, 9, 0, 2, 2, 11, 7, -1, -1, -1, -1],
    [7, 5, 2, 7, 2, 11, 5, 9, 2, 3, 2, 8, 9, 8, 2, -1],
    [2, 5, 10, 2, 3, 5, 3, 7, 5, -1, -1, -1, -1, -1, -1, -1],
    [8, 2, 0, 8, 5, 2, 8, 7, 5, 10, 2, 5, -1, -1, -1, -1],
    [9, 0, 1, 5, 10, 3, 5, 3, 7, 3, 10, 2, -1, -1, -1, -1],
    [9, 8, 2, 9, 2, 1, 8, 7, 2, 10, 2, 5, 7, 5, 2, -1],
    [1, 3, 5, 3, 7, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 7, 0, 7, 1, 1, 7, 5, -1, -1, -1, -1, -1, -1, -1],
    [9, 0, 3, 9, 3, 5, 5, 3, 7, -1, -1, -1, -1, -1, -1, -1],
    [9, 8, 7, 5, 9, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [5, 8, 4, 5, 10, 8, 10, 11, 8, -1, -1, -1, -1, -1, -1, -1],
    [5, 0, 4, 5, 11, 0, 5, 10, 11, 11, 3, 0, -1, -1, -1, -1],
    [0, 1, 9, 8, 4, 10, 8, 10, 11, 10, 4, 5, -1, -1, -1, -1],
    [10, 11, 4, 10, 4, 5, 11, 3, 4, 9, 4, 1, 3, 1, 4, -1],
    [2, 5, 1, 2, 8, 5, 2, 11, 8, 4, 5, 8, -1, -1, -1, -1],
    [0, 4, 11, 0, 11, 3, 4, 5, 11, 2, 11, 1, 5, 1, 11, -1],
    [0, 2, 5, 0, 5, 9, 2, 11, 5, 4, 5, 8, 11, 8, 5, -1],
    [9, 4, 5, 2, 11, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [2, 5, 10, 3, 5, 2, 3, 4, 5, 3, 8, 4, -1, -1, -1, -1],
    [5, 10, 2, 5, 2, 4, 4, 2, 0, -1, -1, -1, -1, -1, -1, -1],
    [3, 10, 2, 3, 5, 10, 3, 8, 5, 4, 5, 8, 0, 1, 9, -1],
    [5, 10, 2, 5, 2, 4, 1, 9, 2, 9, 4, 2, -1, -1, -1, -1],
    [8, 4, 5, 8, 5, 3, 3, 5, 1, -1, -1, -1, -1, -1, -1, -1],
    [0, 4, 5, 1, 0, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [8, 4, 5, 8, 5, 3, 9, 0, 5, 0, 3, 5, -1, -1, -1, -1],
    [9, 4, 5, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 11, 7, 4, 9, 11, 9, 10, 11, -1, -1, -1, -1, -1, -1, -1],
    [0, 8, 3, 4, 9, 7, 9, 11, 7, 9, 10, 11, -1, -1, -1, -1],
    [1, 10, 11, 1, 11, 4, 1, 4, 0, 7, 4, 11, -1, -1, -1, -1],
    [3, 1, 4, 3, 4, 8, 1, 10, 4, 7, 4, 11, 10, 11, 4, -1],
    [4, 11, 7, 9, 11, 4, 9, 2, 11, 9, 1, 2, -1, -1, -1, -1],
    [9, 7, 4, 9, 11, 7, 9, 1, 11, 2, 11, 1, 0, 8, 3, -1],
    [11, 7, 4, 11, 4, 2, 2, 4, 0, -1, -1, -1, -1, -1, -1, -1],
    [11, 7, 4, 11, 4, 2, 8, 3, 4, 3, 2, 4, -1, -1, -1, -1],
    [2, 9, 10, 2, 7, 9, 2, 3, 7, 7, 4, 9, -1, -1, -1, -1],
    [9, 10, 7, 9, 7, 4, 10, 2, 7, 8, 7, 0, 2, 0, 7, -1],
    [3, 7, 10, 3, 10, 2, 7, 4, 10, 1, 10, 0, 4, 0, 10, -1],
    [1, 10, 2, 8, 7, 4, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 9, 1, 4, 1, 7, 7, 1, 3, -1, -1, -1, -1, -1, -1, -1],
    [4, 9, 1, 4, 1, 7, 0, 8, 1, 8, 7, 1, -1, -1, -1, -1],
    [4, 0, 3, 7, 4, 3, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [4, 8, 7, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [9, 10, 8, 10, 11, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [3, 0, 9, 3, 9, 11, 11, 9, 10, -1, -1, -1, -1, -1, -1, -1],
    [0, 1, 10, 0, 10, 8, 8, 10, 11, -1, -1, -1, -1, -1, -1, -1],
    [3, 1, 10, 11, 3, 10, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 11, 1, 11, 9, 9, 11, 8, -1, -1, -1, -1, -1, -1, -1],
    [3, 0, 9, 3, 9, 11, 1, 2, 9, 2, 11, 9, -1, -1, -1, -1],
    [0, 2, 11, 8, 0, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [3, 2, 11, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [2, 3, 8, 2, 8, 10, 10, 8, 9, -1, -1, -1, -1, -1, -1, -1],
    [9, 10, 2, 0, 9, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [2, 3, 8, 2, 8, 10, 0, 1, 8, 1, 10, 8, -1, -1, -1, -1],
    [1, 10, 2, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [1, 3, 8, 9, 1, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 9, 1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [0, 3, 8, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
    [-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1],
];

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cube_parse_slice_and_marching_cubes() {
        let mut cube_str = String::from(
            "Test Cube\nSynthetic radial scalar field\n\
             1 -2.0 -2.0 -2.0\n\
             5 1.0 0.0 0.0\n\
             5 0.0 1.0 0.0\n\
             5 0.0 0.0 1.0\n\
             6 6.0 0.0 0.0 0.0\n",
        );
        for ix in 0..5 {
            for iy in 0..5 {
                for iz in 0..5 {
                    let dx = (ix as f64) - 2.0;
                    let dy = (iy as f64) - 2.0;
                    let dz = (iz as f64) - 2.0;
                    let r2 = dx * dx + dy * dy + dz * dz;
                    // Positive peak at center, negative rim to exercise dual isosurface
                    let val = (-0.5 * r2).exp() - 0.15;
                    cube_str.push_str(&format!("{val:.6} "));
                }
                cube_str.push('\n');
            }
        }

        let cube = CubeData::parse(&cube_str).expect("Cube parse should succeed");
        assert_eq!(cube.dims, [5, 5, 5]);
        assert_eq!(cube.atoms.len(), 1);
        assert_eq!(cube.atoms[0].symbol, "C");

        let slice = cube.extract_slice("xy", Some(2));
        assert_eq!(slice.width, 5);
        assert_eq!(slice.height, 5);
        assert_eq!(slice.values.len(), 25);
        assert!(slice.slice_max > 0.5);

        let dual = cube.extract_dual_isosurface(0.1);
        assert!(dual.positive.triangle_count > 0);
        assert_eq!(dual.positive.positions.len(), dual.positive.vertex_count * 3);
        assert_eq!(dual.positive.normals.len(), dual.positive.vertex_count * 3);
        assert!(dual.has_negative);
        assert!(dual.negative.as_ref().unwrap().triangle_count > 0);
    }
}
