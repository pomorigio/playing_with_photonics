import gdsfactory as gf
import meep as mp

from utils.meep_utils.digital_twins.base import DigitalTwin, GDSFactoryTwin


class StraightCouplerTwin(DigitalTwin):
    def __init__(self, gap, width, length):
        self.gap, self.width, self.length = gap, width, length
        self.y_top = (gap + width) / 2
        self.y_bot = -(gap + width) / 2

    def get_geometry(self, mat_core, mat_clad):
        return [
            mp.Block(mp.Vector3(mp.inf, self.width, mp.inf), center=mp.Vector3(0, self.y_top, 0), material=mat_core),
            mp.Block(mp.Vector3(mp.inf, self.width, mp.inf), center=mp.Vector3(0, self.y_bot, 0), material=mat_core)
        ]

    def get_ports(self):
        x_in, x_out = -self.length / 2, self.length / 2
        port_size = self.width + 1.0
        return {
            "o1": {"center": mp.Vector3(x_in, self.y_top), "size": mp.Vector3(0, port_size)},
            "o2": {"center": mp.Vector3(x_in, self.y_bot), "size": mp.Vector3(0, port_size)},
            "o3": {"center": mp.Vector3(x_out, self.y_top), "size": mp.Vector3(0, port_size)},
            "o4": {"center": mp.Vector3(x_out, self.y_bot), "size": mp.Vector3(0, port_size)},
        }
    
    def get_bounds(self):
        return mp.Vector3(self.length, self.gap + 2*self.width + 3.0, 0)
    

class DirectionalCouplerTwin(GDSFactoryTwin):
    def __init__(self, gap, width, length_straight, length_bend, dy):
        super().__init__()
        self.gap = gap
        self.width = width
        self.l_st = length_straight
        self.l_bend = length_bend
        self.dy = dy

    def _build_component(self):
        xs = gf.get_cross_section("strip", width=self.width)
        return gf.components.coupler(
            gap=self.gap,
            length=self.l_st,
            dx=self.l_bend,
            dy=self.dy,
            cross_section=xs
        )