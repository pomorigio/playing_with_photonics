import gdsfactory as gf
from gdsfactory.typings import ComponentSpec
from typing import List, Optional
import numpy as np
import cspdk.si220.cband
from axiomatic.pic_helpers import plot_circuit

# Activate CSPDK
cspdk.si220.cband.activate_pdk()
pdk = gf.get_active_pdk()

@gf.cell
def clements_NxN(
    n_ports: int,
    mzi: ComponentSpec = "mzi",  # Parameterized MZI
    x_spacing: float = 200,
    y_spacing: float = 200
) -> gf.Component:
    """
    Generates a Clements-style NxN MZI mesh network.

    Args:
        n_ports: Number of input/output ports (must be even).
        mzi: MZI component to use.
        x_spacing: Horizontal spacing between columns.
        y_spacing: Vertical spacing between rows.

    Returns:
        gf.Component: The assembled MZI mesh.
    """
    if n_ports % 2 != 0:
        raise ValueError("The number of ports (n_ports) must be even.")

    c = gf.Component()
    mzi_units: List[List[gf.ComponentReference]] = []

    # Step 1: Place all MZI units.
    def place_mzis() -> None:
        for col_idx in range(n_ports - 1):
            num_mzis_col = n_ports // 2 if col_idx % 2 == 0 else n_ports // 2 - 1
            column: List[gf.ComponentReference] = []

            for row_idx in range(num_mzis_col):
                mzi_ref = c << gf.get_component(mzi)  # Use parameterized MZI!
                mzi_ref.name = f"mzi_{col_idx}_{row_idx}"
                x = col_idx * x_spacing
                y = -row_idx * y_spacing - (y_spacing / 2.0 if col_idx % 2 == 1 else 0)
                mzi_ref.move((x, y))
                column.append(mzi_ref)

            mzi_units.append(column)

    # Step 2: Determine next MZI connections.
    def get_next_mzis(col_idx: int, row_idx: int) -> (Optional[gf.ComponentReference], Optional[gf.ComponentReference]):
        """
        Returns the top and bottom next MZIs for given MZI position.
        """
        next_col = mzi_units[col_idx + 1] if col_idx + 1 < len(mzi_units) else []
        next_col_2 = mzi_units[col_idx + 2] if col_idx + 2 < len(mzi_units) else []

        if col_idx % 2 == 0:
            next_mzi_top = next_col_2[row_idx] if row_idx == 0 and next_col_2 else (next_col[row_idx - 1] if row_idx > 0 else None)
            next_mzi_bottom = next_col[row_idx] if row_idx < len(next_col) else (next_col_2[row_idx] if next_col_2 else None)
        else:
            next_mzi_top = next_col[row_idx] if row_idx < len(next_col) else None
            next_mzi_bottom = next_col[row_idx + 1] if row_idx + 1 < len(next_col) else None

        return next_mzi_top, next_mzi_bottom

    # Step 3: Route connections between MZIs.
    def connect_mzis() -> None:
        for col_idx, col in enumerate(mzi_units[:-1]):
            for row_idx, mzi in enumerate(col):
                out1, out2 = mzi.ports["o3"], mzi.ports["o4"]
                next_mzi_top, next_mzi_bottom = get_next_mzis(col_idx, row_idx)

                # Connect output o3 to next input.
                if next_mzi_top:
                    in1 = next_mzi_top.ports["o2"] if (col_idx % 2 == 0 and row_idx == 0) else next_mzi_top.ports["o1"]
                    gf.routing.route_single(component=c, port1=out1, port2=in1, cross_section='strip')

                # Connect output o4 to next input.
                if next_mzi_bottom:
                    in2 = next_mzi_bottom.ports["o2"] if (col_idx % 2 != 0 or row_idx < len(col) - 1) else next_mzi_bottom.ports["o1"]
                    gf.routing.route_single(component=c, port1=out2, port2=in2, cross_section='strip')

    # Build the circuit.
    place_mzis()
    connect_mzis()

    return c
