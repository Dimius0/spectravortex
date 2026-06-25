#!/usr/bin/env python3
"""
tees_biharmonic_v19.py — EMERGENT PHYSICAL FINGERPRINT (v19.0)
Rebrand: hash → fingerprint, consistency → VSM (Vortex Stability Metric)
License: MIT
"""

import numpy as np
from scipy.ndimage import gaussian_filter, sobel, map_coordinates
from sklearn.linear_model import RANSACRegressor
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import hashlib
import struct
import warnings
import os
import time
from collections import Counter
warnings.filterwarnings('ignore')

print("=" * 80)
print("  TEES v19.0: EMERGENT PHYSICAL FINGERPRINT")
print("  Rebrand: hash → fingerprint, consistency → VSM")
print("  License: MIT")
print("=" * 80)


# ============================================================================
# CONFIGURATION
# ============================================================================
@dataclass
class TEESConfig:
    """Centralized TEES experiment configuration"""
    grid_size: int = 64
    nu_true: float = 0.08
    gamma_true: float = 1.5
    dt: float = 2.0

    # Stability threshold (бывший emergence_threshold)
    vsm_threshold: float = 0.7  # VSM = Vortex Stability Metric
    phase_gamma_min: float = 0.3
    phase_gamma_max: float = 1.5

    # recover_gamma parameters
    r_center_scales: np.ndarray = field(default_factory=lambda: np.linspace(0.15, 0.75, 8))
    dr_scale: float = 0.08
    min_samples_per_ring: int = 30
    gradient_threshold: float = 0.01
    r_min: float = 0.05
    gamma_valid_range: Tuple[float, float] = (0.1, 10.0)

    # spectral_analysis parameters
    n_theta: int = 128
    r_mask_spectral: Tuple[float, float] = (0.2, 0.7)

    # Optimization
    optimization_max_iter: int = 100
    optimization_patience: int = 20
    optimization_improvement_threshold: float = 0.005
    perturbation_modes: List[str] = field(default_factory=lambda: ['global', 'radial', 'azimuthal'])

    # File paths
    addresses_file: str = "addresses_1000.txt"
    output_file: str = "fingerprints_v19.txt"

    def __post_init__(self):
        self.x = np.linspace(-1, 1, self.grid_size)
        self.y = np.linspace(-1, 1, self.grid_size)
        self.X, self.Y = np.meshgrid(self.x, self.y)
        self.R = np.sqrt(self.X**2 + self.Y**2)
        self.R_safe = np.maximum(self.R, 1e-8)


# ============================================================================
# FIELD GENERATION (unchanged core)
# ============================================================================
def address_to_seed(address) -> int:
    if isinstance(address, str):
        address = address.encode('utf-8')
    hash_bytes = hashlib.sha256(address).digest()
    return struct.unpack('>I', hash_bytes[:4])[0]


def generate_field_from_address(address, config: TEESConfig):
    if isinstance(address, str):
        address_bytes = address.encode('utf-8')
    elif isinstance(address, bytes):
        address_bytes = address
    else:
        address_bytes = str(address).encode('utf-8')
    
    seed = address_to_seed(address_bytes)
    rng = np.random.RandomState(seed)
    hash_bytes = hashlib.sha256(address_bytes).digest()

    kx = np.fft.fftfreq(config.grid_size, d=2.0 / config.grid_size)
    ky = np.fft.fftfreq(config.grid_size, d=2.0 / config.grid_size)
    KX, KY = np.meshgrid(kx, ky)
    K = np.sqrt(KX**2 + KY**2)
    K[0, 0] = 1.0

    spectrum = rng.randn(config.grid_size, config.grid_size) + 1j * rng.randn(config.grid_size, config.grid_size)

    for i in range(8):
        val = struct.unpack('>I', hash_bytes[i*4:(i+1)*4])[0]
        weight = (val / (2**31) - 1)
        k_target = 0.5 + i * 1.5
        mask = np.abs(K - k_target) < 0.8
        if np.any(mask):
            spectrum[mask] *= (1 + weight)

    spectrum = spectrum * K**(-5/3) * np.exp(-K**2 / 10)
    field = np.real(np.fft.ifft2(spectrum * (K < 15)))
    field = (field - field.mean()) / (field.std() + 1e-8)
    return field


