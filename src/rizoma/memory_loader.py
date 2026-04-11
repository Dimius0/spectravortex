"""
memory_loader.py — загрузчик ВММП-контента в поле H
Версия 4.2 — ограничена максимальная амплитуда мод (0.7)
"""

import json
from pathlib import Path
from typing import Optional, List, Dict, Any

from .personality import SpectralMode


class VMMSLoader:
    """Загружает теорию, алхимию и предсказания в поле H как спектральные моды"""
    
    def __init__(self, personality):
        self.p = personality
        self.loaded_count = 0
    
    def _compute_tau(self, trace_type: str, themes: List[str], content: str) -> float:
        """
        Вычисляет τ (топологический заряд) для знания.
        Эвристика на основе типа и тем.
        """
        base_tau = {
            'discovery': 5.5,
            'alchemy': 6.5,
            'prediction': 7.0
        }.get(trace_type, 5.0)
        
        # Коррекция по темам
        theme_adjust = 0.0
        if 'VMMS' in themes or 'monism' in themes:
            theme_adjust -= 0.3
        if 'lipzik' in themes or 'formula' in themes:
            theme_adjust += 0.2
        if 'vortex' in themes:
            theme_adjust += 0.2
        if 'prediction' in themes:
            theme_adjust += 0.3
        if 'alchemy' in themes:
            theme_adjust += 0.1
        if 'history' in themes:
            theme_adjust -= 0.2
        
        tau = base_tau + theme_adjust
        return max(3.0, min(9.0, tau))
    
    def _get_base_amplitude(self, trace_type: str, trace_id: str) -> float:
        """
        Возвращает начальную амплитуду для моды.
        Базовые моды получают пониженную амплитуду, чтобы лента могла конкурировать.
        """
        # Базовые моды ВММП — снижаем амплитуду
        if trace_id in ['vmms_monism', 'alchemy_manifesto', 'temperature_decay']:
            return 0.4  # было 0.6, снижено для конкуренции
        
        # Остальные моды
        if trace_type == 'discovery':
            return 0.6
        elif trace_type == 'alchemy':
            return 0.5
        elif trace_type == 'prediction':
            return 0.5
        else:
            return 0.4
    
    def load_from_json(self, json_path: Path) -> int:
        """Загружает трассы из JSON и добавляет их в поле H как спектральные моды"""
        if not json_path.exists():
            print(f"⚠️ Файл не найден: {json_path}")
            return 0
        
        with open(json_path, 'r', encoding='utf-8') as f:
            traces_data = json.load(f)
        
        count = 0
        for data in traces_data:
            trace_type = data.get("trace_type", "unknown")
            themes = data.get("themes", [])
            content = data.get("content", "")
            trace_id = data.get("trace_id", "")
            
            tau = self._compute_tau(trace_type, themes, content)
            amplitude = self._get_base_amplitude(trace_type, trace_id)
            
            mode = SpectralMode(
                tau=tau,
                amplitude=amplitude,
                content=content,
                trace_id=trace_id,
                themes=themes,
                trace_type=trace_type
            )
            
            self.p.add_to_h_field(mode)
            count += 1
        
        self.loaded_count += count
        return count
    
    def load_english_memory(self) -> int:
        """Загружает английскую версию памяти TheoBot"""
        json_path = Path("memory_trees/theobot_vm_387/core_traces_en.json")
        
        print("🦌 Загружаю английскую память TheoBot в поле H...")
        count = self.load_from_json(json_path)
        
        print(f"  ✅ Загружено {count} спектральных мод (базовые моды: амплитуда 0.4)")
        return count


def feed_theobot(personality, lang: str = "en"):
    """Главная функция кормления TheoBot"""
    loader = VMMSLoader(personality)
    
    print("="*50)
    print("🍽️  КОРМЛЕНИЕ THEOBOT_VM_387")
    print(f"   Язык: {'ENGLISH' if lang == 'en' else 'RUSSIAN'}")
    print("="*50)
    
    if lang == "en":
        total = loader.load_english_memory()
    else:
        print("⚠️ Русская версия пока не реализована")
        total = 0
    
    print("="*50)
    print(f"✅ КОРМЛЕНИЕ ЗАВЕРШЕНО! Загружено {total} спектральных мод.")
    print("🦌 Базовые моды: амплитуда 0.4 (чтобы лента могла конкурировать)")
    print("🦌 Максимальная амплитуда любых мод: 0.7")
    print("="*50)
    
    return total