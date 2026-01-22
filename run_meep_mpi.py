import gdsfactory as gf
import gplugins.gmeep as gm

# ==============================================================================
# 1. CRITICAL: Activate the PDK
#    This fixes the "No active PDK" error by ensuring the new process
#    loads the generic PDK layers before Meep starts.
# ==============================================================================
gf.gpdk.PDK.activate()

# 2. Define the Component
#    (Ensure this matches the component you want to simulate)
c = gf.components.coupler(length=8, gap=0.13)

# 3. Run Simulation
#    We use the standard serial function. Meep's MPI backend handles the
#    parallelism when this script is executed via 'mpirun'.
if __name__ == "__main__":
    gm.write_sparameters_meep(
        component=c,
        run=True,
        resolution=30,
        filepath="data/meep_coupler_mpi.npz",

        # Explicit margins to ensure ports are inside the simulation region
        ymargin_top=3.0,
        ymargin_bot=3.0,
        xmargin_left=2.0,
        xmargin_right=2.0,

        is_3d=False
    )