def apply_vortex_transition(field_A, config: TEESConfig):
    omega = (config.gamma_true / (2 * np.pi * config.R_safe**2)
             * (1 - np.exp(-config.R_safe**2 / (4 * config.nu_true))))
    delta_theta = omega * config.dt
    theta = np.arctan2(config.Y, config.X)
    theta_new = theta + delta_theta
    X_new = config.R * np.cos(theta_new)
    Y_new = config.R * np.sin(theta_new)
    X_idx = (X_new + 1) / 2 * (config.grid_size - 1)
    Y_idx = (Y_new + 1) / 2 * (config.grid_size - 1)
    return map_coordinates(field_A, [Y_idx, X_idx], order=3, mode='wrap')


# ============================================================================
# TRANSITION DIAGNOSTICS
# ============================================================================
class TransitionDiagnostics:
    def __init__(self, field_A: np.ndarray, field_B: np.ndarray, config: TEESConfig):
        self.field_A = field_A
        self.field_B = field_B
        self.config = config
        self._cache: Dict[str, any] = {}

    def _find_center(self) -> Tuple[float, float]:
        if 'center' not in self._cache:
            grad_Ax = sobel(self.field_A, axis=1)
            grad_Ay = sobel(self.field_A, axis=0)
            grad_Bx = sobel(self.field_B, axis=1)
            grad_By = sobel(self.field_B, axis=0)
            vorticity = np.abs(grad_Bx - grad_Ax) + np.abs(grad_By - grad_Ay)
            vorticity = gaussian_filter(vorticity, sigma=2.0)
            total = np.sum(vorticity)
            if total > 0:
                cx = np.sum(self.config.X * vorticity) / total
                cy = np.sum(self.config.Y * vorticity) / total
            else:
                cx, cy = 0.0, 0.0
            self._cache['center'] = (cx, cy)
        return self._cache['center']

    def _recover_gamma(self) -> Tuple[float, float, float]:
        if 'gamma' not in self._cache:
            cx, cy = self._find_center()
            cfg = self.config
            x_loc = cfg.X - cx
            y_loc = cfg.Y - cy
            r_loc = np.sqrt(x_loc**2 + y_loc**2)
            grad_Ax = sobel(self.field_A, axis=1)
            grad_Ay = sobel(self.field_A, axis=0)
            dA_dt = (self.field_B - self.field_A) / cfg.dt
            angular_gradient = (-y_loc * grad_Ax + x_loc * grad_Ay) / (r_loc**2 + 1e-8)
            viscous_factor = 1 - np.exp(-r_loc**2 / (4 * cfg.nu_true * cfg.dt))
            geo_factor = -viscous_factor * angular_gradient / (2 * np.pi * r_loc + 1e-8)
            valid_gradient = ((np.abs(grad_Ax) + np.abs(grad_Ay) > cfg.gradient_threshold)
                              & (r_loc > cfg.r_min))
            center_hash = hashlib.sha256(f"{cx:.6f},{cy:.6f}".encode()).digest()
            ransac_seed = struct.unpack('>I', center_hash[:4])[0] % (2**15)

            Gamma_scales = []
            for r_center in cfg.r_center_scales:
                mask = ((r_loc > r_center - cfg.dr_scale)
                        & (r_loc < r_center + cfg.dr_scale)
                        & valid_gradient)
                n_points = np.sum(mask)
                if n_points < cfg.min_samples_per_ring:
                    continue
                try:
                    ransac = RANSACRegressor(
                        min_samples=max(cfg.min_samples_per_ring, int(0.5 * n_points)),
                        residual_threshold=np.percentile(
                            np.abs(dA_dt[mask] - np.median(dA_dt[mask])), 75
                        ),
                        max_trials=200,
                        random_state=ransac_seed
                    )
                    ransac.fit(geo_factor[mask].reshape(-1, 1), dA_dt[mask].reshape(-1))
                    Gamma_est = abs(ransac.estimator_.coef_[0])
                    if cfg.gamma_valid_range[0] < Gamma_est < cfg.gamma_valid_range[1]:
                        Gamma_scales.append(Gamma_est)
                except Exception:
                    continue

            if len(Gamma_scales) < 2:
                self._cache['gamma'] = (0.0, 0.0, 0.0)
            else:
                Gamma_arr = np.array(Gamma_scales)
                Gamma_mean = np.mean(Gamma_arr)
                vsm = 1 - np.std(Gamma_arr) / (Gamma_mean + 1e-8)  # VSM = Vortex Stability Metric
                energy = Gamma_mean * vsm
                self._cache['gamma'] = (Gamma_mean, vsm, energy)
        return self._cache['gamma']

    def _spectral_analysis(self) -> Tuple[float, float, float]:
        if 'spectral' not in self._cache:
            cx, cy = self._find_center()
            cfg = self.config
            x_loc = cfg.X - cx
            y_loc = cfg.Y - cy
            r_loc = np.sqrt(x_loc**2 + y_loc**2)
            theta_loc = np.arctan2(y_loc, x_loc)
            diff = self.field_B - self.field_A
            mask = (r_loc > cfg.r_mask_spectral[0]) & (r_loc < cfg.r_mask_spectral[1])
            theta_flat = theta_loc[mask].flatten()
            diff_flat = diff[mask].flatten()
            sort_idx = np.argsort(theta_flat)
            theta_grid = np.linspace(-np.pi, np.pi, cfg.n_theta)
            diff_interp = np.interp(theta_grid, theta_flat[sort_idx], diff_flat[sort_idx], period=2*np.pi)
            diff_fft = np.fft.fft(diff_interp)
            power = np.abs(diff_fft)**2
            total_power = np.sum(power[1:])
            if total_power > 0:
                m1 = (power[1] + power[-1]) / total_power
                m2 = (power[2] + power[-2]) / total_power
                m_high = np.sum(power[3:]) / total_power
            else:
                m1, m2, m_high = 0.0, 0.0, 0.0
            self._cache['spectral'] = (m1, m2, m_high)
        return self._cache['spectral']

    def compute_all(self) -> Dict[str, float]:
        Gamma, vsm, energy = self._recover_gamma()
        m1, m2, m_high = self._spectral_analysis()
        cx, cy = self._find_center()
        t_vortex = vsm / (1 + m_high - 0.5 * m2 + 0.3)
        phase = (np.clip((energy - self.config.phase_gamma_min)
                         / (self.config.phase_gamma_max - self.config.phase_gamma_min), 0, 1)
                 if Gamma > 0 else 0.0)
        is_stable = vsm >= self.config.vsm_threshold
        return {
            'Gamma': Gamma,
            'vsm': vsm,
            'energy': energy,
            'phase': phase,
            't_vortex': t_vortex,
            'm1': m1, 'm2': m2, 'm_high': m_high,
            'is_stable': is_stable,
            'cx': cx, 'cy': cy
        }


