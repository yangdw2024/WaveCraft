# @yangdw2024/wavecraft

WaveCraft v4.0 — High-performance **Rust + React 19 / Three.js WebGL** quantum chemistry wavefunction visualization workbench for **Multiwfn 3.8**.

## Quick Start

```bash
npx @yangdw2024/wavecraft
```

Or install globally:

```bash
npm install -g @yangdw2024/wavecraft
wavecraft --port 18420
```

## Features
- **3D WebGL Molecule & Orbital Isosurfaces**: Pure Rust Marching Cubes dual-phase isosurface extraction + Three.js interactive measurement & AIM critical point overlay.
- **Realspace 1D / 2D / 3D**: 14 realspace functions (`ρ(r)`, `ELF`, `LOL`, `ESP`, `∇²ρ`, `RDG`, `sign(λ₂)ρ`, `ALIE`, `IRI`, etc.), 1D bond-axis profiles, and 2D slice heatmaps with 5 scientific colormaps.
- **Full Multiwfn 3.8 Coverage (Menus 0–26, 100, 200, 300)**: 16 atomic charge methods, 7+ bond order models, TDOS, IR/Raman/UV-Vis/ECD spectra, NCI/IGM/DORI weak interactions, Fuzzy LI/DI matrices, Conceptual DFT Fukui indices, dipole/multipole moments, and multi-format export.

Repository: https://github.com/yangdw2024/WaveCraft
