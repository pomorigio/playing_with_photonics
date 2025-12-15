import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from typing import Union


def interpolate_design_parameter(
    x_sweep: Union[list, np.array], 
    y_sweep: Union[list, np.array], 
    target_x: float, 
    interpolation_type: str = 'cubic'
) -> float:
    """
    Interpolates simulation sweep data to find the optimal design parameter.
    Generic: Works for Couplers (Gap->Length), MMIs (Width->Length), etc.

    Args:
        x_sweep: The array of swept parameters (e.g., Gaps, Widths).
        y_sweep: The array of simulation results (e.g., L_3dB, Transmission).
        target_x: The specific constraint value you need (e.g., Gap=0.200).
        interpolation_type: 'linear', 'cubic', etc. Passed to scipy.interp1d.

    Returns:
        float: The interpolated result (e.g., Optimal Length).
    """
    # 1. Pythonic Conversion & Cleaning (Masking)
    x = np.array(x_sweep)
    y = np.array(y_sweep)
    
    # Create a mask of valid (finite) data points
    # This removes NaNs (failed sims) and Infs in one line
    mask = np.isfinite(y)
    
    x_clean = x[mask]
    y_clean = y[mask]

    # 2. Safety Checks (Fail Fast)
    if len(x_clean) < 2:
        raise ValueError(f"Insufficient valid data points ({len(x_clean)}) for interpolation.")

    # Check bounds to warn about dangerous extrapolation
    if target_x < x_clean.min() or target_x > x_clean.max():
        print(f"⚠️ Warning: Target {target_x} is outside sweep range "
              f"[{x_clean.min():.3f}, {x_clean.max():.3f}]. Extrapolation may be inaccurate.")

    # 3. Interpolate
    # fill_value="extrapolate" allows predicting values slightly outside the range
    f = interp1d(x_clean, y_clean, kind=interpolation_type, fill_value="extrapolate")
    
    return float(f(target_x))


def plot_spectra(wvl, transmissions, title="Transmission", y_min=None, target_level=None, db_unit=True):
    """
    Generic transmission plotter with toggle for dB or Linear scale.
    
    Args:
        wvl (array): Wavelength array.
        transmissions (dict): {port_name: transmissions_array}.
        title (str): Plot title.
        y_min (float): Minimum Y-axis limit. 
                       - If None and db_unit=True, defaults to -40 dB.
                       - If None and db_unit=False, defaults to 0.0.
        target_level (float): Optional horizontal line to mark a target (e.g. -3 for dB, 0.5 for Linear).
        db_unit (bool): If True, plots in dB. If False, plots in Linear scale (0.0-1.0).
    """
    plt.figure(figsize=(10, 6))
    
    # 1. Sort ports for consistent legend order
    port_names = sorted(transmissions.keys())
    
    # 2. Iterate and Plot
    for name in port_names:
        data = transmissions[name]
        
        if db_unit:
            # Convert to dB (Safe log10)
            y_values = 10 * np.log10(np.abs(data) + 1e-15)
            ylabel = "Transmission (dB)"
            default_ymin = -40
            top_limit = 0.5 # Slightly above 0dB for visibility
        else:
            # Linear Scale
            y_values = np.abs(data)
            ylabel = "Transmission (Linear)"
            default_ymin = 0.0
            top_limit = 1.05 # Slightly above 100%

        plt.plot(wvl, y_values, label=name, linewidth=2)

    # 3. Optional Target Line
    if target_level is not None:
        plt.axhline(target_level, color='k', linestyle='--', alpha=0.5, label=f'Target {target_level}')

    # 4. Styling
    plt.xlabel("Wavelength ($\mu m$)")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.legend(loc='best')
    plt.grid(True, which='both', linestyle='--', alpha=0.5)
    
    # 5. Smart Limits
    # Use user-provided limit if existing, else use smart default
    bottom_limit = y_min if y_min is not None else default_ymin
    
    plt.ylim(bottom=bottom_limit, top=top_limit)
    plt.tight_layout()
    plt.show()