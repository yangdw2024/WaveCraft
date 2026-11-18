#!/usr/bin/env python3
"""CLI entrypoint for WaveCraft v4.0."""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _find_binary() -> Path | None:
    pkg_dir = Path(__file__).resolve().parent
    candidates = [
        pkg_dir / "assets" / "wavecraft-app.exe",
        pkg_dir / "assets" / "wavecraft-app",
        Path.cwd() / "target" / "release" / "wavecraft-app.exe",
        Path.cwd() / "target" / "release" / "wavecraft-app",
    ]
    for c in candidates:
        if c.exists() and c.is_file():
            return c
    return None


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="wavecraft",
        description="WaveCraft v4.0 - Quantum Chemistry Wavefunction Analysis Workbench for Multiwfn 3.8",
    )
    parser.add_argument("--port", type=int, default=18420, help="HTTP server port (default: 18420)")
    parser.add_argument("--no-open", action="store_true", help="Do not auto-open desktop window")
    parser.add_argument("--version", action="store_true", help="Print version and exit")
    args = parser.parse_args()

    if args.version:
        print("wavecraft-gui 4.0.1")
        return 0

    binary = _find_binary()
    pkg_dir = Path(__file__).resolve().parent
    assets_dir = pkg_dir / "assets"

    if binary is None:
        if shutil.which("cargo") and (Path.cwd() / "Cargo.toml").exists():
            cmd = ["cargo", "run", "--release", "--bin", "wavecraft-app", "--", "--port", str(args.port)]
            if args.no_open:
                cmd.append("--no-open")
            return subprocess.call(cmd)
        print(
            "Error: wavecraft-app binary not found. On Linux/macOS, clone https://github.com/yangdw2024/WaveCraft "
            "and build with `cargo build --release`.",
            file=sys.stderr,
        )
        return 1

    # Ensure frontend/dist is discoverable from working directory when launched from assets
    run_cwd = assets_dir if (assets_dir / "dist" / "index.html").exists() else Path.cwd()
    cmd = [str(binary), "--port", str(args.port)]
    if args.no_open:
        cmd.append("--no-open")

    try:
        return subprocess.call(cmd, cwd=str(run_cwd))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())
