#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ЗАПУСК «РИЗОМЫ» — СТРАТЕГИЯ «КВАНТОВЫЙ БРОСОК»
"""
import sys
import threading
import time
from pathlib import Path

HEAD_PATH = Path(__file__).parent / "headquarters"
sys.path.insert(0, str(HEAD_PATH))
sys.path.insert(0, str(Path(__file__).parent))

from headquarters import Coordinator
from headquarters.modules.scout import DeepScoutModule
from headquarters.modules.colonizer import ColonizerModule

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🌱 ЗАПУСК «РИЗОМЫ» — СТРАТЕГИЯ «КВАНТОВЫЙ БРОСОК»")
    print("="*70)

    hq = Coordinator()
    hq.register_module('deep_scout', DeepScoutModule)
    hq.register_module('colonizer', ColonizerModule)

    threads = []
    # Разведчик запускается один раз и умирает
    t1 = threading.Thread(target=hq.modules['deep_scout'].run, daemon=True)
    t1.start()
    threads.append(t1)
    print("   ✅ Разведчик запущен (миссия: 10000)")

    # Колонизатор работает постоянно
    t2 = threading.Thread(target=hq.modules['colonizer'].run, daemon=True)
    t2.start()
    threads.append(t2)
    print("   ✅ Колонизатор запущен (подтягивание фронта)")

    print(f"\n🎯 ГЛАВНАЯ ЦЕЛЬ: {hq.intel.get('primary_target')}")
    print("📡 Данные пишутся в results/battlespace.json")
    print("   Нажми Ctrl+C для остановки\n")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Остановка по запросу")
        hq.intel.save()
        print("✅ Данные сохранены. Ждём новых приказов!")