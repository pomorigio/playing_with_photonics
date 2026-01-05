import gdsfactory as gf
import meep as mp

from utils.meep_utils.digital_twins.base import GDSFactoryTwin

class MMI1x2Twin(GDSFactoryTwin):
    """
    1x2 MMI Splitter.
    Ports: o1 (Input), o2 (Top Out), o3 (Bottom Out)
    """
    def __init__(self, width_mmi, length_mmi, width_taper=1.5, length_taper=10.0):
        super().__init__()

        # Physics: Ports at +/- W/4. Pitch = W/2.
        correct_gap = (width_mmi / 2) - width_taper
        if correct_gap < 0:
            raise ValueError(f"Taper width is too large for the given MMI width. "
                             f"Overlap by {abs(correct_gap)} um.")
        
        self.params = {
            "width_mmi": width_mmi, "length_mmi": length_mmi,
            "width_taper": width_taper, "length_taper": length_taper,
            "gap_mmi": correct_gap, "cross_section": "strip"
        }

    @property
    def symmetry(self):
        return [mp.Mirror(mp.Y)]

    def _build_component(self):
        # 1. Create original component
        c_core = gf.components.mmi1x2(**self.params)

        # 2. Create wrapper
        c = gf.Component()
        ref = c << c_core
        
        # 3. Center the component based on the extended bounding box
        x_orig, y_orig = c_core.center
        ref.move((-x_orig, -y_orig))

        # 4. Add Ports
        c.add_ports(ref.ports)
            
        return c

class MMI2x2Twin(GDSFactoryTwin):
    """
    2x2 MMI Coupler.
    Ports: o1 (In Top), o2 (In Bottom), o3 (Out Top), o4 (Out Bottom)
    """
    def __init__(self, width_mmi, length_mmi, width_taper=1.5, length_taper=10.0):
        super().__init__()
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