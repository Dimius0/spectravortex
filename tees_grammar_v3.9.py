#!/usr/bin/env python3
"""
tees_grammar_v3.9.py — Финальная версия
v3.9: жёсткий глагольный фильтр + правила склонения + чистые паттерны
"""

import re
import os
import glob
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

class ModeRole(Enum):
    SOURCE = "source"
    RECEIVER = "receiver"
    AFTER_ROUTER = "router"

@dataclass
class ExchangePattern:
    source_ending: str
    receiver_ending: str
    router: Optional[str]
    carriers: Counter
    examples: List[Tuple[str, str, str]]
    count: int

@dataclass
class TransformationRule:
    role: ModeRole
    router: Optional[str]
    old_ending: str
    new_ending: str
    examples: List[Tuple[str, str]]
    confidence: float

class ExchangeAnalyzer:
    def __init__(self):
        self.lemma_forms: Dict[str, List[Tuple[str, ModeRole, Optional[str]]]] = defaultdict(list)
        self.surface_to_lemma: Dict[str, str] = {}
        self.lemmas: set = set()
        
        self.exchange_records: List[Tuple[str, str, str, str, Optional[str]]] = []
        self.rules: List[TransformationRule] = []
        self.exchange_patterns: List[ExchangePattern] = []
        self.total_sentences = 0
        
        self.known_routers = {
            'в', 'во', 'на', 'с', 'со', 'к', 'ко', 'по', 'из', 'от', 'для', 'без',
            'над', 'под', 'об', 'обо', 'при', 'за', 'до', 'через', 'между', 'перед',
            'о', 'у', 'около', 'вокруг', 'после', 'про', 'ради', 'сквозь', 'вдоль',
        }
        
        self.MIN_STEM_LEN = 2
        self.MIN_EXCHANGE_COUNT = 3
        self.MIN_RULE_COUNT = 2
        
        self.non_verbs = {
            'и', 'или', 'либо', 'а', 'но', 'да', 'что', 'как', 'это', 'так', 'же',
            'бы', 'ли', 'то', 'всё', 'все', 'сам', 'если', 'когда', 'пока', 'чтобы',
            'хотя', 'ведь', 'раз', 'почти', 'более', 'менее', 'очень', 'весьма',
            'совсем', 'вполне', 'даже', 'именно', 'просто', 'ровно', 'примерно',
            'есть', 'нет', 'можно', 'нужно', 'надо', 'нельзя', 'возможно',
            'всегда', 'никогда', 'часто', 'редко', 'обычно', 'иногда', 'вдруг',
            'наконец', 'снова', 'опять', 'теперь', 'тогда', 'потом', 'уже', 'ещё',
            'только', 'лишь', 'вот', 'вон', 'там', 'здесь', 'тут', 'где', 'куда',
            'откуда', 'почему', 'зачем', 'сколько', 'насколько',
            'он', 'она', 'оно', 'они', 'я', 'ты', 'мы', 'вы', 'его', 'её', 'их',
            'мой', 'твой', 'наш', 'ваш', 'свой', 'весь', 'тот', 'этот', 'такой',
            'который', 'кто', 'чей', 'какой', 'каков', 'нибудь', 'либо',
            'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
            'had', 'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been',
            'http', 'www', 'min', 'max', 'env', 'opt', 'syn', 'this', 'that',
            'with', 'from', 'will', 'they', 'them', 'then', 'than', 'what',
            'which', 'would', 'could', 'should', 'about', 'into', 'more',
            'some', 'such', 'only', 'other', 'over', 'also', 'new', 'any',
            'сущность', 'плотность', 'поверхность', 'закономерность', 'интенсивность',
            'способность', 'точность', 'воспроизводимость', 'принадлежность',
            'эксперимент', 'обжим', 'статус', 'модель', 'узел', 'цикл',
        }
        
    def is_router(self, word: str) -> bool:
        return word.lower() in self.known_routers
    
    def is_verb(self, word: str) -> bool:
        w = word.lower()
        if w in self.non_verbs:
            return False
        if len(w) <= 2:
            return False
        
        # Инфинитивы (только если оканчиваются на -ать/-ять/-еть/-ить/-оть/-уть)
        if w.endswith('ться'):
            return True
        if w.endswith('ть') and len(w) >= 4:
            # Отсекаем существительные на -сть: сущность, плотность, etc
            if w.endswith('ость') or w.endswith('есть') or w.endswith('асть'):
                return False
            return True
        
        # Прошедшее время (надёжный признак)
        if re.search(r'(л|ла|ло|ли|лся|лась|лось|лись)$', w):
            return True
        
        # Настоящее/будущее время (3 лицо — самый надёжный признак)
        if re.search(r'(ет|ёт|ит|ют|ут|ят|ат)$', w) and len(w) >= 3:
            return True
        
        # Возвратные формы
        if w.endswith(('ется', 'ётся', 'ются', 'тся')):
            return True
        
        # Причастия (только если длинное)
        if len(w) >= 7:
            if re.search(r'(ющий|ющийся|вший|вшийся|енный|анный|имый|емый|омый|ащий|ящий|ущий)$', w):
                return True
        
        # Краткие причастия прошедшего времени (надёжный признак)
        if re.search(r'(ен|ан|т|ят|ут)$', w) and len(w) >= 5:
            # Не существительные на -ент/-ант
            if w.endswith(('мент', 'тант', 'гент', 'кент')):
                return False
            return True
        
        return False
    
    def is_noun(self, word: str) -> bool:
        w = word.lower()
        if self.is_verb(w):
            return False
        if self.is_router(w):
            return False
        if w in self.non_verbs:
            return False
        if w.isupper() and len(w) <= 5:
            return False
        if re.search(r'\d', w):
            return False
        return len(w) > 2
    
    def get_lemma(self, surface: str) -> str:
        return self.surface_to_lemma.get(surface, surface)
    
    def _word_ending(self, word: str) -> str:
        if len(word) >= 2:
            return word[-2:]
        elif len(word) == 1:
            return word
        return '-'
    
    def analyze_sentence(self, text: str):
        words = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', text)
        if len(words) < 3:
            return
        
        for i in range(len(words) - 2):
            w1 = words[i].lower()
            w2 = words[i+1].lower()
            w3 = words[i+2].lower()
            
            if not self.is_verb(w2):
                continue
            if not self.is_noun(w1):
                continue
            
            router = None
            w3_idx = i + 2
            if self.is_router(w3):
                router = w3
                if w3_idx + 1 < len(words):
                    w3_idx += 1
                    w3 = words[w3_idx].lower()
                else:
                    continue
            
            if not self.is_noun(w3):
                continue
            
            self.lemmas.add(w1)
            receiver_role = ModeRole.AFTER_ROUTER if router else ModeRole.RECEIVER
            
            self.lemma_forms[w1].append((w1, ModeRole.SOURCE, None))
            self.lemma_forms[w1].append((w3, receiver_role, router))
            
            # Привязываем форму к лемме если общая основа >= MIN_STEM_LEN
            common = self._longest_common_prefix(w1, w3)
            if len(common) >= self.MIN_STEM_LEN and len(common) >= len(w3) * 0.4:
                self.surface_to_lemma[w3] = w1
            
            self.exchange_records.append((w1, w2, w3, w1, router))
        
        self.total_sentences += 1
    
    def process_corpus(self, texts: List[str]):
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 10:
                    self.analyze_sentence(sent)
    
    def process_file(self, filepath: str) -> int:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            sentences = re.split(r'[.!?]+', content)
            count = 0
            for sent in sentences:
                sent = sent.strip()
                if 10 < len(sent) < 500:
                    self.analyze_sentence(sent)
                    count += 1
            return count
        except Exception:
            return 0
    
    def discover_rules(self):
        raw = defaultdict(lambda: {'count': 0, 'examples': []})
        
        for lemma, forms in self.lemma_forms.items():
            source_form = None
            for surface, role, router in forms:
                if role == ModeRole.SOURCE:
                    source_form = surface
                    break
            if source_form is None:
                continue
            
            for surface, role, router in forms:
                if role == ModeRole.SOURCE or surface == source_form:
                    continue
                
                common = self._longest_common_prefix(source_form, surface)
                if len(common) < self.MIN_STEM_LEN:
                    continue
                if len(common) < len(surface) * 0.4:
                    continue
                
                old_end = source_form[len(common):]
                new_end = surface[len(common):]
                if old_end == new_end:
                    continue
                if len(old_end) > len(common) or len(new_end) > len(common):
                    continue
                
                key = (role, router, old_end, new_end)
                raw[key]['count'] += 1
                raw[key]['examples'].append((source_form, surface))
        
        self.rules = []
        for (role, router, old_end, new_end), data in raw.items():
            if data['count'] >= self.MIN_RULE_COUNT:
                unique_lemmas = set(src for src, _ in data['examples'])
                if len(unique_lemmas) >= 2:
                    self.rules.append(TransformationRule(
                        role=role, router=router,
                        old_ending=old_end, new_ending=new_end,
                        examples=data['examples'][:5],
                        confidence=data['count'] / max(1, len(self.lemmas)),
                    ))
        
        self.rules.sort(key=lambda r: (r.confidence, len(r.old_ending)), reverse=True)
        
        filtered = []
        for rule in self.rules:
            redundant = any(
                existing.role == rule.role and
                existing.router == rule.router and
                existing.old_ending.endswith(rule.old_ending) and
                existing.new_ending == rule.new_ending and
                existing.confidence >= rule.confidence
                for existing in filtered
            )
            if not redundant:
                filtered.append(rule)
        self.rules = filtered
        
        print(f"\n   Правил склонения: {len(self.rules)}")
    
    def discover_exchanges(self):
        raw_patterns = defaultdict(lambda: {'carriers': Counter(), 'examples': [], 'count': 0})
        
        for src_surface, carrier, recv_surface, src_lemma, router in self.exchange_records:
            src_end = self._word_ending(src_surface)
            recv_end = self._word_ending(recv_surface)
            
            key = (src_end, recv_end, router)
            raw_patterns[key]['carriers'][carrier] += 1
            raw_patterns[key]['examples'].append((src_surface, carrier, recv_surface))
            raw_patterns[key]['count'] += 1
        
        self.exchange_patterns = []
        for (src_end, recv_end, router), data in raw_patterns.items():
            if data['count'] >= self.MIN_EXCHANGE_COUNT:
                carriers = Counter({k: v for k, v in data['carriers'].items() if v >= 2})
                if len(carriers) >= 1:
                    pattern = ExchangePattern(
                        source_ending=src_end,
                        receiver_ending=recv_end,
                        router=router,
                        carriers=carriers,
                        examples=data['examples'][:5],
                        count=data['count'],
                    )
                    self.exchange_patterns.append(pattern)
        
        self.exchange_patterns.sort(key=lambda p: p.count, reverse=True)
        print(f"   Обменных паттернов (≥{self.MIN_EXCHANGE_COUNT}): {len(self.exchange_patterns)}")
    
    def _longest_common_prefix(self, a: str, b: str) -> str:
        min_len = min(len(a), len(b))
        for i in range(min_len, 0, -1):
            if a[:i] == b[:i]:
                return a[:i]
        return ""
    
    def apply_rules(self, lemma: str, role: ModeRole, router: Optional[str] = None) -> str:
        if role == ModeRole.SOURCE:
            return lemma
        
        best_rule = None
        best_old_len = 0
        
        for rule in self.rules:
            if rule.role != role:
                continue
            if rule.router != router and rule.router is not None and router is not None:
                continue
            if lemma.endswith(rule.old_ending):
                if len(rule.old_ending) > best_old_len:
                    best_old_len = len(rule.old_ending)
                    best_rule = rule
        
        if best_rule:
            return lemma[:-len(best_rule.old_ending)] + best_rule.new_ending
        
        for rule in self.rules:
            if rule.role == role and lemma.endswith(rule.old_ending):
                return lemma[:-len(rule.old_ending)] + rule.new_ending
        
        return lemma
    
    def find_carrier(self, lemma_a: str, lemma_b: str) -> Optional[Tuple[str, Optional[str]]]:
        end_a = self._word_ending(lemma_a)
        end_b = self._word_ending(lemma_b)
        
        for pattern in self.exchange_patterns:
            if pattern.source_ending == end_a and pattern.receiver_ending == end_b:
                carrier = pattern.carriers.most_common(1)[0][0]
                return (carrier, pattern.router)
        
        for pattern in self.exchange_patterns:
            if pattern.source_ending == end_a:
                carrier = pattern.carriers.most_common(1)[0][0]
                return (carrier, pattern.router)
        
        all_carriers = Counter()
        for pattern in self.exchange_patterns:
            all_carriers.update(pattern.carriers)
        
        if all_carriers:
            carrier = all_carriers.most_common(1)[0][0]
            return (carrier, None)
        
        return None
    
    def print_rules(self, max_rules: int = 30):
        print(f"\n📋 ПРАВИЛА СКЛОНЕНИЯ:")
        if not self.rules:
            print("   (не найдены)")
            return
        for i, rule in enumerate(self.rules[:max_rules]):
            router_str = f" после '{rule.router}'" if rule.router else ""
            ex = ", ".join([f"{a}→{b}" for a, b in rule.examples[:3]])
            print(f"   {i+1}. {rule.role.value}{router_str}: '-{rule.old_ending}' → '-{rule.new_ending}' ({ex})")
    
    def print_exchanges(self, max_e: int = 30):
        print(f"\n📋 ОБМЕННЫЕ ПАТТЕРНЫ (TEES = обмен окончаниями):")
        if not self.exchange_patterns:
            print("   (не найдены)")
            return
        for i, p in enumerate(self.exchange_patterns[:max_e]):
            router_str = f" [{p.router}]" if p.router else ""
            carriers_str = ", ".join([f"{c}×{n}" for c, n in p.carriers.most_common(4)])
            print(f"   {i+1}. (-{p.source_ending}) ↔ (-{p.receiver_ending}){router_str}: {carriers_str} (×{p.count})")
    
    def print_stats(self):
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Предложений: {self.total_sentences}")
        print(f"   Лемм: {len(self.lemmas)}")
        print(f"   Обменов (троек с глаголом): {len(self.exchange_records)}")
        print(f"   Правил склонения: {len(self.rules)}")
        print(f"   Обменных паттернов: {len(self.exchange_patterns)}")


