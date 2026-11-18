#!/usr/bin/env node
"use strict";

const { spawnSync } = require("child_process");
const fs = require("fs");
const path = require("path");

function findPython() {
  const candidates = process.platform === "win32" ? ["python", "py", "python3"] : ["python3", "python"];
  for (const cmd of candidates) {
    const res = spawnSync(cmd, ["--version"], { stdio: "ignore" });
    if (res.status === 0) return cmd;
  }
  return null;
}

function main() {
  // 1. Check local Rust release binary if invoked inside WaveCraft workspace
  const localExe = path.resolve(__dirname, "..", "target", "release", "wavecraft-app.exe");
  if (fs.existsSync(localExe)) {
    const r = spawnSync(localExe, process.argv.slice(2), { stdio: "inherit" });
    process.exit(r.status ?? 0);
  }

  // 2. Self-healing Python wavecraft_gui launcher
  const py = findPython();
  if (!py) {
    console.error("[WaveCraft] Error: Python 3.9+ not found in PATH. Please install Python or clone https://github.com/yangdw2026/WaveCraft.");
    process.exit(1);
  }

  const check = spawnSync(py, ["-c", "import wavecraft_gui"], { stdio: "ignore" });
  if (check.status !== 0) {
    console.log("[WaveCraft] Installing wavecraft-gui from PyPI...");
    const install = spawnSync(py, ["-m", "pip", "install", "--upgrade", "wavecraft-gui"], {
      stdio: "inherit",
    });
    if (install.status !== 0) {
      console.error("[WaveCraft] Failed to install wavecraft-gui via pip.");
      process.exit(install.status ?? 1);
    }
  }

  const run = spawnSync(py, ["-m", "wavecraft_gui.cli", ...process.argv.slice(2)], {
    stdio: "inherit",
  });
  process.exit(run.status ?? 0);
}

main();
