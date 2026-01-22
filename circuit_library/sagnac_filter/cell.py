import gdsfactory as gf
import numpy as np
import cspdk.si220.cband
from typing import List
cspdk.si220.cband.activate_pdk()

pdk = gf.get_active_pdk()

def sagnac_filter(
    coupling_length: float,
    target_fsr: float,
    coupling_gap: float = 0.2,
    center_wavelength: float = 1.55,
    n_g: float = 4.3,
    n_eff: float = 2.38,
    bend_radius: float = 5.0,
) -> gf.Component:
    """
    Parameterized Sagnac filter using CSPDK components.
    
    Args:
        coupling_length: Length of the directional coupler (µm).
        target_fsr: Desired Free Spectral Range (nm).
        coupling_gap: Gap of the directional coupler (µm).
        center_wavelength: Center wavelength (µm).
        n_g: Group index of waveguide.
        n_eff: Effective index of waveguide.
        bend_radius: Bend radius for Euler bends (µm).
    
    Returns:
        gf.Component: The Sagnac filter layout.
    """
    c = gf.Component()

    # Convert target FSR from nm to µm
    target_fsr_um = target_fsr * 1e-3

    # Calculate effective cavity length for desired FSR
    cavity_length = (center_wavelength**2) / (n_g * target_fsr_um)
    
    # Coupler component
    coupler = c << pdk.get_component("coupler", length=coupling_length, gap=coupling_gap)
    
    # Get coupler info for accurate length
    coupler_length = coupler.cell.info['length'] + coupling_length
    
    # Compute loop length excluding the coupler
    loop_length = cavity_length - 2 * coupler_length
    if loop_length <= 0:
        raise ValueError(
            f"Computed loop length {loop_length} µm is negative! "
            f"Try increasing target_fsr or reducing coupling_length."
        )

    print(f"Computed loop length: {loop_length} µm")
    y_dist_between_coupler_output_ports = np.abs(coupler.ports[0].center[1] - coupler.ports[1].center[1])
    straight_offset = (loop_length - 6 * np.pi/2 * bend_radius) / 6
    # Place coupler at origin
    coupler.move((0, 0))
    
    # Connections in clock-wise direction
    bend_top = c << pdk.get_component("bend_euler", radius=bend_radius, angle=90)
    bend_top.connect("o1", coupler.ports["o3"])

    vertical_straight_top = c << pdk.get_component("straight", length=straight_offset)
    vertical_straight_top.connect("o1", bend_top.ports["o2"])

    bend_2 = c << pdk.get_component("bend_euler", radius=bend_radius, angle=-90)
    bend_2.connect("o1", vertical_straight_top.ports["o2"])

    horizontal_straight_top = c << pdk.get_component("straight", length=straight_offset)
    horizontal_straight_top.connect("o1", bend_2.ports["o2"])

    bend_3 = c << pdk.get_component("bend_euler", radius=bend_radius, angle=-90)
    bend_3.connect("o1", horizontal_straight_top.ports["o2"])

    vertical_straight = c << pdk.get_component("straight", length=2 * straight_offset + 2 * bend_radius + y_dist_between_coupler_output_ports)
    vertical_straight.connect("o1", bend_3.ports["o2"])

    bend_4 = c << pdk.get_component("bend_euler", radius=bend_radius, angle=-90)
    bend_4.connect("o1", vertical_straight.ports["o2"])

    horizontal_straight_bot = c << pdk.get_component("straight", length=straight_offset)
    horizontal_straight_bot.connect("o1", bend_4.ports["o2"])

    bend_5 = c << pdk.get_component("bend_euler", radius=bend_radius, angle=-90)
    bend_5.connect("o1", horizontal_straight_bot.ports["o2"])

    vertical_straight_bot = c << pdk.get_component("straight", length=straight_offset)
    vertical_straight_bot.connect("o1", bend_5.ports["o2"])

    bend_bot = c << pdk.get_component("bend_euler", radius=bend_radius, angle=90)
    bend_bot.connect("o1", vertical_straight_bot.ports["o2"])
    
    # Add input/output ports
    c.add_port("in", port=coupler.ports["o1"])
    c.add_port("out", port=coupler.ports["o2"])
    
    # Metadata for debug
    c.info["cavity_length"] = cavity_length
    c.info["loop_length"] = loop_length
    c.info["target_fsr"] = target_fsr
    
    return c
