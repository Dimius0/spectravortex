import subprocess
import os
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

RESULTS_DIR = "results/pt_series_fixed"
os.makedirs(RESULTS_DIR, exist_ok=True)

print("=" * 60)
print(f"PT SERIES START: {datetime.now()}")
print(f"Total runs: {len(points)}")
print("=" * 60)

for i, (T, P, name) in enumerate(points, 1):
    print(f"\n[{i}/{len(points)}] Running: T={T}K, P={P}GPa -> {name}")
    
    cmd = [
        "python", "run_3d_table.py",
        "--steps", "300",
        "--grid", "128",
        "--T", str(T),
        "--P", str(P),
        "--no-tune",
        "--output", os.path.join(RESULTS_DIR, f"{name}_final.json")
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"    SUCCESS")
        with open(os.path.join(RESULTS_DIR, f"{name}_log.txt"), 'w') as f:
            f.write(result.stdout)
    else:
        print(f"    ERROR: {result.stderr[:200]}")

print("\n" + "=" * 60)
print(f"PT SERIES FINISHED: {datetime.now()}")
print(f"Results in: {RESULTS_DIR}")
print("=" * 60)
