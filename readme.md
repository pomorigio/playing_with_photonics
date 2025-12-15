# Silicon Photonics Design: From Mode Solving to FDTD Verification

This repository contains a complete workflow for designing Silicon Photonics components (Waveguides, Couplers, Phase Shifters) using open-source Python tools.

It implements a "Physics-First" design methodology:

1.  **Physics:** Solve modes and calculate physical dimensions using **Femwell** (FEM).
2.  **Layout:** Generate manufacturable GDSII geometry using **GDSFactory**.
3.  **Verification:** Verify full-device performance using **Meep** (FDTD).

---

## 🛠️ Installation

**⚠️ Important:** Do not use `pip install meep`. It will not work.
This project requires a **Conda** environment to handle the system-level dependencies (MPI, HDF5) required by the Meep simulation engine.

### 1. Prerequisites

Ensure you have **Miniconda** or **Anaconda** installed.

- [Download Miniconda](https://docs.conda.io/en/latest/miniconda.html)

### 2. Set up the Environment

Run the following commands in your terminal to create a clean environment named `photonics`.

```bash
# 1. Create the environment and install Meep (from conda-forge)
conda create -n photonics -c conda-forge pymeep -y

# 2. Activate the environment
conda activate photonics

# 3. Install the remaining Python libraries
# (Femwell, GDSFactory, and visualization tools)
pip install femwell gdsfactory scikit-fem shapely pandas matplotlib ipykernel
```
