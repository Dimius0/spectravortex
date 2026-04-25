import os
import time
from datetime import datetime

points = [
    (300, 0.1, "T300_P0.1"),
    (300, 5.0, "T300_P5.0"),
    (300, 10.0, "T300_P10.0"),
    (300, 50.0, "T300_P50.0"),
    (1000, 5.0, "T1000_P5.0"),
    (1000, 10.0, "T1000_P10.0"),
    (5000, 50.0, "T5000_P50.0"),
]

RESULTS_DIR = "results/pt_series_grid64_final"
os.makedirs(RESULTS_DIR, exist_ok=True)

print("=" * 60)
print(f"PT SERIES START: {datetime.now()}")
print(f"Grid: 64 | Steps: 150 | Total runs: {len(points)}")
print("=" * 60)

for i, (T, P, name) in enumerate(points, 1):
    print(f"\n[{i}/{len(points)}] Running: T={T}K, P={P}GPa -> {name}")
    
    cmd = f"python run_3d_table.py --steps 150 --grid 64 --T {T} --P {P} --no-tune"
    print(f"    Command: {cmd}")
    
    start_time = time.time()
    exit_code = os.system(cmd)
    elapsed = time.time() - start_time
    
    if exit_code == 0:
        print(f"    SUCCESS ({elapsed:.1f}s)")
        import shutil
        src = f"autosave_T{T}_{P}_64_local_final.json"
        dst = os.path.join(RESULTS_DIR, f"{name}_final.json")
        if os.path.exists(src):
            shutil.copy(src, dst)
            print(f"    Copied to {dst}")
        else:
            print(f"    WARNING: {src} not found")
    else:
        print(f"    ERROR: exit code {exit_code}")

print("\n" + "=" * 60)
print(f"PT SERIES FINISHED: {datetime.now()}")
print(f"Results in: {RESULTS_DIR}")
print("=" * 60)
