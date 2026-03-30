#!/usr/bin/env python3
"""
Тест трёх режимов ответа (версия 11.1)
Проверяет работу поля H с новыми режимами:
- Штамп (резонанс > 0.7)
- Фуркация (0.3 < резонанс < 0.7)
- Уточнение (резонанс < 0.3)
"""
import sys
import os
import json
import time

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from rizoma.personality import Personality

print("=" * 70)
print("🧪 ТЕСТ ТРЁХ РЕЖИМОВ ОТВЕТА (v11.1)")
print("=" * 70)

# Загружаем поле
try:
    p = Personality.load('src/rizoma/data/personalities/p016_full.json')
    print(f"\n✅ Поле загружено:")
    print(f"   Слов: {len(p.vortices)}")
    print(f"   Мод: {len(p.h_field)}")
    print(f"   Алфавит: {len(p.char_tau)} символов")
    print(f"   Фокус: τ={p.focus['tau']:.2f}")
except Exception as e:
    print(f"\n❌ Ошибка загрузки поля: {e}")
    sys.exit(1)

print("\n" + "=" * 70)
print("📋 ТЕСТОВЫЕ ВОПРОСЫ")
print("=" * 70)

# Вопросы разбиты по категориям
questions = {
    "Штамп (ожидаем резонанс > 0.7)": [
        "Что такое вихревая модель?",
        "Что такое ВММП?",
        "Что такое фуркация?",
        "Что такое квантовый конденсат?",
        "Что такое ∇⁴ψ = 0?",
    ],
    "Фуркация (ожидаем 0.3 < резонанс < 0.7)": [
        "Что такое ризома?",
        "Что такое голограмма сознания?",
        "Что такое фрактальный алфавит?",
        "Что такое спектральный резонанс?",
        "Что такое вихрь смысла?",
    ],
    "Уточнение (ожидаем резонанс < 0.3)": [
        "Как работает реальность?",
        "Что такое смысл?",
        "Почему трава зелёная?",
        "Что такое любовь?",
        "Как устроено сознание?",
    ]
}

# Счётчики
stats = {
    "stamp": 0,
    "furcation": 0,
    "clarification": 0,
    "total": 0
}

for category, q_list in questions.items():
    print(f"\n📂 {category}")
    print("-" * 50)
    
    for q in q_list:
        stats["total"] += 1
        print(f"\n❓ {q}")
        
        try:
            start = time.time()
            result = p.process(q)
            elapsed = time.time() - start
            
            mode_type = result.get('mode_type', '?')
            resonance = result.get('resonance', 0)
            answer = result.get('answer', '')
            
            # Считаем статистику
            if mode_type == 'stamp':
                stats["stamp"] += 1
            elif mode_type == 'furcation_explanation' or mode_type == 'suggestion':
                stats["furcation"] += 1
            elif mode_type == 'clarification':
                stats["clarification"] += 1
            
            # Эмодзи для режима
            emoji = {
                'stamp': '📦',
                'suggestion': '💡',
                'furcation_explanation': '🌀',
                'clarification': '❓'
            }.get(mode_type, '❓')
            
            print(f"   {emoji} Режим: {mode_type}")
            print(f"   📊 Резонанс: {resonance:.3f}")
            print(f"   ⏱️ Время: {elapsed*1000:.0f} мс")
            
            # Показываем ответ (обрезанный)
            if answer:
                if len(answer) > 300:
                    print(f"   📝 Ответ: {answer[:300]}...")
                else:
                    print(f"   📝 Ответ: {answer}")
            else:
                print(f"   ⚠️ Нет ответа")
                
        except Exception as e:
            print(f"   ❌ Ошибка: {e}")

print("\n" + "=" * 70)
print("📊 СТАТИСТИКА")
print("=" * 70)
print(f"   Всего вопросов: {stats['total']}")
print(f"   📦 Штампов: {stats['stamp']}")
print(f"   🌀 Фуркаций: {stats['furcation']}")
print(f"   ❓ Уточнений: {stats['clarification']}")

# Распределение по τ
print("\n📈 РАСПРЕДЕЛЕНИЕ τ В СЛОВАРЕ")
print("-" * 50)
tau_dist = {}
for word, vortex in p.vortices.items():
    tau = vortex.get_dominant_tau()
    if tau:
        tau_key = round(tau, 0)
        tau_dist[tau_key] = tau_dist.get(tau_key, 0) + 1

# Показываем топ-10 τ
sorted_tau = sorted(tau_dist.items(), key=lambda x: x[1], reverse=True)[:10]
for tau, count in sorted_tau:
    bar = "█" * min(50, count // 100)
    print(f"   τ≈{tau:.0f}: {count:5d} слов {bar}")

# Показываем примеры слов для каждого режима
print("\n🔍 ПРИМЕРЫ СЛОВ")
print("-" * 50)

# Слова с высокой амплитудой (потенциальные штампы)
high_amp = [(w, v.amplitude, v.usage_count) for w, v in p.vortices.items() 
            if v.amplitude > 0.6][:10]
if high_amp:
    print("\n   📦 Слова с высокой амплитудой (>0.6):")
    for w, amp, use in high_amp:
        print(f"      {w}: amp={amp:.2f}, uses={use}")

# Слова с низкой амплитудой (потенциальные новые)
low_amp = [(w, v.amplitude) for w, v in p.vortices.items() 
           if v.amplitude < 0.2 and v.usage_count < 2][:10]
if low_amp:
    print("\n   🌱 Слова с низкой амплитудой (<0.2):")
    for w, amp in low_amp:
        print(f"      {w}: amp={amp:.2f}")

print("\n" + "=" * 70)
print("✅ ТЕСТ ЗАВЕРШЁН")
print("=" * 70)