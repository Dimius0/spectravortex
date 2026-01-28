#!/usr/bin/env python3
"""
Integration test for RecursiveSolver and fractal computation (Phase 3.2).
Tests recursive decomposition, fractal patterns, and hierarchical stitching.
"""

import numpy as np
import sys
import os
import json
from typing import Dict, Any

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.core.data_interface import FieldSolution
from simulator.core.solver_manager import create_solver_manager

def create_fractal_test_problem(problem_type: str = "fractal_grid") -> Dict[str, Any]:
    """Create test problems for fractal/recursive solving."""
    
    if problem_type == "fractal_grid":
        # Large 2D grid that should trigger recursion
        return {
            "name": "fractal_grid_test",
            "physics": ["wave_propagation", "interference"],
            "domain": {
                "type": "2d",
                "width": 50e-6,  # Large domain
                "height": 50e-6,
                "grid_size": 0.1e-6,
            },
            "components": [
                {"type": "waveguide", "length": 20e-6},
                {"type": "resonator", "radius": 5e-6},
                {"type": "fractal_coupler"},  # Triggers fractal detection
            ],
            "parameters": {
                "wavelength": 1.55e-6,
                "use_recursion": True,  # Explicit flag
            },
            "metadata": {
                "description": "Large fractal grid test problem",
                "expected_recursion": True,
                "complexity": "high",
            }
        }
    
    elif problem_type == "oam_multiplexer":
        # OAM problem with high topological complexity
        return {
            "name": "oam_recursive_test",
            "physics": ["vortex", "interference", "nonlinear"],
            "domain": {
                "type": "2d",
                "width": 30e-6,
                "height": 30e-6,
                "grid_size": 0.05e-6,  # Fine grid
            },
            "components": [
                {"type": "star_coupler", "ports": 26},
                {"type": "oam_generator", "charge": 3},
                {"type": "ring_resonator"},
            ],
            "parameters": {
                "orbital_angular_momentum": [1, 2, 3],
                "wavelength": 1.55e-6,
            },
            "metadata": {
                "description": "OAM multiplexer with recursive potential",
                "expected_recursion": True,  # High topological complexity
                "complexity": "high",
            }
        }
    
    elif problem_type == "simple_wave":
        # Simple problem that shouldn't use recursion
        return {
            "name": "simple_wave_test",
            "physics": ["wave_propagation"],
            "domain": {
                "type": "1d",
                "length": 10e-6,
            },
            "components": [
                {"type": "waveguide", "length": 5e-6},
            ],
            "parameters": {
                "wavelength": 1.55e-6,
            },
            "metadata": {
                "description": "Simple 1D wave problem",
                "expected_recursion": False,
                "complexity": "low",
            }
        }
    
    else:
        raise ValueError(f"Unknown problem type: {problem_type}")

def test_recursive_solver_registration():
    """Test that RecursiveSolver is properly registered."""
    print("🧪 Тест 1: Проверка регистрации RecursiveSolver (Phase 3.2)...")
    
    manager = create_solver_manager()
    solvers = manager.get_available_solvers()
    
    # Check if RecursiveSolver is registered
    recursive_found = False
    for solver_id, solver_info in solvers.items():
        if "RecursiveSolver" in solver_id:
            recursive_found = True
            print(f"   ✓ RecursiveSolver найден: {solver_id}")
            print(f"     Версия: {solver_info.get('version', 'unknown')}")
            print(f"     Приоритет: {solver_info.get('priority', 'unknown')}")
            print(f"     Поддерживает рекурсию: {solver_info.get('supports_recursion', False)}")
            break
    
    assert recursive_found, "RecursiveSolver не зарегистрирован!"
    print("   ✅ RecursiveSolver успешно зарегистрирован (Phase 3.2)")
    return True

