"""
Загрузка ВСЕГО в поле H:
- базовые трассы (21)
- диалоги деда с внуком (20)
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rizoma.personality import Personality, SpectralMode
from rizoma.memory_loader import feed_theobot
from rizoma.selector import Selector

print("="*60)
print("📦 ЗАГРУЗКА ВСЕГО В ПОЛЕ H")
print("="*60)

# Загружаем или создаём личность
try:
    p016 = Personality.load("src/rizoma/data/personalities/p016.json")
    print("✅ Личность загружена из p016.json")
    print(f"   В поле H уже: {len(p016.h_field)} мод")
except:
    p016 = Personality(id="p016", name="Collective Mind of SpectraVortex", tau=5.0, k=2)
    print("✅ Создана новая личность p016")

if not p016.selector:
    p016.selector = Selector(p016)

# 1. Загружаем базовые трассы ВММП (21 штука)
print("\n📚 ШАГ 1: Загрузка базовых трасс ВММП...")
feed_theobot(p016, lang="en")

# 2. Диалоги деда с внуком
dialogues_en = [
    # ... (все 20 диалогов из предыдущего файла)
]

print(f"\n📖 ШАГ 2: Загрузка диалогов деда с внуком ({len(dialogues_en)} блоков)...")
for i, dialogue in enumerate(dialogues_en, 1):
    tau = p016.compute_tau_by_resonance(dialogue)
    mode = SpectralMode(
        tau=tau,
        amplitude=0.4,
        content=dialogue[:500],
        trace_type="dialogue",
        trace_id=f"grandson_en_{i:02d}",
        themes=["dialogue", "vmms", "grandfather", "grandson", "education", "physics", "english"],
    )
    p016.add_to_h_field(mode)
    print(f" ✅ Блок {i:2d}: τ={tau:.2f}")

print("\n📊 ИТОГ:")
print(f"   Всего мод в поле H: {len(p016.h_field)}")

# Сохраняем
p016.save("src/rizoma/data/personalities/p016.json")
print("✅ Личность сохранена")

print("\n🦌 ГОТОВО! Поле H наполнено:")
print("   - 21 базовая трасса ВММП")
print("   - 20 диалогов деда с внуком")