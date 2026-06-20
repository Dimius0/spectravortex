#!/usr/bin/env python3
"""
tees_grammar_v1.4.py — TEES-грамматика текста
v1.4: склонение жен.р. -а/-я в вин.п., интеграция с clean_field_v9 (clusters)
"""

import re
import os
import glob
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Set
from enum import Enum

# ============================================================================
# КЛАССЫ СУЩНОСТЕЙ
# ============================================================================

class ModeState(Enum):
    SOURCE = "им"
    RECEIVER = "вин"
    CO_ROUTER = "твор"
    BUFFER = "род"
    TARGET = "дат"
    CONTEXT = "пр"

class TeesDirection(Enum):
    ACTIVE = "акт"
    PASSIVE = "пасс"
    REFLEXIVE = "возвр"
    RECIPROCAL = "взаим"

class TeesIntensity(Enum):
    IMPULSE = "сов"
    FLOW = "несов"

class TeesTime(Enum):
    PAST = "прош"
    PRESENT = "наст"
    FUTURE = "буд"

@dataclass
class Mod:
    lemma: str
    state: ModeState
    number: str = "ед"
    gender: str = "м"
    attributes: List[str] = field(default_factory=list)
    
    @property
    def id(self) -> str:
        return f"{self.lemma}:{self.state.value}"

@dataclass
class TeesLink:
    lemma: str
    direction: TeesDirection
    intensity: TeesIntensity
    time: TeesTime
    reflexive: bool = False
    router: Optional[str] = None
    
    @property
    def id(self) -> str:
        parts = [self.lemma, self.direction.value, self.intensity.value, self.time.value]
        if self.reflexive:
            parts.append("ся")
        return ":".join(parts)

@dataclass
class TeesGraph:
    source: Mod
    tees: TeesLink
    receiver: Optional[Mod]
    co_mods: List[Mod] = field(default_factory=list)
    routers: List[str] = field(default_factory=list)
    raw_text: str = ""

# ============================================================================
# ПАРСЕР
# ============================================================================

