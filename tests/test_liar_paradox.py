
---

## Акт III. Тест на парадоксе «Лжец»

Создаю интеграционный тест для `consciousness_field.py`.

```python
# tests/test_liar_paradox.py
# Акт XIV: Тестирование поля сознания на парадоксе «Лжец»
# Запуск: pytest tests/test_liar_paradox.py -v

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
import numpy as np
from src.architect.consciousness_field import ConsciousnessField, ParadoxLevel, ResonancePattern

class TestLiarParadox:
    """Верификация TEES-перехода для самореферентных утверждений"""
    
    @pytest.fixture
    def field(self):
        return ConsciousnessField(threshold=0.7, tees_depth_limit=5)
    
    @pytest.fixture
    def liar_statements(self):
        return {
            'classic': "Это утверждение ложно",
            'goedel': "Это утверждение недоказуемо",
            'double': "Следующее утверждение истинно. Предыдущее утверждение ложно",
            'observer': "Наблюдатель не может доказать это утверждение изнутри системы",
            'timeless': "Никогда не будет найдено доказательство этого утверждения"
        }
    
    def test_resonance_for_provable(self, field):
        """1. Доказуемое утверждение → тип 'proof'"""
        result = field.process("2 + 2 = 4")
        assert result.type == 'proof'
        assert result.confidence > 0.7
        assert len(result.new_modes) == 0
    
    def test_liar_triggers_resonance(self, field, liar_statements):
        """2. Парадокс лжеца → тип 'resonance' и фрактальный переход"""
        for name, stmt in liar_statements.items():
            result = field.process(stmt)
            print(f"\n{name}: {result.type}, confidence={result.confidence:.3f}")
            
            # Все парадоксы должны переводить поле в режим резонанса
            assert result.type == 'resonance', f"❌ {name} не вызвал TEES"
            assert result.confidence > 0.0
            
            # Должна родиться хотя бы одна новая аксиома
            assert len(result.new_modes) >= 1
            new_mode = result.new_modes[0]
            assert new_mode.level >= 1
            assert "недоказуемое" in new_mode.content or "безвременье" in new_mode.content
            
            # ЭЭГ-предсказание должно указывать на тета-альфа когеренцию
            assert "theta_alpha_coherence" in result.eeg_prediction
            assert result.eeg_prediction.get("beta_power_change", 0) < 0  # beta падает
            
            print(f"   ✓ Новая аксиома: {new_mode.content} (уровень {new_mode.level})")
    
    def test_paradox_depth_increases_with_recursion(self, field):
        """3. Глубина парадокса растёт с рекурсией"""
        shallow = field.process("Это утверждение ложно")
        deep = field.process("Это утверждение ссылается на себя, которое ссылается на себя, которое недоказуемо")
        
        assert deep.data['tees_depth'] >= shallow.data['tees_depth']
    
    def test_axiom_tree_grows(self, field, liar_statements):
        """4. Дерево аксиом расширяется после обработки парадоксов"""
        initial_levels = set(field.get_axiom_tree().keys())
        
        for stmt in liar_statements.values():
            field.process(stmt)
        
        final_levels = set(field.get_axiom_tree().keys())
        # Должны появиться новые фрактальные уровни (1, возможно 2)
        assert max(final_levels) >= 1
        assert len(final_levels) >= len(initial_levels)
        
        # На уровне 1 должны быть аксиомы о недоказуемом
        level1_axioms = field.get_axiom_tree().get(1, [])
        assert any("недоказуемое" in ax for ax in level1_axioms) or \
               any("безвременье" in ax for ax in level1_axioms)
    
    def test_eeg_prediction_for_liar(self, field):
        """5. ЭЭГ-предсказание для парадокса соответствует TEES-паттерну"""
        result = field.process("Это утверждение недоказуемо")
        eeg = result.eeg_prediction
        
        # Ключевые признаки TEES-паттерна
        assert eeg['theta_alpha_coherence'] > 0.6
        assert eeg['beta_power_change'] < -0.3
        assert eeg['temporal_loss'] == True
        assert 'Глубокая синхронизация' in eeg['interpretation']
        
        print(f"\n   ЭЭГ-предсказание для G: {eeg['interpretation']}")
        print(f"   Тета-альфа когеренция: {eeg['theta_alpha_coherence']}")
    
    def test_liar_generates_new_modes_with_charge(self, field):
        """6. Новые моды наследуют и изменяют топологический заряд"""
        result = field.process("Это утверждение ложно")
        new_mode = result.new_modes[0]
        
        # Заряд новой моды не должен быть нулевым (есть содержание)
        assert new_mode.charge != 0 or new_mode.level > 1
        
        # Фаза должна быть в [0, 2π)
        assert 0 <= new_mode.phase < 2 * np.pi
        
        print(f"   Новая мода: заряд={new_mode.charge}, фаза={new_mode.phase:.2f}")
    
    def test_paradox_memory(self, field, liar_statements):
        """7. Поле помнит историю парадоксов"""
        for stmt in liar_statements.values():
            field.process(stmt)
        
        memory = field.get_paradox_memory()
        assert len(memory) >= len(liar_statements)
        
        # Все записи должны быть типа 'resonance'
        assert all(entry['type'] == 'resonance' for entry in memory)


@pytest.mark.performance
def test_tees_cascade_performance():
    """Производительность: глубина каскада до 5 уровней не должна взрываться"""
    import time
    field = ConsciousnessField(tees_depth_limit=5)
    
    deep_paradox = "Это утверждение недоказуемо, и это утверждение ссылается на себя, и наблюдатель внутри системы"
    
    start = time.time()
    result = field.process(deep_paradox)
    elapsed = time.time() - start
    
    assert elapsed < 1.0, f"TEES-каскад занял {elapsed:.2f} сек > 1 сек"
    assert result.type == 'resonance'
    print(f"\n   Время TEES-каскада: {elapsed*1000:.1f} мс")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])