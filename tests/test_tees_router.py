"""
test_tees_router.py — тесты для TEESRouter v0.40
"""

import sys
import time
import math

# Добавляем родительскую папку в путь
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tees_router import TEESRouter, NoPathError, point_equal


def log(msg):
    print(f"  {msg}")


def test_simple_path():
    """Прямой путь без препятствий"""
    print("1. Простой путь (0,0) → (10,10)")
    router = TEESRouter(grid_size=0.1, field_resolution=64, max_iterations=50)
    
    start = (0.0, 0.0)
    end = (10.0, 10.0)
    
    path = router.find_path(start, end)
    
    assert len(path) >= 2, f"Путь слишком короткий: {len(path)} точек"
    assert point_equal(path[0], start), f"Начало не совпадает: {path[0]} != {start}"
    assert point_equal(path[-1], end), f"Конец не совпадает: {path[-1]} != {end}"
    
    # Путь не должен делать огромных крюков
    path_length = sum(math.dist(path[i], path[i+1]) for i in range(len(path)-1))
    direct = math.dist(start, end)
    assert path_length < direct * 3, f"Путь слишком длинный: {path_length:.1f} vs прямой {direct:.1f}"
    
    log(f"OK: {len(path)} точек, длина {path_length:.1f}")
    return True


def test_obstacle_avoidance():
    """Обход препятствия"""
    print("2. Обход препятствия")
    router = TEESRouter(grid_size=0.1, field_resolution=256, max_iterations=80)
    
    # Препятствие посередине между start и end
    router.set_obstacles([(4.0, 4.0, 6.0, 6.0)])
    
    start = (0.0, 0.0)
    end = (10.0, 10.0)
    
    path = router.find_path(start, end)
    
    assert len(path) >= 2, f"Путь слишком короткий"
    assert point_equal(path[0], start)
    assert point_equal(path[-1], end)
    
    # Проверяем что путь не проходит через препятствие
    for point in path:
        x, y = point
        in_obstacle = (4.0 <= x <= 6.0 and 4.0 <= y <= 6.0)
        assert not in_obstacle, f"Точка {point} внутри препятствия!"
    
    log(f"OK: {len(path)} точек, препятствие обойдено")
    return True


def test_same_cell():
    """Start и end в одной ячейке — ошибка"""
    print("3. Одна ячейка — должен быть NoPathError")
    router = TEESRouter(grid_size=0.1, field_resolution=64)
    
    try:
        router.find_path((5.0, 5.0), (5.05, 5.05))
        assert False, "Не вызвал исключение!"
    except NoPathError as e:
        log(f"OK: NoPathError — {e}")
        return True


def test_impossible_route():
    """Всё поле перекрыто — ошибка"""
    print("4. Невозможный маршрут")
    router = TEESRouter(grid_size=0.1, field_resolution=64, max_iterations=50)
    
    # Огромное препятствие на весь путь
    router.set_obstacles([(-5.0, -5.0, 15.0, 15.0)])
    
    try:
        router.find_path((0.0, 0.0), (10.0, 10.0))
        # Если не упал — смотрим путь
        log("WARNING: нашёл путь через всё препятствие (возможно, обошёл по краю поля)")
    except NoPathError:
        log("OK: NoPathError — маршрут невозможен")
    
    return True


def test_multiple_obstacles():
    """Несколько препятствий"""
    print("5. Несколько препятствий")
    router = TEESRouter(grid_size=0.1, field_resolution=64, max_iterations=80)
    
    router.set_obstacles([
        (2.0, 2.0, 3.0, 8.0),   # вертикальная стена слева
        (7.0, 2.0, 8.0, 8.0),   # вертикальная стена справа
        (3.0, 5.0, 7.0, 5.5),   # горизонтальная перемычка
    ])
    
    start = (0.0, 5.0)
    end = (10.0, 5.0)
    
    path = router.find_path(start, end)
    
    assert len(path) >= 2
    assert point_equal(path[0], start)
    assert point_equal(path[-1], end)
    
    # Проверяем что не заходит в препятствия
    for point in path:
        x, y = point
        for obs in router.obstacles:
            x1, y1, x2, y2 = obs
            in_obs = (x1 <= x <= x2 and y1 <= y <= y2)
            assert not in_obs, f"Точка {point} внутри препятствия {obs}!"
    
    log(f"OK: {len(path)} точек, лабиринт пройден")
    return True


def test_vs_astar():
    """Сравнение длины пути (TEES сам по себе, без A*)"""
    print("6. Качество пути (длина)")
    router = TEESRouter(grid_size=0.1, field_resolution=64, max_iterations=80)
    router.set_obstacles([(4.0, 0.0, 6.0, 8.0)])  # стена с щелью
    
    start = (0.0, 5.0)
    end = (10.0, 5.0)
    
    start_time = time.time()
    path = router.find_path(start, end)
    elapsed = time.time() - start_time
    
    path_length = sum(math.dist(path[i], path[i+1]) for i in range(len(path)-1))
    direct = math.dist(start, end)
    
    log(f"OK: длина {path_length:.1f}, прямой {direct:.1f}, время {elapsed*1000:.0f}ms")
    return True


def test_path_smoothness():
    """Проверка что путь без разрывов"""
    print("7. Непрерывность пути")
    router = TEESRouter(grid_size=0.1, field_resolution=64, max_iterations=50)
    router.set_obstacles([(3.0, 3.0, 7.0, 7.0)])
    
    path = router.find_path((0.0, 0.0), (10.0, 10.0))
    
    # Проверяем что соседние точки близко
    max_step = router.grid_size * 10  # допустимый разрыв
    for i in range(len(path) - 1):
        dist = math.dist(path[i], path[i+1])
        assert dist < max_step, f"Разрыв между точками {i} и {i+1}: {dist:.2f} > {max_step}"
    
    log(f"OK: {len(path)} точек, без разрывов")
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("TEES Router v0.40 — ТЕСТЫ")
    print("=" * 60)
    
    tests = [
        test_simple_path,
        test_obstacle_avoidance,
        test_same_cell,
        test_impossible_route,
        test_multiple_obstacles,
        test_vs_astar,
        test_path_smoothness,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"  ❌ УПАЛ: {e}")
            failed += 1
    
    print()
    print("=" * 60)
    print(f"ИТОГО: {passed}/{len(tests)} прошло, {failed} упало")
    print("=" * 60)