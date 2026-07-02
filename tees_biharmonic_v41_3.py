#!/usr/bin/env python3
"""
tees_biharmonic_v41_3.py — TEES v41.3: Intersection Horizon (ABSOLUTE DRIVE)
==============================================================================
v41.3: The horizon is always ahead!
       + Adaptive grid with range expansion (16→256, never repeats)
       + Adaptive target — always one step beyond current best
       + Blacklist forever — no resets, only forward
       + Narrow overlapping bands for precise peak capture
       + Relaxed phase check + warmup period for stability
       + BALANCED: 5 intersections × 3 configs = 15/iter
       + Path A: approach from below (floor)
       + Path B: approach from above (ceil) 
       + Intersection point = true fractional ratio
       + ALL previous features PRESERVED
       + Random: EXILED (except when necessary)!
       + Ножницы под замком! 🔒
       + Прогресс-бар в бесконечность! 🦂🔭
"""

import sys, time, hashlib, struct, warnings, os, json
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any, Set
from enum import Enum, auto
import numpy as np
from scipy.ndimage import gaussian_filter, sobel
from sklearn.linear_model import RANSACRegressor
from collections import deque, defaultdict
from functools import lru_cache

try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

warnings.filterwarnings("ignore")
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

print("=" * 80)
print("  TEES v41.3: Intersection Horizon — ABSOLUTE DRIVE 🔬🔭🦂")
print("  The horizon is ALWAYS ahead!")
print("  Adaptive grid + Adaptive target + Blacklist forever!")
print("=" * 80)

BASE58_ALPHABET = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"

# ===========================================================================
# VALIDATION & FIELD
# ===========================================================================
def validate_bitcoin_address(address: str) -> Tuple[bool, str]:
    if not address: return False, "EMPTY"
    address = address.strip()
    if len(address) < 26 or len(address) > 35: return False, "LEN"
    for c in address:
        if c not in BASE58_ALPHABET: return False, f"CHAR_{c}"
    if address[0] not in "13": return False, "PREFIX"
    try:
        num = 0
        for c in address: num = num * 58 + BASE58_ALPHABET.index(c)
        decoded = num.to_bytes(25, byteorder="big"); payload, checksum = decoded[:-4], decoded[-4:]
        expected = hashlib.sha256(hashlib.sha256(payload).digest()).digest()[:4]
        return (True, "VALID") if checksum == expected else (False, "CHECKSUM")
    except: return False, "DECODE"

def address_to_seed(address) -> int:
    if isinstance(address, str): address = address.encode("utf-8")
    return struct.unpack(">I", hashlib.sha256(address).digest()[:4])[0]

def generate_field_from_address(address, config):
    if isinstance(address, str): address_bytes = address.encode("utf-8")
    else: address_bytes = address
    seed = address_to_seed(address_bytes); rng = np.random.RandomState(seed)
    hash_bytes = hashlib.sha256(address_bytes).digest(); gs = int(config.grid_size)
    kx = np.fft.fftfreq(gs, d=2.0/gs); ky = np.fft.fftfreq(gs, d=2.0/gs)
    KX, KY = np.meshgrid(kx, ky); K = np.sqrt(KX**2 + KY**2); K[0,0] = 1.0
    spectrum = rng.randn(gs, gs) + 1j*rng.randn(gs, gs)
    for i in range(8):
        val = struct.unpack(">I", hash_bytes[i*4:(i+1)*4])[0]; weight = val/(2**31) - 1
        mask = np.abs(K - (0.5 + i*1.5)) < 0.8
        if np.any(mask): spectrum[mask] *= 1 + weight
    spectrum = spectrum * K**(-5/3) * np.exp(-(K**2)/10)
    field = np.real(np.fft.ifft2(spectrum * (K < 15)))
    return (field - field.mean()) / (field.std() + 1e-8)

@lru_cache(maxsize=256)
def _vortex_kernel(gs, gamma, dt, nu):
    kx = np.fft.fftfreq(gs, d=2.0/gs); ky = np.fft.fftfreq(gs, d=2.0/gs)
    KX, KY = np.meshgrid(kx, ky); K2 = KX**2 + KY**2; K2[0,0] = 1e-8
    return np.exp(1j * gamma * dt / (2*np.pi*K2 + 1e-8) * (1 - np.exp(-K2*nu*dt)))

def apply_vortex_transition(field, config):
    gs = int(config.grid_size)
    return np.real(np.fft.ifft2(np.fft.fft2(field) * _vortex_kernel(gs, config.gamma_true, config.dt, config.nu_true)))

# ===========================================================================
# HUNT STRATEGY
# ===========================================================================
class HuntStrategy(Enum):
    TEES_RESONANCE = auto()

# ===========================================================================
# CONFIG & RANGES
# ===========================================================================
@dataclass
class TEESConfig:
    grid_size: int = 64; nu_true: float = 0.08; gamma_true: float = 1.5; dt: float = 4.0
    emergence_threshold: float = 0.7; phase_gamma_min: float = 0.3; phase_gamma_max: float = 1.5
    r_center_scales: np.ndarray = field(default_factory=lambda: np.linspace(0.15, 0.75, 8))
    dr_scale: float = 0.08; min_samples_per_ring: int = 30; gradient_threshold: float = 0.01
    r_min: float = 0.05; gamma_valid_range: Tuple[float, float] = (0.1, 10.0)
    n_theta: int = 128; r_mask_spectral: Tuple[float, float] = (0.2, 0.7)
    def __post_init__(self):
        gs = int(self.grid_size); self.x = np.linspace(-1, 1, gs); self.y = np.linspace(-1, 1, gs)
        self.X, self.Y = np.meshgrid(self.x, self.y); self.R = np.sqrt(self.X**2 + self.Y**2)
        self.R_safe = np.maximum(self.R, 1e-8); self.Theta = np.arctan2(self.Y, self.X)
        kx = np.fft.fftfreq(gs, d=2.0/gs); ky = np.fft.fftfreq(gs, d=2.0/gs)
        self.KX, self.KY = np.meshgrid(kx, ky); self.K2 = self.KX**2 + self.KY**2; self.K2[0,0] = 1e-8

@dataclass
class FloatingRange:
    lo: float; hi: float; best: float; name: str; is_integer: bool = False
    def get_step(self, distance):
        if self.is_integer: return max(1, int(distance*30))
        if distance < 0.001: return max(1e-8, distance*0.01)
        elif distance < 0.01: return max(1e-6, distance*0.05)
        return max(1e-6, distance*0.1)
    def sample(self, rng, distance):
        if self.is_integer:
            lo, hi = int(min(self.lo, self.hi)), int(max(self.lo, self.hi))
            return float(rng.randint(lo, hi+1)) if lo < hi else float(self.best)
        return rng.uniform(min(self.lo, self.hi), max(self.lo, self.hi))
    def narrow(self, factor=0.7):
        half = (self.hi - self.lo) * factor / 2; center = self.best
        self.lo = max(self.lo, center - half); self.hi = min(self.hi, center + half)
    def update_best(self, value): self.best = value

