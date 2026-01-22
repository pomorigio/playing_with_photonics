import gdsfactory as gf

class StraightCouplerTwin:
    def __init__(self, gap, width, length):
        self.gap, self.width, self.length = gap, width, length
        self.y_top = (gap + width) / 2
        self.y_bot = -(gap + width) / 2
    

class DirectionalCouplerTwin:
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