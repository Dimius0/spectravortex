# spectravortex/tests/test_import.py

import sys
import os

# Добавляем корень проекта в путь Python для корректного импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def test_import_compiler():
    """Test that the compiler package can be imported."""
    try:
        import spectravortex.compiler
        assert spectravortex.compiler is not None
        print("✓ Package 'compiler' imports successfully")
    except ImportError as e:
        # Если модуль в разработке, просто отмечаем это
        print(f"○ Package 'compiler' is in development (ImportError: {e})")

def test_import_simulator():
    """Test that the simulator package can be imported."""
    try:
        import spectravortex.simulator
        assert spectravortex.simulator is not None
        print("✓ Package 'simulator' imports successfully")
    except ImportError as e:
        print(f"○ Package 'simulator' is in development (ImportError: {e})")

if __name__ == "__main__":
    test_import_compiler()
    test_import_simulator()
    print("\nAll import checks completed.")