class TeesGrammarParser:
    def __init__(self):
        self.mod_tees_compat: Dict[str, Dict[str, Counter]] = defaultdict(lambda: defaultdict(Counter))
        self.tees_params: Dict[str, Dict] = {}
        self.mod_state_freq: Dict[str, Counter] = defaultdict(Counter)
        self.router_connections: Dict[str, List[Tuple[str, str]]] = defaultdict(list)
        self.graphs: List[TeesGraph] = []
        self.total_parsed = 0
        self.mod_clusters: Dict[str, List[str]] = defaultdict(list)
        
        self.known_routers = {
            'в', 'во', 'на', 'с', 'со', 'к', 'ко', 'по', 'из', 'от', 'для', 'без',
            'над', 'под', 'об', 'обо', 'при', 'за', 'до', 'через', 'между', 'перед',
            'о', 'у', 'около', 'вокруг', 'после', 'про', 'ради', 'сквозь', 'вдоль',
        }
        
        self.case_endings = {
            ModeState.SOURCE: ['', 'а', 'я', 'ы', 'и', 'о', 'е', 'ий', 'ый', 'ой', 'ь'],
            ModeState.RECEIVER: ['у', 'ю', 'а', 'я', 'о', 'е', 'ы', 'ей', 'ий', 'ый', 'ь'],
            ModeState.CO_ROUTER: ['ом', 'ем', 'ём', 'ой', 'ей', 'ёй', 'ью', 'ами', 'ями', 'ым', 'им'],
            ModeState.BUFFER: ['а', 'я', 'ы', 'и', 'ов', 'ев', 'ей', 'ого', 'его', 'ья'],
            ModeState.TARGET: ['у', 'ю', 'ам', 'ям', 'ому', 'ему', 'ье'],
            ModeState.CONTEXT: ['е', 'и', 'ах', 'ях', 'ом', 'ем', 'ье'],
        }
        
    def detect_case(self, word: str) -> Optional[ModeState]:
        word_lower = word.lower()
        scores = defaultdict(int)
        for case, endings in self.case_endings.items():
            for ending in sorted(endings, key=len, reverse=True):
                if ending and word_lower.endswith(ending):
                    scores[case] += len(ending)
        if scores:
            return max(scores, key=scores.get)
        return None
    
    def is_verb(self, word: str) -> bool:
        word_lower = word.lower()
        
        known_nouns = {
            'онегин', 'деревня', 'поэт', 'стихи', 'любовь', 'душа', 'мысль', 'слово',
            'энергия', 'канал', 'роутер', 'маршрут', 'поле', 'фрагмент', 'зона',
            'температура', 'ветер', 'волна', 'художник', 'картина', 'музыка', 'сердце',
            'учёный', 'природа', 'свобода', 'внимание', 'смысл', 'цель', 'поток',
            'мод', 'связь', 'текст', 'граф', 'узел', 'сеть', 'пульс', 'бит',
        }
        if word_lower in known_nouns:
            return False
        
        if word_lower.endswith(('ть', 'ться', 'ти', 'чь')):
            return True
        
        if re.search(r'(л|ла|ло|ли|лся|лась|лось|лись)$', word_lower):
            noun_exceptions = {'канал', 'сигнал', 'идеал', 'финал', 'пенал', 'бокал', 'вокзал', 'журнал'}
            if word_lower in noun_exceptions:
                return False
            return True
        
        personal_endings = {
            'ешь', 'ёшь', 'ишь',
            'ет', 'ёт', 'ит',
            'ют', 'ут', 'ят', 'ат',
        }
        for ending in personal_endings:
            if word_lower.endswith(ending) and len(word_lower) >= 4:
                if ending in {'ет', 'ёт', 'ит'}:
                    return True
                if ending in {'ешь', 'ёшь', 'ишь'}:
                    return True
                if ending in {'ют', 'ут', 'ят', 'ат'} and len(word_lower) >= 5:
                    return True
        
        if word_lower.endswith(('ется', 'ётся', 'ются', 'тся', 'ться', 'ись', 'ась', 'ось')):
            return True
        
        if len(word_lower) >= 6:
            if re.search(r'(ющий|ющийся|вший|вшийся|енный|анный|имый|емый|омый|ащий|ящий|ущий|ючи|авши|ивши)$', word_lower):
                return True
        
        return False
    
    def is_noun(self, word: str) -> bool:
        if self.is_verb(word):
            return False
        if word.lower() in self.known_routers:
            return False
        stop_words = {'и', 'а', 'но', 'что', 'как', 'это', 'так', 'же', 'бы', 'ли',
                     'он', 'она', 'оно', 'они', 'я', 'ты', 'мы', 'вы', 'его', 'её',
                     'их', 'мой', 'твой', 'наш', 'ваш', 'свой', 'весь', 'сам', 'тот',
                     'этот', 'такой', 'который', 'кто', 'чей', 'где', 'когда', 'весь',
                     'ещё', 'уже', 'вот', 'там', 'здесь', 'тут', 'также'}
        if word.lower() in stop_words:
            return False
        return len(word) > 2
    
    def detect_tees_params(self, verb: str) -> Dict:
        word_lower = verb.lower()
        params = {
            'reflexive': word_lower.endswith(('ся', 'сь')),
            'direction': TeesDirection.ACTIVE,
            'intensity': TeesIntensity.FLOW,
            'time': TeesTime.PRESENT,
        }
        
        if params['reflexive']:
            params['direction'] = TeesDirection.REFLEXIVE
            
        if re.search(r'(л|ла|ло|ли|лся|лась|лось|лись)$', word_lower):
            params['time'] = TeesTime.PAST
        elif re.search(r'(ет|ёт|ит|ют|ут|ят|ат|ешь|ёшь|ишь|им|ем|ёте|ите|ете)$', word_lower):
            params['time'] = TeesTime.PRESENT
            
        if re.search(r'(ну|ану)ть?$', word_lower):
            params['intensity'] = TeesIntensity.IMPULSE
        elif re.search(r'(ыва|ива|ва|ова|ева)ть?$', word_lower):
            params['intensity'] = TeesIntensity.FLOW
        elif re.search(r'(ил|ел|ал|нул)ся?$', word_lower):
            params['intensity'] = TeesIntensity.IMPULSE
        elif len(word_lower.replace('ся', '').replace('сь', '')) <= 5:
            params['intensity'] = TeesIntensity.IMPULSE
            
        return params
    
    def parse_sentence(self, text: str) -> Optional[TeesGraph]:
        words = re.findall(r'[а-яёА-ЯЁ]+', text)
        if len(words) < 2:
            return None
            
        verb_idx = None
        verb_word = None
        for i, word in enumerate(words):
            if self.is_verb(word):
                verb_idx = i
                verb_word = word
                break
                
        if verb_idx is None:
            return None
            
        params = self.detect_tees_params(verb_word)
        
        source_mod = None
        for i in range(verb_idx - 1, -1, -1):
            word = words[i]
            if word.lower() in self.known_routers:
                continue
            if self.is_noun(word):
                case = self.detect_case(word) or ModeState.SOURCE
                source_mod = Mod(lemma=word.lower(), state=case)
                break
                
        receiver_mod = None
        co_mods = []
        routers_found = []
        
        for i in range(verb_idx + 1, len(words)):
            word = words[i]
            if word.lower() in self.known_routers:
                routers_found.append(word.lower())
                continue
                
            if self.is_noun(word):
                case = self.detect_case(word) or ModeState.RECEIVER
                mod = Mod(lemma=word.lower(), state=case)
                
                if receiver_mod is None:
                    receiver_mod = mod
                else:
                    co_mods.append(mod)
        
        if source_mod is None:
            return None
            
        tees = TeesLink(
            lemma=verb_word.lower(),
            direction=params['direction'],
            intensity=params['intensity'],
            time=params['time'],
            reflexive=params['reflexive'],
            router=routers_found[0] if routers_found else None,
        )
        
        self._update_stats(source_mod, tees, receiver_mod, routers_found)
        
        graph = TeesGraph(
            source=source_mod,
            tees=tees,
            receiver=receiver_mod,
            co_mods=co_mods,
            routers=routers_found,
            raw_text=text,
        )
        self.graphs.append(graph)
        self.total_parsed += 1
        
        return graph
    
    def _update_stats(self, source: Mod, tees: TeesLink, receiver: Optional[Mod], routers: List[str]):
        self.mod_tees_compat[source.lemma][tees.lemma][source.state.value] += 1
        if receiver:
            self.mod_tees_compat[receiver.lemma][tees.lemma][receiver.state.value] += 1
            
        source_suffix = source.lemma[-2:] if len(source.lemma) > 2 else source.lemma
        if tees.lemma not in self.mod_clusters:
            self.mod_clusters[source_suffix] = []
        if source.lemma not in self.mod_clusters[source_suffix]:
            self.mod_clusters[source_suffix].append(source.lemma)
        if receiver:
            recv_suffix = receiver.lemma[-2:] if len(receiver.lemma) > 2 else receiver.lemma
            if recv_suffix not in self.mod_clusters:
                self.mod_clusters[recv_suffix] = []
            if receiver.lemma not in self.mod_clusters[recv_suffix]:
                self.mod_clusters[recv_suffix].append(receiver.lemma)
            
        if tees.lemma not in self.tees_params:
            self.tees_params[tees.lemma] = {
                'directions': Counter(),
                'intensities': Counter(),
                'times': Counter(),
                'reflexive_count': 0,
                'routers': Counter(),
                'source_mods': Counter(),
                'receiver_mods': Counter(),
            }
        self.tees_params[tees.lemma]['directions'][tees.direction.value] += 1
        self.tees_params[tees.lemma]['intensities'][tees.intensity.value] += 1
        self.tees_params[tees.lemma]['times'][tees.time.value] += 1
        self.tees_params[tees.lemma]['source_mods'][source.lemma] += 1
        if tees.reflexive:
            self.tees_params[tees.lemma]['reflexive_count'] += 1
        if tees.router:
            self.tees_params[tees.lemma]['routers'][tees.router] += 1
        if receiver:
            self.tees_params[tees.lemma]['receiver_mods'][receiver.lemma] += 1
            
        self.mod_state_freq[source.lemma][source.state.value] += 1
        if receiver:
            self.mod_state_freq[receiver.lemma][receiver.state.value] += 1
            
        for router in routers:
            if receiver:
                self.router_connections[router].append(
                    (source.state.value, receiver.state.value)
                )
    
    def process_corpus(self, texts: List[str]):
        for text in texts:
            sentences = re.split(r'[.!?]+', text)
            for sent in sentences:
                sent = sent.strip()
                if len(sent) > 10:
                    self.parse_sentence(sent)
    
    def process_file(self, filepath: str) -> int:
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            sentences = re.split(r'[.!?]+', content)
            count = 0
            for sent in sentences:
                sent = sent.strip()
                if 10 < len(sent) < 500:
                    if self.parse_sentence(sent):
                        count += 1
            return count
        except Exception as e:
            print(f"Ошибка чтения {filepath}: {e}")
            return 0
    
    def process_directory(self, dirpath: str, pattern: str = "*.txt") -> int:
        total = 0
        for fpath in glob.glob(os.path.join(dirpath, pattern)):
            total += self.process_file(fpath)
        return total
    
    def get_stats(self) -> Dict:
        return {
            'total_parsed': self.total_parsed,
            'unique_mods': len(self.mod_tees_compat),
            'unique_tees': len(self.tees_params),
            'graphs_extracted': len(self.graphs),
        }


