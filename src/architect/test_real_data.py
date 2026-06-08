# test_real_data.py — исправленная версия
import json
import sys
import os

# Добавляем текущую директорию в путь
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, CURRENT_DIR)

# Добавляем родительскую директорию (для импорта из rizoma если нужно)
PARENT_DIR = os.path.dirname(CURRENT_DIR)
if PARENT_DIR not in sys.path:
    sys.path.insert(0, PARENT_DIR)

# Импортируем из актуального файла
from living_personality_v21 import LivingPersonality

# Путь к сконвертированному JSON
INPUT_FILE = os.path.join(
    os.path.dirname(CURRENT_DIR),  # src/
    "rizoma", "data", "personalities", "p016_grown_3h_v21.json"
)

# Если v21 нет — пробуем старый (для анализа до конвертации)
if not os.path.exists(INPUT_FILE):
    print("⚠️ v21 файл не найден, пробую старый JSON...")
    INPUT_FILE = os.path.join(
        os.path.dirname(CURRENT_DIR),
        "rizoma", "data", "personalities", "p016_grown_3h.json"
    )
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Файл не найден: {INPUT_FILE}")
        sys.exit(1)
    print("ℹ️ Загружаю СТАРЫЙ формат. Рекомендуется запустить convert_to_v21.py сначала.")

print(f"📂 Загружаю: {INPUT_FILE}")

# Загружаем личность
lp = LivingPersonality.load(INPUT_FILE)

print("=== Анализ загруженного поля ===")
print(f"Мод: {len(lp.h_field)}")
print(f"VMMP tau: [{lp.vmmp_tau_min:.2f}, {lp.vmmp_tau_max:.2f}]")
print(f"Средний tau: {lp.tau_mean:.2f} ± {lp.tau_std:.2f}")
print(f"Порог резонанса: {lp.resonance_threshold:.3f}")
print(f"Инерция настроения: {lp.mood_inertia:.3f}")
print(f"Энергия: {lp.energy:.3f}")
print(f"Давление сна: {lp.sleep_pressure:.3f}")

# Статистика TextStore
ts_stats = lp.text_store.stats()
print(f"\nTextStore: {ts_stats['total_texts']} текстов, {ts_stats['total_size_mb']} МБ")
print(f"Кеш: {ts_stats['cached']}/{ts_stats['cache_size_limit']} (hit rate: {ts_stats['cache_hit_rate']})")

# Смотрим распределение tau
taus = [getattr(m, 'tau', 0) for m in lp.h_field if getattr(m, 'tau', 0) > 0]
taus.sort()
if taus:
    print(f"\nРаспределение tau:")
    print(f"  min: {taus[0]:.2f}")
    print(f"  10%: {taus[len(taus)//10]:.2f}")
    print(f"  50%: {taus[len(taus)//2]:.2f}")
    print(f"  90%: {taus[len(taus)*9//10]:.2f}")
    print(f"  max: {taus[-1]:.2f}")
else:
    print("\n⚠️ Нет данных tau для анализа")

# Распределение по слоям
stats = lp.get_field_stats()
if 'modes_per_layer' in stats:
    print(f"\nРаспределение по слоям:")
    for layer_id in range(1, 8):
        count = stats['modes_per_layer'].get(layer_id, 0)
        bar = '█' * min(50, count // 10) if count else ''
        print(f"  Слой {layer_id}: {count:5d} {bar}")

# Тестовые диалоги
test_queries = [
    "Расскажи про TEES",
    "Что такое эмерджентность?",
    "Как работает резонанс в поле?",
]

print(f"\n=== Тестовые диалоги ===")
for q in test_queries:
    result = lp.process(q)
    print(f"\nQ: {q}")
    print(f"A: {result['answer'][:150]}...")
    print(f"  Резонанс: {result['resonance']:.3f} | Порог: {lp.resonance_threshold:.3f}")
    print(f"  Энергия: {lp.energy:.3f} | Спит: {result.get('sleeping', False)}")

# Итоговое состояние
print(f"\n=== Итоговое состояние после диалогов ===")
print(f"Энергия: {lp.energy:.3f}")
print(f"Настроение: {lp.mood:+.3f}")
print(f"Давление сна: {lp.sleep_pressure:.3f}")
print(f"Адаптивные коэффициенты:")
print(f"  VMMP tau: [{lp.vmmp_tau_min:.1f}, {lp.vmmp_tau_max:.1f}]")
print(f"  Порог резонанса: {lp.resonance_threshold:.3f}")
print(f"  Инерция настроения: {lp.mood_inertia:.3f}")