# ===========================================================================
# FIELD SENSORS
# ===========================================================================
@dataclass
class FieldSensors:
    consistency: float = 0.0; field_energy: float = 0.0; gradient_energy: float = 0.0
    vorticity: float = 0.0; strain: float = 0.0; helicity: float = 0.0
    spectral_m1: float = 0.0; spectral_m2: float = 0.0; spectral_m3: float = 0.0
    phase_quality: float = 0.0; grid_resonance: float = 0.0
    center_shift: float = 0.0; strike_effectiveness: float = 0.0

class FullDiagnostics:
    def __init__(self): self.sensor_history = deque(maxlen=100); self.grid_resonance_map = {}
    def compute_sensors(self, field_A, field_B, config, state, consistency_before):
        fe = float(np.mean(np.abs(field_A))); ge = float(np.mean(np.abs(np.gradient(field_A))))
        gx, gy = np.gradient(field_A)
        bxs = sobel(field_B, 1) if field_B is not None else np.zeros_like(field_A)
        bys = sobel(field_B, 0) if field_B is not None else np.zeros_like(field_A)
        axs = sobel(field_A, 1); ays = sobel(field_A, 0)
        vo = float(np.mean(np.abs(bys-axs) + np.abs(bxs-ays)))
        st = float(np.mean(np.abs(gx) + np.abs(gy)))
        he = float(np.mean(field_A * (gx - gy)))
        m1 = state.get('m1', 0); m2 = state.get('m2', 0)
        pq = m1 / (m1 + m2 + 0.01) if (m1+m2) > 0 else 0
        gr = self._grid_resonance(config.grid_size, state['consistency'])
        cs = np.sqrt(state.get('cx', 0)**2 + state.get('cy', 0)**2)
        se = state['consistency'] - consistency_before
        return FieldSensors(consistency=state['consistency'], field_energy=fe, gradient_energy=ge,
                           vorticity=vo, strain=st, helicity=he, spectral_m1=m1, spectral_m2=m2,
                           spectral_m3=state.get('m_high',0), phase_quality=pq, grid_resonance=gr,
                           center_shift=cs, strike_effectiveness=se)
    def _grid_resonance(self, grid, consistency):
        if grid not in self.grid_resonance_map: self.grid_resonance_map[grid] = consistency
        else: self.grid_resonance_map[grid] = max(self.grid_resonance_map[grid], consistency)
        if len(self.grid_resonance_map) >= 3:
            nearby = [g for g in self.grid_resonance_map if abs(g-grid) <= 8 and g != grid]
            if nearby: return max(0.0, consistency/(np.mean([self.grid_resonance_map[g] for g in nearby])+0.01) - 1.0)
        return 0.0
    def get_summary(self):
        if not self.sensor_history: return {'energy':0,'phase_quality':0,'grid_resonance':0,'vorticity':0,'energy_trend':'stable'}
        recent = list(self.sensor_history)[-20:]; energies = [s.field_energy for s in recent]
        trend = 'stable'
        if len(energies) >= 5:
            t = np.polyfit(range(5), energies[-5:], 1)[0]
            trend = 'charging' if t > 0.001 else ('discharging' if t < -0.001 else 'stable')
        return {'energy':float(np.mean(energies)),'phase_quality':float(np.mean([s.phase_quality for s in recent])),
                'grid_resonance':float(max([s.grid_resonance for s in recent])),'vorticity':float(np.mean([s.vorticity for s in recent])),
                'helicity':float(np.mean([s.helicity for s in recent])),'energy_trend':trend,
                'strike_effectiveness':float(np.mean([s.strike_effectiveness for s in recent]))}

# ===========================================================================
# ENERGY TRACKER
# ===========================================================================
class EnergyTracker:
    def __init__(self, window_size=50): self.window_size=window_size; self.history=deque(maxlen=window_size); self.charging_detected=False; self.last_strike=-100; self.cooldown=5
    def update(self, sensors, attempt):
        self.history.append(sensors)
        if len(self.history) >= 20:
            recent=list(self.history)[-20:]; energies=[s.field_energy for s in recent]
            if len(energies)>1: self.charging_detected=np.polyfit(range(len(energies)),energies,1)[0]>0.001
    def is_ready(self, attempt):
        if attempt-self.last_strike<self.cooldown: return False,"cooldown"
        if len(self.history)<10: return False,"insufficient"
        recent=list(self.history)[-5:]; avg_e=float(np.mean([s.field_energy for s in recent]))
        if avg_e<max(s.field_energy for s in self.history)*0.7: return False,"low_energy"
        if self.charging_detected: return True,"charging"
        if float(np.mean([s.phase_quality for s in recent]))>0.6: return True,"phase_locked"
        return False,"not_ready"
    def record_strike(self, attempt, ready, reason):
        if ready: self.last_strike=attempt