# ============================================================================
# СБОРЩИК (v1.4 — жен.род -а/-я в вин.п.)
# ============================================================================

class TeesAssembler:
    def __init__(self, parser: TeesGrammarParser):
        self.parser = parser
        
    def find_compatible_tees(self, mod_lemma: str) -> List[Tuple[str, float]]:
        if mod_lemma in self.parser.mod_tees_compat:
            compat = self.parser.mod_tees_compat[mod_lemma]
            scored = [(tees, sum(states.values())) for tees, states in compat.items()]
            scored.sort(key=lambda x: x[1], reverse=True)
            if scored:
                return scored
        
        suffix = mod_lemma[-2:] if len(mod_lemma) > 2 else mod_lemma
        similar_mods = self.parser.mod_clusters.get(suffix, [])
        
        all_tees = Counter()
        for similar in similar_mods:
            if similar in self.parser.mod_tees_compat:
                for tees, states in self.parser.mod_tees_compat[similar].items():
                    all_tees[tees] += sum(states.values())
        
        if all_tees:
            return all_tees.most_common(10)
        
        return [(tees, 1) for tees in self.parser.tees_params.keys()]
    
    def determine_state(self, mod_lemma: str, tees: TeesLink, role: str = 'source') -> ModeState:
        if role == 'source':
            return ModeState.SOURCE
        
        if tees.direction == TeesDirection.ACTIVE:
            return ModeState.RECEIVER
        elif tees.direction == TeesDirection.PASSIVE:
            return ModeState.CO_ROUTER
        elif tees.direction == TeesDirection.REFLEXIVE:
            if tees.router in {'к', 'ко'}:
                return ModeState.TARGET
            elif tees.router in {'в', 'во', 'на'}:
                return ModeState.RECEIVER
            elif tees.router in {'с', 'со', 'из', 'от', 'о', 'об', 'обо'}:
                return ModeState.CONTEXT
            return ModeState.TARGET
        elif tees.router in {'в', 'во', 'на'}:
            return ModeState.RECEIVER
        elif tees.router in {'к', 'ко'}:
            return ModeState.TARGET
        elif tees.router in {'с', 'со', 'из', 'от'}:
            return ModeState.BUFFER
        elif tees.router in {'о', 'об', 'обо', 'при'}:
            return ModeState.CONTEXT
        
        if mod_lemma in self.parser.mod_state_freq:
            states = self.parser.mod_state_freq[mod_lemma]
            most_common = states.most_common(1)
            if most_common:
                return ModeState(most_common[0][0])
        
        return ModeState.RECEIVER
    
    def assemble_graph(self, mod_a: str, mod_b: str) -> Optional[TeesGraph]:
        tees_for_a = dict(self.find_compatible_tees(mod_a))
        tees_for_b = dict(self.find_compatible_tees(mod_b))
        
        common_tees = set(tees_for_a.keys()) & set(tees_for_b.keys())
        
        if not common_tees:
            common_tees = set(tees_for_a.keys())
            if not common_tees:
                return None
        
        best_tees_lemma = max(common_tees, key=lambda t: tees_for_a.get(t, 0) + tees_for_b.get(t, 0))
        
        params = self.parser.tees_params.get(best_tees_lemma, {})
        if params:
            directions = params.get('directions', Counter())
            direction = TeesDirection(directions.most_common(1)[0][0]) if directions else TeesDirection.ACTIVE
            intensities = params.get('intensities', Counter())
            intensity = TeesIntensity(intensities.most_common(1)[0][0]) if intensities else TeesIntensity.FLOW
            times = params.get('times', Counter())
            time = TeesTime(times.most_common(1)[0][0]) if times else TeesTime.PRESENT
            reflexive = params.get('reflexive_count', 0) > 0
            routers = params.get('routers', Counter())
            router = routers.most_common(1)[0][0] if routers else None
        else:
            direction = TeesDirection.ACTIVE
            intensity = TeesIntensity.FLOW
            time = TeesTime.PRESENT
            reflexive = False
            router = None
        
        tees = TeesLink(
            lemma=best_tees_lemma,
            direction=direction,
            intensity=intensity,
            time=time,
            reflexive=reflexive,
            router=router,
        )
        
        source = Mod(lemma=mod_a, state=self.determine_state(mod_a, tees, 'source'))
        receiver = Mod(lemma=mod_b, state=self.determine_state(mod_b, tees, 'receiver'))
        
        return TeesGraph(
            source=source,
            tees=tees,
            receiver=receiver,
        )
    
    def graph_to_text(self, graph: TeesGraph) -> str:
        parts = []
        
        source_form = self._decline(graph.source)
        parts.append(source_form.capitalize())
        
        tees_word = graph.tees.lemma
        if graph.tees.reflexive and not tees_word.endswith(('ся', 'сь')):
            tees_word += 'ся'
        parts.append(tees_word)
        
        if graph.tees.router:
            parts.append(graph.tees.router)
            
        if graph.receiver:
            receiver_form = self._decline(graph.receiver)
            parts.append(receiver_form)
            
        for co_mod in graph.co_mods:
            parts.append(self._decline(co_mod))
            
        return ' '.join(parts) + '.'
    
    def _is_plural(self, lemma: str) -> bool:
        if lemma.endswith(('ы', 'и')) and len(lemma) > 3:
            return True
        known_plural = {'стихи', 'волны', 'фрагменты', 'узлы', 'тайны', 'чувства'}
        if lemma in known_plural:
            return True
        return False
    
    def _decline(self, mod: Mod) -> str:
        lemma = mod.lemma
        state = mod.state
        
        # Именительный — как есть
        if state == ModeState.SOURCE:
            return lemma
        
        # Множественное число
        if self._is_plural(lemma):
            if lemma.endswith('ы'):
                stem = lemma[:-1]
            elif lemma.endswith('и'):
                stem = lemma[:-1]
            elif lemma.endswith('а'):
                stem = lemma[:-1]
            elif lemma.endswith('я'):
                stem = lemma[:-1]
            else:
                stem = lemma
            
            plural_endings = {
                ModeState.RECEIVER: '',
                ModeState.CO_ROUTER: 'ами',
                ModeState.BUFFER: 'ов' if lemma.endswith('ы') else 'ей',
                ModeState.TARGET: 'ам',
                ModeState.CONTEXT: 'ах',
            }
            if state in plural_endings:
                ending = plural_endings[state]
                if ending == '':
                    return lemma
                return stem + ending
            return lemma
        
        # Прилагательные на -ый/-ий
        if lemma.endswith('ый') or lemma.endswith('ий'):
            stem = lemma[:-2]
            adj_endings = {
                ModeState.RECEIVER: 'ого',
                ModeState.CO_ROUTER: 'ым',
                ModeState.BUFFER: 'ого',
                ModeState.TARGET: 'ому',
                ModeState.CONTEXT: 'ом',
            }
            if state in adj_endings:
                return stem + adj_endings[state]
            return lemma
            
        # Прилагательные на -ой
        elif lemma.endswith('ой'):
            stem = lemma[:-2]
            adj_endings = {
                ModeState.RECEIVER: 'ого',
                ModeState.CO_ROUTER: 'ым',
                ModeState.BUFFER: 'ого',
                ModeState.TARGET: 'ому',
                ModeState.CONTEXT: 'ом',
            }
            if state in adj_endings:
                return stem + adj_endings[state]
            return lemma
            
        # Женский род на -я: ВИНИТЕЛЬНЫЙ = -ю
        elif lemma.endswith('я'):
            stem = lemma[:-1]
            endings = {
                ModeState.RECEIVER: 'ю',    # ← душу, свободу? нет — для -я: землю, волю
                ModeState.CO_ROUTER: 'ей',
                ModeState.BUFFER: 'и',
                ModeState.TARGET: 'е',
                ModeState.CONTEXT: 'е',
            }
            if state in endings:
                return stem + endings[state]
            return lemma
            
        # Женский род на -а: ВИНИТЕЛЬНЫЙ = -у
        elif lemma.endswith('а'):
            stem = lemma[:-1]
            endings = {
                ModeState.RECEIVER: 'у',    # ← душу, природу, картину, деревню? нет, -а: воду, траву
                ModeState.CO_ROUTER: 'ой',
                ModeState.BUFFER: 'ы',
                ModeState.TARGET: 'е',
                ModeState.CONTEXT: 'е',
            }
            if state in endings:
                return stem + endings[state]
            return lemma
            
        # Средний род на -о/-е — вин = им
        elif lemma.endswith('о') or lemma.endswith('е'):
            stem = lemma[:-1]
            if lemma.endswith('о'):
                endings = {
                    ModeState.RECEIVER: 'о',
                    ModeState.CO_ROUTER: 'ом',
                    ModeState.BUFFER: 'а',
                    ModeState.TARGET: 'у',
                    ModeState.CONTEXT: 'е',
                }
            else:
                endings = {
                    ModeState.RECEIVER: 'е',
                    ModeState.CO_ROUTER: 'ем',
                    ModeState.BUFFER: 'я',
                    ModeState.TARGET: 'ю',
                    ModeState.CONTEXT: 'е',
                }
            if state in endings:
                return stem + endings[state]
            return lemma
            
        # Женский/мужской род на -ь — вин = им
        elif lemma.endswith('ь'):
            stem = lemma[:-1]
            endings = {
                ModeState.RECEIVER: 'ь',
                ModeState.CO_ROUTER: 'ью',
                ModeState.BUFFER: 'и',
                ModeState.TARGET: 'и',
                ModeState.CONTEXT: 'и',
            }
            if state in endings:
                ending = endings[state]
                if ending == 'ь':
                    return lemma
                return stem + ending
            return lemma
            
        # Мужской род на -й — вин = им (неодуш.)
        elif lemma.endswith('й'):
            stem = lemma[:-1]
            endings = {
                ModeState.RECEIVER: 'й',
                ModeState.CO_ROUTER: 'ем',
                ModeState.BUFFER: 'я',
                ModeState.TARGET: 'ю',
                ModeState.CONTEXT: 'е',
            }
            if state in endings:
                ending = endings[state]
                if ending == 'й':
                    return lemma
                return stem + ending
            return lemma
            
        # Мужской род на согласную — вин = им (неодуш.)
        else:
            if state == ModeState.RECEIVER:
                return lemma
            endings = {
                ModeState.CO_ROUTER: 'ом',
                ModeState.BUFFER: 'а',
                ModeState.TARGET: 'у',
                ModeState.CONTEXT: 'е',
            }
            if state in endings:
                return lemma + endings[state]
            return lemma


