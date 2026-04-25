"""
Автоматическая серия расчётов для разных T и P.
"""

import subprocess
import json
import os
from datetime import datetime

# Конфигурация серии
SERIES = [
    {"T": 300, "P": 0.1, "steps": 300, "grid": 128},
    {"T": 300, "P": 5.0, "steps": 300, "grid": 128},
    {"T": 300, "P": 10.0, "steps": 300, "grid": 128},
    {"T": 300, "P": 50.0, "steps": 300, "grid": 128},
    {"T": 1000, "P": 5.0, "steps": 300, "grid": 128},
    {"T": 1000, "P": 10.0, "steps": 300, "grid": 128},
    {"T": 5000, "P": 50.0, "steps": 300, "grid": 128},
]

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, '..', 'results', 'pt_series')
os.makedirs(RESULTS_DIR, exist_ok=True)

def run_simulation(params, run_id):
    """Запуск одной симуляции"""
    T = params["T"]
    P = params["P"]
    steps = params["steps"]
    grid = params["grid"]
    
    output_file = f"autosave_T{T}_P{P}_{grid}_steps{steps}.json"
    output_path = os.path.join(RESULTS_DIR, output_file)
    
    # Если файл уже есть — пропускаем
    if os.path.exists(output_path):
        print(f"  ⏭️  {output_file} уже существует, пропускаем")
        return output_path
    
    print(f"\n🚀 Запуск #{run_id}: T={T}K, P={P}GPa, steps={steps}")
    start_time = datetime.now()
    
    cmd = [
        "python", "run_3d_table.py",
        "--steps", str(steps),
        "--grid", str(grid),
        "--T", str(T),
        "--P", str(P),
        "--no-tune"  # Отключаем ПИД для скорости
    ]
    
    try:
        subprocess.run(cmd, check=True, cwd=os.path.dirname(__file__))
        
        # Перемещаем финальный файл в pt_series
        default_final = os.path.join(BASE_DIR, '..', 'results', f'autosave_T{T}_P{P}_{grid}_local_final.json')
        if os.path.exists(default_final):
            os.rename(default_final, output_path)
        
        elapsed = (datetime.now() - start_time).total_seconds() / 60
        print(f"  ✅ Завершено за {elapsed:.1f} мин")
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Ошибка: {e}")
        return None

def main():
    print("=" * 60)
    print("СЕРИЯ P-T РАСЧЁТОВ")
    print("=" * 60)
    print(f"Всего запусков: {len(SERIES)}")
    print(f"Результаты будут сохранены в: {RESULTS_DIR}")
    print()
    
    results = []
    for i, params in enumerate(SERIES, 1):
        output = run_simulation(params, i)
        if output:
            results.append({
                "id": i,
                "T": params["T"],
                "P": params["P"],
                "file": os.path.basename(output)
            })
    
    # Сохраняем индекс
    index_path = os.path.join(RESULTS_DIR, "index.json")
    with open(index_path, 'w') as f:
        json.dump({"series": results, "generated": datetime.now().isoformat()}, f, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✅ Серия завершена. {len(results)} из {len(SERIES)} успешно.")
    print(f"Индекс сохранён: {index_path}")

if __name__ == "__main__":
    main()