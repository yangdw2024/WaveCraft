# WaveCraft v4.0 · 量子化学波函数可视化分析平台

WaveCraft v4.0 是对原 PyQt5/Python v3.1 版本（已修复并归档至 `legacy_python/`）进行的**底层全栈重构版本**。系统底层采用 **Rust**（Tokio 异步引擎 + Axum HTTP 服务 + 原生 Gaussian Cube/Marching Cubes 算法 + GBK 编解码管道），前端采用 **React 19 + TypeScript + TailwindCSS + Three.js (WebGL)**，打造 **Quantum Obsidian** 现代暗黑科研工作台。

## 核心技术栈

- **Rust 核心引擎 (`crates/wavecraft-core`)**
  - `config.rs`: 自动探测本地 `Multiwfn.exe` 与官方 `examples/` 波函数示例库，持久化保存配置与历史记录。
  - `engine.rs`: 基于 Tokio 的隔离目录异步 Multiwfn 进程池（GBK 编解码、防目录污染、超时保护、任务队列审计）。
  - `cube.rs`: 高性能 Gaussian `.cub/.cube` 解析器、任意平面 2D 切面提取、以及纯 Rust 原生 **3D Marching Cubes 双相等值面网格提取引擎**。
  - `parser.rs`: 内置 1–86 号元素周期表、共价半径自动成键算法、轨道能级/HOMO-LUMO Gap 解析、16 种原子电荷与 10 种键级解析、QTAIM 临界点、NCI/IGM 散点、Gaussian TDDFT/IR/Raman 谱峰与连续高斯/洛伦兹展宽。
  - `commands.rs` & `menu_catalog.rs`: 针对 Multiwfn 3.8 (2026-Jan-7) 实测校准后的命令序列生成器与完整功能目录。
- **Rust 应用服务 (`crates/wavecraft-app`)**
  - 提供全套 `/api/*` REST 接口、文件上传与下载、并自动托管 `frontend/dist` 静态产物，支持以 Edge/Chrome `--app` 独立桌面窗口模式运行。
- **现代化前端 (`frontend/`)**
  - **Three.js 3D 分子与轨道视口**：支持球棍/空间填充/线框切换、电荷静电映射着色、点击原子实时测量距离与键角、正负双相 3D 等值面透明度/网格控制、AIM 临界点 3D 标注、PNG 高清截图。
  - **HTML5 Canvas 2D 热图**：支持 XY/XZ/YZ 切面滑块、Viridis/Plasma/Inferno/Coolwarm/RdBu 5 种科学色板、等高线与原子投影、鼠标十字准星读取坐标与数值。
  - **11 大全功能工作台 + `Ctrl+K` 全局命令调色板**。

## 快速启动

### 方式一：PyPI 安装（推荐 Windows 用户）
```bash
pip install wavecraft-gui
wavecraft
```

### 方式二：npm / npx 启动
```bash
npx @yangdw2024/wavecraft
```

### 方式三：从源码构建
```bat
:: 1. 构建前端
cd frontend
pnpm build
cd ..

:: 2. 编译 Rust Release 版本并启动桌面应用
cargo build --release
start_wavecraft.bat
```

服务默认监听 `http://127.0.0.1:18420`，支持传入 `--port 18420` 与 `--no-open` 参数。

## 发布地址
- **GitHub**: https://github.com/yangdw2024/WaveCraft
- **PyPI**: https://pypi.org/project/wavecraft-gui/
- **npm**: https://www.npmjs.com/package/@yangdw2024/wavecraft
