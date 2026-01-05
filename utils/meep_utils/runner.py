import meep as mp
import numpy as np
import matplotlib.pyplot as plt

class MeepRunner:
    """
    A generic FDTD simulation engine for DigitalTwin objects.
    Uses Mode Decomposition to extract accurate S-parameters (Reflection & Transmission).
    """
    def __init__(self, n_core=3.47, n_clad=1.444, resolution=30):
        self.materials = {
            "core": mp.Medium(index=n_core),
            "clad": mp.Medium(index=n_clad)
        }
        self.resolution = resolution
        self.sim = None

    def plot_structure(self, component):
        """Visualizes the geometry."""
        self._build_sim(component, setup_only=True)
        plt.figure(figsize=(10, 6))
        self.sim.plot2D()
        for name, p in component.get_ports().items():
            plt.text(p['center'].x, p['center'].y, name, color='red', weight='bold')
        plt.title(f"Digital Twin: {type(component).__name__}")
        plt.show()

    def simulate_component(
            self,
            component,
            wavelength=1.55,
            bandwidth=0.1,
            decay_by=1e-3,
            padding=2.0,
            pml_thickness=1.0,
            **kwargs
    ):
        """
        Runs FDTD simulation and extracts S-parameters using Mode Decomposition.
        """
        sim, monitors = self._build_sim(
            component=component,
            wavelength=wavelength,
            bandwidth=bandwidth,
            padding=padding,
            pml_thickness=pml_thickness
        )

        # 2. Run Simulation
        ports = component.get_ports()
        if ports:
            # Monitor decay at the furthest port from the input
            furthest_port = max(ports.values(), key=lambda p: abs(p['center'].x))
            monitor_point = furthest_port['center']
        else:
            monitor_point = mp.Vector3(0, 0, 0)

        print(f"Running FDTD (Mode Decomposition) for {type(component).__name__}...")
        sim.run(
            until_after_sources=mp.stop_when_fields_decayed(
                50, 
                mp.Ey, 
                monitor_point, 
                decay_by
                )
            ) 

        # 3. Extract Mode Coefficients 
        # We assume the Fundamental TE Mode (Band 1) 
        # A. Analyze Input (o1) for Source Power & Reflection
        res_in = sim.get_eigenmode_coefficients(monitors['o1'], [1], eig_parity=mp.NO_PARITY)
        # Forward wave at Input = SOURCE POWER 
        P_in = np.abs(res_in.alpha[0, :, 0])**2 
        # Backward wave at Input = REFLECTION 
        P_refl = np.abs(res_in.alpha[0, :, 1])**2

        # Get Wavelengths 
        freqs = np.array(mp.get_flux_freqs(monitors['o1'])) 
        wl = 1.0 / freqs 
        
        # 4. Extract S-parameters
        s_params = {}
        # --- Input Port (Reflection S11) ---
        s_params['o1'] = P_refl / P_in 

        # --- Output Ports (Transmission S21, S31, etc.) ---
        for name, monitor in monitors.items():
            if name == 'o1': continue
            res_out = sim.get_eigenmode_coefficients(
                monitor, [1], eig_parity=mp.NO_PARITY)
            P_out = np.abs(res_out.alpha[0, :, 0])**2 
            s_params[name] = P_out / P_in 
            
        return wl, s_params 


    def _build_sim(self, 
                   component, 
                   wavelength=1.55, 
                   bandwidth=0.1, 
                   setup_only=False, 
                   padding=1.0, 
                   pml_thickness=1.0):
        """Helper to build simulation objects."""

        # 1. GET COMPONENT DATA
        geo = component.get_geometry(self.materials["core"], 
                                     self.materials["clad"])
        ports = component.get_ports()
        bounds = component.get_bounds()

        # 2. DEFINE CELL SIZE (The "Automatic Box")
        # The cell grows with the component so the gap is always 'padding'
        cell = mp.Vector3(
            bounds.x + 2*(padding+pml_thickness), 
            bounds.y + 2*(padding+pml_thickness),
            0
        )
        pml_layers = [mp.PML(pml_thickness)]

        # 3. CREATE EXTENSIONS ("Patch cables")
        extension_length = padding + pml_thickness + 1.0 # 1.0 um extra
        extensions = []
        for name, p in ports.items():
            direction = -1 if p['center'].x < 0 else 1

            shift_amount = direction * (extension_length / 2)

            blk = mp.Block(
                size = mp.Vector3(extension_length, 
                                0.5,  # These are the width and height dimensions of the input wg
                                0.22),
                center = p['center'] + mp.Vector3(shift_amount, 0, 0),
                material = self.materials['core']
            )
            extensions.append(blk)

        # 4. MERGE GEOMETRY
        full_geometry = geo + extensions
        
        fcen = 1 / wavelength
        df = bandwidth * fcen
        
        if "o1" not in ports:
            raise ValueError("Component must have 'o1' port.")
        
        p_in = ports["o1"]
        dir_in = -1 if p_in['center'].x < 0 else 1
        # Move Source DEEP into the extension (e.g. 1.0 um away from port)
        source_pos = p_in['center'] + mp.Vector3(dir_in * 1.0, 0, 0) # <--- SHIFT OUT
        
        # Source sits exactly at the port interface
        sources = [mp.EigenModeSource(
            src=mp.GaussianSource(fcen, fwidth=df),
            center=source_pos,
            size=p_in['size'],
            eig_band=1,
            eig_parity=mp.NO_PARITY,
            eig_match_freq=True
        )]
        
        sim = mp.Simulation(
            cell_size=cell,
            boundary_layers=pml_layers,
            geometry=full_geometry, # <--- Uses the extended geometry
            sources=sources,
            resolution=self.resolution,
            symmetries=getattr(component, 'symmetry', []),
            default_material=self.materials["clad"]
        )
        self.sim = sim
        
        if setup_only: return sim, None

        # 5. DYNAMIC MONITORS
        monitors = {}
        for name, p in ports.items():
            # Determine direction of the extension
            # Left Port (-1) -> Extension is Left -> Shift Left
            # Right Port (+1) -> Extension is Right -> Shift Right
            direction = -1 if p['center'].x < 0 else 1
            
            # Shift 0.5 um INTO the extension (away from the device)
            # This ensures we are measuring in the straight "Patch Cable"
            shift = mp.Vector3(direction * 0.5, 0, 0)
            
            monitors[name] = sim.add_mode_monitor(
                fcen, df, 101, 
                mp.FluxRegion(center=p['center'] + shift, size=p['size'])
            )
        
        return sim, monitors