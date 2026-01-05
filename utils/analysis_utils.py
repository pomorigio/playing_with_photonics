import numpy as np
import matplotlib.pyplot as plt
import copy

class CornerAnalyzer:
    """
    Automates Design for Manufacturability (DFM) by simulating 
    process variations (corners) on a Digital Twin.
    """
    def __init__(self, runner):
        self.runner = runner
        self.corners = {}  # Stores {name: {param: delta}}
        self.results = {}  # Stores {name: s_params}

    def add_corner(self, name, variations):
        """
        Define a process corner.
        Args:
            name (str): Label (e.g., 'Over-Etch', 'Thick-Silicon').
            variations (dict): Parameter shifts (e.g., {'width': -0.02, 'gap': +0.02}).
        """
        self.corners[name] = variations

    def run_sweep(self, component_class, nominal_params, wavelength=1.55):
        """
        Runs FDTD for all defined corners.
        Args:
            component_class: The class of the device (e.g., MMI1x2Twin).
            nominal_params (dict): The optimized design parameters.
        """
        print(f"--- Starting Corner Analysis for {component_class.__name__} ---")
        
        # Always run Nominal first if not added
        if 'Nominal' not in self.corners:
            self.corners = {'Nominal': {}} | self.corners

        for corner_name, deltas in self.corners.items():
            print(f"Simulating Corner: {corner_name}...")
            
            # 1. Apply Variations
            # We copy the nominal parameters and add the deltas
            current_params = nominal_params.copy()
            for param, delta in deltas.items():
                if param in current_params:
                    current_params[param] += delta
                else:
                    print(f"Warning: Parameter '{param}' not found in component definition.")

            # 2. Instantiate the Twin with perturbed parameters
            # The ** operator unpacks the dictionary into arguments
            device = component_class(**current_params)
            
            # 3. Simulate
            # Note: For speed, we don't recalibrate every single corner (reflection might be slightly off),
            # but for Transmission trends, self-normalization is usually acceptable here.
            # If you want perfect S11, pass calibration_flux here.
            wl, s_params = self.runner.simulate_component(device, wavelength=wavelength)
            
            # 4. Store Data (Extract scalar value at center wavelength)
            idx = np.argmin(np.abs(wl - wavelength))
            self.results[corner_name] = {port: np.abs(data[idx])**2 for port, data in s_params.items()}

        print("--- Analysis Complete ---")

    def plot_box_whisker(self, port_of_interest='o3'):
        """
        Visualizes the yield/spread of a specific output port.
        """
        labels = []
        values = []
        
        for name, res in self.results.items():
            if port_of_interest in res:
                labels.append(name)
                values.append(10 * np.log10(res[port_of_interest])) # Convert to dB

        plt.figure(figsize=(8, 5))
        plt.bar(labels, values, color='skyblue', edgecolor='black')
        plt.axhline(-3, color='r', linestyle='--', label='Target -3dB')
        plt.ylabel(f"Transmission at {port_of_interest} (dB)")
        plt.title(f"Corner Analysis: Process Tolerance")
        plt.ylim(bottom=min(values)-1, top=0)
        plt.grid(axis='y', alpha=0.5)
        plt.legend()
        plt.show()