# ===========================================================================
# TRANSITION DIAGNOSTICS
# ===========================================================================
class TransitionDiagnostics:
    def __init__(self, fa, fb, cfg): self.fa,self.fb,self.cfg=fa,fb,cfg; self._c={}
    def _fc(self):
        if "c" not in self._c:
            gx,gy=sobel(self.fa,1),sobel(self.fa,0); bx,by=sobel(self.fb,1),sobel(self.fb,0)
            v=np.abs(bx-gx)+np.abs(by-gy); v=gaussian_filter(v,2.); t=np.sum(v)
            self._c["c"]=(float(np.sum(self.cfg.X*v)/t) if t>0 else 0.,float(np.sum(self.cfg.Y*v)/t) if t>0 else 0.)
        return self._c["c"]
    def _rg(self):
        if "g" not in self._c:
            cx,cy=self._fc(); c=self.cfg; xl,yl=c.X-cx,c.Y-cy; rl=np.sqrt(xl**2+yl**2)
            ga,gb=sobel(self.fa,1),sobel(self.fa,0); dA=(self.fb-self.fa)/c.dt
            ag=(-yl*ga+xl*gb)/(rl**2+1e-8); vf=1-np.exp(-(rl**2)/(4*c.nu_true*c.dt))
            gf=-vf*ag/(2*np.pi*rl+1e-8); vl=(np.abs(ga)+np.abs(gb)>c.gradient_threshold)&(rl>c.r_min)
            ch=hashlib.sha256(f"{cx:.6f},{cy:.6f}".encode()).digest(); rs=struct.unpack(">I",ch[:4])[0]%(2**15)
            Gs=[]
            for rc in c.r_center_scales:
                mk=(rl>rc-c.dr_scale)&(rl<rc+c.dr_scale)&vl
                if np.sum(mk)<c.min_samples_per_ring: continue
                try:
                    rn=RANSACRegressor(min_samples=max(c.min_samples_per_ring,int(0.5*np.sum(mk))),residual_threshold=np.percentile(np.abs(dA[mk]-np.median(dA[mk])),75),max_trials=200,random_state=rs)
                    rn.fit(gf[mk].reshape(-1,1),dA[mk].reshape(-1)); Ge=abs(rn.estimator_.coef_[0])
                    if c.gamma_valid_range[0]<Ge<c.gamma_valid_range[1]: Gs.append(Ge)
                except: continue
            if len(Gs)<2: self._c["g"]=(0.,0.,0.)
            else: a=np.array(Gs); m,s=np.mean(a),np.std(a); self._c["g"]=(m,1-s/(m+1e-8),m*(1-s/(m+1e-8)))
        return self._c["g"]
    def _sa(self):
        if "s" not in self._c:
            cx,cy=self._fc(); c=self.cfg; xl,yl=c.X-cx,c.Y-cy; rl=np.sqrt(xl**2+yl**2); tl=np.arctan2(yl,xl)
            df=self.fb-self.fa; mk=(rl>c.r_mask_spectral[0])&(rl<c.r_mask_spectral[1])
            if not np.any(mk): self._c["s"]=(0.,0.,0.); return self._c["s"]
            tf,df=tl[mk].flatten(),df[mk].flatten(); si=np.argsort(tf)
            tg=np.linspace(-np.pi,np.pi,c.n_theta); di=np.interp(tg,tf[si],df[si],period=2*np.pi)
            pw=np.abs(np.fft.fft(di))**2; tt=np.sum(pw[1:])
            if tt>0: self._c["s"]=((pw[1]+pw[-1])/tt,(pw[2]+pw[-2])/tt,np.sum(pw[3:])/tt)
            else: self._c["s"]=(0.,0.,0.)
        return self._c["s"]
    def compute_all(self):
        G,cn,en=self._rg(); m1,m2,mh=self._sa(); cx,cy=self._fc()
        te=cn/(1+mh-0.5*m2+0.3)
        ph=np.clip((en-self.cfg.phase_gamma_min)/(self.cfg.phase_gamma_max-self.cfg.phase_gamma_min),0,1) if G>0 else 0.
        return {'Gamma':G,'consistency':cn,'energy':en,'phase':ph,'t_emerg':te,'m1':m1,'m2':m2,'m_high':mh,'is_emergent':cn>=self.cfg.emergence_threshold,'cx':cx,'cy':cy}

# ===========================================================================
# FRACTAL ZOOM LEVEL
# ===========================================================================
class FractalZoomLevel:
    def __init__(self, level, parent_consistency, grid_range, nu_range, gamma_range, dt_range, stagnation, iteration):
        self.level=level; self.parent_consistency=parent_consistency
        self.remaining=max(0.000001,1.0-parent_consistency)
        self.stagnation_at_zoom=stagnation; self.zoom_iteration=iteration; self.zoom_time=time.time()
        self.best_after_zoom=parent_consistency; self.improvements_count=0
        depth_factor=1.0+level*0.5
        self.min_attempts_per_strategy=max(30,int(30*depth_factor))
        self.expected_improvements=max(2,level)
        self.strategy_attempts=defaultdict(int)
        self.goal_achieved=False; self.goal_achieved_iteration=0; self.total_attempts_on_level=0
        stagnation_norm=stagnation/200.0
        sigmoid_factor=0.3+0.6/(1.0+np.exp(-(stagnation_norm-0.5)*10))
        min_grid_width=max(4,20-level*3); min_nu_width=max(0.001,0.01-level*0.002)
        min_gamma_width=max(0.01,0.1-level*0.02); min_dt_width=max(0.1,1.0-level*0.2)
        self.grid_range=FloatingRange(max(grid_range.lo,grid_range.best-max(min_grid_width,grid_range.get_step(self.remaining)*20*sigmoid_factor)),min(grid_range.hi,grid_range.best+max(min_grid_width,grid_range.get_step(self.remaining)*20*sigmoid_factor)),grid_range.best,"grid_L"+str(level),is_integer=True)
        self.nu_range=FloatingRange(max(0.001,nu_range.best-max(min_nu_width,self.remaining*sigmoid_factor*2)),min(1.0,nu_range.best+max(min_nu_width,self.remaining*sigmoid_factor*2)),nu_range.best,"nu_L"+str(level))
        self.gamma_range=FloatingRange(max(0.05,gamma_range.best-max(min_gamma_width,self.remaining*sigmoid_factor*2)),min(5.0,gamma_range.best+max(min_gamma_width,self.remaining*sigmoid_factor*2)),gamma_range.best,"gamma_L"+str(level))
        self.dt_range=FloatingRange(max(0.1,dt_range.best-max(min_dt_width,self.remaining*sigmoid_factor*3)),min(8.0,dt_range.best+max(min_dt_width,self.remaining*sigmoid_factor*3)),dt_range.best,"dt_L"+str(level))
        self.target=parent_consistency+self.remaining*parent_consistency*0.9
        self.parent_grid_range=grid_range; self.parent_nu_range=nu_range
        self.parent_gamma_range=gamma_range; self.parent_dt_range=dt_range
    def is_exhausted(self, stagnation):
        if not self.strategy_attempts: return stagnation>100
        total_attempts=sum(self.strategy_attempts.values())
        if total_attempts>self.min_attempts_per_strategy*6 and stagnation>30: return True
        strategies_with_enough=sum(1 for c in self.strategy_attempts.values() if c>=self.min_attempts_per_strategy)
        return len(self.strategy_attempts)>=4 and strategies_with_enough>=4 and stagnation>50
    def record_strategy_attempt(self, strategy_name): self.strategy_attempts[strategy_name]+=1; self.total_attempts_on_level+=1
    def check_goal_achieved(self, iteration):
        if not self.goal_achieved and self.improvements_count>=self.expected_improvements: self.goal_achieved=True; self.goal_achieved_iteration=iteration
    def get_progress_summary(self):
        si=", ".join(f"{k}:{v}/{self.min_attempts_per_strategy}" for k,v in sorted(self.strategy_attempts.items()))
        return f"{'🎯' if self.goal_achieved else '⏳'} [{si}] impr={self.improvements_count}/{self.expected_improvements}"