# ============================================================================
# ИНТЕГРАЦИЯ С ПОЛЕМ v9.0 (через clusters)
# ============================================================================

class TeesFieldIntegration:
    def __init__(self, field=None):
        self.field = field
        self.parser = TeesGrammarParser()
        self.assembler = TeesAssembler(self.parser)
        
    def load_from_field(self):
        if not self.field:
            return
        # Поле v9.0 хранит тексты в self.clusters с ключом 'original'
        if hasattr(self.field, 'clusters'):
            texts = [c['original'] for c in self.field.clusters]
            self.parser.process_corpus(texts)
        elif hasattr(self.field, 'fragments'):
            texts = [f['original'] for f in self.field.fragments]
            self.parser.process_corpus(texts)
        
    def furcate_tees(self, mod_a: str, mod_b: str) -> Optional[str]:
        graph = self.assembler.assemble_graph(mod_a, mod_b)
        if graph:
            return self.assembler.graph_to_text(graph)
        return None
    
    def get_tees_table(self) -> Dict:
        return {
            'stats': self.parser.get_stats(),
            'sample_graphs': [
                {
                    'source': g.source.lemma,
                    'tees': g.tees.lemma,
                    'receiver': g.receiver.lemma if g.receiver else None,
                    'text': g.raw_text,
                }
                for g in self.parser.graphs[:10]
            ]
        }