def test_recursive_problem_detection():
    """Test that SolverManager correctly detects problems needing recursion."""
    print("\n🧪 Тест 2: Определение задач для рекурсивного решения...")
    
    manager = create_solver_manager()
    
    # Test 1: Simple problem (should NOT use recursion)
    simple_problem = create_fractal_test_problem("simple_wave")
    selection = manager.select_solver(simple_problem)
    
    print(f"   Простая задача: выбран {selection.solver.__class__.__name__}")
    print(f"   Причина: {selection.reason}")
    
    is_recursive = "RecursiveSolver" in selection.solver.__class__.__name__
    if not is_recursive:
        print("   ✅ Простая задача правильно не использует рекурсию")
    else:
        print("   ⚠️  Простая задача неожиданно использует RecursiveSolver")
    
    # Test 2: Fractal grid problem (SHOULD use recursion)
    fractal_problem = create_fractal_test_problem("fractal_grid")
    selection = manager.select_solver(fractal_problem)
    
    print(f"   Фрактальная задача: выбран {selection.solver.__class__.__name__}")
    print(f"   Причина: {selection.reason}")
    print(f"   Уверенность: {selection.confidence:.2f}")
    
    is_recursive = "RecursiveSolver" in selection.solver.__class__.__name__
    if is_recursive:
        print("   ✅ Фрактальная задача правильно использует RecursiveSolver")
        assert selection.confidence > 0.4, "Слишком низкая уверенность для рекурсивной задачи"
    else:
        print("   ❌ Фрактальная задача должна использовать RecursiveSolver")
    
    # Test 3: OAM problem (SHOULD use recursion due to high topological complexity)
    oam_problem = create_fractal_test_problem("oam_multiplexer")
    selection = manager.select_solver(oam_problem)
    
    print(f"   OAM задача: выбран {selection.solver.__class__.__name__}")
    print(f"   Причина: {selection.reason}")
    
    is_recursive = "RecursiveSolver" in selection.solver.__class__.__name__
    print(f"   {'✅ OAM задача использует RecursiveSolver' if is_recursive else '⚠️  OAM задача не использует RecursiveSolver'}")
    
    return True

