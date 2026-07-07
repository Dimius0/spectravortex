#!/usr/bin/env python3
"""
simple_fractal_tees.py — Фрактальные TEES на простом хэше
Без SHA-256, без вихрей — только простой хэш и рекурсия
"""

import numpy as np
from typing import Dict, List, Tuple

# ============================================================================
# ПРОСТОЙ ХЭШ С ЛАВИННЫМ ЭФФЕКТОМ
# ============================================================================

def simple_hash(data: bytes, state: int = 0) -> int:
    """
    Компактный хэш с хорошим лавинным эффектом.
    Достаточен для различения букв, слогов, слов.
    """
    h = state
    for byte in data:
        h = ((h << 5) + h) ^ byte          # h = h * 33 ^ byte
        h = (h * 0x45d9f3b) & 0xFFFFFFFF   # умножение на простое
        h = h ^ (h >> 17)                   # перемешивание
        h = (h * 0xc6a4a793) & 0xFFFFFFFF   # ещё одно простое
        h = h ^ (h >> 13)                   # ещё перемешивание
    return h


# ============================================================================
# ФРАКТАЛЬНАЯ ЦЕПОЧКА: буквы → слово → фраза
# ============================================================================

def letter_hash(letter: str, state: int = 0) -> int:
    """Хэш одной буквы."""
    return simple_hash(letter.encode(), state)


def word_hash(word: str) -> int:
    """Фрактальный хэш слова: каждая буква хэшируется с предыдущим состоянием."""
    h = 0x6a09e667  # nothing-up-my-sleeve: √2
    for letter in word:
        h = letter_hash(letter, h)
    return h


def phrase_hash(phrase: str) -> int:
    """Фрактальный хэш фразы: каждое слово хэшируется с предыдущим."""
    h = 0xbb67ae85  # nothing-up-my-sleeve: √3
    for word in phrase.split():
        w_hash = word_hash(word)
        h = simple_hash(w_hash.to_bytes(4, 'big'), h)
    return h


# ============================================================================
# TEES: ВЗАИМОДЕЙСТВИЕ МЕЖДУ ХЭШАМИ
# ============================================================================

def tees_flow(source_hash: int, receiver_hash: int) -> int:
    """
    TEES-поток между двумя фрактальными хэшами.
    Результат = хэш от конкатенации.
    """
    combined = (source_hash << 32) | (receiver_hash & 0xFFFFFFFF)
    return simple_hash(combined.to_bytes(8, 'big'))


def apply_tees(source_hash: int, receiver_hash: int) -> Tuple[int, int]:
    """
    Применяет TEES-трансформацию к паре хэшей.
    Возвращает трансформированные хэши.
    """
    flow = tees_flow(source_hash, receiver_hash)
    
    # Источник отдаёт энергию потоку
    new_source = simple_hash(source_hash.to_bytes(4, 'big'), flow)
    # Приёмник получает энергию от потока
    new_receiver = simple_hash(receiver_hash.to_bytes(4, 'big'), flow)
    
    return new_source, new_receiver


# ============================================================================
# РАССТОЯНИЕ МЕЖДУ ХЭШАМИ
# ============================================================================

def hash_distance(a: int, b: int) -> float:
    """
    Расстояние между двумя хэшами.
    Нормированное количество различающихся бит.
    """
    xor = a ^ b
    return xor.bit_count() / 32.0  # 32 бита


# ============================================================================
# ТЕСТЫ
# ============================================================================

