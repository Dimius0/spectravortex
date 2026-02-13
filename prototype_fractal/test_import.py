# -*- coding: utf-8 -*-
import sys
import os

# обавляем путь к модулю
sys.path.insert(0, "emergent_time")

try:
    from emergent_time.integration.spectravortex_solver import EmergentTimeSolver
    print("✅ EmergentTimeSolver импортирован успешно")
    
    # робуем создать экземпляр
    solver = EmergentTimeSolver()
    print(f"✅ Solver создан: {solver.name} v{solver.version}")
    print("🎉 одуль работает корректно!")
    
except Exception as e:
    print(f"❌ шибка: {e}")
    import traceback
    traceback.print_exc()