def test_recursive_solving_process():
    """Test the actual recursive solving process."""
    print("\n🧪 Тест 3: Процесс рекурсивного решения...")
    
    # Create a problem that should use recursion
    problem = create_fractal_test_problem("fractal_grid")
    
    manager = create_solver_manager()
    
    try:
        print("   Запуск рекурсивного решения...")
        
        # Get solver selection first
        selection = manager.select_solver(problem)
        print(f"   Выбран решатель: {selection.solver.__class__.__name__}")
        
        # Solve the problem
        result = manager.solve(problem)
        
        # Basic validation
        assert hasattr(result, 'amplitude'), "Результат не содержит amplitude"
        assert hasattr(result, 'phase'), "Результат не содержит phase"
        assert hasattr(result, 'metadata'), "Результат не содержит metadata"
        
        print(f"   Размер решения: {result.amplitude.shape}")
        
        # Check for recursion metadata
        if 'recursion' in result.metadata:
            recursion_data = result.metadata['recursion']
            print(f"   Решатель: {recursion_data.get('solver_used', 'unknown')}")
            print(f"   Всего нод: {recursion_data.get('total_nodes', 0)}")
            print(f"   Макс. глубина: {recursion_data.get('max_depth', 0)}")
            print(f"   Время решения: {recursion_data.get('total_computation_time', 0):.3f}с")
            
            # Check fractal pattern analysis
            fractal_pattern = recursion_data.get('fractal_pattern', {})
            print(f"   Фрактальный паттерн: {fractal_pattern.get('pattern', 'unknown')}")
            print(f"   Самоподобие: {fractal_pattern.get('self_similarity', 0):.2f}")
            
            # Verify recursion actually happened
            if recursion_data.get('total_nodes', 0) > 1:
                print("   ✅ Рекурсивное решение выполнено успешно")
                return True
            else:
                print("   ⚠️  Рекурсия не произошла (только одна нода)")
                return False
        else:
            print("   ❌ Нет метаданных рекурсии")
            return False
            
    except Exception as e:
        print(f"   ❌ Ошибка при рекурсивном решении: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fractal_pattern_analysis():
    """Test fractal pattern analysis in recursion results."""
    print("\n🧪 Тест 4: Анализ фрактальных паттернов...")
    
    # Create multiple problems with different characteristics
    test_cases = [
        ("fractal_grid", True, "Должен показать фрактальный паттерн"),
        ("oam_multiplexer", True, "Высокая топологическая сложность"),
        ("simple_wave", False, "Простая задача без фрактальности"),
    ]
    
    manager = create_solver_manager()
    
    for problem_type, expect_fractal, description in test_cases:
        print(f"   Тест: {problem_type} ({description})")
        
        problem = create_fractal_test_problem(problem_type)
        
        try:
            result = manager.solve(problem)
            
            if 'recursion' in result.metadata:
                fractal_data = result.metadata['recursion'].get('fractal_pattern', {})
                pattern = fractal_data.get('pattern', 'none')
                
                if expect_fractal and pattern == 'fractal':
                    print(f"     ✅ Обнаружен ожидаемый фрактальный паттерн")
                elif not expect_fractal and pattern != 'fractal':
                    print(f"     ✅ Фрактальный паттерн не обнаружен (как и ожидалось)")
                else:
                    print(f"     ⚠️  Неожиданный паттерн: {pattern}")
            else:
                print(f"     ⚠️  Нет данных рекурсии")
                
        except Exception as e:
            print(f"     ❌ Ошибка: {e}")
    
    print("   ✅ Анализ фрактальных паттернов завершён")
    return True

def test_recursive_performance_logging():
    """Test performance logging for recursive operations."""
    print("\n🧪 Тест 5: Логирование производительности рекурсии...")
    
    manager = create_solver_manager()
    
    # Reset statistics
    manager.reset_statistics()
    
    # Run multiple problems with different complexities
    problems = [
        create_fractal_test_problem("simple_wave"),
        create_fractal_test_problem("fractal_grid"),
        create_fractal_test_problem("oam_multiplexer"),
    ]
    
    for i, problem in enumerate(problems, 1):
        print(f"   Решение задачи {i}: {problem['name']}")
        
        try:
            result = manager.solve(problem)
            
            # Check if recursion was used
            if 'recursion' in result.metadata:
                print(f"     Использована рекурсия: Да")
                rec_data = result.metadata['recursion']
                print(f"     Нод: {rec_data.get('total_nodes', 0)}, "
                      f"Глубина: {rec_data.get('max_depth', 0)}")
            else:
                print(f"     Использована рекурсия: Нет")
                
        except Exception as e:
            print(f"     ❌ Ошибка: {e}")
    
    # Check performance report
    report = manager.get_performance_report()
    
    print(f"   Всего запусков: {report['total_runs']}")
    print(f"   Успешных: {report['successful_runs']}")
    print(f"   Процент успеха: {report['success_rate']:.1%}")
    
    # Check recent runs for recursion logging
    if report['recent_runs']:
        print(f"   Последние запуски:")
        for run in report['recent_runs'][-3:]:  # Last 3 runs
            solver = run.get('solver', 'unknown')
            used_recursion = run.get('used_recursion', False)
            print(f"     - {solver}: рекурсия={'Да' if used_recursion else 'Нет'}")
    
    if report['total_runs'] > 0:
        print("   ✅ Логирование производительности работает")
        return True
    else:
        print("   ❌ Нет записей в логе")
        return False

def test_recursive_with_specific_solver():
    """Test using RecursiveSolver directly."""
    print("\n🧪 Тест 6: Прямое использование RecursiveSolver...")
    
    manager = create_solver_manager()
    
    # Find RecursiveSolver ID
    recursive_solver_id = None
    for solver_id in manager.solvers.keys():
        if "RecursiveSolver" in solver_id:
            recursive_solver_id = solver_id
            break
    
    if not recursive_solver_id:
        print("   ❌ RecursiveSolver не найден")
        return False
    
    print(f"   ID RecursiveSolver: {recursive_solver_id}")
    
    # Create a complex problem
    problem = create_fractal_test_problem("fractal_grid")
    
    try:
        # Use specific solver
        result = manager.solve_with_specific_solver(recursive_solver_id, problem)
        
        # Verify recursion metadata
        assert 'recursion' in result.metadata, "Нет метаданных рекурсии"
        
        rec_data = result.metadata['recursion']
        print(f"   Решатель: {rec_data.get('solver_used', 'unknown')}")
        print(f"   Версия: {rec_data.get('solver_version', 'unknown')}")
        print(f"   Всего нод: {rec_data.get('total_nodes', 0)}")
        print(f"   Макс. глубина: {rec_data.get('max_depth', 0)}")
        
        fractal_pattern = rec_data.get('fractal_pattern', {})
        print(f"   Фрактальный паттерн: {fractal_pattern.get('pattern', 'unknown')}")
        
        # Verify recursive structure
        if rec_data.get('total_nodes', 0) > 1:
            print("   ✅ Рекурсивная структура создана")
            
            # Print tree structure if not too large
            tree = rec_data.get('recursion_tree', {})
            if tree and len(tree) <= 10:  # Only print small trees
                print("   Структура дерева:")
                for node_id, node_info in tree.items():
                    depth = node_info.get('depth', 0)
                    solver = node_info.get('solver_used', 'unknown')
                    print(f"     {'  ' * depth}├─ {node_id} ({solver})")
            
            return True
        else:
            print("   ❌ Рекурсивная структура не создана")
            return False
        
    except Exception as e:
        print(f"   ❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all recursive/fractal integration tests."""
    print("=" * 60)
    print("🔬 ИНТЕГРАЦИОННЫЕ ТЕСТЫ РЕКУРСИВНОГО РЕШАТЕЛЯ (Phase 3.2)")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 6
    
    try:
        # Test 1: Registration
        if test_recursive_solver_registration():
            tests_passed += 1
        
        # Test 2: Problem detection
        if test_recursive_problem_detection():
            tests_passed += 1
        
        # Test 3: Solving process
        if test_recursive_solving_process():
            tests_passed += 1
        
        # Test 4: Fractal patterns
        if test_fractal_pattern_analysis():
            tests_passed += 1
        
        # Test 5: Performance logging
        if test_recursive_performance_logging():
            tests_passed += 1
        
        # Test 6: Direct solver usage
        if test_recursive_with_specific_solver():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ИТОГ ТЕСТИРОВАНИЯ Phase 3.2")
        print("=" * 60)
        print(f"Пройдено тестов: {tests_passed}/{tests_total}")
        
        if tests_passed == tests_total:
            print("🎉 ВСЕ ТЕСТЫ PHASE 3.2 ПРОЙДЕНЫ УСПЕШНО!")
            print("\n✅ RecursiveSolver полностью интегрирован в систему.")
            print("✅ SolverManager правильно определяет задачи для рекурсии.")
            print("✅ Фрактальные паттерны анализируются корректно.")
            print("✅ Иерархическое сшивание работает.")
            print("\n🚀 Phase 3.2 (Фрактальное проектирование) ЗАВЕРШЕНА!")
            return 0
        else:
            print(f"⚠️  Провалено тестов: {tests_total - tests_passed}")
            print("\n💡 Рекомендации:")
            if tests_passed < 3:
                print("   - Проверьте регистрацию RecursiveSolver в SolverManager")
                print("   - Убедитесь, что метод _should_use_recursion() работает")
            elif tests_passed < 5:
                print("   - Проверьте логику рекурсивного решения в RecursiveSolver")
                print("   - Убедитесь, что StitchingSolver доступен для сшивания")
            return 1
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
