@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [WaveCraft v4.0] 启动 Rust 量子化学核心与现代化 WebGL 工作台...
if exist "target\release\wavecraft-app.exe" (
    "target\release\wavecraft-app.exe" %*
) else if exist "target\debug\wavecraft-app.exe" (
    "target\debug\wavecraft-app.exe" %*
) else (
    cargo run --release --bin wavecraft-app -- %*
)
