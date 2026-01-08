# Silicon Photonics Design: From Mode Solving to FDTD Verification

This repository demonstrates an end-to-end, Python-based design workflow for photonic components. It bridges the gap between physical simulation and layout generation, mirroring a PDK-level development environment.

The project focuses on building a robust, material-agnostic framework that can be adapted to various photonic platforms.

It implements a **"Physics-Driven Layout"** methodology:

- **Component Simulation (FEM):** Solve optical modes and optimize waveguide cross-sections using **Femwell**.
- **Verification (FDTD):** Validate full-device performance (S-parameters) using **Meep**, ensuring the layout matches the simulation intent.
- **Parametric Layout (PDK):** Generate DRC-clean, manufacturable GDSII geometry using **GDSFactory** (P-cell approach).

---

## 🛠️ Installation & Environment Management

> **⚠️ Critical Note:**
> This project relies on **Meep** (C++ FDTD engine) and **GDSFactory**. To ensure stability, we enforce a strict installation order via Conda.
>
> **Do NOT use `pip install meep`**, as it will fail to link against system MPI libraries.

### 1. Prerequisites

Ensure you have **Miniconda** or **Anaconda** installed.

- [Download Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### 2. Quick Setup (Recommended)

The easiest way to replicate the environment is using the provided YAML file. This installs Python 3.11, the Meep physics engine, and all layout tools automatically.

1. Open your terminal.
2. Navigate to this repository folder.
3. Run:

```bash
# Create the environment from the file
conda env create -f environment.yml

# Activate the environment
conda activate photonics
```
