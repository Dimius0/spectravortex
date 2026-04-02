"""
fractal_split.py — фрактальная разбивка текста на перекрывающиеся окна
Версия 1.0

Масштабы:
- 0.1  — буквы/символы (скользящее окно)
- 0.3  — слоги/морфемы (скользящее окно)
- 1.0  — слова (скользящее окно или по словам)
- 3.0  — словосочетания (группы слов)
- 10.0 — предложения (по естественным границам)
- 30.0 — абзацы (по естественным границам)
- 100.0 — весь текст (один блок)
"""
import re
import math
from typing import List, Dict, Any, Optional


# Предопределённые масштабы
FRACTAL_SCALES = [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]


def split_by_sentences(text: str) -> List[str]:
    """Разбивает текст на предложения"""
    # Простое разбиение по .!?
    sentences = re.split(r'[.!?]+', text)
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def split_by_paragraphs(text: str) -> List[str]:
    """Разбивает текст на абзацы"""
    paragraphs = re.split(r'\n\s*\n', text)
    return [p.strip() for p in paragraphs if len(p.strip()) > 50]


def sliding_window(text: str, window_size: int, step: int = None) -> List[Dict[str, Any]]:
    """
    Скользящее окно по тексту.
    Возвращает список блоков с их позициями.
    """
    if step is None:
        step = window_size // 2
    
    length = len(text)
    blocks = []
    
    for start in range(0, length - window_size + 1, step):
        block = text[start:start + window_size]
        if len(block.strip()) < 20:
            continue
        blocks.append({
            "content": block,
            "position": start / length,
            "window_size": window_size,
            "start": start,
            "end": start + window_size
        })
    
    return blocks


def split_by_words(text: str, group_size: int = 1) -> List[Dict[str, Any]]:
    """
    Разбивает текст на группы слов.
    """
    words = re.findall(r'\b[a-zA-Zа-яА-ЯёЁ]+\b', text)
    blocks = []
    
    for i in range(0, len(words), group_size):
        block = " ".join(words[i:i+group_size])
        if len(block) < 10:
            continue
        
        # Ищем позицию в исходном тексте
        pos = text.find(block) if block in text else i / max(1, len(words))
        pos = pos / len(text) if isinstance(pos, int) else pos
        
        blocks.append({
            "content": block,
            "position": pos,
            "window_size": len(block),
            "word_count": len(words[i:i+group_size])
        })
    
    return blocks


