"""
Тесты для FractalUnit.
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from fractal.unit import FractalUnit

def test_unit_creation():
    """Тест создания единицы."""
    unit = FractalUnit("test_unit", 0.5)
    assert unit.id == "test_unit"
    assert unit.load == 0.5
    assert unit.health == 1.0
    assert unit.neighbors == []
    print("✓ test_unit_creation пройден")

def test_neighbor_connection():
    """Тест связи между единицами."""
    unit1 = FractalUnit("unit1")
    unit2 = FractalUnit("unit2")
    
    unit1.add_neighbor(unit2)
    
    assert unit2 in unit1.neighbors
    assert unit1 in unit2.neighbors  # Двусторонняя связь
    print("✓ test_neighbor_connection пройден")

def test_potential_calculation():
    """Тест вычисления потенциала."""
    unit = FractalUnit("test_unit", 0.9)
    potential = unit.compute_potential(target_load=0.7)
    
    # При нагрузке 0.9 и цели 0.7: (0.9-0.7)² = 0.04
    expected = (0.9 - 0.7) ** 2
    assert abs(potential - expected) < 0.001
    print("✓ test_potential_calculation пройден")

def test_load_transfer():
    """Тест передачи нагрузки."""
    unit1 = FractalUnit("unit1", 0.8)
    unit2 = FractalUnit("unit2", 0.3)
    
    unit1.add_neighbor(unit2)
    unit1.compute_potential(0.5)
    unit2.compute_potential(0.5)
    
    transferred = unit1.transfer_load(transfer_rate=0.1)
    
    # unit1 должен отдать часть нагрузки unit2
    assert transferred > 0
    assert unit1.load < 0.8
    assert unit2.load > 0.3
    print(f"✓ test_load_transfer пройден (передано {transferred:.3f})")

if __name__ == "__main__":
    print("Запуск тестов FractalUnit...")
    test_unit_creation()
    test_neighbor_connection()
    test_potential_calculation()
    test_load_transfer()
    print("
✅ Все базовые тесты пройдены!")
