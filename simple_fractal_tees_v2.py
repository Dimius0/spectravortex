#!/usr/bin/env python3
"""
simple_fractal_tees_v2.py — Фрактальные TEES на простом хэше
v2: Новые критерии — смысл = изменение расстояния при TEES-взаимодействии
"""

import numpy as np
from typing import Dict, List, Tuple

# ============================================================================
# ПРОСТОЙ ХЭШ С ЛАВИННЫМ ЭФФЕКТОМ
# ============================================================================

def simple_hash(data: bytes, state: int = 0) -> int:
    h = state
    for byte in data:
        h = ((h << 5) + h) ^ byte
        h = (h * 0x45d9f3b) & 0xFFFFFFFF
        h = h ^ (h >> 17)
        h = (h * 0xc6a4a793) & 0xFFFFFFFF
        h = h ^ (h >> 13)
    return h


def letter_hash(letter: str, state: int = 0) -> int:
    return simple_hash(letter.encode(), state)


def word_hash(word: str) -> int:
    h = 0x6a09e667
    for letter in word:
        h = letter_hash(letter, h)
    return h


def phrase_hash(phrase: str) -> int:
    h = 0xbb67ae85
    for word in phrase.split():
        w_hash = word_hash(word)
        h = simple_hash(w_hash.to_bytes(4, 'big'), h)
    return h


# ============================================================================
# TEES: ВЗАИМОДЕЙСТВИЕ МЕЖДУ ХЭШАМИ
# ============================================================================

def tees_flow(source_hash: int, receiver_hash: int) -> int:
    combined = (source_hash << 32) | (receiver_hash & 0xFFFFFFFF)
    return simple_hash(combined.to_bytes(8, 'big'))


def apply_tees(source_hash: int, receiver_hash: int) -> Tuple[int, int]:
    flow = tees_flow(source_hash, receiver_hash)
    new_source = simple_hash(source_hash.to_bytes(4, 'big'), flow)
    new_receiver = simple_hash(receiver_hash.to_bytes(4, 'big'), flow)
    return new_source, new_receiver


# ============================================================================
# РАССТОЯНИЕ
# ============================================================================

def hash_distance(a: int, b: int) -> float:
    xor = a ^ b
    return xor.bit_count() / 32.0


# ============================================================================
# НОВЫЕ КРИТЕРИИ ДЛЯ ТЕСТОВ
# ============================================================================

def tees_meaning_shift(source_word: str, verb: str, receiver_word: str) -> dict:
    """
    Вычисляет смысл TEES-взаимодействия.
    
    Смысл = изменение расстояния между источником и приёмником
    в результате применения глагола (TEES-потока).
    
    Возвращает:
        initial_distance: расстояние до взаимодействия
        final_distance: расстояние после взаимодействия
        shift: изменение расстояния (отрицательное = сближение)
        flow_hash: хэш TEES-потока
    """
    s_hash = word_hash(source_word)
    r_hash = word_hash(receiver_word)
    
    initial_dist = hash_distance(s_hash, r_hash)
    
    # TEES-поток параметризуется глаголом
    verb_modifier = word_hash(verb)
    flow = tees_flow(s_hash, r_hash)
    flow = simple_hash(flow.to_bytes(4, 'big'), verb_modifier)  # глагол модулирует поток
    
    new_source = simple_hash(s_hash.to_bytes(4, 'big'), flow)
    new_receiver = simple_hash(r_hash.to_bytes(4, 'big'), flow)
    
    final_dist = hash_distance(new_source, new_receiver)
    
    return {
        'initial_distance': initial_dist,
        'final_distance': final_dist,
        'shift': final_dist - initial_dist,
        'flow_hash': flow,
        'new_source': new_source,
        'new_receiver': new_receiver
    }


# ============================================================================
# ТЕСТЫ С НОВЫМИ КРИТЕРИЯМИ
# ============================================================================

