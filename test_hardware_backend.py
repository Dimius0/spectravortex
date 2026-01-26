"""
Test suite for SpectraVortex Hardware Backend.
"""

import unittest
import sys
import os

# Добавляем путь к модулю
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hardware_backend import (
    Waveguide,
    MZIInterferometer,
    OAMModeConverter,
    ChipDesigner,
    GDSIIGenerator,
    TECH_220NM
)


class TestChipDesigner(unittest.TestCase):
    """Test ChipDesigner functionality."""
    
    def test_chip_design_from_ast(self):
        """Test designing a chip from AST."""
        print("\n" + "="*60)
        print("Testing ChipDesigner with mock AST...")
        print("="*60)
        
        # Create designer
        designer = ChipDesigner(technology="silicon_photonic_220nm")
        
        # Mock AST (simplified for testing)
        class MockAST:
            def __init__(self):
                self.nodes = [
                    {"type": "vortex", "name": "source_plus1", "oam_charge": 1},
                    {"type": "vortex", "name": "source_minus2", "oam_charge": -2},
                    {"type": "interference", "sources": ["source_plus1", "source_minus2"]}
                ]
        
        mock_ast = MockAST()
        
        # Design chip from AST
        designer.design_from_ast(mock_ast)
        
        # Get metrics
        metrics = designer.get_design_summary()
        
        # Проверяем метрики
        self.assertIn("total_area", metrics)
        self.assertIn("total_loss", metrics)
        self.assertIn("component_count", metrics)
        
        print(f"✅ Chip design completed")
        print(f"   Components: {metrics.get('component_count', 0)}")
        print(f"   Total area: {metrics.get('total_area', 0):.1f} μm²")
        print(f"   Total loss: {metrics.get('total_loss', 0):.2f} dB")
        
        # Генерируем и выводим отчёт
        report = designer.generate_report()
        print("\n" + "="*60)
        print("CHIP DESIGN REPORT:")
        print("="*60)
        print(report)
        print("="*60)
        
        # Сохраняем в GDSII JSON
        if hasattr(designer, 'save_to_gds'):
            designer.save_to_gds("test_output.gds.json")
            print("\n✅ GDSII file saved: test_output.gds.json")
        
        # Проверяем, что дизайн создан
        self.assertGreater(metrics.get('component_count', 0), 0)
        print("\n✅ Chip design test passed!")

    # ... остальные тесты ...


if __name__ == "__main__":
    # Запуск тестов с детальным выводом
    runner = unittest.TextTestRunner(verbosity=2)
    
    print("\n" + "="*60)
    print("SPECTRAVORTEX HARDWARE BACKEND TEST SUITE")
    print("="*60)
    
    # Загружаем тесты
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestChipDesigner)
    
    # Запускаем
    result = runner.run(suite)
    
    # Итог
    print("\n" + "="*60)
    print(f"TESTS COMPLETED: {result.testsRun} tests run")
    print(f"FAILURES: {len(result.failures)}")
    print(f"ERRORS: {len(result.errors)}")
    print("="*60)
    
    sys.exit(0 if result.wasSuccessful() else 1)