def fractal_split(
    text: str,
    scales: List[float] = None,
    min_block_length: int = 20
) -> List[Dict[str, Any]]:
    """
    Фрактальная разбивка текста на все масштабы.
    
    Args:
        text: исходный текст
        scales: список масштабов (по умолчанию FRACTAL_SCALES)
        min_block_length: минимальная длина блока в символах
    
    Returns:
        Список блоков с полями:
        - content: текст блока
        - scale: масштаб
        - position: относительная позиция (0..1)
        - window_size: размер окна в символах
        - type: тип разбивки (sliding/sentence/paragraph/word_group)
    """
    if scales is None:
        scales = FRACTAL_SCALES
    
    length = len(text)
    blocks = []
    
    # Предварительная разбивка для верхних масштабов
    sentences = split_by_sentences(text) if max(scales) >= 10 else []
    paragraphs = split_by_paragraphs(text) if max(scales) >= 30 else []
    
    for scale in scales:
        # Масштаб 100.0 — весь текст
        if scale == 100.0:
            if len(text) >= min_block_length:
                blocks.append({
                    "content": text,
                    "scale": scale,
                    "position": 0.5,
                    "window_size": len(text),
                    "type": "full_text"
                })
            continue
        
        # Масштаб 30.0 — абзацы
        if scale == 30.0:
            for para in paragraphs:
                if len(para) >= min_block_length:
                    # Находим позицию
                    pos = text.find(para) / length if para in text else 0.5
                    blocks.append({
                        "content": para,
                        "scale": scale,
                        "position": pos,
                        "window_size": len(para),
                        "type": "paragraph"
                    })
            continue
        
        # Масштаб 10.0 — предложения
        if scale == 10.0:
            for sent in sentences:
                if len(sent) >= min_block_length:
                    pos = text.find(sent) / length if sent in text else 0.5
                    blocks.append({
                        "content": sent,
                        "scale": scale,
                        "position": pos,
                        "window_size": len(sent),
                        "type": "sentence"
                    })
            continue
        
        # Масштаб 3.0 — словосочетания (группы по 2-5 слов)
        if scale == 3.0:
            word_blocks = split_by_words(text, group_size=3)
            for block in word_blocks:
                if len(block["content"]) >= min_block_length:
                    block["scale"] = scale
                    block["type"] = "word_group"
                    blocks.append(block)
            continue
        
        # Масштаб 1.0 — слова
        if scale == 1.0:
            word_blocks = split_by_words(text, group_size=1)
            for block in word_blocks:
                if len(block["content"]) >= min_block_length // 2:
                    block["scale"] = scale
                    block["type"] = "word"
                    blocks.append(block)
            continue
        
        # Масштабы 0.1 и 0.3 — скользящее окно
        if scale in [0.1, 0.3]:
            # Размер окна зависит от масштаба
            window_size = int(length * scale)
            window_size = max(30, min(window_size, length))
            step = window_size // 2
            
            for block_data in sliding_window(text, window_size, step):
                if len(block_data["content"]) >= min_block_length:
                    block_data["scale"] = scale
                    block_data["type"] = "sliding"
                    blocks.append(block_data)
            continue
        
        # Промежуточные масштабы (если добавим новые)
        # Для scale=0.5, 2.0, 5.0 и т.д. — комбинируем
        if scale not in [0.1, 0.3, 1.0, 3.0, 10.0, 30.0, 100.0]:
            # Гибридный подход: скользящее окно с подогнанным размером
            window_size = int(length * scale / 10)  # эвристика
            window_size = max(50, min(window_size, length))
            step = window_size // 2
            
            for block_data in sliding_window(text, window_size, step):
                if len(block_data["content"]) >= min_block_length:
                    block_data["scale"] = scale
                    block_data["type"] = "sliding_hybrid"
                    blocks.append(block_data)
    
    # Сортировка по масштабу (от меньшего к большему)
    blocks.sort(key=lambda x: x["scale"])
    
    return blocks


def fractal_split_simple(text: str) -> List[Dict[str, Any]]:
    """
    Упрощённая фрактальная разбивка для быстрого тестирования.
    """
    return fractal_split(text, scales=[0.3, 1.0, 3.0, 10.0])


# ========== ТЕСТОВАЯ ФУНКЦИЯ ==========
if __name__ == "__main__":
    test_text = """
    Это тестовый текст для проверки фрактальной разбивки.
    Он состоит из нескольких предложений. И даже из нескольких абзацев.
    
    Вот второй абзац. Здесь тоже есть предложения.
    А это третье предложение во втором абзаце.
    
    Короткий абзац.
    """
    
    print("=" * 60)
    print("ФРАКТАЛЬНАЯ РАЗБИВКА ТЕКСТА")
    print("=" * 60)
    
    blocks = fractal_split(test_text)
    
    print(f"\nВсего блоков: {len(blocks)}")
    print("\nПо масштабам:")
    
    scale_counts = {}
    for b in blocks:
        scale = b["scale"]
        scale_counts[scale] = scale_counts.get(scale, 0) + 1
    
    for scale in sorted(scale_counts.keys()):
        print(f"  scale={scale:5.1f}: {scale_counts[scale]:3d} блоков")
    
    print("\nПримеры блоков:")
    for b in blocks[:5]:
        print(f"\n  scale={b['scale']:.1f} [{b['type']}]")
        print(f"  {b['content'][:100]}...")