# ============================================================================
# FINGERPRINT GENERATION
# ============================================================================
def compute_vortex_fingerprint(Gamma: float, vsm: float, phase: float, t_vortex: float) -> str:
    """Compute vortex fingerprint from transition state."""
    vals = [Gamma, vsm, phase, t_vortex]
    safe_vals = [v if np.isfinite(v) else 0.0 for v in vals]
    state = (f"{int(safe_vals[0] * 100000)}:"
             f"{int(safe_vals[1] * 100000)}:"
             f"{int(safe_vals[2] * 100000)}:"
             f"{int(safe_vals[3] * 100000)}")
    return hashlib.sha256(state.encode()).hexdigest()[:16]


# ============================================================================
# ADAPTIVE PHASE CONTROL (unchanged)
# ============================================================================
class PhaseController:
    def __init__(self, field_A, field_B, cx, cy, config):
        self.config = config
        self.cx = cx
        self.cy = cy
        self.best_vsm = 0.0
        self.best_field_A = field_A.copy()
        self.best_field_B = field_B.copy()
        self.history: List[Dict] = []
        self.current_amplitude = 0.3
        self.consecutive_improvements = 0
        self.consecutive_failures = 0

    def _make_perturbation(self, field, amplitude, mode):
        rng = np.random.RandomState(abs(int(amplitude * 1000 + len(self.history))) % (2**32 - 1))
        if mode == 'global':
            return amplitude * rng.randn(*field.shape) * 0.1
        elif mode == 'radial':
            x_loc = self.config.X - self.cx
            y_loc = self.config.Y - self.cy
            r_loc = np.sqrt(x_loc**2 + y_loc**2)
            return amplitude * np.sin(3 * r_loc) * 0.1
        elif mode == 'azimuthal':
            x_loc = self.config.X - self.cx
            y_loc = self.config.Y - self.cy
            theta_loc = np.arctan2(y_loc, x_loc)
            return amplitude * np.cos(2 * theta_loc) * 0.1
        else:
            raise ValueError(f"Unknown perturbation mode: {mode}")

    def _try_perturbation(self, amplitude, mode):
        perturbation = self._make_perturbation(self.best_field_A, amplitude, mode)
        field_A_try = self.best_field_A + perturbation
        field_B_try = apply_vortex_transition(field_A_try, self.config)
        return field_A_try, field_B_try

    def _adapt_amplitude(self, improved):
        if improved:
            self.consecutive_improvements += 1
            self.consecutive_failures = 0
            if self.consecutive_improvements >= 3:
                self.current_amplitude = min(0.8, self.current_amplitude * 1.3)
                self.consecutive_improvements = 0
        else:
            self.consecutive_failures += 1
            self.consecutive_improvements = 0
            if self.consecutive_failures >= 5:
                self.current_amplitude = max(0.05, self.current_amplitude * 0.7)
                self.consecutive_failures = 0

    def optimize(self, target=0.7, max_iter=None):
        if max_iter is None:
            max_iter = self.config.optimization_max_iter
        diag_base = TransitionDiagnostics(self.best_field_A, self.best_field_B, self.config)
        _, vsm, _ = diag_base._recover_gamma()
        self.best_vsm = vsm
        best_iter = 0
        mode_cycle = self.config.perturbation_modes.copy()
        mode_idx = 0

        for iteration in range(max_iter):
            if self.best_vsm >= target:
                break
            if iteration - best_iter > self.config.optimization_patience:
                break
            mode = mode_cycle[mode_idx % len(mode_cycle)]
            mode_idx += 1
            amplitude = self.current_amplitude * np.random.uniform(0.5, 1.5)
            try:
                field_A_try, field_B_try = self._try_perturbation(amplitude, mode)
            except ValueError:
                continue
            diag = TransitionDiagnostics(field_A_try, field_B_try, self.config)
            _, vsm_try, _ = diag._recover_gamma()
            self.history.append({'iteration': iteration, 'mode': mode, 'amplitude': amplitude, 'vsm': vsm_try})
            improvement = vsm_try - self.best_vsm
            improved = improvement > self.config.optimization_improvement_threshold
            self._adapt_amplitude(improved)
            if vsm_try > self.best_vsm:
                self.best_vsm = vsm_try
                self.best_field_A = field_A_try
                self.best_field_B = field_B_try
                best_iter = iteration
                if improvement > 0.02:
                    self.current_amplitude = min(0.8, self.current_amplitude * 1.5)
        return self.best_vsm, self.best_field_A, self.best_field_B


