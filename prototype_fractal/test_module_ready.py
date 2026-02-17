"""
СТ ТСТ ТЫ Я
"""

import os
import sys

print("🔧 Тест работы модуля эмерджентного времени")
print("=" * 50)

# уть к модулю
module_path = os.path.join(os.getcwd(), "emergent_time")
print(f"уть к модулю: {module_path}")

# роверяем существование
if not os.path.exists(module_path):
    print("❌ апка emergent_time не найдена!")
    print("Текущая директория:", os.getcwd())
    print("Содержимое:")
    for item in os.listdir('.'):
        print(f"  - {item}")
    exit(1)

print("✅ апка emergent_time найдена")

# роверяем структуру
required_files = [
    "emergent_time/__init__.py",
    "emergent_time/core/emergent_engine.py",
    "emergent_time/integration/spectravortex_solver.py"
]

all_files_exist = True
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} не найден")
        all_files_exist = False

if not all_files_exist:
    print("\n⚠️  е все файлы найдены")
    exit(1)

print("\n✅ се файлы модуля на месте")

# робуем импортировать
print("\n🔍 опытка импорта...")

# обавляем путь
sys.path.insert(0, module_path)
sys.path.insert(0, os.path.join(module_path, "integration"))

try:
    # робуем импортировать через пакет
    import emergent_time
    print("✅ акет emergent_time загружен")
    
    from emergent_time.integration.spectravortex_solver import EmergentTimeSolver
    print("✅ EmergentTimeSolver импортирован")
    
    # Тестируем
    solver = EmergentTimeSolver(config={"validation": True})
    print(f"✅ Solver создан: {solver.name} v{solver.version}")
    
    # ыстрый тест
    problem = {"type": "temporal_synchronization", "network": {"num_nodes": 3}}
    
    can_solve, confidence = solver.can_solve(problem)
    print(f"✅ can_solve: {confidence:.0%} уверенности")
    
    solution = solver.solve(problem)
    print(f"✅ ешение получено: {solution['status']}")
    
    if solution['status'] == 'solved':
        order = solution['data']['synchronization']['order_parameter']
        print(f"📊 араметр порядка: {order:.3f}")
    
    print("\n" + "=" * 50)
    print("🎉 Ь ТТ Т!")
    print("=" * 50)
    
    print("\n📋 ля интеграции в SpectraVortex добавьте в phase3_demo.py:")
    print('''
# осле создания SolverManager
try:
    from emergent_time.integration.spectravortex_solver import EmergentTimeSolver
    temporal_solver = EmergentTimeSolver()
    solver_id = solver_mgr.register_solver(temporal_solver)
    print(f"🌀 EmergentTimeSolver зарегистрирован: {solver_id}")
except ImportError as e:
    print(f"⚠️  одуль эмерджентного времени не загружен: {e}")
''')
    
except Exception as e:
    print(f"❌ шибка: {e}")
    import traceback
    traceback.print_exc()