# ===========================================================================
# GLOBAL EXPLORATION MAP
# ===========================================================================
class GlobalExplorationMap:
    def __init__(self, base_tolerance=0.01, max_entries=10000):
        self.base_tolerance=base_tolerance; self.max_entries=max_entries
        self.visited_hashes=set(); self.visited_details=deque(maxlen=max_entries)
        self.total_probes=0; self.rejected_duplicates=0
        self.unique_by_method=defaultdict(int); self.zoom_depth=0
    def set_zoom_depth(self, d): self.zoom_depth=d
    @property
    def effective_tolerance(self): return self.base_tolerance/(1.0+self.zoom_depth*0.5)
    def _hash_point(self, grid, nu, gamma, dt):
        tol=self.effective_tolerance
        return (round(grid), round(nu/tol)*tol, round(gamma/tol)*tol, round(dt/(tol*2))*(tol*2))
    def is_visited(self, grid, nu, gamma, dt): return self._hash_point(grid, nu, gamma, dt) in self.visited_hashes
    def mark_visited(self, grid, nu, gamma, dt, consistency, method):
        ph=self._hash_point(grid, nu, gamma, dt)
        if ph in self.visited_hashes: self.rejected_duplicates+=1; return False
        self.visited_hashes.add(ph); self.visited_details.append((grid, nu, gamma, dt, consistency, method, ph))
        self.total_probes+=1; self.unique_by_method[method]+=1; return True
    def get_unexplored_near(self, grid, nu, gamma, dt, rng, max_attempts=100):
        for _ in range(max_attempts):
            ng=int(grid)+rng.randint(-8,9); nn=nu+rng.uniform(-0.1,0.1)
            ngm=gamma+rng.uniform(-0.2,0.2); nd=dt+rng.uniform(-1.0,1.0)
            ng=max(30,min(130,ng)); nn=max(0.001,min(1.0,nn))
            ngm=max(0.05,min(5.0,ngm)); nd=max(0.1,min(8.0,nd))
            if not self.is_visited(ng,nn,ngm,nd): return ng,nn,ngm,nd
        return None
    def get_stats(self):
        total=self.total_probes+self.rejected_duplicates
        return {'total_probes':self.total_probes,'rejected_duplicates':self.rejected_duplicates,
                'rejection_rate':self.rejected_duplicates/max(1,total),'unique_points':len(self.visited_hashes),
                'by_method':dict(self.unique_by_method),'tolerance':self.effective_tolerance}

# ===========================================================================
# ACTIVITY MONITOR
# ===========================================================================
class ActivityMonitor:
    def __init__(self):
        self.start_time=time.time(); self.iteration_times=deque(maxlen=50)
        self.eval_times=deque(maxlen=100); self.config_times=deque(maxlen=100)
        self.total_configs=0; self.total_evals=0; self.peak_memory=0; self.memory_warnings=0
        self._iter_start=0; self._eval_start=0; self._config_start=0
        self.process=psutil.Process() if HAS_PSUTIL else None
    def sample_memory(self):
        if self.process is None: return 0.0
        try: mem=self.process.memory_info().rss/1024/1024; self.peak_memory=max(self.peak_memory,mem); return mem
        except: return 0.0
    def start_iteration(self): self._iter_start=time.time()
    def end_iteration(self): self.iteration_times.append(time.time()-self._iter_start)
    def start_config(self): self._config_start=time.time()
    def end_config(self): self.config_times.append(time.time()-self._config_start); self.total_configs+=1
    def start_eval(self): self._eval_start=time.time()
    def end_eval(self): self.eval_times.append(time.time()-self._eval_start); self.total_evals+=1
    def check_memory_pressure(self):
        mem=self.sample_memory()
        if mem>2000: self.memory_warnings+=1; return "🔴CRITICAL"
        elif mem>1500: self.memory_warnings+=1; return "🟠HIGH"
        elif mem>1000: return "🟡MODERATE"
        return "🟢OK"
    def get_dashboard(self):
        mem=self.sample_memory(); elapsed=time.time()-self.start_time
        ai=np.mean(self.iteration_times) if self.iteration_times else 0
        ae=np.mean(self.eval_times) if self.eval_times else 0
        return (f"⏱️{elapsed:.0f}s | 💾{mem:.0f}MB{self.check_memory_pressure()} | 🔄iter={ai:.2f}s | 🎯eval={ae:.3f}s | 📊cfg={self.total_configs} evals={self.total_evals}")
    def get_final_report(self):
        return (f"⏱️{time.time()-self.start_time:.1f}s | 💾peak={self.peak_memory:.0f}MB | 📊{self.total_configs} cfgs | 🎯{self.total_evals} evals | ⚠️{self.memory_warnings} warnings")

# ===========================================================================
# ADAPTIVE STING
# ===========================================================================
def adaptive_sting(field, config, consistency, energy_tracker, attempt, stagnation, strategy, diagnostics):
    distance=max(0.0001,1.0-consistency); stagnation_factor=1.0+min(stagnation/200,2.0)
    ready,reason=energy_tracker.is_ready(attempt); energy_tracker.record_strike(attempt,ready,reason)
    theta,r=config.Theta,config.R
    intensity=0.5+distance*1.5; phase_kick=0.5; relax_steps=max(5,int(distance*18))
    strike_type="🔭horizon"
    push=intensity*np.sin(theta)*r*np.exp(-(r**2)/0.12)
    push+=intensity*0.3*np.sin(theta)*np.sin(2*theta)*r**2; field+=push
    boost=1.2+distance*0.3
    for _ in range(max(1,int(3*distance))):
        field=apply_vortex_transition(field,config)
        fft=np.fft.fft(field,axis=0); fft[1]*=boost; fft[-1]*=boost
        field=np.real(np.fft.ifft(fft,axis=0))
    fB=apply_vortex_transition(field,config); diag=TransitionDiagnostics(field,fB,config); st=diag.compute_all()
    phase_mod=np.abs(np.sin(st['phase']*np.pi+np.sqrt(st['cx']**2+st['cy']**2)*3))
    sting=phase_kick*phase_mod*np.sin(theta+st['phase']*np.pi)*r*np.exp(-(r**2)/0.15); field+=sting
    for _ in range(relax_steps): field=apply_vortex_transition(field,config)
    fft2=np.fft.fft2(field); K=np.sqrt(config.KX**2+config.KY**2); fft2*=np.exp(-(K**2)*0.02)
    return np.real(np.fft.ifft2(fft2)),strike_type

# ===========================================================================
# INTERSECTION HORIZON DETECTOR — v41.3
# ===========================================================================
@dataclass
class HorizonIntersection:
    """Точка пересечения двух путей к горизонту"""
    ratio: float
    approach_low: float
    approach_high: float
    convergence: float
    N_estimated: int
    stability: float = 0.0
    k_low: float = 0.0
    k_mid: float = 0.0
    k_high: float = 0.0
    
    def to_config(self, base_amplitude=0.5):
        if self.ratio > 5:
            grid = int(np.clip(self.ratio * 8, 30, 130))
        else:
            grid = int(np.clip(1.0 / max(0.01, self.ratio) * 30, 30, 130))
        nu = np.clip(base_amplitude * self.ratio / 3, 0.005, 1.0)
        gamma = np.clip(self.ratio * 0.8, 0.1, 5.0)
        dt = np.clip(4.0 * (1.0 + self.convergence * max(0.1, self.stability)), 0.5, 8.0)
        return TEESConfig(grid_size=grid, nu_true=nu, gamma_true=gamma, dt=dt)


