#!/usr/bin/env python3
"""
run_furcations.py — Ночной запуск фуркаций на готовом графе
Оптимизировано: Furcator встроен, не зависит от импорта из v5.6.
"""
import json
import sys
import time
import random
import gc
import os
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter
from typing import List, Dict, Optional, Set
from itertools import combinations

# Минимальный импорт из v5.6 — только то, что точно есть
from core.tees_knowledge_engine_v5_6_fixed import (
    VMMPGraph, VMMPChecker, PipelineConfig,
    fast_16bit_hash, tees_shift, compute_topological_charge
)


# ============================================================================
# Furcator — автономное определение
# ============================================================================

class Furcator:
    """
    Генерирует новые связи (фуркации) на основе существующих:
    - Если A → TEES → B и B → TEES → C, то A → TEES → C (цепная дедукция)
    - Если A → TEES → B и C → TEES → B, то A ← TEES → C (общий приёмник)
    - Если A → TEES → B и A → TEES → C, то A → TEES → B⊕C (расщепление)
    """
    
    def __init__(self, graph: VMMPGraph, config: PipelineConfig, checker: VMMPChecker):
        self.graph = graph
        self.config = config
        self.checker = checker
        self.furcations: List[Dict] = []
        
        # Индексы для быстрого поиска
        self._source_index: Dict[str, Set[str]] = defaultdict(set)  # source -> {edge_id}
        self._tees_index: Dict[str, Set[str]] = defaultdict(set)   # tees -> {edge_id}
        self._receiver_index: Dict[str, Set[str]] = defaultdict(set)  # receiver -> {edge_id}
        
        self._build_indices()
    
    def _build_indices(self):
        """Строит индексы для быстрого поиска."""
        for edge in self.graph.edges:
            eid = edge['id']
            self._source_index[edge['source']].add(eid)
            self._tees_index[edge['tees']].add(eid)
            self._receiver_index[edge['receiver']].add(eid)
        
        print(f"   Индексы построены: {len(self._source_index)} источников, "
              f"{len(self._tees_index)} связок, {len(self._receiver_index)} приёмников")
    
    def _edge_by_id(self, eid: str) -> Optional[Dict]:
        """Быстрый поиск ребра по ID через индекс."""
        parts = eid.split('|')
        if len(parts) != 3:
            return None
        bucket_idx = fast_16bit_hash(eid) % 65536
        return self.graph._find_in_bucket(bucket_idx, parts[0], parts[1], parts[2])
    
    def _generate_chain_furcations(self, max_per_tees: int = 100) -> List[Dict]:
        """Цепные дедукции: A→T→B и B→T→C ⇒ A→T→C."""
        candidates = []
        
        for tees_word in list(self._tees_index.keys())[:5000]:  # Ограничиваем для RAM
            edge_ids = list(self._tees_index[tees_word])[:50]
            
            for eid1, eid2 in combinations(edge_ids, 2):
                edge1 = self._edge_by_id(eid1)
                edge2 = self._edge_by_id(eid2)
                if not edge1 or not edge2:
                    continue
                
                # A→T→B и B→T→C
                if edge1['receiver'] == edge2['source']:
                    new_source = edge1['source']
                    new_receiver = edge2['receiver']
                    
                    # Не создаём петли
                    if new_source == new_receiver:
                        continue
                    
                    pair_id = f"{new_source}|{tees_word}|{new_receiver}"
                    
                    if self.graph._find_in_bucket(
                        fast_16bit_hash(pair_id) % 65536,
                        new_source, tees_word, new_receiver
                    ):
                        continue  # Уже существует
                    
                    candidates.append({
                        'source': new_source,
                        'tees': tees_word,
                        'receiver': new_receiver,
                        'type': 'chain',
                        'parents': [eid1, eid2]
                    })
        
        return candidates
    
    def _generate_convergent_furcations(self, max_per_receiver: int = 50) -> List[Dict]:
        """Конвергентные: A→T1→C и B→T2→C ⇒ A→T_synthetic→B."""
        candidates = []
        
        for receiver in list(self._receiver_index.keys())[:5000]:  # Ограничиваем
            edge_ids = list(self._receiver_index[receiver])[:max_per_receiver]
            if len(edge_ids) < 2:
                continue
            
            source_edges = defaultdict(list)
            for eid in edge_ids:
                edge = self._edge_by_id(eid)
                if edge:
                    source_edges[edge['source']].append(edge)
            
            for src1, src2 in combinations(list(source_edges.keys())[:10], 2):
                edges1 = source_edges[src1]
                edges2 = source_edges[src2]
                
                # Берём самый частый tees
                tees1 = Counter(e['tees'] for e in edges1).most_common(1)
                tees2 = Counter(e['tees'] for e in edges2).most_common(1)
                
                if tees1 and tees2:
                    synthetic_tees = tees1[0][0] if tees1[0][1] >= tees2[0][1] else tees2[0][0]
                    
                    candidates.append({
                        'source': src1,
                        'tees': synthetic_tees,
                        'receiver': src2,
                        'type': 'convergent',
                        'parents': [edges1[0]['id'], edges2[0]['id']]
                    })
        
        return candidates
    
    def generate_and_apply(self) -> int:
        """
        Генерирует фуркации и применяет лучшие.
        Возвращает количество применённых.
        """
        print("\n🔍 Генерация цепных фуркаций...")
        chain = self._generate_chain_furcations()
        print(f"   Найдено цепных: {len(chain)}")
        
        print("🔍 Генерация конвергентных фуркаций...")
        convergent = self._generate_convergent_furcations()
        print(f"   Найдено конвергентных: {len(convergent)}")
        
        all_candidates = chain + convergent
        random.shuffle(all_candidates)
        
        # Ограничиваем количество для проверки (экономия RAM)
        max_to_check = min(len(all_candidates), 10000)
        candidates_to_check = all_candidates[:max_to_check]
        
        print(f"\n🧪 Проверяем {len(candidates_to_check)} кандидатов через ВММП...")
        
        applied = 0
        batch_size = 100
        
        for i in range(0, len(candidates_to_check), batch_size):
            batch = candidates_to_check[i:i+batch_size]
            triple_tuples = [(c['source'], c['tees'], c['receiver']) for c in batch]
            
            results = self.checker.check_triples_batch(triple_tuples)
            
            for candidate, result in zip(batch, results):
                candidate['score'] = result['score']
                candidate['vmmp_compliant'] = result['vmmp_compliant']
                candidate['src_charge'] = result.get('src_charge', 0)
                candidate['tees_charge'] = result.get('tees_charge', 0)
                candidate['rec_charge'] = result.get('rec_charge', 0)
                candidate['shift_src'] = result.get('shift_src', 0)
                candidate['shift_rec'] = result.get('shift_rec', 0)
                
                self.furcations.append(candidate)
                
                if result['vmmp_compliant']:
                    self.graph.add_edge(
                        candidate['source'],
                        candidate['tees'],
                        candidate['receiver'],
                        result,
                        text_source=f"furcation:{candidate['type']}"
                    )
                    applied += 1
            
            # Прогресс
            if (i // batch_size) % 5 == 0:
                pct = min(100, (i + batch_size) / len(candidates_to_check) * 100)
                print(f"\r   Прогресс проверки: {pct:.0f}% | Применено: {applied}", end='')
            
            # Очистка каждые 500 кандидатов
            if (i // batch_size) % 5 == 0:
                gc.collect()
        
        print(f"\n   ✅ Применено: {applied}/{len(candidates_to_check)}")
        return applied


# ============================================================================
# Сохранение результатов
# ============================================================================

def save_furcation_log(furcations: List[Dict], graph_path: str, elapsed: float, 
                       applied: int, awakened: int, output_dir: Path):
    """Сохраняет детальный лог фуркаций в отдельный JSON."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = output_dir / f"furcations_log_{timestamp}.json"
    
    # Сортируем по score
    sorted_furcations = sorted(furcations, key=lambda x: x.get('score', 0), reverse=True)
    
    # Разделяем на применённые и отвергнутые
    applied_list = [f for f in sorted_furcations if f.get('vmmp_compliant')]
    rejected_list = [f for f in sorted_furcations if not f.get('vmmp_compliant')]
    
    # Статистика по типам
    type_stats = Counter(f['type'] for f in sorted_furcations)
    type_applied = Counter(f['type'] for f in applied_list)
    
    # Топ-связки (tees)
    top_tees = Counter(f['tees'] for f in applied_list).most_common(20)
    
    # Топ-источники
    top_sources = Counter(f['source'] for f in applied_list).most_common(10)
    
    # Топ-приёмники
    top_receivers = Counter(f['receiver'] for f in applied_list).most_common(10)
    
    log = {
        'meta': {
            'timestamp': datetime.now().isoformat(),
            'source_graph': graph_path,
            'total_generated': len(sorted_furcations),
            'total_applied': applied,
            'total_rejected': len(sorted_furcations) - applied,
            'elapsed_seconds': round(elapsed, 1),
            'awakened_edges': awakened,
            'compliance_rate': round(applied / len(sorted_furcations) * 100, 1) if sorted_furcations else 0
        },
        'statistics': {
            'by_type': dict(type_stats),
            'by_type_applied': dict(type_applied),
            'top_tees': [{'word': w, 'count': c} for w, c in top_tees],
            'top_sources': [{'word': w, 'count': c} for w, c in top_sources],
            'top_receivers': [{'word': w, 'count': c} for w, c in top_receivers],
            'avg_score_applied': round(
                sum(f.get('score', 0) for f in applied_list) / len(applied_list), 4
            ) if applied_list else 0,
            'avg_score_rejected': round(
                sum(f.get('score', 0) for f in rejected_list) / len(rejected_list), 4
            ) if rejected_list else 0
        },
        'applied_furcations': [
            {
                'source': f['source'],
                'tees': f['tees'],
                'receiver': f['receiver'],
                'score': round(f.get('score', 0), 4),
                'type': f['type'],
                'parents': f.get('parents', [])[:2],
                'charges': {
                    'src': round(f.get('src_charge', 0), 4),
                    'tees': round(f.get('tees_charge', 0), 4),
                    'rec': round(f.get('rec_charge', 0), 4)
                }
            }
            for f in applied_list[:500]  # Топ-500 применённых
        ],
        'rejected_furcations': [
            {
                'source': f['source'],
                'tees': f['tees'],
                'receiver': f['receiver'],
                'score': round(f.get('score', 0), 4),
                'type': f['type'],
                'reason': 'low_score' if f.get('score', 0) < 0.5 else 'charge_imbalance'
            }
            for f in rejected_list[:100]  # Топ-100 отвергнутых
        ]
    }
    
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(log, f, ensure_ascii=False, indent=2)
    
    print(f"\n📋 Лог фуркаций сохранён: {log_path}")
    print(f"   Применённых в логе: {len(applied_list[:500])}")
    print(f"   Отвергнутых в логе: {len(rejected_list[:100])}")
    
    return log_path


def save_updated_graph(graph: VMMPGraph, output_dir: Path):
    """Сохраняет обновлённый граф с фуркациями."""
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    graph_path = output_dir / f"graph_vmmp_furcated_{timestamp}.json"
    
    stats = graph.get_statistics()
    
    def convert(obj):
        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        elif isinstance(obj, dict):
            return {k: convert(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [convert(i) for i in obj]
        return str(obj)
    
    data = {
        'meta': {
            'version': '5.6-furcated',
            'created': datetime.now().isoformat(),
            'description': 'Граф после применения фуркаций'
        },
        'stats': stats,
        'active_edges': [
            {
                'source': e['source'],
                'tees': e['tees'],
                'receiver': e['receiver'],
                'weight': float(e['weight']),
                'age': e.get('age', 0),
                'vmmp_compliant': e['vmmp_compliant']
            }
            for e in graph.edges
        ],
        'dormant_edges': [
            {
                'source': e['source'],
                'tees': e['tees'],
                'receiver': e['receiver'],
                'weight': float(e['weight']),
                'age': e.get('age', 0)
            }
            for e in graph.dormant_edges
        ]
    }
    
    data = convert(data)
    
    with open(graph_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Размер файла
    size_mb = os.path.getsize(graph_path) / (1024 * 1024)
    
    print(f"💾 Обновлённый граф сохранён: {graph_path}")
    print(f"   Размер: {size_mb:.1f} MB")
    print(f"   Связей: {stats['active_edges']} (истина: {stats['compliant_edges']}, шум: {stats['noise_edges']})")
    
    return graph_path


# ============================================================================
# Основной код
# ============================================================================

def run_furcations_on_graph(graph_path: str):
    print("=" * 70)
    print("🌙 НОЧНЫЕ ФУРКАЦИИ")
    print(f"   {datetime.now():%Y-%m-%d %H:%M:%S}")
    print("=" * 70)
    
    # 1. Загружаем граф
    print(f"\n📂 Загружаем граф: {graph_path}")
    try:
        with open(graph_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Файл не найден: {graph_path}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка JSON: {e}")
        return
    
    meta = data.get('meta', {})
    print(f"   Версия: {meta.get('version', 'неизвестно')}")
    print(f"   Создан: {meta.get('created', 'неизвестно')}")
    
    # 2. Восстанавливаем граф
    config = PipelineConfig()
    graph = VMMPGraph(config)
    
    active_count = 0
    for edge_data in data.get('active_edges', []):
        edge_id = f"{edge_data['source']}|{edge_data['tees']}|{edge_data['receiver']}"
        bucket_idx = graph._bucket_key(
            edge_data['source'], edge_data['tees'], edge_data['receiver']
        )
        
        edge_obj = {
            'id': edge_id,
            'source': edge_data['source'],
            'tees': edge_data['tees'],
            'receiver': edge_data['receiver'],
            'weight': edge_data['weight'],
            'age': edge_data.get('age', 0),
            'vmmp_compliant': edge_data.get('vmmp_compliant', False),
            'charges': {'src': 0.0, 'tees': 0.0, 'rec': 0.0}
        }
        
        graph._buckets[bucket_idx].append(edge_obj)
        graph.edges.append(edge_obj)
        active_count += 1
    
    dormant_count = 0
    for edge_data in data.get('dormant_edges', []):
        graph.dormant_edges.append({
            'id': f"{edge_data['source']}|{edge_data['tees']}|{edge_data['receiver']}",
            'source': edge_data['source'],
            'tees': edge_data['tees'],
            'receiver': edge_data['receiver'],
            'weight': edge_data['weight'],
            'age': edge_data.get('age', 25),
            'vmmp_compliant': False
        })
        dormant_count += 1
    
    print(f"✅ Загружено: {active_count} активных, {dormant_count} в архиве")
    
    # Проверяем целостность
    if active_count == 0:
        print("❌ Нет активных связей — нечего фуркировать")
        return
    
    # 3. Пробуждаем дормантные связи
    context_words = ['quantum', 'energy', 'consciousness', 'Гаусс', 'память',
                     'система', 'структура', 'функция', 'метод', 'модель',
                     'данные', 'связь', 'процесс', 'анализ']
    
    awakened = 0
    to_awaken = []
    
    for edge in graph.dormant_edges[:]:
        for word in context_words:
            if (word.lower() in edge['source'].lower() or 
                word.lower() in edge['tees'].lower() or 
                word.lower() in edge['receiver'].lower()):
                to_awaken.append(edge)
                break
    
    for edge in to_awaken:
        edge['age'] = 0
        edge['vmmp_compliant'] = False
        graph.dormant_edges.remove(edge)
        graph.edges.append(edge)
        bucket_idx = graph._bucket_key(edge['source'], edge['tees'], edge['receiver'])
        graph._buckets[bucket_idx].append(edge)
        awakened += 1
    
    print(f"⚡ Пробуждено из архива по контексту: {awakened}")
    
    # 4. Запускаем фуркации
    checker = VMMPChecker(config)
    furcator = Furcator(graph, config, checker)
    
    print(f"\n🔄 Запуск фуркаций...")
    start = time.time()
    added = furcator.generate_and_apply()
    elapsed = time.time() - start
    
    # 5. Сохраняем лог фуркаций
    output_dir = Path("./output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    log_path = save_furcation_log(
        furcator.furcations, graph_path, elapsed, added, awakened, output_dir
    )
    
    # 6. Сохраняем обновлённый граф
    graph_path_new = save_updated_graph(graph, output_dir)
    
    # 7. Финальная статистика
    stats = graph.get_statistics()
    
    print(f"\n{'='*70}")
    print(f"📊 ИТОГИ ФУРКАЦИЙ")
    print(f"{'='*70}")
    print(f"⏱️  Время:            {elapsed:.1f} сек")
    print(f"🔗 Сгенерировано:    {len(furcator.furcations)}")
    print(f"✅ Применено:        {added}")
    print(f"❌ Отвергнуто:      {len(furcator.furcations) - added}")
    print(f"⚡ Пробуждено:       {awakened}")
    print(f"📈 Активных связей:  {stats['active_edges']} (было {active_count})")
    print(f"💚 Истинных:         {stats['compliant_edges']}")
    print(f"🟡 Шумовых:          {stats['noise_edges']}")
    print(f"😴 В архиве:         {stats['dormant_edges']}")
    print(f"")
    print(f"📋 Лог фуркаций:     {log_path}")
    print(f"💾 Граф:             {graph_path_new}")
    print(f"\n🌙 Спокойной ночи!")
    print(f"{'='*70}")

if __name__ == "__main__":
    graph_file = sys.argv[1] if len(sys.argv) > 1 else "output/graph_vmmp_20260714_233840.json"
    run_furcations_on_graph(graph_file)
