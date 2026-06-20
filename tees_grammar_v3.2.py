#!/usr/bin/env python3
"""
tees_grammar_v3.2.py — Честный вывод с очисткой правил
v3.2: фильтр коротких основ, защита от аббревиатур, улучшенная лемматизация
"""

import re
import os
import glob
from collections import defaultdict, Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
from enum import Enum

# ============================================================================
# СУЩНОСТИ
# ============================================================================

class ModeRole(Enum):
    SOURCE = "source"
    RECEIVER = "receiver"
    AFTER_ROUTER = "router"

@dataclass 
class TeesRecord:
    tees: str
    source_lemma: str
    receiver_surface: str
    router: Optional[str] = None

@dataclass
class TransformationRule:
    role: ModeRole
    router: Optional[str]
    old_ending: str
    new_ending: str
    examples: List[Tuple[str, str]]
    confidence: float

# ============================================================================
# АНАЛИЗАТОР
# ============================================================================

class HonestAnalyzer:
    def __init__(self):
        self.lemma_forms: Dict[str, List[Tuple[str, ModeRole, Optional[str]]]] = defaultdict(list)
        self.surface_to_lemma: Dict[str, str] = {}
        self.lemmas: set = set()
        self.tees_records: List[TeesRecord] = []
        self.rules: List[TransformationRule] = []
        self.total_sentences = 0
        self.total_texts = 0
        
        self.known_routers = {
            'в', 'во', 'на', 'с', 'со', 'к', 'ко', 'по', 'из', 'от', 'для', 'без',
            'над', 'под', 'об', 'обо', 'при', 'за', 'до', 'через', 'между', 'перед',
            'о', 'у', 'около', 'вокруг', 'после', 'про', 'ради', 'сквозь', 'вдоль',
        }
        
        # Минимальная длина общей основы для правила
        self.MIN_STEM_LEN = 3
        
    def is_verb(self, word: str) -> bool:
        w = word.lower()
        if len(w) <= 2:
            return False
        if w.endswith(('ть', 'ться', 'ти', 'чь')):
            return True
        if re.search(r'(л|ла|ло|ли|лся|лась|лось|лись)$', w):
            return True
        if re.search(r'(ет|ёт|ит|ют|ут|ят|ат|ешь|ёшь|ишь)$', w):
            return True
        if w.endswith(('ется', 'ётся', 'ются', 'тся')):
            return True
        return False
    
    def is_router(self, word: str) -> bool:
        return word.lower() in self.known_routers
    
    def is_noun(self, word: str) -> bool:
        if self.is_verb(word):
            return False
        if self.is_router(word):
            return False
        stop_words = {'и', 'а', 'но', 'что', 'как', 'это', 'так', 'же', 'бы', 'ли',
                     'он', 'она', 'оно', 'они', 'я', 'ты', 'мы', 'вы', 'его', 'её',
                     'их', 'мой', 'твой', 'наш', 'ваш', 'свой', 'весь', 'сам', 'тот',
                     'этот', 'такой', 'который', 'кто', 'чей', 'где', 'когда', 'весь',
                     'ещё', 'уже', 'вот', 'там', 'здесь', 'тут', 'также', 'потому',
                     'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all', 'can',
                     'had', 'her', 'was', 'one', 'our', 'out', 'has', 'have', 'been',
                     'http', 'www', 'min', 'max', 'env', 'opt', 'syn'}
        if word.lower() in stop_words:
            return False
        # Аббревиатуры (все заглавные или короткие с цифрами)
        if word.isupper() and len(word) <= 5:
            return False
        if re.search(r'\d', word):
            return False
        return len(word) > 2
    
    def get_lemma(self, surface: str) -> str:
        if surface in self.surface_to_lemma:
            return self.surface_to_lemma[surface]
        return surface
    
    def analyze_sentence(self, text: str):
        words = re.findall(r'[а-яёА-ЯЁa-zA-Z]+', text)
        if len(words) < 2:
            return
        
        verb_idx = None
        verb_word = None
        for i, word in enumerate(words):
            if self.is_verb(word):
                verb_idx = i
                verb_word = word.lower()
                break
        if verb_idx is None:
            return
        
        source_surface = None
        for i in range(verb_idx - 1, -1, -1):
            word = words[i]
            if self.is_router(word):
                continue
            if self.is_noun(word):
                source_surface = word.lower()
                self.lemmas.add(source_surface)
                self.lemma_forms[source_surface].append((source_surface, ModeRole.SOURCE, None))
                self.surface_to_lemma[source_surface] = source_surface
                break
        
        if source_surface is None:
            return
        
        current_router = None
        for i in range(verb_idx + 1, len(words)):
            word = words[i]
            if self.is_router(word):
                current_router = word.lower()
                continue
            if self.is_noun(word):
                surface = word.lower()
                role = ModeRole.AFTER_ROUTER if current_router else ModeRole.RECEIVER
                
                self.lemma_forms[source_surface].append((surface, role, current_router))
                
                # Привязываем форму к лемме только если общая основа >= MIN_STEM_LEN
                common = self._longest_common_prefix(source_surface, surface)
                if len(common) >= self.MIN_STEM_LEN:
                    self.surface_to_lemma[surface] = source_surface
                
                self.tees_records.append(TeesRecord(
                    tees=verb_word,
                    source_lemma=source_surface,
                    receiver_surface=surface,
                    router=current_router,
                ))
                
                current_router = None
        
        self.total_sentences += 1
    
    def process_corpus(self, texts: List[str]):
        for text in texts:
            self.total_texts += 1
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
        except Exception as e:
            print(f"   ⚠ {filepath}: {e}")
            return 0
    
    def discover_rules(self):
        raw_observations = defaultdict(lambda: {'count': 0, 'examples': []})
        
        for lemma, forms in self.lemma_forms.items():
            source_form = None
            for surface, role, router in forms:
                if role == ModeRole.SOURCE:
                    source_form = surface
                    break
            if source_form is None:
                continue
            
            for surface, role, router in forms:
                if role == ModeRole.SOURCE:
                    continue
                if surface == source_form:
                    continue
                
                common = self._longest_common_prefix(source_form, surface)
                
                # Фильтр: основа должна быть достаточно длинной
                if len(common) < self.MIN_STEM_LEN:
                    continue
                
                # Фильтр: основа должна быть не меньше половины обоих слов
                if len(common) < len(source_form) * 0.4 or len(common) < len(surface) * 0.4:
                    continue
                
                old_ending = source_form[len(common):]
                new_ending = surface[len(common):]
                
                if old_ending == new_ending:
                    continue
                
                # Фильтр: окончания не должны быть слишком длинными (мусор)
                if len(old_ending) > len(common) or len(new_ending) > len(common):
                    continue
                
                key = (role, router, old_ending, new_ending)
                raw_observations[key]['count'] += 1
                raw_observations[key]['examples'].append((source_form, surface))
        
        # Отбираем правила: минимум 2 примера
        self.rules = []
        for (role, router, old_end, new_end), data in raw_observations.items():
            if data['count'] >= 2:
                # Дополнительная проверка: примеры должны быть с разными леммами
                unique_lemmas = set(src for src, _ in data['examples'])
                if len(unique_lemmas) >= 2:
                    rule = TransformationRule(
                        role=role,
                        router=router,
                        old_ending=old_end,
                        new_ending=new_end,
                        examples=data['examples'][:5],
                        confidence=data['count'] / max(1, len(self.lemmas)),
                    )
                    self.rules.append(rule)
        
        self.rules.sort(key=lambda r: (r.confidence, len(r.old_ending)), reverse=True)
        
        # Оставляем только лучшие (убираем пересекающиеся)
        filtered_rules = []
        for rule in self.rules:
            # Проверяем, не поглощается ли правило более сильным
            is_redundant = False
            for existing in filtered_rules:
                if (existing.role == rule.role and 
                    existing.router == rule.router and
                    existing.old_ending.endswith(rule.old_ending) and
                    existing.new_ending == rule.new_ending and
                    existing.confidence >= rule.confidence):
                    is_redundant = True
                    break
            if not is_redundant:
                filtered_rules.append(rule)
        
        self.rules = filtered_rules
        print(f"\n   Найдено замен: {len(raw_observations)}")
        print(f"   Выведено правил (≥2 примеров, ≥2 лемм): {len(self.rules)}")
    
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
            stem = lemma[:-len(best_rule.old_ending)]
            return stem + best_rule.new_ending
        
        for rule in self.rules:
            if rule.role == role and lemma.endswith(rule.old_ending):
                stem = lemma[:-len(rule.old_ending)]
                return stem + rule.new_ending
        
        return lemma
    
    def find_tees(self, lemma_a: str, lemma_b: str) -> Optional[TeesRecord]:
        for record in self.tees_records:
            recv_lemma = self.get_lemma(record.receiver_surface)
            if record.source_lemma == lemma_a and recv_lemma == lemma_b:
                return record
        
        suffix_a = lemma_a[-2:] if len(lemma_a) >= 2 else ''
        if suffix_a:
            for rec in self.tees_records:
                if rec.source_lemma.endswith(suffix_a):
                    return rec
        
        if self.tees_records:
            return self.tees_records[0]
        return None
    
    def print_rules(self, max_rules: int = 30):
        print(f"\n📋 ВЫВЕДЕННЫЕ ПРАВИЛА СКЛОНЕНИЯ:")
        if not self.rules:
            print("   (правила не найдены)")
            return
        for i, rule in enumerate(self.rules[:max_rules]):
            router_str = f" после '{rule.router}'" if rule.router else ""
            examples_str = ", ".join([f"{a}→{b}" for a, b in rule.examples[:3]])
            print(f"   {i+1}. {rule.role.value}{router_str}: "
                  f"'-{rule.old_ending}' → '-{rule.new_ending}' "
                  f"({examples_str})")
    
    def print_stats(self):
        print(f"\n📊 СТАТИСТИКА:")
        print(f"   Текстов: {self.total_texts}")
        print(f"   Предложений: {self.total_sentences}")
        print(f"   Лемм: {len(self.lemmas)}")
        print(f"   Форм всего: {sum(len(v) for v in self.lemma_forms.values())}")
        print(f"   TEES-связей: {len(self.tees_records)}")
        print(f"   Правил: {len(self.rules)}")
        
        multi_form = sum(1 for forms in self.lemma_forms.values() if len(forms) > 1)
        print(f"   Лемм с >1 формы: {multi_form}")