class IntersectionHorizonDetector:
    """🔬🔭 v41.3: Детектор пересечений горизонта"""
    
    def __init__(self, n_peaks=15, min_stability=0.3):
        self.n_peaks = n_peaks
        self.min_stability = min_stability
        self.intersections: List[HorizonIntersection] = []
        self.total_scans = 0
        self.intersections_found = 0
        self.best_convergence = 0.0
        self.configs_generated = 0
        self.config_hits = 0
        self.ratio_history = deque(maxlen=100)
        self.convergence_history = deque(maxlen=100)
        self.bands = [
            (0.5, 2.0), (1.5, 3.5), (3.0, 5.5), (5.0, 8.0),
            (7.0, 11.0), (10.0, 14.0), (13.0, 18.0), (16.0, 22.0),
            (20.0, 26.0), (24.0, 30.0)
        ]
    
    def _get_adaptive_threshold(self) -> float:
        if len(self.convergence_history) < 10: return 0.25
        convs = np.array(self.convergence_history)
        median = np.median(convs)
        iqr = np.percentile(convs, 75) - np.percentile(convs, 25)
        return max(0.10, min(0.5, median - 0.5 * iqr))
    
    def _compute_stability(self, ratio: float, tolerance: float = 0.08) -> float:
        if len(self.ratio_history) == 0: return 0.0
        matches = sum(1 for r in self.ratio_history if abs(r - ratio) < tolerance)
        return matches / len(self.ratio_history)
    
    def _get_band_peaks(self, power, kx, ky, phases, k_min, k_max):
        k_mag = np.sqrt(kx**2 + ky**2)
        band_mask = (k_mag >= k_min) & (k_mag < k_max) & (k_mag > 0.01)
        if not np.any(band_mask): return []
        bp = power[band_mask].flatten(); bk = k_mag[band_mask].flatten()
        bkx = kx[band_mask].flatten(); bky = ky[band_mask].flatten()
        bph = phases[band_mask].flatten()
        si = np.argsort(bp)[::-1]
        peaks = []; seen_k = []
        for idx in si[:self.n_peaks * 3]:
            k_val = float(bk[idx])
            if any(abs(k_val - sk) < 0.5 for sk in seen_k): continue
            seen_k.append(k_val)
            peaks.append({'kx':float(bkx[idx]),'ky':float(bky[idx]),'k':k_val,'amplitude':float(bp[idx]),'phase':float(bph[idx])})
            if len(peaks) >= self.n_peaks: break
        return peaks
    
    def _get_peaks_from_all_bands(self, power, KX, KY, phases):
        all_peaks = []
        for k_min, k_max in self.bands:
            for p in self._get_band_peaks(power, KX, KY, phases, k_min, k_max):
                p['band'] = (k_min, k_max); all_peaks.append(p)
        low = sorted([p for p in all_peaks if p['k']<5], key=lambda x:x['amplitude'], reverse=True)
        mid = sorted([p for p in all_peaks if 5<=p['k']<15], key=lambda x:x['amplitude'], reverse=True)
        high = sorted([p for p in all_peaks if p['k']>=15], key=lambda x:x['amplitude'], reverse=True)
        return low, mid, high
    
    def find_intersections(self, field_A, field_B, config):
        diff = field_B - field_A
        fft = np.fft.fft2(diff); fft_s = np.fft.fftshift(fft)
        power = np.abs(fft_s)**2; phases = np.angle(fft_s)
        gs = int(config.grid_size)
        kx_arr = np.fft.fftfreq(gs, d=2.0/gs); ky_arr = np.fft.fftfreq(gs, d=2.0/gs)
        KX, KY = np.meshgrid(kx_arr, ky_arr)
        low_peaks, mid_peaks, high_peaks = self._get_peaks_from_all_bands(power, KX, KY, phases)
        self.total_scans += 1
        intersections = []; candidates = []
        
        for lp in low_peaks[:8]:
            for mp in mid_peaks[:8]:
                ratio = mp['k'] / max(0.01, lp['k'])
                approach_low = np.floor(ratio); approach_high = np.ceil(ratio)
                if approach_low == approach_high: continue
                dist_low = ratio - approach_low; dist_high = approach_high - ratio
                intersection_ratio = approach_low + dist_low / (dist_low + dist_high)
                convergence = 1.0 - abs(dist_low - dist_high)
                candidates.append({'ratio':ratio,'intersection_ratio':intersection_ratio,'approach_low':approach_low,
                                  'approach_high':approach_high,'convergence':convergence,'lp':lp,'mp':mp})
        
        for c in candidates:
            best_hp = None
            for hp in high_peaks[:5]:
                phase_sum = c['lp']['phase'] + c['mp']['phase'] + hp['phase']
                N_est = int(round(c['intersection_ratio']))
                phase_target = 2 * np.pi * N_est
                phase_diff = abs((phase_sum % (2*np.pi)) - (phase_target % (2*np.pi)))
                if phase_diff > np.pi: phase_diff = 2*np.pi - phase_diff
                if phase_diff < 0.8: best_hp = hp; break
            if best_hp is None and high_peaks: best_hp = high_peaks[0]
            hp = best_hp if best_hp else {'phase':0.0,'k':0.0}
            stability = self._compute_stability(c['intersection_ratio'])
            intersection = HorizonIntersection(
                ratio=float(c['intersection_ratio']), approach_low=float(c['approach_low']),
                approach_high=float(c['approach_high']), convergence=float(c['convergence']),
                N_estimated=int(round(c['intersection_ratio'])), stability=stability,
                k_low=c['lp']['k'], k_mid=c['mp']['k'], k_high=hp.get('k',0.0))
            intersections.append(intersection)
            self.intersections_found += 1
            self.best_convergence = max(self.best_convergence, c['convergence'])
        
        for c in candidates: self.convergence_history.append(c['convergence'])
        for inter in intersections: self.ratio_history.append(inter.ratio)
        intersections.sort(key=lambda x: x.convergence * (0.3 + 0.7 * max(0.1, x.stability)), reverse=True)
        self.intersections = intersections[:50]
        return self.intersections
    
    def intersections_to_configs(self):
        configs = []
        rng = np.random.RandomState(42)
        for inter in self.intersections[:5]:
            base_config = inter.to_config()
            configs.append(base_config); self.configs_generated += 1
            base_grid = base_config.grid_size
            for v in range(2):
                variant_grid = int(np.clip(base_grid + rng.randint(-10, 11), 30, 130))
                variant_nu = np.clip(base_config.nu_true + rng.uniform(-0.1, 0.1), 0.005, 1.0)
                variant_gamma = np.clip(base_config.gamma_true + rng.uniform(-0.3, 0.3), 0.1, 5.0)
                variant_dt = np.clip(base_config.dt + rng.uniform(-0.5, 0.5), 0.5, 8.0)
                configs.append(TEESConfig(grid_size=variant_grid, nu_true=variant_nu, gamma_true=variant_gamma, dt=variant_dt))
                self.configs_generated += 1
        return configs
    
    def record_hit(self): self.config_hits += 1
    @property
    def hit_rate(self): return self.config_hits / max(1, self.configs_generated)
    
    def get_sensor_data(self):
        return {
            'total_scans': self.total_scans, 'intersections_found': self.intersections_found,
            'best_convergence': self.best_convergence, 'adaptive_threshold': self._get_adaptive_threshold(),
            'top_ratios': [f"{i.ratio:.4f}" for i in self.intersections[:5]],
            'top_convergences': [f"{i.convergence:.4f}" for i in self.intersections[:5]],
            'top_stabilities': [f"{i.stability:.3f}" for i in self.intersections[:5]],
            'top_Ns': [i.N_estimated for i in self.intersections[:5]],
            'top_k_details': [f"k_low={i.k_low:.1f}→k_mid={i.k_mid:.1f}" for i in self.intersections[:3]],
            'configs_generated': self.configs_generated, 'config_hits': self.config_hits,
            'hit_rate': self.hit_rate, 'is_working': len(self.intersections) > 0
        }


