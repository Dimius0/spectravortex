# run_pt_series_1024.py
import subprocess
import os
import shutil
import sys
from datetime import datetime

# Точки для расчёта (полная матрица для анализа паттернов)
POINTS = [
    (300, 0.1, "T300_P0.1"),
    (300, 5.0, "T300_P5.0"),
    (300, 10.0, "T300_P10.0"),
    (300, 50.0, "T300_P50.0"),
    (1000, 5.0, "T1000_P5.0"),
    (1000, 10.0, "T1000_P10.0"),
    (5000, 50.0, "T5000_P50.0"),
]

# Параметры релаксации (КРИТИЧЕСКИ ВАЖНО: 1024 шага)
STEPS = 1024
GRID = 64
RESULTS_DIR = "results/pt_series_1024"

def main():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    
    print("=" * 70)
    print(f"PT SERIES (FULL RELAXATION): 1024 steps, grid={GRID}")
    print(f"Start: {datetime.now()}")
    print(f"Total runs: {len(POINTS)} (expected ~2-3h each)")
    print("=" * 70)

    for i, (T, P, name) in enumerate(POINTS, 1):
        print(f"\n[{i}/{len(POINTS)}] Running: T={T}K, P={P}GPa -> {name}")
        
        # Команда запуска
        cmd = [
            sys.executable, "run_3d_table.py",
            "--steps", str(STEPS),
            "--grid", str(GRID),
            "--T", str(T),
            "--P", str(P),
            "--no-tune"
        ]
        
        print(f" Command: {' '.join(cmd)}")
        
        try:
            # Запускаем и ждём завершения
            result = subprocess.run(cmd, capture_output=False, text=True)
            
            if result.returncode == 0:
                print(f" [✓] Simulation finished successfully.")
                
                # Ищем созданный файл в папке results
                src_file = f"../results/autosave_T{T}_P{P}_{GRID}_local_final.json"
                dst_file = os.path.join(RESULTS_DIR, f"{name}_final.json")
                
                if os.path.exists(src_file):
                    shutil.copy(src_file, dst_file)
                    print(f" [✓] Copied to {dst_file}")
                    
                    # Копируем также шаг 100 (до 5 уровня) и шаг 500 (после 5 уровня)
                    step_files = [100, 500]
                    for s in step_files:
                        step_src = f"../results/autosave_T{T}_P{P}_{GRID}_local_step_{s}.json"
                        if os.path.exists(step_src):
                            shutil.copy(step_src, os.path.join(RESULTS_DIR, f"{name}_step_{s}.json"))
                            print(f" [✓] Saved intermediate step {s}")
                else:
                    print(f" [!] WARNING: {src_file} not found!")
            else:
                print(f" [✗] ERROR: Simulation failed.")
                
        except Exception as e:
            print(f" [✗] EXCEPTION: {e}")

    print("\n" + "=" * 70)
    print(f"PT SERIES FINISHED: {datetime.now()}")
    print(f"Results in: {RESULTS_DIR}")
    print("=" * 70)

if __name__ == "__main__":
    main()