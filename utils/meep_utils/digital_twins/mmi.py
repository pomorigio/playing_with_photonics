import gdsfactory as gf

class MMI1x2Twin:
    """
    1x2 MMI Splitter.
    Ports: o1 (Input), o2 (Top Out), o3 (Bottom Out)
    """
    def __init__(self, width_mmi, length_mmi, width_taper=1.5, length_taper=10.0):
        # Physics: Ports at +/- W/4. Pitch = W/2.
        correct_gap = (width_mmi / 2) - width_taper
        if correct_gap < 0:
            raise ValueError(f"Taper width is too large for the given MMI width. "
                             f"Overlap by {abs(correct_gap)} um.")
        
        self.params = {
            "width_mmi": width_mmi, 
            "length_mmi": length_mmi,
            "width_taper": width_taper, 
            "length_taper": length_taper,
            "gap_mmi": correct_gap, 
            "cross_section": "strip"
        }

    def get_component(self):
        """
        Returns the finalized GDSFactory component ready for simulation or tape-out.
        """
        # Create the core device
        c_core = gf.components.mmi1x2(**self.params)
        
        # Wrap it in a clean container (standard practice to avoid mutating library cells)
        c = gf.Component()
        ref = c << c_core
        
        # Center it at (0,0) - Crucial for consistent simulation grids
        ref.center = (0, 0)
        
        # Expose ports to the outside world
        c.add_ports(ref.ports)
        
        # Name it explicitly so your GDS file is readable
        c.name = f"mmi1x2_W{self.params['width_mmi']:.2f}_L{self.params['length_mmi']:.2f}"
        
        return c

class MMI2x2Twin:
    """
    2x2 MMI Coupler.
    Ports: o1 (In Top), o2 (In Bottom), o3 (Out Top), o4 (Out Bottom)
    """
    def __init__(self, width_mmi, length_mmi, width_taper=1.5, length_taper=10.0):
        correct_gap = (width_mmi / 3) - width_taper
        if correct_gap < 0:
            raise ValueError(f"Taper width is too large for the given MMI width. "
                             f"Overlap by {abs(correct_gap)} um.")
        self.params = {
            "width_mmi": width_mmi, "length_mmi": length_mmi,
            "width_taper": width_taper, "length_taper": length_taper,
            "gap_mmi": correct_gap, "cross_section": "strip"
        }

    def _build_component(self):
        c_core = gf.components.mmi2x2(**self.params)
        
        # --- CHANGED: Extend ports here as well ---
        c_extended = gf.components.extend_ports(c_core, length=5.0)
        
        # Container method
        c = gf.Component()
        ref = c << c_extended
        
        # Center the component
        x_orig, y_orig = c_extended.center
        ref.move((-x_orig, -y_orig))
        
        c.add_ports(ref.ports)
        
        return c