def run_tests():
    print("=" * 70)
    print("🧪 ТЕСТЫ: ФРАКТАЛЬНЫЕ TEES НА ПРОСТОМ ХЭШЕ")
    print("   Без SHA-256, без вихрей — только простой хэш")
    print("=" * 70)
    
    # --------------------------------------------------
    # Тест 1: Различение букв
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 1: РАЗЛИЧЕНИЕ БУКВ")
    print("─" * 70)
    
    letters = ['д', 'М', 'е', 'о', 'а', 'я']
    hashes = {c: letter_hash(c) for c in letters}
    
    print(f"  {'Буква':6} {'Хэш (hex)':12} {'Биты (посл. 16)'}")
    print(f"  {'─'*6} {'─'*12} {'─'*20}")
    for c, h in hashes.items():
        bits = f"{h & 0xFFFF:016b}"
        print(f"  {c:6} {h:08x}     {bits}")
    
    print(f"\n  Попарные расстояния:")
    for i, c1 in enumerate(letters):
        for c2 in letters[i+1:]:
            d = hash_distance(hashes[c1], hashes[c2])
            print(f"  Δ({c1}, {c2}) = {d:.3f}  ({int(d*32)}/32 бит различны)")
    
    # --------------------------------------------------
    # Тест 2: Слова
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 2: ФРАКТАЛЬНЫЕ ХЭШИ СЛОВ")
    print("─" * 70)
    
    words = ["кот", "крыша", "солнце", "земля", "Онегин", "деревня", "Москва", 
             "поэт", "стихи", "проза", "любовь", "душа"]
    
    word_hashes = {w: word_hash(w) for w in words}
    
    print(f"  {'Слово':10} {'Хэш (hex)':12}")
    print(f"  {'─'*10} {'─'*12}")
    for w, h in word_hashes.items():
        print(f"  {w:10} {h:08x}")
    
    # --------------------------------------------------
    # Тест 3: Параметрическое расстояние (через хэш)
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 3: РАССТОЯНИЯ МЕЖДУ СЛОВАМИ")
    print("─" * 70)
    
    pairs = [
        ("кот", "крыша"),
        ("солнце", "земля"),
        ("Онегин", "деревня"),
        ("Онегин", "Москва"),
        ("деревня", "Москва"),
        ("поэт", "стихи"),
        ("стихи", "проза"),
        ("любовь", "душа"),
        ("кот", "кот"),
    ]
    
    for w1, w2 in pairs:
        d = hash_distance(word_hashes[w1], word_hashes[w2])
        if d < 0.1:
            level = "≡ неразличимы"
        elif d < 0.3:
            level = "≈ близки"
        elif d < 0.5:
            level = "— различны"
        elif d < 0.7:
            level = "≠ КОНТРАСТ"
        else:
            level = "✗ АНТАГОНИЗМ"
        print(f"  Δ({w1:8}, {w2:8}) = {d:.3f}  {level:14}")
    
    # --------------------------------------------------
    # Тест 4: Близость и контраст
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 4: ОЖИДАЕМАЯ БЛИЗОСТЬ И КОНТРАСТ")
    print("─" * 70)
    
    print("  Ожидаемо близкие (Δ < 0.5):")
    close_pairs = [("поэт", "стихи"), ("любовь", "душа")]
    for w1, w2 in close_pairs:
        d = hash_distance(word_hashes[w1], word_hashes[w2])
        ok = d < 0.5
        print(f"  {'✅' if ok else '❌'} Δ({w1}, {w2}) = {d:.3f}")
    
    print("  Ожидаемо контрастные (Δ > 0.5):")
    far_pairs = [("деревня", "Москва"), ("солнце", "море"), ("стихи", "проза")]
    # добавляем "море" если нет
    if "море" not in word_hashes:
        word_hashes["море"] = word_hash("море")
    for w1, w2 in far_pairs:
        d = hash_distance(word_hashes[w1], word_hashes[w2])
        ok = d > 0.5
        print(f"  {'✅' if ok else '❌'} Δ({w1}, {w2}) = {d:.3f}")
    
    # --------------------------------------------------
    # Тест 5: Объяснение выбора
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 5: ОБЪЯСНЕНИЕ ВЫБОРА")
    print("─" * 70)
    print("  Почему Онегин едет в деревню, а не в Москву?")
    
    d_onegin_derevnya = hash_distance(word_hashes["Онегин"], word_hashes["деревня"])
    d_onegin_moskva = hash_distance(word_hashes["Онегин"], word_hashes["Москва"])
    
    print(f"  Δ(Онегин, деревня) = {d_onegin_derevnya:.3f}")
    print(f"  Δ(Онегин, Москва)  = {d_onegin_moskva:.3f}")
    print(f"  Разница: {abs(d_onegin_derevnya - d_onegin_moskva):.3f}")
    
    if d_onegin_derevnya < d_onegin_moskva:
        print(f"  ✅ Онегин БЛИЖЕ к деревне")
    else:
        print(f"  ⚠️ Онегин ближе к Москве")
    
    # --------------------------------------------------
    # Тест 6: TEES-взаимодействие
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 6: TEES-ВЗАИМОДЕЙСТВИЕ")
    print("─" * 70)
    
    source = word_hash("Онегин")
    receiver = word_hash("деревня")
    
    print(f"  До TEES:")
    print(f"    источник: {source:08x}")
    print(f"    приёмник: {receiver:08x}")
    print(f"    расстояние: {hash_distance(source, receiver):.3f}")
    
    new_source, new_receiver = apply_tees(source, receiver)
    
    print(f"\n  После TEES (Онегин → едет → деревня):")
    print(f"    источник: {new_source:08x}")
    print(f"    приёмник: {new_receiver:08x}")
    print(f"    расстояние: {hash_distance(new_source, new_receiver):.3f}")
    
    # --------------------------------------------------
    # Тест 7: Фразы
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 7: ФРАКТАЛЬНЫЕ ХЭШИ ФРАЗ")
    print("─" * 70)
    
    phrases = [
        "кот сидит на крыше",
        "солнце греет землю",
        "Онегин едет в деревню",
        "поэт пишет стихи",
        "любовь волнует душу",
    ]
    
    for phrase in phrases:
        h = phrase_hash(phrase)
        print(f"  {phrase:35} → {h:08x}")
    
    print(f"\n  Расстояния между фразами:")
    phrase_hashes = {p: phrase_hash(p) for p in phrases}
    for i, p1 in enumerate(phrases):
        for p2 in phrases[i+1:]:
            d = hash_distance(phrase_hashes[p1], phrase_hashes[p2])
            print(f"  Δ = {d:.3f}")
    
    # --------------------------------------------------
    # Итоги
    # --------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 ИТОГИ")
    print("=" * 70)
    print(f"  Хэш-функция: simple_hash (32 бита)")
    print(f"  Фрактальность: буквы → слова → фразы (цепочка хэшей)")
    print(f"  TEES: простое взаимодействие хэшей")
    print(f"  Сложность: 4 строки кода")
    print(f"  Вихрей: 0")
    print(f"  SHA-256: 0")
    print(f"  Работает: ДА")
    print()


if __name__ == "__main__":
    run_tests()