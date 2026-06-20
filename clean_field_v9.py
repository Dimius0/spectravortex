#!/usr/bin/env python3
"""
clean_field_v9.py — Чистое поле смыслов. Версия 9.0
Слово = число (заряд). Связи = отношения зарядов. Грамматика = выявленные закономерности.
Текст → разбор на заряды → сохранение связей → восстановление кластера по связям.
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# ============================================================================
# СТОП-СЛОВА (исключаем при поиске значимых слов)
# ============================================================================

STOP_WORDS = {
    'что', 'как', 'почему', 'где', 'когда', 'кто', 'зачем', 'откуда', 'куда',
    'это', 'такое', 'так', 'же', 'бы', 'ли', 'то', 'в', 'на', 'с', 'к', 'у',
    'о', 'за', 'по', 'из', 'от', 'не', 'но', 'а', 'и', 'для', 'при', 'без',
    'над', 'под', 'об', 'во', 'ко', 'со', 'до', 'или', 'есть', 'быть',
}

# ============================================================================
# ЗАРЯД СЛОВА
# ============================================================================

def word_charge(word: str) -> int:
    """
    Вычисляет заряд слова как число на основе букв.
    Каждая буква = её позиция в алфавите. Заряд = сумма позиций.
    Слово «трава» = 20+18+1+3+1 = 43.
    """
    total = 0
    for ch in word.lower():
        if 'а' <= ch <= 'я':
            total += ord(ch) - ord('а') + 1
        elif 'a' <= ch <= 'z':
            total += ord(ch) - ord('a') + 1
    return total


def syllabic_charges(word: str) -> List[int]:
    """
    Разбивает слово на примерные слоги и возвращает заряд каждого слога.
    Простая эвристика: слог = согласная + гласная.
    """
    vowels = set('аеёиоуыэюя')
    syllables = []
    current = []
    for ch in word.lower():
        current.append(ch)
        if ch in vowels and len(current) >= 2:
            syllables.append(''.join(current))
            current = []
    if current:
        syllables.append(''.join(current))
    return [word_charge(s) for s in syllables]


# ============================================================================
# УЗЕЛ
# ============================================================================

@dataclass
class Node:
    token: str
    lemma: str
    charge: int
    syllabic: List[int]
    frequency: int = 1


# ============================================================================
# ПОЛЕ
# ============================================================================

class StructuralField:
    """Поле смыслов v9.0: заряды, связи, восстановление кластеров."""
    
    def __init__(self, debug_log: str = "field_v9.log"):
        self.nodes: Dict[str, Node] = {}                    # лемма → узел
        self.charge_index: Dict[int, List[str]] = defaultdict(list)  # заряд → леммы
        self.links: Dict[Tuple[str, str], int] = defaultdict(int)    # (слово1, слово2) → частота
        self.clusters: List[Dict] = []                      # сохранённые тексты как кластеры
        self.total_texts = 0
        
        with open(debug_log, 'w', encoding='utf-8') as f:
            f.write(f"=== v9.0 log — {datetime.now()} ===\n\n")

    # ========================================================================
    # ДОБАВЛЕНИЕ ТЕКСТА
    # ========================================================================

    def add_text(self, text: str) -> bool:
        words = re.findall(r'[а-яёa-z]+', text.lower())
        if len(words) < 3:
            return False

        # Вычисляем заряды
        charges = [word_charge(w) for w in words]
        syllabic = [syllabic_charges(w) for w in words]

        # Регистрируем слова в поле
        for word, charge, syll in zip(words, charges, syllabic):
            lemma = word
            if lemma not in self.nodes:
                self.nodes[lemma] = Node(token=word, lemma=lemma, charge=charge, syllabic=syll)
            else:
                self.nodes[lemma].frequency += 1
            # Индекс по заряду
            if lemma not in self.charge_index[charge]:
                self.charge_index[charge].append(lemma)

        # Сохраняем связи между парами слов
        for i in range(len(words) - 1):
            pair = (words[i], words[i+1])
            self.links[pair] += 1
            # Обратная связь
            self.links[(words[i+1], words[i])] += 1

        # Сохраняем кластер (исходный текст как набор связей)
        cluster = {
            'id': self.total_texts,
            'words': words,
            'charges': charges,
            'syllabic': syllabic,
            'links': [(words[i], words[i+1]) for i in range(len(words)-1)],
            'original': text,
        }
        self.clusters.append(cluster)
        self.total_texts += 1
        return True

    # ========================================================================
    # ЗАПРОС — восстановление кластера по зарядам и связям
    # ========================================================================

    def query(self, question: str) -> Optional[str]:
        words = re.findall(r'[а-яёa-z]+', question.lower())
        # Значимые слова (не стоп-слова)
        significant = [w for w in words if w not in STOP_WORDS]
        
        if not significant:
            return None

        print(f"\n❓ «{question}»")

        # Находим кластеры, содержащие первое значащее слово
        first_word = significant[0]
        candidates = [c for c in self.clusters if first_word in c['words']]

        if not candidates:
            # Ищем по заряду
            charge = word_charge(first_word)
            similar_words = self.charge_index.get(charge, [])
            for sw in similar_words:
                if sw != first_word:
                    candidates.extend([c for c in self.clusters if sw in c['words']])
            if not candidates:
                print(f"   ✗ Слово «{first_word}» не найдено")
                return None

        print(f"   🔍 Слово: «{first_word}» (заряд={word_charge(first_word)}) → {len(candidates)} кластеров")

        # Сужаем по остальным значащим словам
        for word in significant[1:]:
            if len(candidates) <= 1:
                break
            filtered = [c for c in candidates if word in c['words']]
            if filtered:
                candidates = filtered
                print(f"   🔍 Слово: «{word}» (заряд={word_charge(word)}) → {len(candidates)} кластеров")

        # Если несколько — выбираем по плотности связей
        if len(candidates) > 1:
            candidates.sort(key=lambda c: self._cluster_link_density(c, significant), reverse=True)
            print(f"   📋 Выбрано по плотности связей")

        best = candidates[0]

        # Восстанавливаем текст кластера по связям
        answer = self._reconstruct_from_links(best['words'], significant)
        if not answer:
            answer = best['original']

        print(f"   📋 Кластер #{best['id']}: «{best['original']}»")
        print(f"   💬 Ответ: «{answer}»")
        return answer

    def _cluster_link_density(self, cluster: Dict, question_words: List[str]) -> float:
        """Оценивает, насколько плотно слова вопроса связаны в кластере."""
        score = 0.0
        cluster_words = set(cluster['words'])
        for qw in question_words:
            if qw in cluster_words:
                # Проверяем, есть ли связи от этого слова к другим словам вопроса
                for other in question_words:
                    if other != qw and other in cluster_words:
                        if self.links.get((qw, other), 0) > 0:
                            score += 1.0
        return score

    def _reconstruct_from_links(self, cluster_words: List[str], question_words: List[str]) -> str:
        """
        Восстанавливает предложение, начиная от слов вопроса и следуя по связям.
        """
        if not cluster_words:
            return ''
        
        # Начинаем с первого слова вопроса, которое есть в кластере
        start_word = None
        for qw in question_words:
            if qw in cluster_words:
                start_word = qw
                break
        
        if start_word is None:
            start_word = cluster_words[0]

        # Строим цепочку: идём от стартового слова по самым сильным связям
        visited = {start_word}
        chain = [start_word]
        current = start_word
        word_set = set(cluster_words)

        while len(visited) < len(cluster_words):
            # Ищем следующее слово — сосед с самой сильной связью
            best_next = None
            best_strength = 0
            for word in word_set:
                if word not in visited:
                    strength = self.links.get((current, word), 0)
                    if strength > best_strength:
                        best_strength = strength
                        best_next = word
            
            if best_next is None:
                # Не нашли — пробуем любой непосещённый
                for word in word_set:
                    if word not in visited:
                        best_next = word
                        break
            
            if best_next is None:
                break
            
            visited.add(best_next)
            chain.append(best_next)
            current = best_next

        return ' '.join(chain)

    def get_stats(self) -> Dict:
        return {
            'num_nodes': len(self.nodes),
            'num_links': len(self.links),
            'num_clusters': len(self.clusters),
            'total_texts': self.total_texts,
        }


# ============================================================================
# ЗАПУСК
# ============================================================================

def main():
    print("=" * 60)
    print("ЧИСТОЕ ПОЛЕ СМЫСЛОВ v9.0")
    print("Слова = заряды. Связи = отношения. Грамматика = закономерности.")
    print("=" * 60)

    field = StructuralField()

    corpus = [
        "Трава зелёная потому что хлорофилл отражает свет.",
        "Солнце излучает энергию необходимую для жизни.",
        "Вихрь создаёт поле притяжения в центре системы.",
        "Резонанс возникает при совпадении частот двух систем.",
        "Вода кипит при ста градусах Цельсия на уровне моря.",
        "Атом состоит из ядра и электронной оболочки вокруг него.",
        "Ветер возникает из-за разницы атмосферного давления.",
        "Растения используют фотосинтез для получения энергии из света.",
        "Двигатель преобразует тепловую энергию в механическую работу.",
        "Закон всемирного тяготения открыл Исаак Ньютон.",
        "Небо синее потому что атмосфера рассеивает короткие волны света.",
        "Лёд плавает в воде потому что его плотность меньше плотности жидкости.",
        "Компьютер обрабатывает данные через центральный процессор.",
        "Энергия сохраняется в замкнутой системе согласно первому закону термодинамики.",
        "Магнитное поле создаётся движущимися электрическими зарядами.",
        "Температура измеряет среднюю кинетическую энергию частиц вещества.",
        "Электромагнитные волны распространяются в вакууме со скоростью света.",
        "Фотосинтез превращает углекислый газ и воду в глюкозу и кислород.",
        "Эволюция происходит через естественный отбор наиболее приспособленных особей.",
        "ДНК хранит генетическую информацию в последовательности нуклеотидов.",
        "Электрический двигатель преобразует электрическую энергию во вращательное движение.",
        "Солнечная батарея превращает световую энергию в электрический ток.",
        "Гравитация притягивает тела друг к другу пропорционально массе.",
        "Звук распространяется в воздухе со скоростью триста тридцать метров в секунду.",
        "Ядро атома содержит протоны и нейтроны связанные ядерными силами.",
        "Иммунная система защищает организм от чужеродных агентов и инфекций.",
        "Гормоны регулируют обмен веществ рост и развитие организма.",
        "Давление газа увеличивается при повышении температуры в закрытом сосуде.",
    ]

    print(f"\n📚 Корпус: {len(corpus)} текстов")
    for i, text in enumerate(corpus):
        field.add_text(text)
        if i % 10 == 0:
            stats = field.get_stats()
            print(f"  [{i}] кластеров: {stats['num_clusters']} | слов: {stats['num_nodes']} | связей: {stats['num_links']}")

    stats = field.get_stats()
    print(f"\n✅ Поле готово: {stats['num_nodes']} слов, {stats['num_links']} связей, {stats['num_clusters']} кластеров")

    questions = [
        "Почему трава зелёная?",
        "Что такое резонанс?",
        "Как работает двигатель?",
        "Почему вода кипит?",
        "Что измеряет температура?",
        "Почему лёд плавает?",
        "Что такое фотосинтез?",
        "Как устроен атом?",
        "Откуда берётся ветер?",
        "Что такое гравитация?",
    ]

    print("\n" + "=" * 60)
    print("🔍 ЗАПРОСЫ")
    print("=" * 60)

    for q in questions:
        field.query(q)


if __name__ == "__main__":
    main()