# ===========================================================================
# INTERSECTION HORIZON HUNTER v41.3 (ABSOLUTE DRIVE)
# ===========================================================================
class IntersectionHorizonHunter:
    """v41.3: The horizon is ALWAYS ahead! Adaptive grid + Adaptive target + Blacklist forever!"""
    
    def __init__(self, max_attempts=500, target=0.99999, n_scouts=2000, max_fractal_levels=5):
        self.max_attempts = max_attempts; self.initial_target = target
        self.base_n_scouts = min(n_scouts, 5000); self.max_fractal_levels = max_fractal_levels
        self.rng = np.random.RandomState(42); self.energy_tracker = EnergyTracker(50)
        self.diagnostics = FullDiagnostics(); self.exploration_map = GlobalExplorationMap()
        self.activity = ActivityMonitor()
        self.horizon_detector = IntersectionHorizonDetector(n_peaks=15, min_stability=0.3)
        self.grid_range = FloatingRange(30, 130, 64, "grid", is_integer=True)
        self.nu_range = FloatingRange(0.005, 1.0, 0.08, "nu")
        self.gamma_range = FloatingRange(0.1, 5.0, 1.5, "gamma")
        self.dt_range = FloatingRange(0.5, 8.0, 4.0, "dt")
        self.best_consistency = 0.0; self.stagnation_counter = 0
        self.fractal_zoom_levels = []; self.freefall_depth = 0.0
        self.last_improvement_iteration = 0; self.premature_zooms = 0
        self._current_address = None
        self.max_configs_per_iteration = 15
    
    @property
    def n_scouts(self):
        depth = len(self.fractal_zoom_levels); multiplier = 2 + depth * 2
        scouts = self.base_n_scouts * multiplier
        mem = self.activity.sample_memory()
        if mem > 1500: scouts = min(scouts, 2000)
        elif mem > 1000: scouts = min(scouts, 5000)
        if self.fractal_zoom_levels:
            remaining = self.fractal_zoom_levels[-1].remaining
            if remaining < 0.0001: scouts = min(max(scouts, 500), 5000)
        return min(scouts, 10000)
    
    def _get_adaptive_target(self):
        """🆕 Адаптивная цель — всегда на шаг впереди!"""
        c = self.best_consistency
        if c < 0.5: return 0.7
        elif c < 0.9: return c + 0.1
        elif c < 0.99: return c + 0.01
        elif c < 0.999: return c + 0.001
        elif c < 0.9999: return c + 0.0001
        elif c < 0.99999: return c + 0.00001
        else: return 1.0
    
    def _get_adaptive_zoom_threshold(self):
        min_cons = 0.65; max_cons = 0.99
        x = (self.stagnation_counter - 100) / 30.0
        sigmoid = 1.0 / (1.0 + np.exp(-x))
        threshold = max_cons - (max_cons - min_cons) * sigmoid
        if self.premature_zooms > 0: threshold = min(0.99, threshold + min(0.05, self.premature_zooms * 0.01))
        return threshold
    
    def _get_zoom_quality(self, level):
        if self.best_consistency > level.parent_consistency:
            return (self.best_consistency - level.parent_consistency) / level.remaining
        return 0.0
    
    def _can_zoom(self, iteration):
        if len(self.fractal_zoom_levels) >= self.max_fractal_levels: return False, "max_levels"
        if self.fractal_zoom_levels:
            cl = self.fractal_zoom_levels[-1]
            if not cl.is_exhausted(self.stagnation_counter):
                return False, f"level_not_exhausted: {cl.get_progress_summary()}"
        threshold = self._get_adaptive_zoom_threshold()
        if self.best_consistency < threshold:
            return False, f"below_threshold({self.best_consistency:.4f}<{threshold:.4f})"
        return True, "ready"
    
    def _generate_horizon_configs(self):
        """🆕 Адаптивный grid с расширением диапазона + blacklist навсегда"""
        all_configs = []
        
        if not hasattr(self, '_grid_scan_blacklist'):
            self._grid_scan_blacklist = set()
            self._grid_scan_history = deque(maxlen=20)
            self._current_scan_grid = int(self.grid_range.best)
            self._scan_momentum = 0
            self._grid_min = 30
            self._grid_max = 130
        
        # Проверяем, не исчерпан ли текущий диапазон
        available_in_range = [g for g in range(self._grid_min, self._grid_max + 1) 
                             if g not in self._grid_scan_blacklist]
        
        if len(available_in_range) == 0:
            # Диапазон исчерпан — РАСШИРЯЕМ горизонт!
            old_min, old_max = self._grid_min, self._grid_max
            self._grid_min = max(8, self._grid_min - 16)
            self._grid_max = min(256, self._grid_max + 32)
            available_in_range = [g for g in range(self._grid_min, self._grid_max + 1) 
                                 if g not in self._grid_scan_blacklist]
            self._scan_momentum = 0  # Сброс momentum на новой территории
        
        candidate = None
        if available_in_range:
            for attempt in range(30):
                if len(self._grid_scan_history) >= 3:
                    recent = list(self._grid_scan_history)[-3:]
                    improvements = [imp for g, imp in recent]
                    grids = [g for g, imp in recent]
                    
                    if max(improvements) > 0.001:
                        best_g = grids[improvements.index(max(improvements))]
                        candidate = int(np.clip(best_g + self.rng.randint(-8, 9), self._grid_min, self._grid_max))
                        self._scan_momentum = min(3, self._scan_momentum + 1)
                    else:
                        spread = 8 * (1 + abs(self._scan_momentum))
                        candidate = int(np.clip(int(self.grid_range.best) + self.rng.randint(-spread, spread+1), 
                                               self._grid_min, self._grid_max))
                        self._scan_momentum = max(-3, self._scan_momentum - 1)
                else:
                    candidate = int(self.rng.choice(available_in_range))
                
                if candidate is not None and candidate not in self._grid_scan_blacklist:
                    break
        else:
            candidate = int(self.rng.randint(self._grid_min, self._grid_max + 1))
        
        scan_grid = candidate
        self._grid_scan_blacklist.add(scan_grid)
        self._current_scan_grid = scan_grid
        
        base_cfg = TEESConfig(grid_size=scan_grid, nu_true=self.nu_range.best,
                             gamma_true=self.gamma_range.best, dt=self.dt_range.best)
        
        try:
            field_A = generate_field_from_address(self._current_address, base_cfg)
            field_B = apply_vortex_transition(field_A, base_cfg)
            intersections = self.horizon_detector.find_intersections(field_A, field_B, base_cfg)
            if intersections:
                configs = self.horizon_detector.intersections_to_configs()
                all_configs.extend(configs)
        except Exception:
            pass
        
        self._grid_scan_history.append((scan_grid, 0.0))
        self._last_scan_grid = scan_grid
        
        if not all_configs:
            for _ in range(5):
                g = int(self.grid_range.sample(self.rng, 0.5))
                n = self.nu_range.sample(self.rng, 0.5)
                gm = self.gamma_range.sample(self.rng, 0.5)
                d = self.dt_range.sample(self.rng, 0.5)
                all_configs.append(TEESConfig(grid_size=g, nu_true=n, gamma_true=gm, dt=d))
        
        return all_configs
    
    def _evaluate(self, address, config, strategy):
        self.activity.start_eval()
        field_A = generate_field_from_address(address, config)
        field_A, strike_type = adaptive_sting(field_A, config, self.best_consistency, self.energy_tracker,
                                              self.stagnation_counter, self.stagnation_counter, strategy, self.diagnostics)
        field_B = apply_vortex_transition(field_A, config)
        diag = TransitionDiagnostics(field_A, field_B, config); state = diag.compute_all()
        sensors = self.diagnostics.compute_sensors(field_A, field_B, config, state, self.best_consistency)
        self.diagnostics.sensor_history.append(sensors); self.energy_tracker.update(sensors, self.stagnation_counter)
        is_new = self.exploration_map.mark_visited(config.grid_size, config.nu_true, config.gamma_true, config.dt,
                                                    state['consistency'], strategy.name)
        self.activity.end_eval()
        return state, sensors, strike_type, is_new
    
    def _try_fractal_zoom(self, iteration):
        can_zoom, reason = self._can_zoom(iteration)
        if not can_zoom: return False
        new_level = FractalZoomLevel(level=len(self.fractal_zoom_levels)+1, parent_consistency=self.best_consistency,
                                     grid_range=self.grid_range, nu_range=self.nu_range, gamma_range=self.gamma_range,
                                     dt_range=self.dt_range, stagnation=self.stagnation_counter, iteration=iteration)
        self.fractal_zoom_levels.append(new_level)
        self.grid_range = new_level.grid_range; self.nu_range = new_level.nu_range
        self.gamma_range = new_level.gamma_range; self.dt_range = new_level.dt_range
        self.freefall_depth += new_level.remaining
        self.exploration_map.set_zoom_depth(len(self.fractal_zoom_levels))
        map_stats = self.exploration_map.get_stats(); dashboard = self.activity.get_dashboard()
        print(f"\n  🌀😱 [GOAL ZOOM L{new_level.level}] cons={self.best_consistency:.6f} stag={self.stagnation_counter}")
        print(f"     Goal: {new_level.min_attempts_per_strategy} att/str | Scouts: {self.n_scouts} | Map: {map_stats['unique_points']}pts")
        print(f"     📊 {dashboard}")
        self.stagnation_counter = 0; return True
    
    def _try_fractal_unzoom(self, iteration):
        if len(self.fractal_zoom_levels) == 0: return False
        current_level = self.fractal_zoom_levels[-1]
        if current_level.goal_achieved: return False
        zoom_quality = self._get_zoom_quality(current_level)
        iterations_on_zoom = iteration - current_level.zoom_iteration
        if iterations_on_zoom < current_level.min_attempts_per_strategy * 4: return False
        should_unzoom = False; reason = ""
        if self.stagnation_counter > 300 and zoom_quality < 0.001:
            should_unzoom = True; reason = f"extreme stag={self.stagnation_counter}"
        elif self.stagnation_counter > 200 and zoom_quality < 0.0001:
            should_unzoom = True; reason = f"stag={self.stagnation_counter} quality={zoom_quality:.4f}"
        if should_unzoom:
            old_level = self.fractal_zoom_levels.pop()
            self.grid_range = old_level.parent_grid_range; self.nu_range = old_level.parent_nu_range
            self.gamma_range = old_level.parent_gamma_range; self.dt_range = old_level.parent_dt_range
            self.premature_zooms += 1; self.freefall_depth -= old_level.remaining
            self.exploration_map.set_zoom_depth(len(self.fractal_zoom_levels))
            print(f"\n  ↩️🦂 [GOAL FAIL UNZOOM] L{old_level.level}→L{len(self.fractal_zoom_levels)} ({reason})")
            self.stagnation_counter = 0; return True
        return False
    
    def hunt(self, address):
        self._current_address = address
        self.best_consistency = 0.0; self.stagnation_counter = 0
        self.fractal_zoom_levels = []; self.freefall_depth = 0.0
        self.premature_zooms = 0; self.last_improvement_iteration = 0
        self.energy_tracker = EnergyTracker(50); self.diagnostics = FullDiagnostics()
        self.exploration_map = GlobalExplorationMap(); self.activity = ActivityMonitor()
        self.horizon_detector = IntersectionHorizonDetector(n_peaks=15, min_stability=0.3)
        # Сброс состояния grid-сканера
        if hasattr(self, '_grid_scan_blacklist'): del self._grid_scan_blacklist
        best_result = None; last_improvement = 0

        print(f"  [INTERSECTION HORIZON v41.3 ABSOLUTE DRIVE] {address[:30]}...")
        print(f"  {'─'*155}")
        print(f"  {'Iter':<6} {'Strategy':<18} {'Grid':<5} {'Sc':<6} {'Cons':<14} {'ΔCons':<10} {'🎯Target':<10} {'🔭Horizon Sensor':<55}")
        print(f"  {'─'*155}")

        for iteration in range(self.max_attempts):
            self.activity.start_iteration()
            adaptive_target = self._get_adaptive_target()

            if self._try_fractal_unzoom(iteration): continue
            if self.stagnation_counter > 50:
                if self._try_fractal_zoom(iteration): continue

            strategy = HuntStrategy.TEES_RESONANCE
            if self.fractal_zoom_levels:
                self.fractal_zoom_levels[-1].record_strategy_attempt(strategy.name)

            configs = self._generate_horizon_configs()
            n_cfgs = len(configs)

            if n_cfgs == 0:
                self.stagnation_counter += 1
                if iteration % 10 == 0:
                    print(f"  ⏳ iter {iteration}: no configs generated...")
                self.activity.end_iteration()
                continue

            configs_to_eval = configs[:self.max_configs_per_iteration]
            n_eval = len(configs_to_eval)
            best_improvement_this_iteration = 0.0

            for cfg in configs_to_eval:
                try:
                    state, sensors, strike_type, is_new = self._evaluate(address, cfg, strategy)
                except Exception:
                    self.stagnation_counter += 1; continue

                cons = state['consistency']
                if cons > self.best_consistency:
                    improvement = cons - self.best_consistency
                    self.best_consistency = cons
                    best_improvement_this_iteration = max(best_improvement_this_iteration, improvement)
                    best_result = {"config": cfg, "state": state, "iteration": iteration,
                                  "sensors": sensors, "strategy": strategy}
                    last_improvement = iteration
                    self.last_improvement_iteration = iteration
                    self.stagnation_counter = 0
                    self.horizon_detector.record_hit()

                    if self.fractal_zoom_levels:
                        cl = self.fractal_zoom_levels[-1]
                        cl.best_after_zoom = max(cl.best_after_zoom, cons)
                        cl.improvements_count += 1
                        cl.check_goal_achieved(iteration)

                    self.grid_range.update_best(float(cfg.grid_size))
                    self.nu_range.update_best(cfg.nu_true)
                    self.gamma_range.update_best(cfg.gamma_true)
                    self.dt_range.update_best(cfg.dt)

                    horizon_sensor = self.horizon_detector.get_sensor_data()
                    dashboard = self.activity.get_dashboard()

                    sensor_str = (f"🔭thr={horizon_sensor['adaptive_threshold']:.3f} "
                                  f"ratios={horizon_sensor['top_ratios'][:3] if horizon_sensor['top_ratios'] else 'none'} "
                                  f"N={horizon_sensor['top_Ns'][:3] if horizon_sensor['top_Ns'] else 'none'} "
                                  f"cfg={horizon_sensor['configs_generated']} "
                                  f"hits={horizon_sensor['config_hits']} "
                                  f"{'✅' if horizon_sensor['is_working'] else '🔍'}")

                    print(f"  {iteration:<6} {strategy.name:<18} {cfg.grid_size:<5} {n_eval:<6} "
                          f"{cons:<14.6f} {improvement:<10.6f} {adaptive_target:<10.6f} {sensor_str}")
                    print(f"         📊 {dashboard}")

                    if cons > 0.85:
                        self.grid_range.narrow(0.7); self.nu_range.narrow(0.7); self.gamma_range.narrow(0.7)

                    if cons >= adaptive_target:
                        new_target = self._get_adaptive_target()
                        print(f"  🎯 [TARGET HIT] {cons:.6f} >= {adaptive_target:.6f} → new target: {new_target:.6f}")
                        if cons > 0.99 and len(self.fractal_zoom_levels) < self.max_fractal_levels:
                            self._try_fractal_zoom(iteration)
                else:
                    self.stagnation_counter += 1

            # Обновление истории grid-сканирования
            if hasattr(self, '_grid_scan_history') and hasattr(self, '_last_scan_grid'):
                self._grid_scan_history[-1] = (self._last_scan_grid, best_improvement_this_iteration)

            if best_improvement_this_iteration == 0 and n_eval > 0:
                self.stagnation_counter += 1

            if iteration % 25 == 0 and iteration > 0:
                horizon_sensor = self.horizon_detector.get_sensor_data()
                print(f"  ── iter {iteration:<4} best={self.best_consistency:.6f} stag={self.stagnation_counter} "
                      f"target={adaptive_target:.6f} "
                      f"🔭thr={horizon_sensor['adaptive_threshold']:.3f} "
                      f"grid_range=[{self._grid_min if hasattr(self,'_grid_min') else 30},"
                      f"{self._grid_max if hasattr(self,'_grid_max') else 130}] "
                      f"bl={len(self._grid_scan_blacklist) if hasattr(self,'_grid_scan_blacklist') else 0}")

            self.activity.end_iteration()
            if self.best_consistency >= 1.0: break

        print(f"  {'─'*155}")
        horizon_sensor = self.horizon_detector.get_sensor_data()
        print(f"  [FINAL v41.3 ABSOLUTE DRIVE] {self.best_consistency:.8f}")
        print(f"  🔭 HORIZON INTERSECTIONS:")
        print(f"     Found: {horizon_sensor['intersections_found']} | Best convergence: {horizon_sensor['best_convergence']:.4f}")
        print(f"     Adaptive threshold: {horizon_sensor['adaptive_threshold']:.4f}")
        print(f"     Top ratios: {horizon_sensor['top_ratios'][:5] if horizon_sensor['top_ratios'] else 'none'}")
        print(f"     Top Ns: {horizon_sensor['top_Ns'][:5] if horizon_sensor['top_Ns'] else 'none'}")
        print(f"     Configs: {horizon_sensor['configs_generated']} | Hits: {horizon_sensor['config_hits']} | Rate: {horizon_sensor['hit_rate']:.2%}")
        if hasattr(self, '_grid_scan_blacklist'):
            print(f"  🗺️ Grid scanner: {len(self._grid_scan_blacklist)} grids tried, range=[{self._grid_min},{self._grid_max}]")
        print(f"  📊 {self.activity.get_final_report()}")
        print()

        return {"address": address, "best_consistency": self.best_consistency,
                "best_grid": best_result["config"].grid_size if best_result else 64,
                "attempts": iteration+1, "intersections_found": horizon_sensor['intersections_found'],
                "best_convergence": horizon_sensor['best_convergence'],
                "adaptive_threshold": horizon_sensor['adaptive_threshold']}


# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    addresses = [
        "1LdRcdxfbSnmCYYNdeYpUnztiYzVfBEQeC",
        "12ib7dApVFvg82TXKycWBNpN8kFyiAN1dr",
        "12tkqA9xSoowkzoERHMWNKsTey55YEBqkv",
        "1F34duy2eeMz5mSrvFepVzy7Y1rBsnAyWC",
    ]
    print("\n[VALIDATING] ...")
    valid = [a for a in addresses if validate_bitcoin_address(a)[0]]
    print(f"  {len(valid)}/{len(addresses)} valid\n")

    hunter = IntersectionHorizonHunter(max_attempts=500, target=0.99999, n_scouts=2000, max_fractal_levels=5)
    results = []
    t0 = time.time()

    for i, addr in enumerate(valid):
        print(f"[{i+1}/{len(valid)}]")
        res = hunter.hunt(addr)
        results.append(res)

    elapsed = time.time() - t0
    cons_list = [r["best_consistency"] for r in results]

    print(f"\n{'='*80}")
    print(f"  🔭 v41.3 ABSOLUTE DRIVE: Avg={np.mean(cons_list):.8f} Max={np.max(cons_list):.8f}")
    print(f"  Time: {elapsed:.1f}s | Adaptive grid + Adaptive target + Blacklist forever!")
    print(f"  The horizon is ALWAYS ahead! 🦂🔭💀")
    print(f"{'='*80}")