# ============================================================================
# ТЕСТЫ
# ============================================================================

def test_tees_grammar():
    print("=" * 60)
    print("TEES-ГРАММАТИКА v1.4 (жен.род вин.п.)")
    print("Текст как схема энергообмена")
    print("=" * 60)
    
    parser = TeesGrammarParser()
    
    test_corpus = [
        "Онегин едет в деревню. Деревня посещается Онегиным.",
        "Поэт пишет стихи. Стихи читаются публикой.",
        "Любовь волнует душу. Душа стремится к свободе.",
        "Мысль рождает слово. Слово передаёт смысл.",
        "Энергия течёт через канал. Канал направляет поток.",
        "Роутер выбирает маршрут. Маршрут ведёт к цели.",
        "Поле хранит фрагменты. Фрагменты связываются узлами.",
        "Температура растёт в зоне. Зона притягивает внимание.",
        "Учёный исследует природу. Природа раскрывает тайны.",
        "Художник создаёт картину. Картина вдохновляет зрителя.",
        "Музыка пробуждает чувства. Чувства наполняют сердце.",
        "Ветер гонит волны. Волны разбиваются о берег.",
    ]
    
    print("\n📚 Обработка корпуса...")
    parser.process_corpus(test_corpus)
    stats = parser.get_stats()
    print(f"   Разобрано предложений: {stats['total_parsed']}")
    print(f"   Уникальных модов: {stats['unique_mods']}")
    print(f"   Уникальных TEES: {stats['unique_tees']}")
    print(f"   TEES-графов: {stats['graphs_extracted']}")
    
    print("\n📊 ИЗВЛЕЧЁННЫЕ TEES-ГРАФЫ:")
    for i, g in enumerate(parser.graphs[:14]):
        recv = g.receiver.lemma if g.receiver else "—"
        recv_state = g.receiver.state.value if g.receiver else "—"
        router = f" [{g.tees.router}]" if g.tees.router else ""
        print(f"   {i+1}. {g.source.lemma}({g.source.state.value}) "
              f"—{g.tees.lemma}({g.tees.direction.value},{g.tees.intensity.value}){router}→ "
              f"{recv}({recv_state})")
    
    print("\n🔧 СБОРКА НОВЫХ TEES-КОНСТРУКЦИЙ:")
    assembler = TeesAssembler(parser)
    
    test_pairs = [
        ("любовь", "душа"),
        ("мысль", "слово"),
        ("энергия", "канал"),
        ("поле", "фрагменты"),
        ("роутер", "маршрут"),
        ("музыка", "сердце"),
        ("ветер", "волны"),
        ("учёный", "природа"),
        ("художник", "картина"),
        ("онегин", "деревня"),
        ("поэт", "стихи"),
    ]
    
    success = 0
    for mod_a, mod_b in test_pairs:
        graph = assembler.assemble_graph(mod_a, mod_b)
        if graph:
            text = assembler.graph_to_text(graph)
            print(f"   {mod_a} + {mod_b} → {text}")
            success += 1
        else:
            print(f"   {mod_a} + {mod_b} → не удалось собрать")
    
    print(f"\n   Успешно собрано: {success}/{len(test_pairs)}")
    
    return parser, assembler


