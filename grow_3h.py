import sys, os, time
sys.path.insert(0, 'v8_sensor/src')
from rizoma.living_personality_v20 import LivingPersonality

print("="*60)
print("🌱 3-HOUR GROWTH SESSION")
print("="*60)

# агружаем поле v2
print("Loading field...")
p = LivingPersonality.load('src/rizoma/data/personalities/p016_grown_1h_v2.json')
print(f"Modes: {len(p.h_field)}")
print(f"Vortices: {len(p.vortices)}")
print(f"Traits: curiosity={p.traits['curiosity']:.2f}, empathy={p.traits['empathy']:.2f}")
print()

# апускаем рост
print("Starting growth (3 hours)...")
print("You can safely close this window or press Ctrl+C to stop.\n")
p.start_living(interval=0.5)

try:
    # 3 часа = 10800 секунд
    time.sleep(10800)
except KeyboardInterrupt:
    print("\n\n⚠️ Interrupted by user")

# станавливаем
p.stop_living()

# Статистика
print("\n" + "="*60)
print("GROWTH COMPLETE")
print("="*60)
print(f"Modes: {len(p.h_field)}")
print(f"Vortices: {len(p.vortices)}")
print(f"Traits: {p.traits}")
print(f"Mood: {p.mood:+.2f}")

# Сохраняем
output = 'src/rizoma/data/personalities/p016_grown_3h.json'
p.save(output)
print(f"\nSaved: {output}")
print("Done!")