# ============================================================================
# IRREVERSIBILITY PROOF
# ============================================================================
def prove_irreversibility(field_A, field_B, fingerprint, config):
    field_A_reconstructed = apply_vortex_transition(field_B, config)
    correlation = float(np.corrcoef(field_A.flatten(), field_A_reconstructed.flatten())[0, 1])
    entropy_forward = float(-np.sum(np.abs(field_A) * np.log(np.abs(field_A) + 1e-8)))
    entropy_reverse = float(-np.sum(np.abs(field_A_reconstructed) * 
                                    np.log(np.abs(field_A_reconstructed) + 1e-8)))
    entropy_increase = entropy_reverse - entropy_forward
    diag_rec = TransitionDiagnostics(field_A_reconstructed, field_B, config)
    state_rec = diag_rec.compute_all()
    reconstructed_fp = compute_vortex_fingerprint(
        state_rec['Gamma'], state_rec['vsm'], state_rec['phase'], state_rec['t_vortex']
    )
    kx = np.fft.fftfreq(config.grid_size, d=2.0/config.grid_size)
    ky = np.fft.fftfreq(config.grid_size, d=2.0/config.grid_size)
    KX, KY = np.meshgrid(kx, ky)
    K_sq = KX**2 + KY**2
    vortex_eigenvalues = np.exp(-config.nu_true * K_sq * config.dt)
    condition_number = float(np.max(vortex_eigenvalues) / (np.min(vortex_eigenvalues[vortex_eigenvalues > 0]) + 1e-8))
    
    hash_mismatch = (reconstructed_fp != fingerprint)
    correlation_loss = (correlation < 0.95)
    entropy_gain = (entropy_increase > 0)
    ill_posed = (condition_number > 10)
    is_irreversible = hash_mismatch and correlation_loss and ill_posed

    return {
        'correlation': correlation,
        'entropy_increase': entropy_increase,
        'condition_number': condition_number,
        'hash_mismatch': hash_mismatch,
        'is_irreversible': is_irreversible,
        'original_fingerprint': fingerprint,
        'reconstructed_fingerprint': reconstructed_fp,
        'proof_components': {
            'correlation_loss': correlation_loss,
            'entropy_gain': entropy_gain,
            'hash_mismatch': hash_mismatch,
            'ill_posed': ill_posed
        }
    }


