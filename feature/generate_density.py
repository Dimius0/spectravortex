import json
import numpy as np
from pathlib import Path
from datetime import datetime

# ===== ПАРАМЕТРЫ =====
GRID_SIZE = 100
RESOLUTION = 64
FRAMES_LIMIT = -500  # последние 500 фреймов

print("=" * 50)
print("Генератор карты плотности поля H")
print("=" * 50)

# Загрузка
print("\n1. Загружаем траектории...")
with open('data/log_trajectories_3d.json', 'r') as f:
    data = json.load(f)

print(f"   Фреймов: {len(data)}")
frames = data[FRAMES_LIMIT:]

# Создание карты
print(f"\n2. Строим карту {RESOLUTION}x{RESOLUTION}x{RESOLUTION}...")
density_map = np.zeros((RESOLUTION, RESOLUTION, RESOLUTION), dtype=np.float32)
scale = RESOLUTION / GRID_SIZE

for i, frame in enumerate(frames):
    if i % 100 == 0:
        print(f"   Фрейм {i}/{len(frames)}")
    for atoms in frame['groups'].values():
        for atom in atoms:
            x, y, z = atom
            ix = int(x * scale)
            iy = int(y * scale)
            iz = int(z * scale)
            if 0 <= ix < RESOLUTION and 0 <= iy < RESOLUTION and 0 <= iz < RESOLUTION:
                density_map[ix, iy, iz] += 1

# Статистика
nonzero = density_map[density_map > 0]
stats = {
    "max": float(density_map.max()),
    "mean": float(density_map.mean()),
    "nonzero_cells": int(len(nonzero)),
    "total_cells": RESOLUTION ** 3,
    "fill_ratio": round(len(nonzero) / (RESOLUTION ** 3) * 100, 2)
}

print(f"\n3. Статистика:")
print(f"   Максимум: {stats['max']}")
print(f"   Заполнено: {stats['fill_ratio']}%")

# Сохранение
print(f"\n4. Сохраняем...")
density_json = {
    "metadata": {
        "resolution": RESOLUTION,
        "grid_size": GRID_SIZE,
        "frames_used": len(frames),
        "dtype": "float32",
        "stats": stats,
        "description": "3D-карта плотности поля H"
    },
    "density_3d": density_map.flatten().tolist()
}

with open('data/field_h_density_3d.json', 'w') as f:
    json.dump(density_json, f)

size_mb = Path('data/field_h_density_3d.json').stat().st_size / (1024 * 1024)
print(f"   Готово: {size_mb:.1f} MB")
print("\n✓ Файл сохранён: data/field_h_density_3d.json")