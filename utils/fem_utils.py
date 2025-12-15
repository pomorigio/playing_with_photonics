import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from collections import OrderedDict
from shapely.geometry import box
from shapely.ops import clip_by_rect, unary_union
from skfem import Basis, ElementTriP0
from skfem.io.meshio import from_meshio
from femwell.mesh import mesh_from_OrderedDict
from femwell.maxwell.waveguide import compute_modes
from femwell.pn_analytical import index_pn_junction

class WaveguideTemplate:
    def __init__(self, n_core, n_box, n_clad=1.0, thickness=0.22, slab_thickness=0.0, 
                 clad_height=4.0, domain_width=7.0, resolution=0.05):
        self.n_core = n_core
        self.n_box = n_box
        self.n_clad = n_clad
        self.thickness = thickness
        self.slab_thickness = slab_thickness
        self.clad_height = clad_height
        self.domain_width = domain_width
        self.resolution = resolution

    def create_mesh(self, width):
        """Generates the finite element mesh for a single waveguide."""
        core = box(-width/2, -self.thickness/2, width/2, self.thickness/2)
        sim_box = box(-self.domain_width/2, -self.clad_height/2, self.domain_width/2, self.clad_height/2)
        
        polygons = OrderedDict(core=core)
        
        if self.slab_thickness > 0:
            slab = box(-self.domain_width/2, -self.thickness/2, self.domain_width/2, -self.thickness/2 + self.slab_thickness)
            polygons["slab"] = slab

        polygons["box"] = clip_by_rect(sim_box, -np.inf, -np.inf, np.inf, 0)
        polygons["clad_top"] = clip_by_rect(sim_box, -np.inf, 0, np.inf, np.inf)

        resolutions = {
            "core": {"resolution": self.resolution, "distance": 0.5},
            "slab": {"resolution": self.resolution * 2, "distance": 0.5},
        }

        return from_meshio(mesh_from_OrderedDict(polygons, resolutions, default_resolution_max=0.5))

    def create_coupler_mesh(self, width, gap):
        """Generates a mesh with TWO waveguides separated by 'gap'."""
        offset = (gap + width) / 2
        core_left = box(-offset - width/2, -self.thickness/2, -offset + width/2, self.thickness/2)
        core_right = box(offset - width/2, -self.thickness/2, offset + width/2, self.thickness/2)
        cores = unary_union([core_left, core_right])
        
        sim_width = max(self.domain_width, 2 * offset + 4.0)
        sim_box = box(-sim_width/2, -self.clad_height/2, sim_width/2, self.clad_height/2)
        
        polygons = OrderedDict(core=cores)
        
        if self.slab_thickness > 0:
            slab = box(-sim_width/2, -self.thickness/2, sim_width/2, -self.thickness/2 + self.slab_thickness)
            polygons["slab"] = slab

        polygons["box"] = clip_by_rect(sim_box, -np.inf, -np.inf, np.inf, 0)
        polygons["clad_top"] = clip_by_rect(sim_box, -np.inf, 0, np.inf, np.inf)

        resolutions = {
            "core": {"resolution": self.resolution, "distance": 0.5},
            "slab": {"resolution": self.resolution * 2, "distance": 0.5},
        }

        return from_meshio(mesh_from_OrderedDict(polygons, resolutions, default_resolution_max=0.5))

    def _build_index_map(self, mesh, perturbation_func=None):
        """
        Internal Helper: Constructs the Refractive Index Map (Basis and n values).
        This logic is now shared between the Solver and the Plotter.
        """
        basis0 = Basis(mesh, ElementTriP0())
        n_map = basis0.zeros(dtype=complex)
        
        # 1. Static Materials
        material_map = {
            "core": self.n_core, "slab": self.n_core,
            "box": self.n_box, "clad_top": self.n_clad
        }
        for subname, n_val in material_map.items():
            if subname in mesh.subdomains:
                n_map[basis0.get_dofs(elements=subname)] = n_val

        # 2. Perturbation (PN / Heater)
        if perturbation_func:
            dn = basis0.project(perturbation_func, dtype=complex)
            for semi_region in ["core", "slab"]:
                if semi_region in mesh.subdomains:
                    dofs = basis0.get_dofs(elements=semi_region)
                    n_map[dofs] += dn[dofs]
                    
        return basis0, n_map

    def plot_cross_section(self, width, perturbation_func=None, part='real'):
        """
        Visualizes the Refractive Index profile of the cross-section.
        Useful for verifying geometry and PN/Heater profiles.
        
        Args:
            width (float): Waveguide width.
            perturbation_func: Optional physics function (e.g. PN junction).
            part (str): 'real' for Refractive Index, 'imag' for Loss/Gain.
        """
        mesh = self.create_mesh(width)
        basis0, n_map = self._build_index_map(mesh, perturbation_func)
        
        fig, ax = plt.subplots(figsize=(8, 5))
        
        # Select data to plot
        data = np.real(n_map) if part == 'real' else np.imag(n_map)
        title = "Refractive Index (Real)" if part == 'real' else "Absorption Index (Imag)"
        
        # Plot using skfem's built-in visualizer on our axes
        basis0.plot(data, ax=ax, colorbar=True)
        
        ax.set_title(f"{title} Profile (w={width} $\mu m$)")
        ax.set_xlabel("x ($\mu m$)")
        ax.set_ylabel("y ($\mu m$)")
        ax.set_aspect('equal')
        plt.tight_layout()
        
        return fig

    def solve_modes(self, width, wavelength=1.55, num_modes=10, perturbation_func=None):
        """Generates mesh and solves for GUIDED modes."""
        mesh = self.create_mesh(width)
        
        # Use the helper to get the map
        basis0, n_map = self._build_index_map(mesh, perturbation_func)
        epsilon = n_map ** 2
        
        modes = compute_modes(basis0, epsilon, wavelength=wavelength, num_modes=num_modes + 2)
        modes = sorted(modes, key=lambda m: np.real(m.n_eff), reverse=True)

        cutoff_index = max(np.real(self.n_clad), np.real(self.n_box))
        return [m for m in modes if np.real(m.n_eff) > cutoff_index + 1e-4]

    def solve_coupler(self, width, gap, wavelength=1.55):
        """Solves for the Even and Odd supermodes of a coupler."""
        mesh = self.create_coupler_mesh(width, gap)
        
        # Manual build for coupler (since _build_index_map assumes single core mesh input)
        # We could refactor this too, but for now we duplicate the simple map logic
        basis0 = Basis(mesh, ElementTriP0())
        n_map = basis0.zeros(dtype=complex)
        material_map = {"core": self.n_core, "slab": self.n_core, "box": self.n_box, "clad_top": self.n_clad}
        for subname, n_val in material_map.items():
            if subname in mesh.subdomains:
                n_map[basis0.get_dofs(elements=subname)] = n_val
        epsilon = n_map ** 2
        
        modes = compute_modes(basis0, epsilon, wavelength=wavelength, num_modes=4)
        modes = sorted(modes, key=lambda m: np.real(m.n_eff), reverse=True)
        
        cutoff = max(np.real(self.n_clad), np.real(self.n_box))
        guided = [m for m in modes if np.real(m.n_eff) > cutoff + 1e-4]
        
        if len(guided) < 2:
            raise ValueError(f"Gap {gap:.2f}um: Fewer than 2 guided modes found.")
            
        return np.real(guided[0].n_eff), np.real(guided[1].n_eff)

    def plot_modes(self, results, title="Effective Index vs. Width"):
        # ... (Keep existing plot_modes code unchanged) ...
        df = pd.DataFrame(results)
        df_pivot = df.pivot(index="width", columns="label", values="n_eff")
        if df_pivot.empty: return
        col_order = df_pivot.mean().sort_values(ascending=False).index
        df_pivot = df_pivot[col_order]
        mode_counts = df_pivot.count(axis=1)
        multimode_widths = mode_counts[mode_counts >= 2].index
        cutoff_width = multimode_widths.min() if not multimode_widths.empty else None
        fig, ax = plt.subplots(figsize=(12, 8))
        df_pivot.plot(ax=ax, marker='o', markersize=5, linewidth=2)
        cutoff_index = max(np.real(self.n_clad), np.real(self.n_box))
        ax.axhline(cutoff_index, color='black', linestyle='--', linewidth=1.5, alpha=0.6, label='$n_{cutoff}$')
        ax.axhline(self.n_core, color='green', linestyle='--', linewidth=1.5, alpha=0.6, label='$n_{core}$')
        if cutoff_width:
            ax.axvline(cutoff_width, color='red', linestyle='-.', linewidth=2, label=f'Cutoff (~{cutoff_width:.2f} µm)')
            ax.axvspan(df.width.min(), cutoff_width, color='green', alpha=0.1, label='Monomode Region')
        ax.set_xlabel(r"Width ($\mu m$)", fontsize=14)
        ax.set_ylabel(r"Effective Index ($n_{eff}$)", fontsize=14)
        ax.set_title(title, fontsize=16, fontweight='bold')
        ax.grid(True, which='both', alpha=0.4)
        ax.tick_params(axis='both', which='major', labelsize=12)
        ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.12), fancybox=True, shadow=True, ncol=6, fontsize=12)
        plt.tight_layout()
        return fig

