"""
Обёртка для запуска run_3d_table.py с резонансным ПИД-регулятором.
Запускается из изолированной среды feature/.
"""

import sys
import os
import pathlib
import argparse

# Определяем базовую директорию (feature/)
base_dir = pathlib.Path(__file__).parent.resolve()

# Добавляем все необходимые пути
sys.path.insert(0, str(base_dir))
sys.path.insert(0, str(base_dir / 'periodic_table_model'))
sys.path.insert(0, str(base_dir / 'periodic_table_model' / 'scripts'))
sys.path.insert(0, str(base_dir / 'periodic_table_model' / 'src'))  # на случай, если модули там

# Импортируем наш модифицированный fractal_time
import fractal_time

# Импортируем резонансный ПИД
from resonance_pid import ResonancePIDController

# Импортируем оригинальный главный модуль
import run_3d_table_base

# ========== ПАТЧ (подмена) КЛАССОВ ВМЕСТО ФУНКЦИИ ==========
# Подменяем классы в оригинальном модуле на наши модифицированные.
# Это нужно сделать ДО того, как оригинальный код начнёт их использовать.
run_3d_table_base.FractalTimeEvolution = fractal_time.FractalTimeEvolution
run_3d_table_base.FractalTimeBuffer = fractal_time.FractalTimeBuffer
run_3d_table_base.FractalFieldWrapper = fractal_time.FractalFieldWrapper
print("[ЭКЗОРЦИЗМ] Классы FractalTime* ПОДМЕНЕНЫ в run_3d_table_base.")
# ===========================================================

# ========== ГЛОБАЛЬНАЯ ПЕРЕМЕННАЯ ДЛЯ ПИД ==========
_resonance_pid = None

def get_resonance_pid():
    return _resonance_pid

# ========== ХИТРЫЙ ХУК: Подмена САМОГО ВЫЗОВА КОНСТРУКТОРА ==========
# Мы сохраняем оригинальный конструктор класса FractalTimeEvolution
_original_FractalTimeEvolution = run_3d_table_base.FractalTimeEvolution

# Создаём функцию-обёртку, которая будет вызываться вместо конструктора
def patched_FractalTimeEvolution(*args, **kwargs):
    print("[ЭКЗОРЦИЗМ] ВЫЗВАН patched_FractalTimeEvolution! ПИД будет подключён.")
    # Внедряем ПИД как дополнительный аргумент в конструктор
    if _resonance_pid is not None:
        kwargs['resonance_pid'] = _resonance_pid
        print(f"[ЭКЗОРЦИЗМ] ПИД ДОБАВЛЕН В kwargs для конструктора.")
    else:
        print("[ЭКЗОРЦИЗМ] ПИД НЕ БЫЛ ПЕРЕДАН! _resonance_pid is None")
    
    # Вызываем НАШ модифицированный конструктор, а не оригинальный
    # Вместо _original_FractalTimeEvolution используем fractal_time.FractalTimeEvolution
    evolution = fractal_time.FractalTimeEvolution(*args, **kwargs)
    print(f"[ЭКЗОРЦИЗМ] Создан объект evolution из НАШЕГО класса. ПИД внутри: {evolution.resonance_pid}")
    return evolution

# Подменяем класс на нашу функцию-обёртку
run_3d_table_base.FractalTimeEvolution = patched_FractalTimeEvolution
# =====================================================================

# ========== МОДИФИКАЦИЯ АРГУМЕНТОВ КОМАНДНОЙ СТРОКИ ==========
if __name__ == "__main__":
    # Парсим аргументы, включая наши новые
    parser = argparse.ArgumentParser(
        description="3D моделирование таблицы Менделеева с резонансным ПИД-управлением",
        parents=[run_3d_table_base.parser] if hasattr(run_3d_table_base, 'parser') else []
    )
    
    # Добавляем наши аргументы
    parser.add_argument('--resonance-pid', action='store_true',
                        help='Включить резонансный ПИД-регулятор через Буфер Безвременья')
    parser.add_argument('--target-d', type=float, default=2.12,
                        help='Целевое значение d_min для ПИД-регулятора')
    parser.add_argument('--pid-kp', type=float, default=1.0,
                        help='Пропорциональный коэффициент ПИД')
    parser.add_argument('--pid-ki', type=float, default=0.01,
                        help='Интегральный коэффициент ПИД')
    parser.add_argument('--pid-kd', type=float, default=0.1,
                        help='Дифференциальный коэффициент ПИД')
    parser.add_argument('--pid-level', type=int, default=5,
                        help='Целевой фрактальный уровень для резонансного воздействия (1-7)')
    
    # Парсим аргументы
    args, unknown = parser.parse_known_args()
    
    # Инициализируем ПИД, если нужно
    if args.resonance_pid:
        _resonance_pid = ResonancePIDController(
            target_d=args.target_d,
            Kp=args.pid_kp,
            Ki=args.pid_ki,
            Kd=args.pid_kd,
            target_level=args.pid_level
        )
        print("=" * 60)
        print("[ЭКЗОРЦИЗМ] ПИД СОЗДАН. Объект:", _resonance_pid)
        print("=" * 60)
        print("[РЕЗОНАНСНЫЙ ПИД] АКТИВИРОВАН")
        print(f"    Целевое d_min: {args.target_d}")
        print(f"    Коэффициенты: Kp={args.pid_kp}, Ki={args.pid_ki}, Kd={args.pid_kd}")
        print(f"    Целевой фрактальный уровень: {args.pid_level}")
        print("=" * 60)
    
    # Подменяем sys.argv, чтобы оригинальный парсер не ругался на неизвестные аргументы
    new_argv = [sys.argv[0]]
    skip_next = False
    for arg in sys.argv[1:]:
        if skip_next:
            skip_next = False
            continue
        if arg.startswith('--resonance-pid'):
            continue  # это флаг, значения нет
        elif arg.startswith('--target-d') or arg.startswith('--pid-'):
            skip_next = True  # следующий аргумент - значение, его тоже пропускаем
            continue
        else:
            new_argv.append(arg)
    sys.argv = new_argv
    
    # Запускаем оригинальную main
    try:
        run_3d_table_base.main()
    except KeyboardInterrupt:
        print("\n[ПИД] Выполнение прервано пользователем")
    
    # Выводим статистику ПИД
    if _resonance_pid is not None:
        stats = _resonance_pid.get_statistics()
        print("\n" + "=" * 60)
        print("[РЕЗОНАНСНЫЙ ПИД] СТАТИСТИКА РАБОТЫ")
        for key, value in stats.items():
            print(f"    {key}: {value}")
        print("=" * 60)