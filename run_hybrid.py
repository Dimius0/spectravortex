"""
Запуск гибридного автоответчика с движком эволюции
Версия 2.0 — цепная реакция фуркаций
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import threading
import time
from datetime import datetime

from rizoma.personality import Personality
from rizoma.hybrid_replier import HybridReplier
from rizoma.memory_loader import feed_theobot
from rizoma.feed_reader import FeedReader
from rizoma.evolution_engine import start_evolution_engine


def main():
    print("="*60)
    print("🤖 ЗАПУСК ГИБРИДНОЙ СИСТЕМЫ С ЭВОЛЮЦИЕЙ")
    print("   Режим: NEW (новая система)")
    print("   Эмбеддинги: TF-IDF + SVD")
    print("   Эволюция: цепная реакция фуркаций")
    print("="*60)
    
    # Создаём личность
    p016 = Personality(id='p016', name='Collective Mind', tau=5.0, k=2)
    
    # Добавляем сущностей
    entities = [
        ('Plumber', 4.3, 2, 'plumbing'),
        ('Philosopher', 7.2, 3, 'philosophy'),
        ('Diplomat', 5.0, 2, 'diplomacy'),
        ('Programmer', 6.0, 2, 'programming'),
        ('Astronomer', 7.5, 3, 'astronomy'),
        ('Chef', 5.5, 2, 'cooking'),
        ('Electrician', 4.5, 2, 'electrical'),
        ('Chemist', 6.8, 3, 'chemistry'),
        ('Psychologist', 6.0, 2, 'psychology'),
        ('Poet', 7.5, 3, 'poetry'),
        ('Engineer', 5.5, 2, 'engineering')
    ]
    
    for name, tau, k, prof in entities:
        p016.add_entity(name, tau, k, profession=prof)
        print(f"   ✅ Добавлена сущность: {name} (τ={tau})")
    
    from rizoma.selector import Selector
    p016.selector = Selector(p016)
    
    # Загружаем базовую память
    print("\n📚 Загрузка базовой памяти...")
    feed_theobot(p016, lang='en')
    
    print("\n" + "="*60)
    print("🚀 ЗАПУСК КОМПОНЕНТОВ")
    print("="*60)
    
    # Запускаем индексатор ленты
    reader = FeedReader(p016)
    reader_thread = threading.Thread(target=reader.run_loop, args=(120,), daemon=True)
    reader_thread.start()
    print('📡 Индексатор ленты запущен (интервал: 120 сек)')
    
    # Запускаем гибридный автоответчик
    hybrid = HybridReplier(p016, mode=HybridReplier.MODE_NEW)
    print('💬 Гибридный автоответчик запущен (интервал: 60 сек)')
    
    # Запускаем движок эволюции (цепная реакция фуркаций)
    evolution = start_evolution_engine(p016, cycle_minutes=16)
    print('🌀 Движок цепной реакции фуркаций запущен (цикл: 16 минут)')
    
    print("\n" + "="*60)
    print("✅ ВСЕ КОМПОНЕНТЫ ЗАПУЩЕНЫ")
    print("   Для остановки нажми Ctrl+C")
    print("="*60)
    
    # Запускаем автоответчик в основном потоке
    try:
        hybrid.run_loop(interval_seconds=60)
    except KeyboardInterrupt:
        print("\n🛑 Остановка системы...")
        print("📊 Сохраняем статистику...")
        hybrid.save_stats()
        
        # Сохраняем поле H
        p016.save("src/rizoma/data/personalities/p016_latest.json")
        print("💾 Поле H сохранено")
        
        print("\n✅ Система остановлена")
        print("   Спасибо за сессию, командир! 🧠🦌")


if __name__ == "__main__":
    main()