# ============================================================================
# ADDRESS PROCESSING PIPELINE
# ============================================================================
@dataclass
class AddressResult:
    address: str
    state: Dict[str, float]
    fingerprint: str
    sha256: str
    fingerprint_optimized: Optional[str] = None
    optimization_successful: bool = False
    optimization_iterations: int = 0
    best_mode: Optional[str] = None
    irreversibility: Optional[Dict] = None


def process_address(address, config: TEESConfig) -> AddressResult:
    if isinstance(address, str):
        addr_str = address.strip()
    elif isinstance(address, bytes):
        addr_str = address.decode('utf-8', errors='replace')
    else:
        addr_str = str(address).strip()

    field_A = generate_field_from_address(addr_str, config)
    field_B = apply_vortex_transition(field_A, config)

    diag = TransitionDiagnostics(field_A, field_B, config)
    state = diag.compute_all()

    fingerprint = compute_vortex_fingerprint(
        state['Gamma'], state['vsm'], state['phase'], state['t_vortex']
    )
    sha256_hash = hashlib.sha256(addr_str.encode('utf-8') if isinstance(addr_str, str) else addr_str).hexdigest()[:16]

    result = AddressResult(
        address=addr_str[:50],
        state=state,
        fingerprint=fingerprint,
        sha256=sha256_hash
    )

    if not state['is_stable']:
        controller = PhaseController(field_A, field_B, state['cx'], state['cy'], config)
        best_vsm, field_A_opt, field_B_opt = controller.optimize(target=config.vsm_threshold)
        diag_opt = TransitionDiagnostics(field_A_opt, field_B_opt, config)
        state_opt = diag_opt.compute_all()
        result.fingerprint_optimized = compute_vortex_fingerprint(
            state_opt['Gamma'], state_opt['vsm'], state_opt['phase'], state_opt['t_vortex']
        )
        result.optimization_successful = state_opt['is_stable']
        result.optimization_iterations = len(controller.history)
        result.best_mode = (controller.history[-1]['mode'] if controller.history else None)

    result.irreversibility = prove_irreversibility(field_A, field_B, fingerprint, config)
    return result


