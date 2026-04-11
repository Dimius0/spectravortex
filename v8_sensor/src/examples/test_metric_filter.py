#!/usr/bin/env python3
"""
Тест метрического фильтра
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from rizoma.metric_filter import MetricFilter


def main():
    print("="*60)
    print("🧪 ТЕСТ: МЕТРИЧЕСКИЙ ФИЛЬТР")
    print("   Автоопределение контекста и ритма")
    print("="*60)
    
    filter = MetricFilter()
    
    # Тестовые тексты
    tests = [
        {
            "name": "Стихи (Пушкин)",
            "text": """
Мама, не плачь, устала ты,
Святослав — сыночек мой,
Милана — радость, свет мечты,
Надежда светит нам с тобой.
"""
        },
        {
            "name": "Диалог",
            "text": """
— Мама, ты устала?
— Немного, сынок. Всё будет хорошо.
— Я помогу тебе.
— Спасибо, Святослав. Ты мой герой.
"""
        },
        {
            "name": "Научная статья",
            "text": """
В данной работе представлена архитектура спектрального поля H. 
Экспериментальные данные показывают, что фуркации происходят 
при достижении амплитудой порога 0.7. Адаптивная динамика 
позволяет системе самонастраиваться.
"""
        },
        {
            "name": "Код",
            "text": """
def furcate(parent, partners):
    new_tau = parent.tau + random.uniform(-0.3, 0.3)
    child = SpectralMode(tau=new_tau, amplitude=parent.amplitude * 0.6)
    return child
"""
        }
    ]
    
    for test in tests:
        print(f"\n📝 {test['name']}:")
        print("-"*40)
        print(test['text'].strip()[:100] + "...")
        
        profile = filter.detect_context(test['text'])
        print(f"\n   Контекст: {profile.context_type}")
        print(f"   Метр: {profile.meter}")
        print(f"   Строгость: {profile.strictness:.2f}")
        print(f"   Рифма: {profile.rhyme}")
        print(f"   Уверенность: {profile.confidence:.2f}")
    
    print("\n" + "="*60)
    print("✅ ТЕСТ ЗАВЕРШЁН")


if __name__ == "__main__":
    main()