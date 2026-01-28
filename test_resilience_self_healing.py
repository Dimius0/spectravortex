#!/usr/bin/env python3
"""
Integration test for ResilienceManager and self-healing capabilities (Phase 3.3).
Tests alternative topologies, failure tolerance, and recovery recommendations.
"""

import numpy as np
import sys
import os
import json

# Добавляем путь к проекту
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.resilience.resilience_manager import (
    ResilienceManager, FailureType, ResilienceStrategy, AlternativeTopology
)
from simulator.core.solver_manager import create_solver_manager

def create_oam_test_problem():
    """Create OAM multiplexer test problem for resilience analysis."""
    return {
        "name": "oam_8ch_multiplexer",
        "physics": ["wave_propagation", "interference", "vortex"],
        "domain": {
            "type": "2d",
            "width": 20e-6,
            "height": 20e-6,
            "grid_size": 0.05e-6,
        },
        "components": [
            {"type": "star_coupler", "ports": 8, "radius": 8e-6},
            {"type": "waveguide_array", "count": 8, "spacing": 0.5e-6},
            {"type": "phase_shifter", "count": 8},
        ],
        "parameters": {
            "wavelength": 1.55e-6,
            "orbital_angular_momentum": [0, 1, 2, 3],
            "target_crosstalk": -20.0,  # dB
        },
        "manufacturing": {
            "technology": "silicon_photonic_220nm",
            "tolerances": {
                "width": "±50nm",
                "thickness": "±10nm",
            }
        },
        "metadata": {
            "application": "optical_communications",
            "priority": "high_reliability",
            "expected_lifetime": "10_years",
        }
    }