# ... (Keep get_pn_perturbation and plot_phase_shifter unchanged) ...
def get_pn_perturbation(voltage, wavelength, NA=1e18, ND=1e18, xpn=0):
    return lambda x: index_pn_junction(
        x[0], xpn=xpn, NA=NA, ND=ND, V=voltage, wavelength=wavelength
    )

def plot_phase_shifter(voltages, delta_neff, loss_db_cm, length_cm=None, title="Phase Shifter Performance"):
    fig, ax1 = plt.subplots(figsize=(10, 6))
    color = 'tab:blue'
    ax1.set_xlabel('Reverse Bias Voltage (V)', fontsize=12)
    ax1.set_ylabel(r'Effective Index Change ($\Delta n_{eff}$)', color=color, fontsize=12)
    ax1.plot(voltages, delta_neff, marker='o', color=color, linewidth=2, label='$\Delta n_{eff}$')
    ax1.tick_params(axis='y', labelcolor=color)
    ax1.grid(True, alpha=0.3)
    ax2 = ax1.twinx()
    color = 'tab:red'
    ax2.set_ylabel('Loss (dB/cm)', color=color, fontsize=12)
    ax2.plot(voltages, loss_db_cm, marker='s', linestyle='--', color=color, linewidth=2, label='Loss')
    ax2.tick_params(axis='y', labelcolor=color)
    if length_cm:
        ax1.set_title(f"{title} (L={length_cm} cm)", fontsize=14)
    else:
        ax1.set_title(title, fontsize=14)
    plt.tight_layout()
    return fig