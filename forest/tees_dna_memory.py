# tees_dna_memory.py
# 🧬 TEES ДНК-память — эволюционная память узла

import hashlib
import time
import json
import numpy as np
from typing import Dict, List, Optional, Any


class DNAMemory:
    """
    🧬 ДНК-память узла.
    Хранит не данные, а их ЭВОЛЮЦИОННЫЕ ОТПЕЧАТКИ.
    
    Принципы:
    - Наследственность — каждый отпечаток связан с родителем
    - Мутации — отпечатки могут изменяться
    - Селекция — успешные отпечатки выживают
    - Гомеостаз — память стремится к стабильности
    """
    
    def __init__(self, node_id: str, max_genes: int = 100):
        self.node_id = node_id
        self.max_genes = max_genes
        
        # Геном — словарь генов
        self.genome: Dict[str, Dict] = {}
        
        # История мутаций
        self.mutation_history: List[Dict] = []
        
        # Поколение
        self.generation = 0
        
        # Счётчик застоя
        self._stagnation_counter = 0
        
        # Статистика
        self.stats = {
            'total_mutations': 0,
            'successful_mutations': 0,
            'failed_mutations': 0,
            'exchanges': 0
        }
    
    def create_gene(self, data: Any, parent_id: Optional[str] = None) -> str:
        """
        Создаёт новый ген из данных.
        Возвращает ID гена.
        """
        # Генерируем ID
        gene_id = self._generate_gene_id(data)
        
        # Проверяем на дубликат
        if gene_id in self.genome and self.genome[gene_id].get('alive', True):
            # Обновляем фитнес существующего гена
            self.genome[gene_id]['fitness'] = min(2.0, self.genome[gene_id]['fitness'] + 0.1)
            return gene_id
        
        # Создаём ген
        gene = {
            'id': gene_id,
            'data': data,
            'parent': parent_id,
            'born': time.time(),
            'generation': self.generation,
            'fitness': 1.0,
            'mutations': 0,
            'alive': True
        }
        
        # Сохраняем в геном
        self.genome[gene_id] = gene
        
        # Ограничиваем размер
        self._prune_genome()
        
        return gene_id
    
    def _generate_gene_id(self, data: Any) -> str:
        """Генерация ID гена на основе данных."""
        try:
            data_str = json.dumps(data, sort_keys=True, default=str)
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
        except (TypeError, ValueError):
            data_str = str(data)
            return hashlib.sha256(data_str.encode()).hexdigest()[:16]
    
    def mutate_gene(self, gene_id: str, mutation_rate: float = 0.1) -> bool:
        """
        Мутирует ген.
        Возвращает True, если мутация успешна.
        """
        if gene_id not in self.genome:
            return False
        
        if not self.genome[gene_id].get('alive', True):
            return False
        
        # Валидация параметров
        mutation_rate = max(0.0, min(1.0, mutation_rate))
        if mutation_rate == 0.0:
            return False
        
        gene = self.genome[gene_id]
        
        # Мутация данных
        mutated_data = self._mutate_data(gene['data'], mutation_rate)
        
        # Создаём новый ген с мутацией
        new_gene_id = self._generate_gene_id(mutated_data)
        
        if new_gene_id == gene_id or new_gene_id in self.genome:
            # Мутация не изменила данные или дубликат
            self.stats['failed_mutations'] += 1
            return False
        
        # Новый ген — потомок
        new_gene = {
            'id': new_gene_id,
            'data': mutated_data,
            'parent': gene_id,
            'born': time.time(),
            'generation': self.generation + 1,
            'fitness': max(0.1, gene['fitness'] * 0.9),
            'mutations': gene['mutations'] + 1,
            'alive': True
        }
        
        # Сохраняем
        self.genome[new_gene_id] = new_gene
        
        # Записываем в историю
        self.mutation_history.append({
            'time': time.time(),
            'parent': gene_id,
            'child': new_gene_id,
            'success': True
        })
        if len(self.mutation_history) > 1000:
            self.mutation_history = self.mutation_history[-500:]
        
        self.stats['total_mutations'] += 1
        self.stats['successful_mutations'] += 1
        
        self._prune_genome()
        
        return True
    
    def _mutate_data(self, data: Any, rate: float) -> Any:
        """Мутация данных."""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if np.random.random() < rate:
                    result[key] = self._mutate_value(value)
                else:
                    result[key] = value
            return result
        
        elif isinstance(data, list):
            result = []
            for item in data:
                if np.random.random() < rate:
                    result.append(self._mutate_value(item))
                else:
                    result.append(item)
            return result
        
        else:
            return data
    
    def _mutate_value(self, value: Any) -> Any:
        """Мутация одного значения."""
        if isinstance(value, (int, float)):
            return value * (1 + np.random.uniform(-0.2, 0.2))
        elif isinstance(value, str):
            if len(value) > 2 and np.random.random() < 0.5:
                pos = np.random.randint(0, len(value) - 1)
                return value[:pos] + value[pos+1:pos+2] + value[pos:pos+1] + value[pos+2:]
            return value + "_m" if len(value) < 20 else value
        elif isinstance(value, bool):
            return not value
        else:
            return value
    
    def exchange_genes(self, other_memory: 'DNAMemory', count: int = 1) -> int:
        """
        Обмен генами с другим узлом.
        Возвращает количество обменянных генов.
        """
        if not other_memory.genome or self is other_memory:
            return 0
        
        other_alive = [g for g in other_memory.genome.values() if g.get('alive', True)]
        if not other_alive:
            return 0
        
        other_genes = sorted(
            other_alive,
            key=lambda g: g['fitness'],
            reverse=True
        )[:count]
        
        exchanged = 0
        for other_gene in other_genes:
            if other_gene['id'] not in self.genome:
                new_data = self._mutate_data(other_gene['data'], 0.05)
                new_id = self._generate_gene_id(new_data)
                
                if new_id not in self.genome:
                    self.genome[new_id] = {
                        'id': new_id,
                        'data': new_data,
                        'parent': other_gene['id'],
                        'born': time.time(),
                        'generation': self.generation + 1,
                        'fitness': other_gene['fitness'] * 0.95,
                        'mutations': other_gene['mutations'],
                        'alive': True
                    }
                    
                    exchanged += 1
                    self.stats['exchanges'] += 1
        
        self._prune_genome()
        return exchanged
    
    def select_best_genes(self, count: int = 10) -> List[Dict]:
        """Отбор лучших генов (селекция)."""
        alive_genes = [g for g in self.genome.values() if g.get('alive', True)]
        sorted_genes = sorted(alive_genes, key=lambda g: g['fitness'], reverse=True)
        return sorted_genes[:count]
    
    def get_best_gene(self) -> Optional[Dict]:
        """Возвращает лучший живой ген."""
        alive = [g for g in self.genome.values() if g.get('alive', True)]
        if not alive:
            return None
        return max(alive, key=lambda g: g['fitness'])
    
    def kill_weak_genes(self, threshold: float = 0.3) -> int:
        """Удаление слабых генов (естественный отбор)."""
        killed = 0
        
        for gene_id, gene in list(self.genome.items()):
            if gene.get('alive', True) and gene['fitness'] < threshold:
                gene['alive'] = False
                killed += 1
                self.stats['failed_mutations'] += 1
        
        self.genome = {
            gid: g for gid, g in self.genome.items() if g.get('alive', True)
        }
        
        return killed
    
    def next_generation(self):
        """Переход к следующему поколению."""
        self.generation += 1
        self.kill_weak_genes(threshold=0.2)
        self._prune_genome()
        return self.generation

    def get_mutation_rate(self, coherence: float) -> float:
        """
        Определяет скорость мутаций в зависимости от состояния.
        Гармония → нет мутаций. Кризис → быстрые мутации!
        """
        if coherence >= 0.9999:
            return 0.0  # Нирвана — не мутируем!
        elif coherence >= 0.95:
            return 0.0  # Норма — не мутируем!
        elif coherence >= 0.85:
            return 0.05  # Стресс — немного мутаций
        elif coherence >= 0.70:
            return 0.15  # Критично — больше мутаций
        else:
            return 0.30  # Катастрофа — максимальные мутации!
    
    def adaptive_mutate(self, coherence: float) -> bool:
        """
        Адаптивная мутация — только при необходимости!
        """
        mutation_rate = self.get_mutation_rate(coherence)
        
        if mutation_rate == 0.0:
            return False  # В гармонии — не мутируем!
        
        best_gene = self.get_best_gene()
        if best_gene:
            return self.mutate_gene(best_gene['id'], mutation_rate)
        
        return False    
    
    def auto_evolve(self, coherence: float = 1.0, stagnation_threshold: int = 5):
        """
        Адаптивная эволюция.
        Мутации включаются только при стрессе или застое!
        """
        # Проверяем адаптивную мутацию
        mutation_rate = self.get_mutation_rate(coherence)
        
        if mutation_rate > 0.0:
            # Стресс — мутируем активно!
            best_gene = self.get_best_gene()
            if best_gene:
                self.mutate_gene(best_gene['id'], mutation_rate)
                self._stagnation_counter = 0
                return True
        
        # Если гармония — только при застое
        if len(self.genome) > 0:
            self._stagnation_counter += 1
            
            if self._stagnation_counter > stagnation_threshold:
                # Застой — одна мягкая мутация
                best_gene = self.get_best_gene()
                if best_gene:
                    self.mutate_gene(best_gene['id'], mutation_rate=0.01)
                self._stagnation_counter = 0
                return True
        else:
            self._stagnation_counter = 0
        
        return False
    
    def similarity(self, other: 'DNAMemory') -> float:
        """Степень генетического сходства двух узлов."""
        if not self.genome or not other.genome:
            return 0.0
        
        my_ids = set(self.genome.keys())
        other_ids = set(other.genome.keys())
        
        intersection = my_ids & other_ids
        union = my_ids | other_ids
        
        return len(intersection) / len(union) if union else 0.0
    
    def _prune_genome(self):
        """Ограничение размера генома."""
        if len(self.genome) <= self.max_genes:
            return
        
        alive_genes = {gid: g for gid, g in self.genome.items() if g.get('alive', True)}
        if len(alive_genes) > self.max_genes:
            best_genes = sorted(
                alive_genes.values(),
                key=lambda g: g['fitness'],
                reverse=True
            )[:self.max_genes]
            best_ids = {g['id'] for g in best_genes}
            self.genome = {gid: g for gid, g in alive_genes.items() if gid in best_ids}
        else:
            self.genome = alive_genes
    
    def get_dna_fingerprint(self) -> str:
        """
        Получение ДНК-отпечатка всего генома.
        Это "генетический паспорт" узла!
        """
        gene_ids = sorted(self.genome.keys())
        combined = ''.join(gene_ids)
        return hashlib.sha256(combined.encode()).hexdigest()
    
    def get_genome_stats(self) -> Dict:
        """Статистика генома."""
        return {
            'node_id': self.node_id,
            'genes': len(self.genome),
            'generation': self.generation,
            'fingerprint': self.get_dna_fingerprint()[:16],
            **self.stats
        }