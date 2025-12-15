# Silicon Photonics Design: From Mode Solving to FDTD Verification

This repository demonstrates an end-to-end, Python-based design workflow for photonic components. It bridges the gap between physical simulation and layout generation, mirroring a PDK-level development environment.

The project focuses on building a robust, material-agnostic framework that can be adapted to various photonic platforms.

It implements a "Physics-Driven Layout" methodology:

- Component Simulation (FEM): Solve optical modes and optimize waveguide cross-sections using Femwell.

- Verification (FDTD): Validate full-device performance (S-parameters) using Meep, ensuring the layout matches the simulation intent.

- Parametric Layout (PDK): Generate DRC-clean, manufacturable GDSII geometry using GDSFactory (P-cell approach).

---

## 🛠️ Installation & Environment Management

⚠️ Critical Note for Users: To ensure stability with system-level MPI/HDF5 dependencies, this project enforces a Conda-based environment. Please do not use pip install meep directly, as it often leads to linkage errors.

### 1. Prerequisites

Ensure you have **Miniconda** or **Anaconda** installed.

- [Download Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### 2. Set up the Environment

Run the following commands in your terminal to create a clean environment named e.g. `photonics`.

```bash
# 1. Create the environment and install Meep (from conda-forge)
conda create -n photonics -c conda-forge pymeep -y

# 2. Activate the environment
conda activate photonics

# 3. Install the remaining Python libraries
# (Femwell, GDSFactory, and visualization tools)
pip install femwell gdsfactory scikit-fem shapely pandas matplotlib ipykernel
```
