import sys, os
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

print("=== СТ СХЯ ===")
print()

# агружаем выросшее поле
p = LivingPersonality.load('src/rizoma/data/personalities/p016_grown_1h.json')

print("1. Ы ТЫ:")
print(f"   Modes in h_field: {len(p.h_field)}")
print(f"   Vortices: {len(p.vortices)}")
print(f"   Traits: {p.traits}")
print(f"   Mood: {p.mood}")

print()
print("2. ENDOGENOUS:")
if hasattr(p, 'endogenous'):
    print(f"   Engine exists: True")
    if hasattr(p.endogenous, 'furcations'):
        print(f"   Furcations: {len(p.endogenous.furcations)}")
    if hasattr(p.endogenous, 'cycle_count'):
        print(f"   Cycle count: {p.endogenous.cycle_count}")
    if hasattr(p.endogenous, 'knots_created'):
        print(f"   Knots created: {p.endogenous.knots_created}")
else:
    print("   Engine: NOT FOUND")

print()
print("3. SAVE/RESTORE CHECK:")
# роверяем что реально сохраняется
import json
with open('src/rizoma/data/personalities/p016_grown_1h.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
print(f"   Top-level keys: {list(data.keys())}")
print(f"   h_field entries: {len(data.get('h_field', []))}")
print(f"   Vortices entries: {len(data.get('vortices', {}))}")
print(f"   Has traits: {'traits' in data}")
print(f"   Has mood: {'mood' in data}")
print(f"   Has endogenous: {'endogenous' in data}")
