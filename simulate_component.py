import sys
import os
import argparse
import yaml
import inspect
import numpy as np
import meep as mp
import gdsfactory as gf

# --- Path Setup ---
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

from utils.meep_utils.runner import MeepRunner
from utils.meep_utils import digital_twins

COMPONENT_REGISTRY = {}
for name, obj in inspect.getmembers(digital_twins):
    if inspect.isclass(obj) and obj.__module__.startswith("utils.meep_utils.digital_twins"):
        COMPONENT_REGISTRY[name] = obj

def run_simulation():
    parser = argparse.ArgumentParser()
    parser.add_argument("--component", type=str, required=True)
    parser.add_argument("--config", type=str, required=True)
    parser.add_argument("--out", type=str, required=True)
    args = parser.parse_args()

    # --- Load Params ---
    with open(args.config, 'r') as f:
        params = yaml.safe_load(f)

    n_eff = params.pop('neff', 2.85)
    resolution = params.pop('resolution', 30)
    
    # --- Run Simulation (Single Step) ---
    runner = MeepRunner(n_core=n_eff, n_clad=1.444, resolution=resolution)

    if args.component not in COMPONENT_REGISTRY:
        print(f"❌ Error: {args.component} not found.")
        sys.exit(1)

    print(f"🚀 Running Device Simulation: {args.component}")
    ComponentClass = COMPONENT_REGISTRY[args.component]
    dut = ComponentClass(**params)

    # Note: No 'calibration_flux' needed anymore!
    wavelengths, s_params = runner.simulate_component(dut, wavelength=1.55)

    # --- Save Results ---
    out_dir = os.path.dirname(args.out)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir)

    np.savez(args.out, wvl=np.array(wavelengths), trans=s_params)
    print(f"✅ Simulation Complete. Results saved to: {args.out}")

if __name__ == "__main__":
    run_simulation()