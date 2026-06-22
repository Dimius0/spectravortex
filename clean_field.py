#!/usr/bin/env python3
"""
clean_field_v8.py — Чистое поле смыслов. Версия 8.0
Без парсера. Без POS. Без грамматики.
Маркировка при добавлении. Вопрос — обращение к массивам. Ответ — извлечение последовательности.
"""

import re
from collections import defaultdict
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

# ============================================================================
# УЗЕЛ
# ============================================================================

@dataclass
class Node:
    token: str
    lemma: str
    frequency: int = 1


# ============================================================================
# ПОЛЕ
# ============================================================================

class StructuralField:
    """Поле смыслов v8.0: память массивов и связей."""
    
    def __init__(self, debug_log: str = "field_v8.log"):
        self.nodes: Dict[str, Node] = {}          # все уникальные слова
        self.fragments: List[Dict] = []            # сохранённые массивы
        self.total_texts = 0
        
        with open(debug_log, 'w', encoding='utf-8') as f:
            f.write(f"=== v8.0 log — {datetime.now()} ===\n\n")

    def _node_id(self, lemma: str) -> str:
        return lemma

    def _get_or_create_node(self, word: str) -> str:
        """Найти или создать узел."""
        lemma = word.lower()
        node_id = self._node_id(lemma)
        if node_id not in self.nodes:
            self.nodes[node_id] = Node(token=word, lemma=lemma)
        else:
            self.nodes[node_id].frequency += 1
        return node_id

    # ========================================================================
    # МАРКИРОВКА — добавление текста
    # ========================================================================

    def add_text(self, text: str) -> bool:
        """
        Разобрать текст в массив, сохранить как фрагмент.
        Каждое слово маркируется (связывается с узлом).
        Связи между словами сохраняются внутри фрагмента.
        """
        words = re.findall(r'[а-яёa-z]+', text.lower())
        if len(words) < 3:
            return False

        # Строим массив: для каждого слова — его узел и связи вперёд
        fragment = {
            'id': self.total_texts,
            'words': [],        # последовательность node_id
            'links': defaultdict(list),  # от позиции к списку следующих позиций
            'original': text,
        }

        for i, word in enumerate(words):
            node_id = self._get_or_create_node(word)
            fragment['words'].append(node_id)
            # Связь с предыдущим словом (двунаправленная внутри фрагмента)
            if i > 0:
                fragment['links'][i-1].append(i)
                fragment['links'][i].append(i-1)

        self.fragments.append(fragment)
        self.total_texts += 1
        return True

    # ========================================================================
    # ВОПРОС — обращение к массивам
    # ========================================================================

    def query(self, question: str) -> Optional[str]:
        """
        1. Разбираем вопрос на слова.
        2. Ищем фрагмент, где слова вопроса встречаются вместе (резонанс).
        3. Извлекаем последовательность из этого фрагмента.
        """
        question_words = re.findall(r'[а-яёa-z]+', question.lower())
        if not question_words:
            return None

        question_ids = [self._node_id(w) for w in question_words]
        # Оставляем только те, что есть в поле
        question_ids = [nid for nid in question_ids if nid in self.nodes]

        if not question_ids:
            return None

        # Ищем фрагмент с максимальным резонансом
        best_fragment = None
        best_score = 0

        for frag in self.fragments:
            frag_ids = set(frag['words'])
            matching = frag_ids & set(question_ids)
            if not matching:
                continue
            
            # Резонанс: сколько слов вопроса во фрагменте + насколько они близко
            score = self._resonance_score(frag, question_ids)
            if score > best_score:
                best_score = score
                best_fragment = frag

        if best_fragment is None:
            return None

        # Извлекаем ответ: полная последовательность фрагмента
        answer_words = [self.nodes[nid].token for nid in best_fragment['words']]
        answer = ' '.join(answer_words)

        print(f"\n❓ «{question}»")
        print(f"   📋 Фрагмент #{best_fragment['id']}: «{best_fragment['original']}»")
        print(f"   🎯 Резонанс: {best_score:.2f}")
        print(f"   💬 Ответ: «{answer}»")
        return answer

    def _resonance_score(self, frag: Dict, question_ids: List[str]) -> float:
        """
        Оценка резонанса: сколько слов вопроса присутствует,
        насколько они сконцентрированы (близость позиций).
        """
        positions = []
        for qid in question_ids:
            for i, wid in enumerate(frag['words']):
                if wid == qid:
                    positions.append(i)

        if not positions:
            return 0.0

        # Базовая оценка: доля совпавших слов вопроса
        coverage = len(set(positions)) / len(question_ids)

        # Близость: среднее расстояние между найденными позициями
        if len(positions) > 1:
            positions.sort()
            gaps = [positions[i+1] - positions[i] for i in range(len(positions)-1)]
            avg_gap = sum(gaps) / len(gaps)
            # Чем меньше разброс — тем выше концентрация
            concentration = 1.0 / (1.0 + avg_gap / len(frag['words']))
        else:
            concentration = 1.0

        return coverage * 0.5 + concentration * 0.5

    def get_stats(self) -> Dict:
        return {
            'num_nodes': len(self.nodes),
            'num_fragments': len(self.fragments),
            'total_texts': self.total_texts,
        }


# ============================================================================
# ЗАПУСК
# ============================================================================

def main():
    print("=" * 60)
    print("ЧИСТОЕ ПОЛЕ СМЫСЛОВ v8.0")
    print("Маркировка → Массивы → Резонанс → Извлечение")
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
            print(f"  [{i}] фрагментов: {stats['num_fragments']} | узлов: {stats['num_nodes']}")

    stats = field.get_stats()
    print(f"\n✅ Поле готово: {stats['num_nodes']} узлов, {stats['num_fragments']} фрагментов")

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