class ExchangeAssembler:
    def __init__(self, analyzer: ExchangeAnalyzer):
        self.analyzer = analyzer
        
    def assemble(self, lemma_a: str, lemma_b: str) -> Optional[str]:
        found = self.analyzer.find_carrier(lemma_a, lemma_b)
        if not found:
            return None
        
        carrier, router = found
        receiver_role = ModeRole.AFTER_ROUTER if router else ModeRole.RECEIVER
        
        source_form = self.analyzer.apply_rules(lemma_a, ModeRole.SOURCE)
        receiver_form = self.analyzer.apply_rules(lemma_b, receiver_role, router)
        
        parts = [source_form.capitalize(), carrier]
        if router:
            parts.append(router)
        parts.append(receiver_form)
        
        return ' '.join(parts) + '.'


def test():
    print("=" * 60)
    print("TEES-ГРАММАТИКА v3.9 — ФИНАЛ")
    print("=" * 60)
    
    analyzer = ExchangeAnalyzer()
    
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
    
    print("\n📚 Загрузка корпуса...")
    analyzer.process_corpus(corpus)
    
    print("\n📂 Загрузка файлов...")
    total = 0
    for d in ['discoveries', 'brain_dump', 'predictions', '.']:
        if os.path.isdir(d):
            for pat in ['*.md', '*.txt']:
                for fp in glob.glob(os.path.join(d, pat)):
                    c = analyzer.process_file(fp)
                    if c > 10:
                        total += c
    if total > 0:
        print(f"   Загружено из файлов: {total} предложений")
    
    print("\n🔍 Вывод правил...")
    analyzer.discover_rules()
    analyzer.discover_exchanges()
    
    analyzer.print_stats()
    analyzer.print_rules(30)
    analyzer.print_exchanges(30)
    
    print("\n🔧 СБОРКА:")
    assembler = ExchangeAssembler(analyzer)
    
    pairs = [
        ("трава", "свет"),
        ("энергия", "жизнь"),
        ("резонанс", "система"),
        ("вихрь", "поле"),
        ("вода", "газ"),
        ("температура", "вещество"),
        ("гравитация", "тело"),
    ]
    
    for a, b in pairs:
        result = assembler.assemble(a, b)
        print(f"   {a} + {b} → {result if result else '—'}")
    
    return analyzer


if __name__ == "__main__":
    test()