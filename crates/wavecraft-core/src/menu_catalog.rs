use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenuParam {
    pub key: String,
    pub name: String,
    pub param_type: String, // "int" | "float" | "select" | "text"
    pub default_value: String,
    pub options: Vec<String>,
    pub description: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenuFunctionTemplate {
    pub id: String,
    pub main_id: String,
    pub sub_id: String,
    pub name: String,
    pub description: String,
    pub result_type: String,
    pub params: Vec<MenuParam>,
    pub command_template: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MenuCategory {
    pub id: String,
    pub name: String,
    pub description: String,
    pub icon: String,
    pub items: Vec<MenuFunctionTemplate>,
}

fn param_grid() -> MenuParam {
    MenuParam {
        key: "grid".into(),
        name: "网格质量".into(),
        param_type: "select".into(),
        default_value: "1".into(),
        options: vec![
            "1:粗糙(极速)".into(),
            "2:中等(推荐)".into(),
            "3:精细(慢)".into(),
            "4:超精细(极慢)".into(),
        ],
        description: "空间网格疏密程度，1=粗糙，2=中等，3=精细，4=超精细".into(),
    }
}

fn param_orbital() -> MenuParam {
    MenuParam {
        key: "orbital".into(),
        name: "轨道编号".into(),
        param_type: "int".into(),
        default_value: "1".into(),
        options: vec![],
        description: "分子轨道索引（可通过波函数轨道列表查看 HOMO/LUMO 编号）".into(),
    }
}

fn param_xyz() -> Vec<MenuParam> {
    vec![
        MenuParam {
            key: "x".into(),
            name: "X 坐标 (Bohr)".into(),
            param_type: "float".into(),
            default_value: "0.0".into(),
            options: vec![],
            description: "采样点 X 坐标".into(),
        },
        MenuParam {
            key: "y".into(),
            name: "Y 坐标 (Bohr)".into(),
            param_type: "float".into(),
            default_value: "0.0".into(),
            options: vec![],
            description: "采样点 Y 坐标".into(),
        },
        MenuParam {
            key: "z".into(),
            name: "Z 坐标 (Bohr)".into(),
            param_type: "float".into(),
            default_value: "0.0".into(),
            options: vec![],
            description: "采样点 Z 坐标".into(),
        },
    ]
}

fn fn_item(
    main_id: &str,
    sub_id: &str,
    name: &str,
    desc: &str,
    result_type: &str,
    params: Vec<MenuParam>,
    cmds: Vec<&str>,
) -> MenuFunctionTemplate {
    MenuFunctionTemplate {
        id: format!("{main_id}_{sub_id}"),
        main_id: main_id.into(),
        sub_id: sub_id.into(),
        name: name.into(),
        description: desc.into(),
        result_type: result_type.into(),
        params,
        command_template: cmds.into_iter().map(String::from).collect(),
    }
}

pub fn build_full_menu_catalog() -> Vec<MenuCategory> {
    vec![
        MenuCategory {
            id: "0".into(),
            name: "0 · 波函数与轨道预览".into(),
            description: "导出分子几何、MO 轨道立方体与电子密度三维等值面".into(),
            icon: "Orbit".into(),
            items: vec![
                fn_item("0", "1", "列出全部分子轨道信息", "输出轨道能量(a.u./eV)、占据数与自旋类型", "text", vec![], vec!["6", "3", "-1", "q"]),
                fn_item("0", "2", "生成指定轨道 3D Cube", "计算分子轨道波函数值并导出 .cub 网格", "cube", vec![param_orbital(), param_grid()], vec!["5", "4", "{orbital}", "{grid}", "2", "0", "q"]),
                fn_item("0", "3", "生成电子密度 3D Cube", "计算 ρ(r) 三维网格并渲染 3D 等值面", "cube", vec![param_grid()], vec!["5", "1", "{grid}", "2", "0", "q"]),
                fn_item("0", "4", "导出 XYZ 三维结构", "转换当前分子几何至 XYZ 格式", "text", vec![], vec!["100", "2", "2", "wavecraft_geom.xyz", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "1".into(),
            name: "1 · 单点实空间性质".into(),
            description: "计算空间指定位置或原子核位置的全部实空间物理量".into(),
            icon: "Crosshair".into(),
            items: vec![
                fn_item("1", "1", "计算指定坐标全部性质", "计算某点 ρ、|∇ρ|、∇²ρ、ELF、LOL、K、G、ESP 等", "text", param_xyz(), vec!["1", "{x},{y},{z}", "q"]),
                fn_item("1", "2", "查看体系原子核与坐标", "列出全部原子核坐标及 GTF 信息", "text", vec![], vec!["100", "2", "2", "wavecraft_geom.xyz", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "2".into(),
            name: "2 · AIM 拓扑分析".into(),
            description: "Bader 量子原子拓扑理论 (QTAIM) 临界点搜索与性质分析".into(),
            icon: "GitFork".into(),
            items: vec![
                fn_item("2", "1", "自动搜索全部临界点(NCP/BCP)", "从核位置及原子对中点搜索临界点并导出 CPs.txt", "aim", vec![], vec!["2", "2", "3", "7", "0", "-4", "4", "0", "-10", "q"]),
                fn_item("2", "2", "仅搜索核临界点 (3,-3)", "从原子核坐标出发定位核临界点", "aim", vec![], vec!["2", "2", "7", "0", "-4", "4", "0", "-10", "q"]),
                fn_item("2", "3", "仅搜索键临界点 (3,-1)", "从成键原子对中点定位键临界点 BCP", "aim", vec![], vec!["2", "3", "7", "0", "-4", "4", "0", "-10", "q"]),
                fn_item("2", "4", "搜索环与笼临界点 (RCP/CCP)", "搜索三角环心与四面体笼心临界点", "aim", vec![], vec!["2", "4", "5", "7", "0", "-4", "4", "0", "-10", "q"]),
                fn_item("2", "20", "计算 Shannon 芳香性指数", "基于键临界点电子密度计算芳香性", "text", vec![], vec!["2", "20", "-10", "q"]),
            ],
        },
        MenuCategory {
            id: "3".into(),
            name: "3 · 线性质剖面分析".into(),
            description: "沿两原子连线或任意路径导出电子密度/ELF/ESP 等一维分布曲线".into(),
            icon: "TrendingUp".into(),
            items: vec![
                fn_item("3", "1", "沿两原子导出电子密度 ρ(r) 曲线", "生成 line.txt 并提取键轴电子密度剖面", "line", vec![], vec!["3", "1", "1", "1,2", "2", "0", "q"]),
                fn_item("3", "9", "沿两原子导出 ELF 分布曲线", "沿化学键提取电子定域化函数剖面", "line", vec![], vec!["3", "9", "1", "1,2", "2", "0", "q"]),
                fn_item("3", "12", "沿两原子导出 ESP 静电势曲线", "沿键轴提取总静电势剖面", "line", vec![], vec!["3", "12", "1", "1,2", "2", "0", "q"]),
                fn_item("3", "3", "沿两原子导出 ∇²ρ(r) 拉普拉斯曲线", "评估键轴电子聚集与耗竭特征", "line", vec![], vec!["3", "3", "1", "1,2", "2", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "4".into(),
            name: "4 · 平面性质填色分析".into(),
            description: "在自定义分子平面（XY/XZ/YZ 或三原子平面）上计算 2D 网格性质".into(),
            icon: "Square".into(),
            items: vec![
                fn_item("4", "1", "XY 平面电子密度 ρ(r) 导出", "计算 Z=0 平面电子密度并导出 plane.txt", "text", vec![], vec!["4", "1", "1", "1", "0", "4", "-10", "q"]),
                fn_item("4", "9", "XY 平面 ELF 定域化导出", "计算平面 ELF 并导出数据", "text", vec![], vec!["4", "9", "1", "1", "0", "4", "-10", "q"]),
                fn_item("4", "12", "XY 平面静电势 ESP 导出", "计算平面总静电势并导出数据", "text", vec![], vec!["4", "12", "1", "1", "0", "4", "-10", "q"]),
            ],
        },
        MenuCategory {
            id: "5".into(),
            name: "5 · 实空间函数三维网格".into(),
            description: "在三维网格空间内计算 14 种核心量子化学实空间函数".into(),
            icon: "Grid".into(),
            items: vec![
                fn_item("5", "1", "电子密度 ρ(r)", "计算总电子密度三维网格", "cube", vec![param_grid()], vec!["5", "1", "{grid}", "2", "0", "q"]),
                fn_item("5", "2", "密度梯度模 |∇ρ(r)|", "计算电子密度梯度模三维网格", "cube", vec![param_grid()], vec!["5", "2", "{grid}", "2", "0", "q"]),
                fn_item("5", "3", "密度拉普拉斯 ∇²ρ(r)", "计算电子密度拉普拉斯三维网格", "cube", vec![param_grid()], vec!["5", "3", "{grid}", "2", "0", "q"]),
                fn_item("5", "4", "分子轨道波函数 ψ(r)", "计算指定编号分子轨道三维网格", "cube", vec![param_orbital(), param_grid()], vec!["5", "4", "{orbital}", "{grid}", "2", "0", "q"]),
                fn_item("5", "5", "自旋密度 ρ_s(r)", "计算开壳层体系自旋密度网格", "cube", vec![param_grid()], vec!["5", "5", "{grid}", "2", "0", "q"]),
                fn_item("5", "6", "Hamiltonian 动能密度 K(r)", "计算 K(r) 动能密度网格", "cube", vec![param_grid()], vec!["5", "6", "{grid}", "2", "0", "q"]),
                fn_item("5", "7", "Lagrange 动能密度 G(r)", "计算 G(r) 动能密度网格", "cube", vec![param_grid()], vec!["5", "7", "{grid}", "2", "0", "q"]),
                fn_item("5", "9", "电子定域化函数 ELF", "计算 ELF 三维定域化网格", "cube", vec![param_grid()], vec!["5", "9", "{grid}", "2", "0", "q"]),
                fn_item("5", "10", "局部轨道定位函数 LOL", "计算 LOL 三维定位网格", "cube", vec![param_grid()], vec!["5", "10", "{grid}", "2", "0", "q"]),
                fn_item("5", "12", "总静电势 ESP", "计算总分子静电势网格", "cube", vec![param_grid()], vec!["5", "12", "{grid}", "2", "0", "q"]),
                fn_item("5", "13", "约化密度梯度 RDG", "计算 RDG 网格", "cube", vec![param_grid()], vec!["5", "13", "{grid}", "2", "0", "q"]),
                fn_item("5", "15", "sign(λ₂)ρ(r)", "计算符号密度函数网格", "cube", vec![param_grid()], vec!["5", "15", "{grid}", "2", "0", "q"]),
                fn_item("5", "18", "平均局部电离能 ALIE", "计算 Ī(r) 局部电离能网格", "cube", vec![param_grid()], vec!["5", "18", "{grid}", "2", "0", "q"]),
                fn_item("5", "24", "相互作用指示函数 IRI", "计算 IRI 网格", "cube", vec![param_grid()], vec!["5", "24", "{grid}", "2", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "6".into(),
            name: "6 · 波函数检查与矩阵".into(),
            description: "检查 GTF、基函数、轨道能量与重叠/密度积分矩阵".into(),
            icon: "FileCode".into(),
            items: vec![
                fn_item("6", "1", "列出所有 GTF 原函数", "显示所有基组原函数指数与收缩系数", "text", vec![], vec!["6", "1", "-1", "q"]),
                fn_item("6", "2", "列出所有基函数", "显示基函数壳层与原子归属", "text", vec![], vec!["6", "2", "-1", "q"]),
                fn_item("6", "3", "列出所有分子轨道", "输出全部轨道能量、占据数与自旋", "text", vec![], vec!["6", "3", "-1", "q"]),
                fn_item("6", "4", "查看指定轨道详细信息", "输出特定分子轨道的主成分分布", "text", vec![param_orbital()], vec!["6", "4", "{orbital}", "-1", "q"]),
            ],
        },
        MenuCategory {
            id: "7".into(),
            name: "7 · 原子电荷与布居分析".into(),
            description: "完整覆盖 16 种量子化学电荷模型（Hirshfeld/ADCH/CM5/RESP 等）".into(),
            icon: "Zap".into(),
            items: vec![
                fn_item("7", "1", "Hirshfeld 电荷", "基于自由原子电子密度比例划分", "charge", vec![], vec!["7", "1", "1", "y", "0", "q"]),
                fn_item("7", "2", "VDD 电荷", "Voronoi 变形密度电荷", "charge", vec![], vec!["7", "2", "1", "y", "0", "q"]),
                fn_item("7", "5", "Mulliken 电荷", "经典基函数布居划分", "charge", vec![], vec!["7", "5", "1", "y", "0", "0", "q"]),
                fn_item("7", "6", "Lowdin 电荷", "对称正交化布居电荷", "charge", vec![], vec!["7", "6", "lowdin_pop.txt", "y", "0", "q"]),
                fn_item("7", "7", "SCPA 电荷", "Ros-Schuit 对称化布居", "charge", vec![], vec!["7", "7", "y", "0", "q"]),
                fn_item("7", "10", "Becke 电荷", "模糊多中心空间积分电荷", "charge", vec![], vec!["7", "10", "0", "y", "0", "q"]),
                fn_item("7", "11", "ADCH 电荷", "原子偶极矩校正 Hirshfeld 电荷（推荐）", "charge", vec![], vec!["7", "11", "1", "y", "0", "q"]),
                fn_item("7", "12", "CHELPG 电荷", "空间网格静电势拟合电荷", "charge", vec![], vec!["7", "12", "1", "y", "0", "0", "q"]),
                fn_item("7", "13", "MK 电荷", "Merz-Kollmann 静电势拟合电荷", "charge", vec![], vec!["7", "13", "1", "y", "0", "0", "q"]),
                fn_item("7", "14", "AIM 电荷", "Bader 原子盆积分电荷", "charge", vec![], vec!["17", "1", "1", "1", "2", "1", "0", "-10", "q"]),
                fn_item("7", "15", "Hirshfeld-I 电荷", "迭代自洽 Hirshfeld 电荷", "charge", vec![], vec!["7", "15", "1", "1", "y", "0", "q"]),
                fn_item("7", "16", "CM5 电荷", "Charge Model 5 经验修正电荷", "charge", vec![], vec!["7", "16", "1", "y", "0", "q"]),
                fn_item("7", "17", "EEM 电荷", "电负性均衡快速经验电荷", "charge", vec![], vec!["7", "17", "g", "0", "y", "-1", "0", "q"]),
                fn_item("7", "18", "RESP 电荷", "力场标准受限静电势拟合电荷", "charge", vec![], vec!["7", "18", "1", "y", "0", "0", "q"]),
                fn_item("7", "19", "Gasteiger 电荷", "PEOE 电负性迭代电荷", "charge", vec![], vec!["7", "19", "y", "0", "q"]),
                fn_item("7", "20", "MBIS 电荷", "最小基迭代 Stockholder 电荷", "charge", vec![], vec!["7", "20", "1", "y", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "8".into(),
            name: "8 · 轨道成分分析".into(),
            description: "Mulliken / SCPA / Hirshfeld / NAO 分子轨道原子贡献剖析".into(),
            icon: "Layers".into(),
            items: vec![
                fn_item("8", "1", "Mulliken 轨道成分", "分析指定轨道在各原子上的贡献占比", "orbital_comp", vec![param_orbital()], vec!["8", "1", "{orbital}", "0", "-10", "q"]),
                fn_item("8", "3", "SCPA 轨道成分", "使用 SCPA 方法消除交叉项分配", "orbital_comp", vec![param_orbital()], vec!["8", "3", "{orbital}", "0", "-10", "q"]),
                fn_item("8", "8", "Hirshfeld 轨道成分", "实空间 Hirshfeld 划分轨道成分（基组无关）", "orbital_comp", vec![param_orbital()], vec!["8", "8", "1", "{orbital}", "0", "-10", "q"]),
                fn_item("8", "9", "Becke 轨道成分", "实空间 Becke 划分轨道成分", "orbital_comp", vec![param_orbital()], vec!["8", "9", "{orbital}", "0", "-10", "q"]),
            ],
        },
        MenuCategory {
            id: "9".into(),
            name: "9 · 化学键键级分析".into(),
            description: "Mayer、Wiberg、Fuzzy、Laplacian 与 IBSI 键强度分析".into(),
            icon: "Link".into(),
            items: vec![
                fn_item("9", "1", "Mayer 键级", "经典共价键键级与原子价分析", "bond", vec![], vec!["9", "1", "n", "0", "q"]),
                fn_item("9", "3", "Wiberg 键级 (Lowdin 基)", "正交化基组下的 Wiberg 键级", "bond", vec![], vec!["9", "3", "n", "0", "q"]),
                fn_item("9", "4", "Mulliken 键级", "Mulliken 重叠布居键级", "bond", vec![], vec!["9", "4", "n", "0", "q"]),
                fn_item("9", "6", "占据扰动 Mayer 键级", "评估反键/成键电子占据对键级贡献", "bond", vec![], vec!["9", "6", "n", "0", "q"]),
                fn_item("9", "7", "Fuzzy 键级 (FBO)", "实空间模糊原子划分键级，适合极性/弱键", "bond", vec![], vec!["9", "7", "n", "0", "q"]),
                fn_item("9", "8", "Laplacian 键级 (LBO)", "基于电子密度拉普拉斯的共价键强度指标", "bond", vec![], vec!["9", "8", "n", "0", "q"]),
                fn_item("9", "10", "IBSI 本征键强指数", "Intrinsic Bond Strength Index，涵盖弱作用与共价键", "bond", vec![], vec!["9", "10", "n", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "10".into(),
            name: "10 · 态密度与能级谱 (DOS)".into(),
            description: "提取轨道能量并绘制高分辨 TDOS / 占据-虚轨道态密度谱".into(),
            icon: "Activity".into(),
            items: vec![
                fn_item("10", "1", "全电子态密度 (TDOS)", "提取全轨道能级并展宽绘制 TDOS 曲线", "dos", vec![], vec!["6", "3", "-1", "q"]),
                fn_item("10", "2", "查看轨道能级分布表", "通过菜单 10 输出完整轨道能级信息", "dos", vec![], vec!["10", "-4", "-10", "q"]),
            ],
        },
        MenuCategory {
            id: "11".into(),
            name: "11 · 光谱分析 (IR/Raman/UV/NMR)".into(),
            description: "支持 Gaussian .out/.log 振动与激发态光谱展宽及峰表导出".into(),
            icon: "Waves".into(),
            items: vec![
                fn_item("11", "1", "IR 红外光谱", "绘制并导出红外吸收光谱 (需 .out/.log)", "spectrum", vec![], vec!["11", "1", "0", "q"]),
                fn_item("11", "2", "Raman 拉曼光谱", "绘制并导出拉曼散射光谱 (需 .out/.log)", "spectrum", vec![], vec!["11", "2", "0", "q"]),
                fn_item("11", "3", "UV-Vis 紫外-可见光谱", "绘制并导出 TDDFT 电子吸收光谱", "spectrum", vec![], vec!["11", "3", "0", "q"]),
                fn_item("11", "4", "ECD 电子圆二色谱", "手性分子电子圆二色谱模拟", "spectrum", vec![], vec!["11", "4", "0", "q"]),
                fn_item("11", "5", "VCD 振动圆二色谱", "手性分子振动圆二色谱模拟", "spectrum", vec![], vec!["11", "5", "0", "q"]),
                fn_item("11", "6", "ROA 拉曼光学活性", "拉曼光学活性光谱模拟", "spectrum", vec![], vec!["11", "6", "0", "q"]),
                fn_item("11", "7", "NMR 核磁共振谱", "解析 GIAO 化学屏蔽与 NMR 谱", "spectrum", vec![], vec!["11", "7", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "12".into(),
            name: "12 · 分子表面定量分析".into(),
            description: "计算 vdW 表面积、体积、ESP 极值及正负静电势统计".into(),
            icon: "Globe".into(),
            items: vec![
                fn_item("12", "1", "定量分子表面静电势分析", "默认 0.001 a.u. 等电子密度面 ESP 统计分析", "text", vec![], vec!["12", "0", "-1", "q"]),
            ],
        },
        MenuCategory {
            id: "13".into(),
            name: "13 · 网格数据处理".into(),
            description: "对空间网格数据进行积分、统计极值、投影与代数运算".into(),
            icon: "Database".into(),
            items: vec![
                fn_item("13", "1", "生成密度网格并统计极值", "先生成密度网格再进入菜单 13 输出统计量", "text", vec![], vec!["5", "1", "1", "0", "13", "1", "-1", "q"]),
            ],
        },
        MenuCategory {
            id: "14".into(),
            name: "14 · AdNDP 自适应自然密度划分".into(),
            description: "多中心化学键与离域成键模式识别 (需含 NBO .47/.out)".into(),
            icon: "Hexagon".into(),
            items: vec![
                fn_item("14", "1", "启动 AdNDP 多中心键搜索", "在 NBO 基下自动搜索 1c-2e / 2c-2e / nc-2e 键", "text", vec![], vec!["14", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "15".into(),
            name: "15 · Fuzzy 模糊原子空间分析".into(),
            description: "Becke/Hirshfeld 模糊空间积分、LI/DI 局域离域指数、PDI、FLU 与 C6".into(),
            icon: "Cpu".into(),
            items: vec![
                fn_item("15", "4", "计算局域化指数 LI 与离域化指数 DI", "输出每个原子的 LI 与全分子 DI 矩阵", "fuzzy", vec![], vec!["15", "4", "n", "0", "q"]),
                fn_item("15", "2", "计算原子多极矩与 <r²>", "计算 Fuzzy 空间原子偶极/四极矩", "text", vec![], vec!["15", "2", "0", "q"]),
                fn_item("15", "5", "计算 PDI 对位离域指数", "评估六元环对位电子离域程度", "text", vec![], vec!["15", "5", "0", "q"]),
                fn_item("15", "6", "计算 FLU 芳香性波动指数", "评估环共轭芳香性波动", "text", vec![], vec!["15", "6", "0", "q"]),
                fn_item("15", "13", "计算原子有效体积、极化率与 C6 系数", "输出原子的自由/有效体积与色散系数", "text", vec![], vec!["15", "13", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "16".into(),
            name: "16 · CDA 电荷分解分析".into(),
            description: "片段间给体-受体电子转移、极化与轨道相互作用图".into(),
            icon: "GitMerge".into(),
            items: vec![
                fn_item("16", "1", "CDA 模块入口说明", "需提供复合物及片段波函数文件", "text", vec![], vec!["16", "q"]),
            ],
        },
        MenuCategory {
            id: "17".into(),
            name: "17 · Basin 原子盆分析".into(),
            description: "QTAIM 电子密度盆、ELF 盆与 LOL 盆划分与数值积分".into(),
            icon: "Box".into(),
            items: vec![
                fn_item("17", "1", "生成电子密度原子盆并积分电子数", "按 Bader 零通量面划分盆并积分总电子密度", "text", vec![], vec!["17", "1", "1", "1", "2", "1", "0", "-10", "q"]),
                fn_item("17", "2", "生成 ELF 盆并计算电子布居", "按 ELF 吸引子划分孤对电子与成键盆", "text", vec![], vec!["17", "1", "9", "1", "2", "1", "0", "-10", "q"]),
            ],
        },
        MenuCategory {
            id: "18".into(),
            name: "18 · 电子激发分析".into(),
            description: "空穴-电子分布、Δr 电荷转移指数、NTO 与 IFCT 片段转移".into(),
            icon: "Sparkles".into(),
            items: vec![
                fn_item("18", "15", "打印所有激发态主要 MO 跃迁贡献", "解析 TDDFT 激发态主要轨道跃迁成分", "text", vec![], vec!["18", "15", "0", "q"]),
                fn_item("18", "4", "计算 Δr 电荷转移长度指数", "区分局域激发 (LE) 与电荷转移激发 (CT)", "text", vec![], vec!["18", "4", "0", "q"]),
                fn_item("18", "14", "计算 Λ 轨道重叠指数", "定量表征激发态空穴-电子空间重叠", "text", vec![], vec!["18", "14", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "19".into(),
            name: "19 · 轨道定域化分析".into(),
            description: "Pipek-Mezey / Foster-Boys 占据与虚分子轨道定域化".into(),
            icon: "Layers".into(),
            items: vec![
                fn_item("19", "1", "Pipek-Mezey 定域化占据轨道", "将离域正则 MO 转换为局域化学键/孤对轨道", "text", vec![], vec!["19", "1", "0", "q"]),
                fn_item("19", "2", "定域化占据轨道与虚轨道", "同时对占据态与未占态进行定域化", "text", vec![], vec!["19", "2", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "20".into(),
            name: "20 · 弱相互作用可视化 (NCI/IGM)".into(),
            description: "NCI、IGM、mIGM、IGMH、DORI 弱相互作用散点与等值面数据".into(),
            icon: "Sparkles".into(),
            items: vec![
                fn_item("20", "1", "NCI (RDG) 散点分析", "计算非共价相互作用散点数据 output.txt", "nci", vec![param_grid()], vec!["20", "1", "1", "{grid}", "2", "0", "0", "q"]),
                fn_item("20", "2", "NCI 3D 等值面 Cube", "生成 RDG 与 sign(λ₂)ρ 三维网格", "cube", vec![param_grid()], vec!["20", "1", "1", "{grid}", "1", "0", "0", "q"]),
                fn_item("20", "3", "IGM 弱相互作用分析", "独立梯度模型散点计算", "nci", vec![param_grid()], vec!["20", "2", "1", "{grid}", "2", "0", "0", "q"]),
                fn_item("20", "4", "mIGM 弱相互作用分析", "改进型独立梯度模型分析", "nci", vec![param_grid()], vec!["20", "3", "1", "{grid}", "2", "0", "0", "q"]),
                fn_item("20", "5", "IGMH (Hirshfeld) 分析", "基于 Hirshfeld 密度的 IGM 分析", "nci", vec![param_grid()], vec!["20", "4", "1", "{grid}", "2", "0", "0", "q"]),
                fn_item("20", "6", "DORI 密度重叠指示", "密度重叠区域指示函数计算", "nci", vec![param_grid()], vec!["20", "5", "1", "{grid}", "2", "0", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "21".into(),
            name: "21 · 能量分解分析 (EDA)".into(),
            description: "EDA-FF 分子力场能量分解与 sobEDA/色散贡献分析".into(),
            icon: "Flame".into(),
            items: vec![
                fn_item("21", "1", "EDA-FF 分子力场能量分解", "计算片段间静电与范德华相互作用能", "text", vec![], vec!["21", "1", "0", "q"]),
                fn_item("21", "4", "原子色散能量贡献分析", "分析体系色散作用的原子级分布", "text", vec![], vec!["21", "4", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "22".into(),
            name: "22 · 概念 DFT 分析 (CDFT)".into(),
            description: "Fukui 函数、双描述符、轨道权重 (OW) 反应性指标与超离域度".into(),
            icon: "Compass".into(),
            items: vec![
                fn_item("22", "6", "轨道权重 (OW) 简缩 Fukui 与双描述符", "单波函数直接计算亲核/亲电反应位点指标", "cdft", vec![], vec!["22", "6", "0", "q"]),
                fn_item("22", "8", "亲核/亲电超离域度计算", "输出各原子的亲核/亲电超离域性指数", "text", vec![], vec!["22", "8", "0", "q"]),
                fn_item("22", "5", "打印当前轨道权重因子", "查看 OW-CDFT 各轨道参与权重", "text", vec![], vec!["22", "5", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "23".into(),
            name: "23 · ETS-NOCV 分析".into(),
            description: "扩展过渡态与化学价自然轨道能量分解分析".into(),
            icon: "Activity".into(),
            items: vec![
                fn_item("23", "1", "ETS-NOCV 分析入口", "基于复合物与片段波函数分解成键通道", "text", vec![], vec!["23", "q"]),
            ],
        },
        MenuCategory {
            id: "24".into(),
            name: "24 · (超)极化率分析".into(),
            description: "静态/动态极化率、一阶/二阶超极化率与 SOS 分析".into(),
            icon: "Zap".into(),
            items: vec![
                fn_item("24", "1", "解析 Gaussian (超)极化率输出", "提取 α, β, γ 张量及各向异性", "text", vec![], vec!["24", "1", "0", "q"]),
                fn_item("24", "4", "计算分子中原子极化率", "分解分子极化率至各个原子贡献", "text", vec![], vec!["24", "4", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "25".into(),
            name: "25 · 电子离域与芳香性".into(),
            description: "HOMA、FLU、PDI、Shannon、多中心键级等芳香性量化指标".into(),
            icon: "Hexagon".into(),
            items: vec![
                fn_item("25", "7", "Shannon 芳香性指数", "计算体系电子密度 Shannon 芳香性指数", "aromaticity", vec![], vec!["25", "7", "0", "q"]),
                fn_item("25", "6", "HOMA / Bird 几何芳香性", "计算谐振子芳香性测度指数", "aromaticity", vec![], vec!["25", "6", "", "0", "q"]),
                fn_item("25", "9", "FLU 芳香性波动指数", "计算环电子离域波动指数", "aromaticity", vec![], vec!["25", "9", "", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "26".into(),
            name: "26 · 结构与几何分析".into(),
            description: "分子直径、长宽高、vdW 体积与平面性参数 (MPP/SDP)".into(),
            icon: "Ruler".into(),
            items: vec![
                fn_item("26", "3", "分子平面性 MPP / SDP", "评估分子共轭平面偏离程度", "text", vec![], vec!["26", "3", "a", "0", "q"]),
                fn_item("26", "8", "分子直径与三维包络尺寸", "计算分子最大直径及长宽高尺寸", "text", vec![], vec!["26", "8", "0", "q"]),
                fn_item("26", "14", "Marching Tetrahedron vdW 体积", "精确计算电子密度等值面包络分子体积", "text", vec![], vec!["26", "14", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "100".into(),
            name: "100 · 格式转换与扩展工具".into(),
            description: "导出 PDB / XYZ / WFN / WFX / Molden / FCH / MWFN 等多软件格式".into(),
            icon: "Share2".into(),
            items: vec![
                fn_item("100", "1", "导出为 XYZ 坐标文件", "生成标准笛卡尔坐标文件", "export", vec![], vec!["100", "2", "2", "wavecraft_export.xyz", "0", "q"]),
                fn_item("100", "2", "导出为 PDB 结构文件", "生成蛋白质数据库标准 PDB 文件", "export", vec![], vec!["100", "2", "1", "wavecraft_export.pdb", "0", "q"]),
                fn_item("100", "3", "导出为 WFN 波函数文件", "转换为 AIMALL/TopMod 通用 WFN 格式", "export", vec![], vec!["100", "2", "5", "wavecraft_export.wfn", "0", "q"]),
                fn_item("100", "4", "导出为 MWFN 现代格式", "导出 Multiwfn 专属高效文本波函数格式", "export", vec![], vec!["100", "2", "32", "wavecraft_export.mwfn", "0", "q"]),
                fn_item("100", "5", "计算分子 vdW 体积", "调用 Monte Carlo / 网格法估算 vdW 体积", "text", vec![], vec!["100", "3", "0", "q"]),
                fn_item("100", "9", "计算原子连通性与配位数", "输出每个原子的有效配位数", "text", vec![], vec!["100", "9", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "200".into(),
            name: "200 · 其他高级分析 (Part 2)".into(),
            description: "CVB 指数、径向分布函数、EI/BPI、电子相关指数与 BOD/NAdO".into(),
            icon: "Terminal".into(),
            items: vec![
                fn_item("200", "1", "计算核心-价层分叉指数 (CVB)", "定量表征氢键强弱的 ELF 分叉指标", "text", vec![], vec!["200", "1", "0", "q"]),
                fn_item("200", "9", "计算平均键长与平均配位数", "统计分子骨架平均成键参数", "text", vec![], vec!["200", "9", "0", "q"]),
                fn_item("200", "11", "计算实空间函数质心、矩与回转半径", "量化电子云空间扩展尺度", "text", vec![], vec!["200", "11", "1", "0", "q"]),
                fn_item("200", "18", "计算键长交替/键级交替 (BLA/BOA)", "共轭体系电子离域核心几何指标", "text", vec![], vec!["200", "18", "0", "q"]),
            ],
        },
        MenuCategory {
            id: "300".into(),
            name: "300 · 扩展物理量与模拟 (Part 3)".into(),
            description: "电偶极/四极/八极矩与 <r²>、费米能级、STM 模拟与自由体积".into(),
            icon: "Cpu".into(),
            items: vec![
                fn_item("300", "5", "计算电偶极/多极矩与电子空间范围 <r²>", "精确输出总偶极矩(Debye)、四极矩与 <R^2>", "multipole", vec![], vec!["300", "5", "0", "q"]),
                fn_item("300", "9", "确定体系费米能级", "输出体系 HOMO/LUMO 中点费米能级", "text", vec![], vec!["300", "9", "0", "q"]),
            ],
        },
    ]
}