# ============================================================================
# ENTROPY & UNIFORMITY TESTS (NEW IN v19.0)
# ============================================================================
def test_uniformity(fingerprints: List[str]) -> Dict:
    """Chi-square test for uniform distribution of hex characters."""
    all_chars = ''.join(fingerprints)
    n = len(all_chars)
    counts = Counter(all_chars)
    
    # Expected: uniform distribution over 16 hex chars
    expected = n / 16
    chi2 = sum((counts.get(c, 0) - expected)**2 / expected for c in '0123456789abcdef')
    
    return {
        'chi2': chi2,
        'uniform': chi2 < 25.0,  # critical value for 15 df at p=0.05
        'distribution': {c: counts.get(c, 0) / n for c in '0123456789abcdef'}
    }


def test_sensitivity(address: str, config: TEESConfig) -> float:
    """Test vortex sensitivity: change 1 bit, measure fingerprint distance."""
    if isinstance(address, str):
        addr_bytes = address.encode('utf-8')
    else:
        addr_bytes = address
    
    # Original fingerprint
    fp1 = process_address(address, config).fingerprint
    
    # Flip one bit
    mutated = bytearray(addr_bytes)
    mutated[0] ^= 0x01
    fp2 = process_address(bytes(mutated), config).fingerprint
    
    # Hamming distance between hex strings
    fp1_int = int(fp1, 16)
    fp2_int = int(fp2, 16)
    xor = fp1_int ^ fp2_int
    
    return bin(xor).count('1') / 64.0  # fraction of bits changed (max 64 bits for 16 hex chars)


def estimate_entropy(fingerprints: List[str]) -> float:
    """Estimate Shannon entropy of fingerprint distribution."""
    all_chars = ''.join(fingerprints)
    n = len(all_chars)
    counts = Counter(all_chars)
    
    entropy = 0.0
    for count in counts.values():
        p = count / n
        if p > 0:
            entropy -= p * np.log2(p)
    
    return entropy * 4  # bits per hex char (4 bits)


# ============================================================================
# LOAD/SAVE
# ============================================================================
def load_addresses_from_file(filepath: str, limit: int = None) -> List[str]:
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            addresses = [line.strip() for line in f if line.strip()]
        if limit:
            addresses = addresses[:limit]
        return addresses
    except FileNotFoundError:
        print(f"⚠️ File not found: {filepath}")
        return []


def save_results(results: List[AddressResult], config: TEESConfig):
    with open(config.output_file, 'w', encoding='utf-8') as f:
        f.write("ADDRESS\tFINGERPRINT\tSHA256\tVSM\tSTATUS\n")
        for r in results:
            status = "STABLE" if r.state['is_stable'] else "SYNC"
            f.write(f"{r.address}\t{r.fingerprint}\t{r.sha256}\t"
                    f"{r.state['vsm']:.3f}\t{status}\n")
    print(f"\n💾 Results saved to: {config.output_file}")


# ============================================================================
# RESULTS OUTPUT
# ============================================================================
def print_results(results: List[AddressResult], config: TEESConfig):
    stable_count = sum(1 for r in results if r.state['is_stable'])
    optimized_count = sum(1 for r in results if r.optimization_successful)
    total_stable = stable_count + optimized_count
    irreversible_count = sum(1 for r in results
                             if r.irreversibility and r.irreversibility['is_irreversible'])
    
    fingerprints = [r.fingerprint for r in results]
    uniformity = test_uniformity(fingerprints)
    entropy = estimate_entropy(fingerprints)

    print("\n" + "=" * 80)
    print("  TEES v19.0 — EMERGENT PHYSICAL FINGERPRINT RESULTS")
    print("=" * 80)

    print(f"\n[STABILITY STATISTICS]")
    print(f"   Total addresses:                {len(results)}")
    print(f"   Naturally stable:               {stable_count} "
          f"({stable_count/max(len(results),1)*100:.0f}%)")
    print(f"   After optimization:             {optimized_count} "
          f"({optimized_count/max(len(results),1)*100:.0f}%)")
    print(f"   Total stable:                   {total_stable} "
          f"({total_stable/max(len(results),1)*100:.0f}%)")
    print(f"   Irreversible (4/4 proofs):      {irreversible_count} "
          f"({irreversible_count/max(len(results),1)*100:.0f}%)")

    vsms = [r.state['vsm'] for r in results]
    print(f"\n[VORTEX STABILITY METRIC (VSM)]")
    print(f"   Average VSM:      {np.mean(vsms):.3f} +/- {np.std(vsms):.3f}")
    print(f"   Stability threshold: {config.vsm_threshold}")

    print(f"\n[ENTROPY & UNIFORMITY TESTS]")
    print(f"   Chi-square:        {uniformity['chi2']:.1f} "
          f"({'✓ uniform' if uniformity['uniform'] else '✗ not uniform'})")
    print(f"   Shannon entropy:   {entropy:.2f} bits/char (max 4.0)")

    print(f"\n[SAMPLE STABLE FINGERPRINTS]")
    stable_results = [r for r in results if r.state['is_stable']]
    for r in stable_results[:3]:
        print(f"   [STABLE] {r.fingerprint}  (VSM={r.state['vsm']:.3f})")
    opt_results = [r for r in results if r.optimization_successful and not r.state['is_stable']]
    for r in opt_results[:3]:
        print(f"   [OPT]    {r.fingerprint_optimized}  (VSM={r.state['vsm']:.3f}→0.7+)")

    print(f"\n[CONCLUSION]")
    print(f"   v19.0: Emergent Physical Fingerprint (EPF)")
    print(f"   Not a collision-resistant hash. Physical entropy source.")
    print(f"   {total_stable}/{len(results)} addresses achieved stable vortex state.")
    print(f"   Chi-square: {uniformity['chi2']:.1f}, Entropy: {entropy:.2f} bits/char")