# ============================================================================
# СБОРЩИК
# ============================================================================

class HonestAssembler:
    def __init__(self, analyzer: HonestAnalyzer):
        self.analyzer = analyzer
        
    def assemble(self, lemma_a: str, lemma_b: str) -> Optional[str]:
        record = self.analyzer.find_tees(lemma_a, lemma_b)
        if not record:
            return None
        
        receiver_role = ModeRole.AFTER_ROUTER if record.router else ModeRole.RECEIVER
        
        source_form = self.analyzer.apply_rules(lemma_a, ModeRole.SOURCE)
        receiver_form = self.analyzer.apply_rules(lemma_b, receiver_role, record.router)
        
        parts = [source_form.capitalize(), record.tees]
        if record.router:
            parts.append(record.router)
        parts.append(receiver_form)
        
        return ' '.join(parts) + '.'


# ============================================================================
# ТЕСТЫ
# ============================================================================

def test():
    print("=" * 60)
    print("TEES-ГРАММАТИКА v3.2 — ЧЕСТНЫЙ ВЫВОД (с очисткой)")
    print("=" * 60)
    
    analyzer = HonestAnalyzer()
    
    # Встроенный корпус
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
    
    print("\n📚 Загрузка встроенного корпуса...")
    analyzer.process_corpus(corpus)
    
    print("\n📂 Поиск файлов...")
    search_dirs = ['discoveries', 'brain_dump', 'predictions', '.']
    total_loaded = 0
    for d in search_dirs:
        if os.path.isdir(d):
            for pat in ['*.md', '*.txt']:
                files = glob.glob(os.path.join(d, pat))
                for fpath in files:
                    count = analyzer.process_file(fpath)
                    if count > 10:
                        total_loaded += count
    if total_loaded > 0:
        print(f"\n   Загружено из файлов: {total_loaded} предложений")
    
    print("\n🔍 Поиск закономерностей...")
    analyzer.discover_rules()
    
    analyzer.print_stats()
    analyzer.print_rules(30)
    
    # Сборка
    print("\n🔧 СБОРКА НОВЫХ КОНСТРУКЦИЙ:")
    assembler = HonestAssembler(analyzer)
    
    test_pairs = [
        ("трава", "свет"),
        ("энергия", "жизнь"),
        ("резонанс", "система"),
        ("вихрь", "поле"),
        ("вода", "газ"),
        ("ветер", "давление"),
        ("температура", "вещество"),
        ("гравитация", "тело"),
    ]
    
    for a, b in test_pairs:
        result = assembler.assemble(a, b)
        if result:
            print(f"   {a} + {b} → {result}")
        else:
            print(f"   {a} + {b} → не удалось")
    
    return analyzer


if __name__ == "__main__":
    test()