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
    
    def visualize_fields(self, component, wavelength=1.55, padding=2.0, pml_thickness=1.0):
        """Runs a quick simulation and plots the field intensity."""
        sim, _ = self._build_sim(
            component, 
            wavelength=wavelength, 
            padding=padding, 
            pml_thickness=pml_thickness
        )
        
        print("Running field visualization...")
        # Run just long enough for light to pass through (e.g. 2 passes)
        duration = (component.get_bounds().x + 2*padding) * 3.47 * 2 
        sim.run(until=duration)
        
        plt.figure(figsize=(12, 8))
        # plot2D with fields=mp.Ey (or mp.Ez) creates the heatmap
        # output_plane=mp.Volume(...) ensures we slice the correct plane
        sim.plot2D(fields=mp.Ey, plot_sources=True, plot_monitors=False)
        plt.title(f"Field Profile (Ey) at $\lambda$={wavelength} $\mu m$")
        plt.show()


    def plot_performance_dashboard(self, component, wavelength=1.55, padding=2.0, pml_thickness=1.0):
        """
        Runs a simulation to get quantitative S-parameters, then plots the 
        fields with the transmission values overlayed as text labels.
        """
        # 1. QUANTITATIVE STEP: Get the S-parameters
        # We assume the user has already fixed the 'simulate_component' method
        # with the symmetry correction we discussed.
        print("Calculating S-parameters...")
        wl, s_params = self.simulate_component(
            component, 
            wavelength=wavelength, 
            padding=padding, 
            pml_thickness=pml_thickness,
            decay_by=1e-5
        )
        
        # Extract values at the target wavelength
        # (Since simulate_component returns a spectrum, we pick the center point)
        idx = (np.abs(wl - wavelength)).argmin()
        trans_data = {}
        for port, val in s_params.items():
            if port == 'o1': continue
            trans_db = 10 * np.log10(val[idx])
            trans_data[port] = trans_db

        # 2. QUALITATIVE STEP: Run Field Visualization
        print("Generating Field Plot...")
        sim, _ = self._build_sim(
            component, 
            wavelength=wavelength, 
            padding=padding, 
            pml_thickness=pml_thickness
        )
        
        # Run just long enough for light to propagate through
        duration = (component.get_bounds().x + 2*padding) * 3.47 * 1.5 
        sim.run(until=duration)
        
        # 3. PLOT COMBINED VIEW
        plt.figure(figsize=(14, 6))
        
        # A. The Field Plot (Ez)
        sim.plot2D(fields=mp.Ey, plot_sources=True, plot_monitors=False)
        
        # B. The Overlay Text
        ports = component.get_ports()
        
        # Add Input Label
        p1 = ports['o1']['center']
        plt.text(p1.x - 1.5, p1.y + 0.5, "Input Source", 
                 color='white', weight='bold', fontsize=12,
                 bbox=dict(facecolor='black', alpha=0.6))

        # Add Output Labels with Transmission Data
        for name, db_val in trans_data.items():
            p = ports[name]['center']
            
            # Formatting: Green if > -4dB (Good), Red if < -4dB (Bad)
            color = 'green' if db_val > -4.0 else 'red'
            
            label = f"{name.upper()}\n{db_val:.2f} dB"
            
            # Place text slightly to the right of the port
            plt.text(p.x + 1.0, p.y, label, 
                     color='white', weight='bold', fontsize=12,
                     bbox=dict(facecolor=color, alpha=0.7, edgecolor='white'),
                     horizontalalignment='left',
                     verticalalignment='center')

        plt.title(f"MMI Performance Dashboard @ {wavelength} $\mu m$", fontsize=16)
        plt.show()


    def _build_sim(self, 
                   component, 
                   wavelength=1.55, 
                   bandwidth=0.1, 
                   setup_only=False, 
                   padding=2.0, 
                   pml_thickness=1.0):
        """Helper to build simulation objects."""

        # 1. GET COMPONENT DATA
        geo = component.get_geometry(self.materials["core"], 
                                     self.materials["clad"])
        ports = component.get_ports()
        bounds = component.get_bounds()

        # 2. DEFINE CELL SIZE
        # We add padding + PML thickness to the component's bounding box
        cell = mp.Vector3(
            bounds.x + 2*(padding+pml_thickness), 
            bounds.y + 2*(padding+pml_thickness),
            0 # Z=0 forces a 2D simulation grid
        )
        pml_layers = [mp.PML(pml_thickness)]

        # 3. CREATE EXTENSIONS ("Virtual Fibers")
        # Length = Padding + PML + 1.0um Safety Margin
        # This ensures the waveguide goes ALL THE WAY out of the simulation
        extension_length = padding + pml_thickness + 1.0 
        
        extensions = []
        for name, p in ports.items():
            # Determine direction: -1 for Left (Input), +1 for Right (Outputs)
            direction = -1 if p['center'].x < 0 else 1

            # Shift the block so it starts exactly at the port and goes outward
            shift_amount = direction * (extension_length / 2)
            
            wg_width = 0.5

            blk = mp.Block(
                # --- FIX 2: INFINITE Z FOR 2D ---
                size = mp.Vector3(extension_length, wg_width, mp.inf),
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
        
        # 5. SOURCE PLACEMENT
        p_in = ports["o1"]
        dir_in = -1 if p_in['center'].x < 0 else 1
        
        # Move Source into the padding region (e.g., 1.0um away from taper)
        # This allows the mode to form before hitting the device
        monitor_size = mp.Vector3(0, 2.0, 0)
        source_pos = p_in['center'] + mp.Vector3(dir_in * 1.0, 0, 0)
        
        sources = [mp.EigenModeSource(
            src=mp.GaussianSource(fcen, fwidth=df),
            component=mp.Ey,
            center=source_pos,
            size=monitor_size,
            eig_band=1,
            eig_parity=mp.NO_PARITY,
            eig_match_freq=True
        )]
        
        # 6. BUILD SIMULATION
        sim = mp.Simulation(
            cell_size=cell,
            boundary_layers=pml_layers,
            geometry=full_geometry,
            sources=sources,
            resolution=self.resolution,
            symmetries=getattr(component, 'symmetry', []),
            default_material=self.materials["clad"]
        )
        self.sim = sim
        
        if setup_only: return sim, None

        # 7. DYNAMIC MONITORS
        monitors = {}
        for name, p in ports.items():
            direction = -1 if p['center'].x < 0 else 1
            
            # Place monitor 0.5um away from the device, inside the padding
            shift = mp.Vector3(direction * 0.5, 0, 0)
            
            monitors[name] = sim.add_mode_monitor(
                fcen, df, 101, 
                mp.FluxRegion(center=p['center'] + shift, size=monitor_size)
            )
        
        return sim, monitors