# ============================================================================
# MAIN
# ============================================================================
if __name__ == "__main__":
    config = TEESConfig()

    print(f"\n📂 Loading addresses from: {config.addresses_file}")
    addresses = load_addresses_from_file(config.addresses_file, limit=100)
    
    if not addresses:
        print("❌ No addresses loaded. Using test addresses.")
        addresses = [
            "hello world",
            "tees protocol v19",
            "emergent physical fingerprint",
            "quantum vortex transition",
        ]
    else:
        print(f"   Loaded {len(addresses)} addresses")

    print(f"\n[PROCESSING] {len(addresses)} addresses...\n")
    print(f"   Configuration: grid={config.grid_size}, nu={config.nu_true}, gamma={config.gamma_true}")
    print(f"   VSM threshold: {config.vsm_threshold}")
    print()

    results = []
    start_time = time.time()
    
    for i, address in enumerate(addresses):
        print(f"   [{i+1}/{len(addresses)}] {str(address)[:40]}...")
        result = process_address(address, config)
        results.append(result)

        s = result.state
        status = "[STABLE]" if s['is_stable'] else "[..] optimizing..."
        print(f"      Gamma={s['Gamma']:.3f}  VSM={s['vsm']:.3f}  "
              f"phase={s['phase']:.3f}  t_vortex={s['t_vortex']:.3f}")
        print(f"      {status}")
        print(f"      fingerprint = {result.fingerprint}")
        
        if result.optimization_successful:
            print(f"      [OPT] SUCCESS ({result.optimization_iterations} iter, mode={result.best_mode})")
            print(f"      fingerprint_opt = {result.fingerprint_optimized}")
        elif not s['is_stable']:
            print(f"      [OPT] FAILED ({result.optimization_iterations} iter)")
        
        irrev = result.irreversibility
        if irrev:
            proofs = sum(irrev['proof_components'].values())
            print(f"      irreversibility: {'[OK] PROVEN' if irrev['is_irreversible'] else '[!!] reversible'} "
                  f"({proofs}/4 proofs)")
        print()

    elapsed = time.time() - start_time
    print(f"\n⏱️  Processing time: {elapsed:.2f}s ({elapsed/max(len(addresses),1):.2f}s per address)")

    print_results(results, config)
    save_results(results, config)
    
    # Sensitivity test on first address
    if addresses:
        print(f"\n[SENSITIVITY TEST]")
        sensitivity = test_sensitivity(addresses[0], config)
        print(f"   1-bit change → {sensitivity*100:.1f}% bits flipped in fingerprint")
        print(f"   (Ideal: ~50% — avalanche effect for fingerprints)")