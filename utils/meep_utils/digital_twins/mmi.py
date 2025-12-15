import gdsfactory as gf

from utils.meep_utils.digital_twins.base import GDSFactoryTwin


class MMI1x2Twin(GDSFactoryTwin):
    """
    1x2 MMI Splitter.
    Ports: o1 (Input), o2 (Top Out), o3 (Bottom Out)
    """
    def __init__(self, width_mmi, length_mmi, width_taper=1.5, length_taper=10.0):
        super().__init__()
        self.params = {
            "width_mmi": width_mmi, "length_mmi": length_mmi,
            "width_taper": width_taper, "length_taper": length_taper,
            "gap_mmi": width_mmi/2, "cross_section": "strip"
        }

    def _build_component(self):
        return gf.components.mmi1x2(**self.params)


class MMI2x2Twin(GDSFactoryTwin):
    """
    2x2 MMI Coupler.
    Ports: o1 (In Top), o2 (In Bottom), o3 (Out Top), o4 (Out Bottom)
    """
    def __init__(self, width_mmi, length_mmi, width_taper=1.5, length_taper=10.0):
        super().__init__()
        self.params = {
            "width_mmi": width_mmi, "length_mmi": length_mmi,
            "width_taper": width_taper, "length_taper": length_taper,
            "gap_mmi": width_mmi/3, "cross_section": "strip"
        }

    def _build_component(self):
        return gf.components.mmi2x2(**self.params)