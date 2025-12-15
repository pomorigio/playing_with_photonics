import meep as mp
import numpy as np
import matplotlib.pyplot as plt


class MeepRunner:
    """
    A generic FDTD simulation engine for DigitalTwin objects.
    Handles geometry building, port monitoring, and auto-normalized data extraction.
    """
    def __init__(self, n_core=3.47, n_clad=1.444, resolution=50):
        self.materials = {
            "core": mp.Medium(index=n_core),
            "clad": mp.Medium(index=n_clad)
        }
        self.resolution = resolution
        self.sim = None  # Holds the latest simulation instance

    def plot_structure(self, component):
        """
        Visualizes the geometry of the component without running a simulation.
        Useful for verifying port positions and source sizes.
        """
        self._build_sim(component, setup_only=True)
        
        plt.figure(figsize=(10, 6))
        self.sim.plot2D()
        
        # Overlay port labels for clarity
        for name, p in component.get_ports().items():
            plt.text(p['center'].x, p['center'].y, name, color='white', weight='bold')
            
        plt.title(f"Digital Twin Geometry: {type(component).__name__}")
        plt.show()

    def simulate_component(self, component, wavelength=1.55, bandwidth=0.1):
        """
        Runs the FDTD simulation until fields decay and returns normalized S-parameters.
        
        Returns:
            wl (np.array): Wavelength array.
            s_params (dict): Normalized transmission {port_name: np.array(0.0 - 1.0)}.
        """
        # 1. Build & Run
        sim, monitors = self._build_sim(component, wavelength, bandwidth)
        
        # Determine run time: stop when fields decay at the furthest output port
        furthest_port = max(component.get_ports().values(), key=lambda p: p['center'].x)
        print(f"Running FDTD for {type(component).__name__}...")
        
        sim.run(until_after_sources=mp.stop_when_fields_decayed(50, mp.Ey, furthest_port['center'], 1e-3))
        
        # 2. Extract & Normalize Data
        # Get freq points from the first monitor available
        freqs = np.array(mp.get_flux_freqs(next(iter(monitors.values()))))
        wl = 1.0 / freqs
        
        # Get raw flux (power) from all monitors
        raw_flux = {name: np.array(mp.get_fluxes(mon)) for name, mon in monitors.items()}
        
        # Calculate Total Power at outputs for self-normalization
        # Assumption: P_in ~ sum(P_out) for low-loss devices
        total_power = np.zeros_like(freqs)
        for p_data in raw_flux.values():
            total_power += p_data
            
        # Avoid division by zero
        total_power[total_power == 0] = 1.0
        
        # Normalize: T_port = P_port / P_total
        s_params = {name: data / total_power for name, data in raw_flux.items()}
        
        return wl, s_params

    def visualize_fields(self, component, wavelength=1.55, time=50):
        """
        Runs a short 'video' simulation to check mode launching and physics.
        Does NOT run to completion. Use this to debug source/mode issues.
        """
        sim, _ = self._build_sim(component, wavelength)
        print(f"Running field snapshot (t={time})...")
        sim.run(until=time)
        
        plt.figure(figsize=(10, 6))
        sim.plot2D(fields=mp.Ey, plot_sources=True, plot_monitors=True)
        plt.title(f"Field Snapshot at t={time}")
        plt.show()

    def visualize_last_run(self):
        """Plots the final field state of the most recent simulation."""
        if self.sim:
            plt.figure(figsize=(10, 6))
            self.sim.plot2D(fields=mp.Ey)
            plt.title("Field State (End of Run)")
            plt.show()
        else:
            print("No simulation has been run yet.")

    def _build_sim(self, component, wavelength=1.55, bandwidth=0.1, setup_only=False):
        """Internal helper to construct the Simulation object."""
        # 1. Geometry & Domain
        pad, dpml = 2.0, 1.0
        geo = component.get_geometry(self.materials["core"], self.materials["clad"])
        ports = component.get_ports()
        bounds = component.get_bounds()
        
        cell = mp.Vector3(bounds.x + 2*(pad+dpml), bounds.y + 2*(pad+dpml), 0)
        
        # 2. Source (Input at 'o1')
        fcen = 1 / wavelength
        df = bandwidth * fcen
        p_in = ports["o1"]
        
        sources = [mp.Source(
            mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ey, # TE Mode
            center=p_in['center'],
            size=p_in['size']
        )]
        
        # 3. Initialize Sim
        sim = mp.Simulation(
            cell_size=cell,
            boundary_layers=[mp.PML(dpml)],
            geometry=geo,
            sources=sources,
            resolution=self.resolution,
            default_material=self.materials["clad"]
        )
        self.sim = sim # Store reference
        
        if setup_only: return sim, None

        # 4. Monitors (All ports except 'o1')
        # We use 101 freq points for smooth spectra
        monitors = {
            name: sim.add_flux(fcen, df, 101, mp.FluxRegion(center=p['center'], size=p['size']))
            for name, p in ports.items() if name != "o1"
        }
        
        return sim, monitors