def main():
    parser, assembler = test_tees_grammar()
    
    print("\n" + "=" * 60)
    print("ИНТЕГРАЦИЯ С ПОЛЕМ v9.0 (clean_field_v9.py)")
    print("=" * 60)
    
    field_module = None
    for fname in ['clean_field_v9_0', 'clean_field_v9.0', 'clean_field_v9']:
        try:
            field_module = __import__(fname)
            print(f"   Найдено: {fname}.py")
            break
        except ImportError:
            continue
    
    if field_module:
        FieldClass = None
        for attr_name in ['StructuralFieldV9', 'StructuralField', 'StructuralFieldV9_0']:
            if hasattr(field_module, attr_name):
                FieldClass = getattr(field_module, attr_name)
                print(f"   Класс поля: {attr_name}")
                break
        
        if FieldClass:
            field = FieldClass()
            test_texts = [
                "Онегин едет в деревню. Деревня посещается Онегиным.",
                "Поэт пишет стихи. Стихи читаются публикой.",
                "Любовь волнует душу. Душа стремится к свободе.",
                "Мысль рождает слово. Слово передаёт смысл.",
            ]
            for text in test_texts:
                field.add_text(text)
                
            integration = TeesFieldIntegration(field)
            integration.load_from_field()
            
            print(f"   Загружено кластеров: {len(field.clusters)}")
            print(f"   Разобрано TEES-графов: {integration.parser.total_parsed}")
            
            print("\n🔧 TEES-ФУРКАЦИЯ ИЗ ПОЛЯ:")
            hot_mods = ["любовь", "душа", "свобода", "мысль"]
            for i in range(len(hot_mods) - 1):
                result = integration.furcate_tees(hot_mods[i], hot_mods[i+1])
                print(f"   {hot_mods[i]} + {hot_mods[i+1]} → {result}")
        else:
            print("   Не найден класс поля в модуле")
    else:
        print("   Поле v9.0 не найдено.")


if __name__ == "__main__":
    main()