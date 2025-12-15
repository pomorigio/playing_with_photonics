import gdsfactory as gf
import meep as mp

class DigitalTwin:
    """Base interface for all photonic components."""
    def get_geometry(self, mat_core, mat_clad):
        raise NotImplementedError
    def get_ports(self):
        raise NotImplementedError
    def get_bounds(self):
        raise NotImplementedError

class GDSFactoryTwin(DigitalTwin):
    def __init__(self):
        self._component = None 

    def _build_component(self):
        raise NotImplementedError

    def get_component(self):
        if self._component is None:
            self._component = self._build_component()
        return self._component

    def get_geometry(self, mat_core, mat_clad):
        # FIX 1: Copy component to avoid LockedError
        c_locked = self.get_component()
        c = c_locked.copy() 
        
        scale = c.kcl.dbu
        geometry = []
        
        # Extract Polygons
        polygons_dict = c.get_polygons(merge=True) 
        
        for polygon_list in polygons_dict.values():
            for poly in polygon_list:
                try:
                    # Scale to Microns
                    points = [(p.x * scale, p.y * scale) for p in poly.each_point_hull()]
                    vertices = [mp.Vector3(x, y) for x, y in points]
                    geometry.append(mp.Prism(vertices, height=mp.inf, material=mat_core))
                except AttributeError:
                    continue
        return geometry

    def get_ports(self):
        c = self.get_component()
        scale = c.kcl.dbu
        port_dict = {}
        
        # FIX 2: Iterate over port objects directly to avoid KeyError
        for p in c.ports:
            name = p.name 
            center_x = p.center[0] * scale
            center_y = p.center[1] * scale
            
            port_dict[name] = {
                "center": mp.Vector3(center_x, center_y),
                "size": mp.Vector3(0, 2.5) 
            }
        return port_dict

    def get_bounds(self):
        c = self.get_component()
        
        # FIX 3: Use dbbox() for robust bounds in microns
        box = c.dbbox() 
        
        width_x = box.width()
        height_y = box.height()
        
        return mp.Vector3(width_x + 4.0, height_y + 4.0, 0)