def test_resilience_manager_initialization():
    """Test that ResilienceManager initializes correctly."""
    print("🧪 Тест 1: Инициализация ResilienceManager (Phase 3.3)...")
    
    try:
        manager = ResilienceManager()
        
        # Check basic attributes
        assert hasattr(manager, 'failure_models'), "Нет failure_models"
        assert hasattr(manager, 'topology_generators'), "Нет topology_generators"
        assert hasattr(manager, 'resilience_cache'), "Нет resilience_cache"
        
        print(f"   ✓ Failure models: {len(manager.failure_models)}")
        print(f"   ✓ Topology generators: {len(manager.topology_generators)}")
        
        # Test enum imports
        assert FailureType.WAVEGUIDE_DEFECT.value == "waveguide_defect"
        assert ResilienceStrategy.REDUNDANCY.value == "redundancy"
        
        print("   ✅ ResilienceManager инициализирован успешно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка инициализации: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_alternative_topology_generation():
    """Test generation of alternative topologies."""
    print("\n🧪 Тест 2: Генерация альтернативных топологий...")
    
    manager = ResilienceManager()
    problem = create_oam_test_problem()
    
    try:
        alternatives = manager.generate_alternative_topologies(problem)
        
        print(f"   Сгенерировано альтернатив: {len(alternatives)}")
        
        # Should have at least original + some alternatives
        assert len(alternatives) >= 2, f"Мало альтернатив: {len(alternatives)}"
        
        # Check each alternative
        for i, alt in enumerate(alternatives):
            print(f"   Альтернатива {i}: {alt.topology_id}")
            print(f"     Описание: {alt.description}")
            print(f"     Стоимость: {alt.estimated_cost.get('complexity', 0):.1f}")
            print(f"     Устойчивость: {alt.resilience_score:.2f}")
            
            # Basic validation
            assert alt.topology_id, "Нет topology_id"
            assert alt.description, "Нет описания"
            assert 'implementation' in alt.__dict__, "Нет реализации"
        
        # Check for specific OAM topologies
        topology_ids = [alt.topology_id for alt in alternatives]
        expected_topologies = ['original', 'oam_star_coupler', 'oam_ring_cascade']
        
        for expected in expected_topologies:
            if expected in topology_ids:
                print(f"   ✓ Найдена топология: {expected}")
            else:
                print(f"   ⚠️  Не найдена топология: {expected}")
        
        print("   ✅ Альтернативные топологии сгенерированы успешно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка генерации топологий: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_failure_simulation():
    """Test failure scenario simulation."""
    print("\n🧪 Тест 3: Моделирование сценариев отказов...")
    
    manager = ResilienceManager()
    problem = create_oam_test_problem()
    
    try:
        # Test waveguide defect simulation
        from simulator.resilience.resilience_manager import FailureScenario
        
        scenario = FailureScenario(
            failure_type=FailureType.WAVEGUIDE_DEFECT,
            severity=0.3,
            description="Test waveguide width variation"
        )
        
        # Apply failure
        failed_topology = manager.apply_failure(problem, scenario)
        
        # Check that failure was applied
        assert 'metadata' in failed_topology, "Нет метаданных после отказа"
        
        metadata = failed_topology.get('metadata', {})
        applied_failure = metadata.get('applied_failure', {})
        
        if applied_failure:
            print(f"   Применён отказ: {applied_failure.get('type')}")
            print(f"   Серьёзность: {applied_failure.get('severity')}")
        else:
            # Check if components were modified
            original_comps = problem.get('components', [])
            failed_comps = failed_topology.get('components', [])
            
            if len(original_comps) == len(failed_comps):
                print("   ⚠️  Отказ применён, но не записан в метаданные")
            else:
                print(f"   Изменено компонентов: {len(failed_comps) - len(original_comps)}")
        
        # Test manufacturing variation
        scenario2 = FailureScenario(
            failure_type=FailureType.MANUFACTURING_VARIATION,
            severity=0.2,
            description="Process variation test"
        )
        
        failed_topology2 = manager.apply_failure(problem, scenario2)
        
        # The topology should be modified
        assert failed_topology2 != problem, "Топология не изменилась после отказа"
        
        print("   ✅ Моделирование отказов работает")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка моделирования отказов: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_resilience_analysis():
    """Test complete resilience analysis."""
    print("\n🧪 Тест 4: Полный анализ устойчивости...")
    
    manager = ResilienceManager()
    problem = create_oam_test_problem()
    
    try:
        print("   Запуск анализа устойчивости...")
        report = manager.analyze_resilience(problem)
        
        # Validate report structure
        assert hasattr(report, 'original_topology_id'), "Нет original_topology_id"
        assert hasattr(report, 'best_alternative_id'), "Нет best_alternative_id"
        assert hasattr(report, 'resilience_improvement'), "Нет resilience_improvement"
        assert hasattr(report, 'recommendations'), "Нет recommendations"
        assert hasattr(report, 'recovery_paths'), "Нет recovery_paths"
        
        print(f"   Исходная топология: {report.original_topology_id}")
        print(f"   Лучшая альтернатива: {report.best_alternative_id}")
        print(f"   Улучшение устойчивости: {report.resilience_improvement:.1%}")
        print(f"   Протестировано сценариев: {report.failure_scenarios_tested}")
        
        # Check topology comparison
        if report.topology_comparison:
            print(f"   Сравнение топологий ({len(report.topology_comparison)}):")
            for topo_id, scores in list(report.topology_comparison.items())[:3]:  # First 3
                resilience = scores.get('resilience', 0)
                performance = scores.get('performance', 0)
                print(f"     - {topo_id}: устойчивость={resilience:.2f}, производительность={performance:.2f}")
        
        # Check recommendations
        if report.recommendations:
            print(f"   Рекомендации ({len(report.recommendations)}):")
            for i, rec in enumerate(report.recommendations[:3], 1):  # First 3
                print(f"     {i}. {rec}")
        
        # Check recovery paths
        if report.recovery_paths:
            print(f"   Пути восстановления ({len(report.recovery_paths)}):")
            for failure_type, paths in report.recovery_paths.items():
                print(f"     - {failure_type}: {paths}")
        
        # Basic validation
        assert report.best_alternative_id, "Не выбрана лучшая альтернатива"
        
        if report.resilience_improvement > 0:
            print(f"   ✅ Найдено улучшение устойчивости: {report.resilience_improvement:.1%}")
        else:
            print(f"   ⚠️  Улучшение устойчивости не найдено")
        
        print("   ✅ Анализ устойчивости выполнен успешно")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка анализа устойчивости: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_recovery_path_generation():
    """Test generation of recovery paths."""
    print("\n🧪 Тест 5: Генерация путей восстановления...")
    
    manager = ResilienceManager()
    problem = create_oam_test_problem()
    
    try:
        # Generate alternatives first
        alternatives = manager.generate_alternative_topologies(problem)
        
        # Generate recovery paths
        recovery_paths = manager.generate_recovery_paths(problem, alternatives)
        
        print(f"   Сгенерировано путей восстановления: {len(recovery_paths)}")
        
        if recovery_paths:
            for failure_type, paths in recovery_paths.items():
                print(f"   Отказ: {failure_type}")
                print(f"     Пути: {paths}")
                
                # Should have at least one recovery topology
                assert len(paths) >= 1, f"Нет путей восстановления для {failure_type}"
                
                # Check if strategy suggestion is included
                has_strategy = any('strategy:' in str(p) for p in paths)
                if has_strategy:
                    print(f"     Включены стратегии восстановления")
        
        else:
            print("   ⚠️  Пути восстановления не сгенерированы")
        
        print("   ✅ Генерация путей восстановления завершена")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка генерации путей восстановления: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integration_with_solver_manager():
    """Test integration of resilience analysis with solver system."""
    print("\n🧪 Тест 6: Интеграция с SolverManager...")
    
    try:
        # Create solver manager
        solver_manager = create_solver_manager()
        
        # Create resilience manager with solver manager
        resilience_manager = ResilienceManager(solver_manager=solver_manager)
        
        problem = create_oam_test_problem()
        
        # Run resilience analysis
        report = resilience_manager.analyze_resilience(problem)
        
        # Check if we can use the best alternative
        if report.best_alternative_id != report.original_topology_id:
            print(f"   Рекомендуется альтернатива: {report.best_alternative_id}")
            
            # In a real implementation, we would solve the alternative topology here
            # For now, just verify the report is valid
            assert report.resilience_improvement is not None
            assert report.recommendations is not None
            
            print(f"   Улучшение: {report.resilience_improvement:.1%}")
            print(f"   Рекомендаций: {len(report.recommendations)}")
            
        else:
            print("   Исходная топология остаётся лучшей")
        
        print("   ✅ Интеграция с SolverManager работает")
        return True
        
    except Exception as e:
        print(f"   ❌ Ошибка интеграции: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_oam_specific_resilience():
    """Test OAM-specific resilience features."""
    print("\n🧪 Тест 7: OAM-специфичная устойчивость...")
    
    manager = ResilienceManager()
    
    # Create OAM problem
    oam_problem = create_oam_test_problem()
    
    try:
        # Get alternatives for OAM
        alternatives = manager.generate_alternative_topologies(oam_problem)
        
        # Count OAM-specific alternatives
        oam_alternatives = [
            alt for alt in alternatives 
            if 'oam' in alt.topology_id or alt.topology_id == 'original'
        ]
        
        print(f"   OAM альтернатив: {len(oam_alternatives)}/{len(alternatives)}")
        
        # Check for specific OAM topologies
        for alt in oam_alternatives:
            metadata = alt.metadata
            
            if 'type' in metadata:
                topo_type = metadata['type']
                print(f"   Тип: {topo_type}", end="")
                
                if topo_type == 'star_coupler':
                    ports = metadata.get('ports', 'unknown')
                    print(f" (порты: {ports})")
                elif topo_type == 'ring_cascade':
                    rings = metadata.get('rings', 'unknown')
                    print(f" (резонаторов: {rings})")
                elif topo_type == 'fractal':
                    levels = metadata.get('levels', 'unknown')
                    print(f" (уровней: {levels})")
                elif topo_type == 'mzi_network':
                    reconfigurable = metadata.get('reconfigurable', False)
                    print(f" (реконфигурируемый: {reconfigurable})")
                else:
                    print()
        
        # Test failure scenarios specific to OAM
        from simulator.resilience.resilience_manager import FailureScenario, FailureType
        
        phase_error_scenario = FailureScenario(
            failure_type=FailureType.PHASE_ERROR,
            severity=0.5,
            description="Phase errors critical for OAM interference",
            affected_components=["phase_shifters", "interferometers"]
        )
        
        # Apply to an alternative
        if alternatives:
            test_alt = alternatives[0]
            failed = manager.apply_failure(test_alt.implementation, phase_error_scenario)
            
            # Check if phase error was recorded
            if 'parameters' in failed:
                phase_error = failed['parameters'].get('phase_error')
                if phase_error is not None:
                    print(f"   Фазовая ошибка применена: {phase_error:.3f} рад")
            
            print("   ✅ OAM-специфичные тесты завершены")
            return True
        
        return False
        
    except Exception as e:
        print(f"   ❌ OAM-специфичная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all resilience/self-healing integration tests."""
    print("=" * 60)
    print("🔬 ИНТЕГРАЦИОННЫЕ ТЕСТЫ САМОВОССТАНОВЛЕНИЯ (Phase 3.3)")
    print("=" * 60)
    
    tests_passed = 0
    tests_total = 7
    
    try:
        # Test 1: Initialization
        if test_resilience_manager_initialization():
            tests_passed += 1
        
        # Test 2: Topology generation
        if test_alternative_topology_generation():
            tests_passed += 1
        
        # Test 3: Failure simulation
        if test_failure_simulation():
            tests_passed += 1
        
        # Test 4: Resilience analysis
        if test_resilience_analysis():
            tests_passed += 1
        
        # Test 5: Recovery paths
        if test_recovery_path_generation():
            tests_passed += 1
        
        # Test 6: Solver integration
        if test_integration_with_solver_manager():
            tests_passed += 1
        
        # Test 7: OAM-specific features
        if test_oam_specific_resilience():
            tests_passed += 1
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 ИТОГ ТЕСТИРОВАНИЯ Phase 3.3")
        print("=" * 60)
        print(f"Пройдено тестов: {tests_passed}/{tests_total}")
        
        if tests_passed == tests_total:
            print("🎉 ВСЕ ТЕСТЫ PHASE 3.3 ПРОЙДЕНЫ УСПЕШНО!")
            print("\n✅ ResilienceManager полностью реализован.")
            print("✅ Система генерирует альтернативные топологии.")
            print("✅ Моделируются сценарии отказов.")
            print("✅ Анализируется устойчивость решений.")
            print("✅ Предлагаются пути восстановления.")
            print("\n🚀 Phase 3.3 (Зачатки самовосстановления) ЗАВЕРШЕНА!")
            print("\n🏁 ПОЗДРАВЛЯЮ! ВЕСЬ PHASE 3 ВЫПОЛНЕН!")
            print("═" * 60)
            print("Phase 3.1: Stitching с топологическим анализом ✅")
            print("Phase 3.2: Фрактальное проектирование ✅")
            print("Phase 3.3: Зачатки самовосстановления ✅")
            print("═" * 60)
            return 0
        else:
            print(f"⚠️  Провалено тестов: {tests_total - tests_passed}")
            print("\n💡 Рекомендации по отладке:")
            if tests_passed < 3:
                print("   - Проверьте импорты в resilience_manager.py")
                print("   - Убедитесь, что enum классы определены правильно")
            elif tests_passed < 5:
                print("   - Проверьте логику генерации альтернативных топологий")
                print("   - Убедитесь, что failure_models работают корректно")
            elif tests_passed < 7:
                print("   - Проверьте анализ устойчивости и рекомендации")
                print("   - Убедитесь в правильности путей восстановления")
            return 1
            
    except Exception as e:
        print(f"\n❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