def run_tests():
    print("=" * 70)
    print("🧪 ТЕСТЫ v2: СМЫСЛ = ИЗМЕНЕНИЕ РАССТОЯНИЯ ПРИ TEES")
    print("   Фрактальные хэши + TEES-взаимодействие")
    print("=" * 70)
    
    # --------------------------------------------------
    # Тест 1: Буквы различаются
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 1: РАЗЛИЧЕНИЕ БУКВ")
    print("─" * 70)
    
    letters = ['д', 'М', 'е', 'о', 'а', 'я', 'к', 'т']
    hashes = {c: letter_hash(c) for c in letters}
    
    distances = []
    for i, c1 in enumerate(letters):
        for c2 in letters[i+1:]:
            distances.append(hash_distance(hashes[c1], hashes[c2]))
    
    avg_dist = np.mean(distances)
    min_dist = np.min(distances)
    max_dist = np.max(distances)
    
    print(f"  Среднее расстояние между буквами: {avg_dist:.3f}")
    print(f"  Минимальное: {min_dist:.3f}")
    print(f"  Максимальное: {max_dist:.3f}")
    
    if avg_dist > 0.3:
        print(f"  ✅ Буквы хорошо различаются (avg > 0.3)")
    else:
        print(f"  ❌ Буквы плохо различаются")
    
    # --------------------------------------------------
    # Тест 2: Идентичность
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 2: ИДЕНТИЧНОСТЬ")
    print("─" * 70)
    
    d_identical = hash_distance(word_hash("кот"), word_hash("кот"))
    print(f"  Δ(кот, кот) = {d_identical:.3f}")
    print(f"  {'✅' if d_identical == 0.0 else '❌'} Идентичные слова должны иметь расстояние 0")
    
    # --------------------------------------------------
    # Тест 3: TEES-взаимодействие меняет расстояние
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 3: TEES МЕНЯЕТ РАССТОЯНИЕ")
    print("─" * 70)
    
    test_cases = [
        ("Онегин", "едет", "деревня"),
        ("Онегин", "едет", "Москва"),
        ("кот", "сидит", "крыша"),
        ("солнце", "греет", "земля"),
        ("поэт", "пишет", "стихи"),
        ("поэт", "пишет", "проза"),
        ("любовь", "волнует", "душа"),
        ("ветер", "дует", "море"),
        ("дождь", "поливает", "сад"),
    ]
    
    # Предварительно кэшируем все слова
    all_words_in_tests = set()
    for s, v, r in test_cases:
        all_words_in_tests.add(s)
        all_words_in_tests.add(v)
        all_words_in_tests.add(r)
    for w in all_words_in_tests:
        word_hash(w)  # кэшируем
    
    print(f"  {'Источник':8} {'─Глагол─':10} {'Приёмник':8}  {'Δнач':>5} {'Δкон':>5} {'Сдвиг':>6}  Эффект")
    print(f"  {'─'*8} {'─'*10} {'─'*8}  {'─'*5} {'─'*5} {'─'*6} {'─'*10}")
    
    all_shifts = []
    
    for source, verb, receiver in test_cases:
        result = tees_meaning_shift(source, verb, receiver)
        
        shift = result['shift']
        all_shifts.append(shift)
        
        if shift < -0.05:
            effect = "📉 СБЛИЖЕНИЕ"
        elif shift > 0.05:
            effect = "📈 РАСХОЖДЕНИЕ"
        else:
            effect = "➡️ НЕЙТРАЛЬНО"
        
        print(f"  {source:8} {verb:10} {receiver:8}  {result['initial_distance']:.3f}  "
              f"{result['final_distance']:.3f}  {shift:+.3f}  {effect}")
    
    non_zero_shifts = sum(1 for s in all_shifts if abs(s) > 0.01)
    print(f"\n  Ненулевых сдвигов: {non_zero_shifts}/{len(all_shifts)}")
    print(f"  {'✅' if non_zero_shifts > 0 else '❌'} TEES должен менять расстояние")
    
    # --------------------------------------------------
    # Тест 4: Глагол параметризует TEES-поток
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 4: ГЛАГОЛ ПАРАМЕТРИЗУЕТ ПОТОК")
    print("─" * 70)
    print("  Один источник и приёмник — разные глаголы:")
    
    verbs = ["едет", "летит", "плывет", "бежит", "ползет"]  # без ё для простоты
    source, receiver = "Онегин", "деревня"
    
    # Кэшируем глаголы
    for v in verbs:
        word_hash(v)
    
    results_by_verb = {}
    for verb in verbs:
        result = tees_meaning_shift(source, verb, receiver)
        results_by_verb[verb] = result
    
    print(f"  {'Глагол':10} {'Δнач':>6} {'Δкон':>6} {'Сдвиг':>7}")
    print(f"  {'─'*10} {'─'*6} {'─'*6} {'─'*7}")
    
    shifts_by_verb = []
    for verb in verbs:
        r = results_by_verb[verb]
        shifts_by_verb.append(r['shift'])
        print(f"  {verb:10} {r['initial_distance']:6.3f}  {r['final_distance']:6.3f}  {r['shift']:+7.3f}")
    
    unique_shifts = len(set(round(s, 3) for s in shifts_by_verb))
    print(f"\n  Уникальных сдвигов: {unique_shifts}/{len(verbs)}")
    print(f"  {'✅' if unique_shifts > 1 else '❌'} Разные глаголы должны давать разные сдвиги")
    
    # --------------------------------------------------
    # Тест 5: Контраст через TEES
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 5: КОНТРАСТ ЧЕРЕЗ TEES")
    print("─" * 70)
    print("  Почему Онегин едет в деревню, а не в Москву?")
    
    r_derevnya = tees_meaning_shift("Онегин", "едет", "деревня")
    r_moskva = tees_meaning_shift("Онегин", "едет", "Москва")
    
    print(f"\n  С деревней:")
    print(f"    Начальное расстояние: {r_derevnya['initial_distance']:.3f}")
    print(f"    Конечное расстояние:  {r_derevnya['final_distance']:.3f}")
    print(f"    Сдвиг:               {r_derevnya['shift']:+.3f}")
    
    print(f"\n  С Москвой:")
    print(f"    Начальное расстояние: {r_moskva['initial_distance']:.3f}")
    print(f"    Конечное расстояние:  {r_moskva['final_distance']:.3f}")
    print(f"    Сдвиг:               {r_moskva['shift']:+.3f}")
    
    if r_derevnya['shift'] < r_moskva['shift']:
        print(f"\n  📉 Онегин СИЛЬНЕЕ сближается с деревней")
        print(f"  ✅ Выбор деревни оправдан через TEES")
    elif r_derevnya['shift'] > r_moskva['shift']:
        print(f"\n  📉 Онегин СИЛЬНЕЕ сближается с Москвой")
        print(f"  ⚠️ Выбор деревни не оправдан через TEES")
    else:
        print(f"\n  ➡️ Сдвиги одинаковы")
    
    if r_derevnya['final_distance'] < r_moskva['final_distance']:
        print(f"  ✅ После TEES Онегин БЛИЖЕ к деревне")
    else:
        print(f"  ⚠️ После TEES Онегин ближе к Москве")
    
    # --------------------------------------------------
    # Тест 6: Фразы через TEES-цепочку
    # --------------------------------------------------
    print("\n" + "─" * 70)
    print("📏 ТЕСТ 6: ФРАЗЫ КАК TEES-ЦЕПОЧКА")
    print("─" * 70)
    
    def phrase_tees_chain(phrase: str) -> Tuple[int, List[dict]]:
        words = phrase.split()
        if len(words) < 2:
            return word_hash(words[0]), []
        
        h = word_hash(words[0])
        chain = []
        
        for i in range(1, len(words)):
            prev_h = h
            next_h = word_hash(words[i])
            result = apply_tees(prev_h, next_h)
            h = result[1]
            
            chain.append({
                'step': i,
                'from': words[i-1],
                'to': words[i],
                'distance': hash_distance(prev_h, next_h),
                'new_distance': hash_distance(result[0], result[1]),
                'shift': hash_distance(result[0], result[1]) - hash_distance(prev_h, next_h)
            })
        
        return h, chain
    
    phrases = [
        "Онегин едет в деревню",
        "Онегин едет в Москву",
    ]
    
    # Кэшируем все слова из фраз
    for p in phrases:
        for w in p.split():
            word_hash(w)
    
    phrase_results = {}
    for phrase in phrases:
        h, chain = phrase_tees_chain(phrase)
        phrase_results[phrase] = {'hash': h, 'chain': chain}
    
    print("  Сравнение: Онегин едет в деревню vs Онегин едет в Москву")
    print()
    
    chain_d = phrase_results["Онегин едет в деревню"]['chain']
    chain_m = phrase_results["Онегин едет в Москву"]['chain']
    
    print(f"  {'Шаг':5} {'Переход':20} {'Δнач':>6} {'Δкон':>6} {'Сдвиг':>7}")
    print(f"  {'─'*5} {'─'*20} {'─'*6} {'─'*6} {'─'*7}")
    
    total_shift_d = 0
    total_shift_m = 0
    
    for step_d, step_m in zip(chain_d, chain_m):
        print(f"  {step_d['step']:5} {step_d['from'] + '→' + step_d['to']:20} "
              f"{step_d['distance']:6.3f}  {step_d['new_distance']:6.3f}  {step_d['shift']:+7.3f}")
        print(f"  {'':5} {step_m['from'] + '→' + step_m['to']:20} "
              f"{step_m['distance']:6.3f}  {step_m['new_distance']:6.3f}  {step_m['shift']:+7.3f}")
        print()
        total_shift_d += step_d['shift']
        total_shift_m += step_m['shift']
    
    print(f"  Суммарный сдвиг (деревня): {total_shift_d:+.3f}")
    print(f"  Суммарный сдвиг (Москва):  {total_shift_m:+.3f}")
    
    if total_shift_d < total_shift_m:
        print(f"  ✅ Фраза с деревней даёт БОЛЬШЕЕ сближение")
    elif total_shift_d > total_shift_m:
        print(f"  ⚠️ Фраза с Москвой даёт большее сближение")
    else:
        print(f"  ➡️ Сдвиги одинаковы")
    
    # --------------------------------------------------
    # Итоги
    # --------------------------------------------------
    print("\n" + "=" * 70)
    print("📊 ИТОГИ v2")
    print("=" * 70)
    print(f"  Модель: фрактальные хэши + TEES-взаимодействие")
    print(f"  Смысл = изменение расстояния при TEES")
    print(f"  Контраст = разница сдвигов для разных приёмников")
    print(f"  Вихрей: 0")
    print(f"  SHA-256: 0")
    print()


if __name__ == "__main__":
    run_tests()