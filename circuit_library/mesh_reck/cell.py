import gdsfactory as gf
import cspdk.si220.cband
from typing import List

cspdk.si220.cband.activate_pdk()
pdk = gf.get_active_pdk()

@gf.cell
def reck_NxN(
    n_ports: int,
    x_spacing: float = 250,
    y_spacing: float = 100
) -> gf.Component:
    """
    Generates a Reck-style NxN interferometer mesh (triangular/pyramidal layout).

    Args:
        n_ports: Number of input/output ports.
        x_spacing: Horizontal spacing between MZI columns.
        y_spacing: Vertical spacing between MZI rows.

    Returns:
        gf.Component: The assembled Reck interferometer mesh.
    """
    c = gf.Component()
    mzi_units: List[List[gf.ComponentReference]] = []

    def place_mzis() -> None:
        """Places the MZIs in a triangular/pyramidal layout."""
        for row_idx in range(n_ports - 1):
            row: List[gf.ComponentReference] = []
            for col_idx in range(row_idx + 1):
                mzi = c << pdk.get_component("mzi")
                mzi.name = f"mzi_{row_idx}_{col_idx}"
                x = -x_spacing * (row_idx / 2) + col_idx * x_spacing
                y = -row_idx * y_spacing
                mzi.move((x, y))
                row.append(mzi)
            mzi_units.append(row)

    def connect_mzis() -> None:
        """Connects MZIs to their neighbors following the Reck triangular pattern."""
        for row_idx, row in enumerate(mzi_units[:-1]):
            for col_idx, mzi in enumerate(row):
                # Connect output o4 to next row's diagonal MZI input
                if col_idx + 1 < len(mzi_units[row_idx + 1]):
                    next_mzi_diag = mzi_units[row_idx + 1][col_idx + 1]
                    gf.routing.route_single(
                        component=c,
                        port1=mzi.ports["o4"],
                        port2=next_mzi_diag.ports["o2"],
                        cross_section='strip'
                    )

                # Connect output o1 to next row's vertical MZI input
                next_mzi_vert = mzi_units[row_idx + 1][col_idx]
                gf.routing.route_single(
                    component=c,
                    port1=mzi.ports["o1"],
                    port2=next_mzi_vert.ports["o3"],
                    cross_section='strip'
                )

        # Last row horizontal connections
        last_row = mzi_units[-1]
        for col_idx, mzi in enumerate(last_row[:-1]):
            next_mzi = last_row[col_idx + 1]
            gf.routing.route_single(
                component=c,
                port1=mzi.ports["o4"],
                port2=next_mzi.ports["o1"],
                cross_section='strip'
            )

    # Build the circuit
    place_mzis()
    connect_mzis()

    return c
