import numpy as np
import skrf as rf # pip install scikit-rf


class SParameterExporter:
    @staticmethod
    def get_complex_s_params(wvl, T_linear, phase_rad=None):
        """
        Converts linear transmission (T) to complex S-parameter (S).
        S = sqrt(T) * exp(j * phase)
        """
        magnitude = np.sqrt(np.abs(T_linear))
        
        if phase_rad is None:
            # If we don't track phase, assume 0 (intensity only model)
            # IPKISS/SAX can often work with just intensity for simple DC checks
            phase_rad = np.zeros_like(T_linear)
            
        return magnitude * np.exp(1j * phase_rad)

    @staticmethod
    def export_to_sax(wvl, s_dict):
        """
        Formats a dictionary of complex S-parameters for SAX.
        SAX expects: {('port1', 'port2'): array_of_complex_values, ...}
        """
        # SAX uses JAX, but standard numpy arrays work for data loading
        return s_dict

    @staticmethod
    def export_to_touchstone(filename, wvl, s_dict, port_map):
        """
        Exports a .sNp (Touchstone) file for IPKISS / Lumerical / KLayout.
        
        Args:
            filename: Output path (e.g. 'coupler.s4p')
            wvl: Wavelength array in MICRONS
            s_dict: Dictionary {(port_in, port_out): complex_array}
            port_map: List of port names in order [p1, p2, p3, p4]
                      Example: ['o1', 'o2', 'o3', 'o4']
        """
        # 1. Convert Wavelength (um) to Frequency (Hz)
        c_m_s = 299792458
        freq_hz = c_m_s / (wvl * 1e-6)
        
        # Scikit-RF expects frequency to be increasing
        # Meep usually returns decreasing wavelength (increasing freq), but we check:
        if freq_hz[0] > freq_hz[-1]:
            freq_hz = np.flip(freq_hz)
            for k, v in s_dict.items():
                s_dict[k] = np.flip(v)

        # 2. Build S-Matrix (N_freqs x N_ports x N_ports)
        n_points = len(freq_hz)
        n_ports = len(port_map)
        s_matrix = np.zeros((n_points, n_ports, n_ports), dtype=complex)
        
        # Map port names to indices (0, 1, 2...)
        p_idx = {name: i for i, name in enumerate(port_map)}
        
        for (p_in, p_out), data in s_dict.items():
            if p_in in p_idx and p_out in p_idx:
                i, j = p_idx[p_out], p_idx[p_in] # S_out_in
                s_matrix[:, i, j] = data

        # 3. Write File
        network = rf.Network(frequency=freq_hz, s=s_matrix)
        network.write_touchstone(filename)
        print(f"Exported {n_ports}-port Touchstone file: {filename}")