# tees_economy.py
# 💎 Монистическая экономика TEES — метаболизм организма!

import time
import math
import threading
import hashlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field


@dataclass
class Task:
    """📦 Задача для фрактала."""
    id: str
    type: str = 'generic'
    priority: int = 1
    data: Any = None
    created_at: float = field(default_factory=time.time)
    status: str = 'pending'


class SmartScar:
    """🧠 Умный рубец — память об ошибке, не мешает, а учит!"""
    def __init__(self, error_type: str, cost: float, lesson: str):
        self.error_type = error_type
        self.cost = cost
        self.lesson = lesson
        self.healed = False
        self.wisdom = 0.0
    
    def heal(self) -> float:
        """Рубец заживает в мудрость!"""
        self.healed = True
        self.wisdom = self.cost * 0.1
        return self.wisdom


class ErrorAccounting:
    """Учёт ошибок с умными рубцами."""
    MAX_SCARS = 100
    
    def __init__(self):
        self.error_history = []
        self.smart_scars = []
        self.total_wisdom = 0.0
    
    def record_error(self, node_id: str, error_type: str, cost: float, lesson: str):
        """Запись ошибки."""
        self.error_history.append({
            'node': node_id, 'type': error_type,
            'cost': cost, 'lesson': lesson, 'time': time.time()
        })
        
        scar = SmartScar(error_type, cost, lesson)
        self.smart_scars.append(scar)
        
        if len(self.smart_scars) > self.MAX_SCARS:
            self._convert_scars_to_wisdom()
    
    def _convert_scars_to_wisdom(self):
        """Рубцы → мудрость!"""
        old_scars = self.smart_scars[:50]
        wisdom_gain = sum(scar.heal() for scar in old_scars)
        self.total_wisdom += wisdom_gain
        self.smart_scars = self.smart_scars[50:]
        print(f"  🧠 Рубцы → мудрость: +{wisdom_gain:.1f}")


class ResourceIntegrity:
    """🛡️ Мгновенная проверка: баланс = работа × цена!"""
    def __init__(self):
        self.valid_actions = {
            'solve_task', 'establish_connection', 'store_data',
            'heal_node', 'optimize', 'form_cluster'
        }
        self.economy = None
    
    def validate_action(self, node, action: str) -> bool:
        """Мгновенная проверка аномалий!"""
        node_id = getattr(node, 'id', str(id(node)))
        
        if action not in self.valid_actions:
            print(f"  ⛔ Неизвестное действие: {action}")
            return False
        
        expected = self._calculate_expected_balance(node)
        actual = self.economy.active_nodes.get(node_id, 0)
        
        if actual > expected * 1.01:
            print(f"  ⚡ АНОМАЛИЯ! {node_id}: {actual:.1f} > {expected:.1f}")
            print(f"  🔥 Ресурс из ниоткуда! Отключение!")
            return False
        
        return True
    
    def _calculate_expected_balance(self, node) -> float:
        """Ожидаемый баланс = сумма(работа × цена). Адаптивно!"""
        expected = 0.0
        rewards = self.economy.base_rewards
        
        # Пробуем разные варианты (маяк, фрактал, тестовый узел!)
        metrics = getattr(node, 'metrics', {})
        if isinstance(metrics, dict):
            tasks_done = metrics.get('tasks_completed', 0)
        else:
            tasks_done = getattr(node, 'blocks_mined', 0)  # Маяк!
        
        expected += tasks_done * rewards['solve_task']
        expected += len(getattr(node, 'neighbors', [])) * rewards['establish_connection']
        expected += getattr(node, 'storage_used', 0) * rewards['store_data']
        expected += getattr(node, 'ores_shared', 0) * rewards['heal_node'] * 0.1
        
        return expected


class SmartContract:
    """📜 Контракт взаимопомощи — очередь, а не накопление!"""
    def __init__(self, contract_id, helper, receiver, task_type, aid_amount):
        self.id = contract_id
        self.helper = helper
        self.receiver = receiver
        self.task_type = task_type
        self.aid_amount = aid_amount
        self.status = 'pending'
        self.created_at = time.time()
    
    def activate(self, economy) -> bool:
        if economy.active_nodes.get(self.helper, 0) >= self.aid_amount:
            self.status = 'active'
            return True
        return False
    
    def execute(self, economy, task) -> bool:
        if self.status == 'active':
            if economy.transfer(self.helper, self.receiver, self.aid_amount):
                self.status = 'completed'
                print(f"  📜 {self.helper} → {self.receiver}: {self.aid_amount:.1f} на {task.id}")
                return True
        return False
    
    def settle(self, economy, task_result) -> bool:
        if self.status == 'completed':
            # Возврат + бонус ЗА КАЧЕСТВО!
            quality = task_result.get('quality', 0.5)
            bonus = 1.0 + quality * 0.2  # До 20% бонуса!
            settlement = self.aid_amount * bonus
            
            if economy.transfer(self.receiver, self.helper, settlement):
                self.status = 'settled'
                print(f"  ✅ Расчёт: {settlement:.1f} → {self.helper} (качество {quality:.2f})")
                return True
        return False


class ContractRateLimiter:
    """🚫 Защита от спама контрактами."""
    def __init__(self):
        self.contract_history = {}
        self.max_contracts = 3
        self.time_window = 60.0
        self.suspicious_nodes = set()
        self.economy = None
    
    def can_create_contract(self, node_id) -> bool:
        current_time = time.time()
        
        if node_id in self.contract_history:
            self.contract_history[node_id] = [
                ts for ts in self.contract_history[node_id]
                if current_time - ts < self.time_window
            ]
        
        recent = self.contract_history.get(node_id, [])
        if len(recent) >= self.max_contracts:
            print(f"  🚫 Спам! {node_id} превысил лимит!")
            self.suspicious_nodes.add(node_id)
            
            # Штраф жирком!
            penalty = self.economy.base_rewards['solve_task'] * 0.5
            if self.economy.active_nodes.get(node_id, 0) >= penalty:
                self.economy.active_nodes[node_id] -= penalty
                self.economy.fat_reserves += penalty
                print(f"  💸 Штраф {penalty:.1f} → жирок")
            
            return False
        
        if node_id not in self.contract_history:
            self.contract_history[node_id] = []
        self.contract_history[node_id].append(current_time)
        return True


class TEESEconomy:
    """💎 Монистическая экономика — живой организм!"""
    def __init__(self):
        # Органы
        self.active_nodes = {}
        self.fat_reserves = 0.0
        self.bone_structure = 0.0
        self.blood_sugar = 0.0
        self.total_energy = 0.0
        self.wisdom = 0.0
        self.education = 0.0       # 🎓 Образование
        self.social_fund = 0.0     # 🏥 Социалка
        self.science = 0.0         # 🔬 Наука
        self.global_efficiency = 1.0  # Множитель эффективности!
        
        # Калорийность
        self.base_rewards = {
            'solve_task': 10,
            'establish_connection': 5,
            'store_data': 3,
            'heal_node': 15,
            'optimize': 8,
            'form_cluster': 20
        }
        
        self.metabolic_rates = {
            'muscle_growth': 0.70,      # Мышцы — работа
            'fat_storage': 0.10,        # Жирок — стабфонд
            'bone_building': 0.05,      # Кости — инфраструктура
            'blood_circulation': 0.03,  # Кровь — оборот
            'education': 0.05,          # 🎓 Образование!
            'social_support': 0.04,     # 🏥 Социалка!
            'science': 0.03             # 🔬 Наука!
        }
        
        # Гомеостаз
        self.SET_POINTS = {
            'fat_percentage': 0.15,
            'muscle_percentage': 0.75,
            'bone_percentage': 0.07,
            'blood_percentage': 0.03
        }
        
        # Защита
        self.integrity = ResourceIntegrity()
        self.integrity.economy = self
        self.contract_limiter = ContractRateLimiter()
        self.contract_limiter.economy = self
        self.error_accounting = ErrorAccounting()
        
        # Контракты
        self.contracts = []
        self.contract_queue = {}
        self.disconnected_nodes = {}
        
        self.lock = threading.Lock()

        # 🌀 Фрактальная память (подключится позже!)
        self.transaction_memory = None
        self.error_memory = None
    
    def accrue(self, node, action: str) -> bool:
        """Начисление = метаболизм!"""
        with self.lock:
            node_id = getattr(node, 'id', str(id(node)))
            
            if not self.integrity.validate_action(node, action):
                self.disconnect_node(node_id, "resource_anomaly")
                return False
            
            # Проверка ДО начисления: нет работы = нет ресурса! (АДАПТИВНО!)
            if action == 'solve_task':
                tasks = 0
                if hasattr(node, 'metrics') and isinstance(node.metrics, dict):
                    tasks = node.metrics.get('tasks_completed', 0)
                else:
                    tasks = getattr(node, 'blocks_mined', 0)  # Маяк!
                
                if tasks == 0:
                    print(f"  ⛔ Нет работы! {node_id} не решал задач!")
                    return False
            
            if action == 'establish_connection' and len(getattr(node, 'neighbors', [])) == 0:
                print(f"  ⛔ Нет связей! {node_id} не устанавливал связи!")
                return False

            calories = self.base_rewards[action]
            
            muscle_gain = calories * self.metabolic_rates['muscle_growth']
            fat_gain = calories * self.metabolic_rates['fat_storage']
            bone_gain = calories * self.metabolic_rates['bone_building']
            blood_gain = calories * self.metabolic_rates['blood_circulation']
            education_gain = calories * self.metabolic_rates['education']
            social_gain = calories * self.metabolic_rates['social_support']
            science_gain = calories * self.metabolic_rates['science']
            
            self.active_nodes[node_id] = self.active_nodes.get(node_id, 0) + muscle_gain
            self.fat_reserves += fat_gain
            self.bone_structure += bone_gain
            self.blood_sugar += blood_gain
            self.education += education_gain
            self.social_fund += social_gain
            self.science += science_gain
            self.total_energy += calories
            
            # Обновляем эффективность!
            self.global_efficiency = 1.0 + (self.education / max(1, self.total_energy)) * 0.5
            
            print(f"  💪 {node_id}: +{muscle_gain:.1f} за {action}")
            
            self._maintain_homeostasis()
            self._check_concentration(node_id)
            
            # 🌀 Фрактальная память (не забываем, сворачиваем!)
            if self.transaction_memory is not None:
                self.transaction_memory.add({
                    'action': action,
                    'amount': calories,
                    'node': node_id,
                    'time': time.time()
                })
            
            return True
    
    def _maintain_homeostasis(self):
        """Гомеостаз с защитой от отрицательной энергии!"""
        if self.total_energy <= 0:
            return
        
        fat_pct = self.fat_reserves / self.total_energy
        
        if fat_pct < self.SET_POINTS['fat_percentage'] * 0.5:
            self.metabolic_rates['fat_storage'] += 0.01
            self.metabolic_rates['muscle_growth'] -= 0.01
            print(f"  🧬 Мало жирка ({fat_pct*100:.1f}%)! Копим!")
        elif fat_pct > self.SET_POINTS['fat_percentage'] * 2:
            self.metabolic_rates['fat_storage'] -= 0.01
            self.metabolic_rates['muscle_growth'] += 0.01
            self._invest_fat_in_growth()
            print(f"  🧬 Много жирка ({fat_pct*100:.1f}%)! Инвестируем!")
        
        # НОРМАЛИЗАЦИЯ с защитой от отрицательных!
        for key in self.metabolic_rates:
            self.metabolic_rates[key] = max(0.01, self.metabolic_rates[key])
        
        total_rate = sum(self.metabolic_rates.values())
        if total_rate > 0:
            for key in self.metabolic_rates:
                self.metabolic_rates[key] /= total_rate
    
    def _invest_fat_in_growth(self):
        investment = self.fat_reserves * 0.1
        self.fat_reserves -= investment
        self.bone_structure += investment * 0.6
        self.blood_sugar += investment * 0.4
    
    def _check_concentration(self, node_id):
        """Анти-концентрация: 30% порог!"""
        if not self.active_nodes:
            return
        
        max_allowed = self.total_energy * 0.3
        node_balance = self.active_nodes.get(node_id, 0)
        
        if node_balance > max_allowed:
            excess = node_balance - max_allowed
            self.active_nodes[node_id] = max_allowed
            self.fat_reserves += excess
            print(f"  🔥 Изъято {excess:.1f} у {node_id} → жирок!")
    
    def transfer(self, from_id, to_id, amount) -> bool:
        with self.lock:
            if self.active_nodes.get(from_id, 0) < amount:
                return False
            
            self.active_nodes[from_id] -= amount
            self.active_nodes[to_id] = self.active_nodes.get(to_id, 0) + amount
            print(f"  💸 {amount:.1f}: {from_id} → {to_id}")
            return True
    
    def use_fat_reserves(self, node_id, amount) -> bool:
        """Сжигание жирка: 90% энергия, 7% ремонт, 3% мудрость!"""
        with self.lock:
            if self.fat_reserves < amount:
                return False
            
            self.fat_reserves -= amount
            
            energy = amount * 0.90
            repair = amount * 0.07
            wisdom = amount * 0.03
            
            self.active_nodes[node_id] = self.active_nodes.get(node_id, 0) + energy
            self.bone_structure += repair
            self.wisdom += wisdom
            
            print(f"  🔥 {node_id}: +{energy:.1f} энергии, +{repair:.1f} ремонт, +{wisdom:.1f} мудрость")
            return True

    def create_contract(self, helper_id: str, receiver_id: str, 
                        task_type: str, aid_amount: float) -> Optional[SmartContract]:
        """Создание контракта с защитой от спама."""
        # Проверка на спам
        if not self.contract_limiter.can_create_contract(helper_id):
            return None
        
        # Проверка ресурса
        if self.active_nodes.get(helper_id, 0) < aid_amount:
            print(f"  ❌ Недостаточно ресурса у {helper_id}")
            return None
        
        # Создаём контракт
        contract = SmartContract(
            contract_id=f"contract_{time.time()}",
            helper=helper_id,
            receiver=receiver_id,
            task_type=task_type,
            aid_amount=aid_amount
        )
        
        # В очередь
        if task_type not in self.contract_queue:
            self.contract_queue[task_type] = []
        self.contract_queue[task_type].append(contract)
        
        print(f"  📋 Контракт {contract.id} в очереди ({task_type})")
        return contract
    
    def process_contract_cycle(self, helper_id: str, receiver_id: str, 
                               task_type: str, task: Task) -> bool:
        """Полный цикл: помощь → задача → расчёт!"""
        if task_type not in self.contract_queue or not self.contract_queue[task_type]:
            print(f"  📋 Нет контрактов ({task_type})")
            return False
        
        contract = self.contract_queue[task_type].pop(0)
        
        if not contract.activate(self):
            return False
        if not contract.execute(self, task):
            return False
        
        task_result = {'completed': True, 'quality': 0.8}
        if contract.settle(self, task_result):
            print(f"  🔄 Цикл завершён!")
            return True
        
        return False        

    def social_support(self):
        """🏥 Поддержка слабых узлов!"""
        if self.social_fund < 1.0:
            return
        
        weak_nodes = [
            node_id for node_id, balance in self.active_nodes.items()
            if balance < self.total_energy * 0.01
        ]
        
        if weak_nodes:
            support = self.social_fund * 0.1
            per_node = support / len(weak_nodes)
            
            for node_id in weak_nodes:
                self.active_nodes[node_id] += per_node
            
            self.social_fund -= support
            print(f"  🏥 Социалка: {len(weak_nodes)} слабых узлов получили по {per_node:.3f}")
    
    def invest_in_science(self):
        """🔬 Наука открывает новые возможности!"""
        if self.science < 100:
            return
        
        self.science -= 100
        self.wisdom += 50
        
        # Наука повышает эффективность!
        self.global_efficiency += 0.05
        
        print(f"  🔬 Научное открытие! Мудрость +50, эффективность: {self.global_efficiency:.2f}")

    def spend_education(self, node_id: str, amount: float) -> bool:
        """🎓 Расходование образования на обучение узла!"""
        with self.lock:
            if self.education < amount:
                print(f"  ❌ Мало образования! ({self.education:.1f})")
                return False
            
            self.education -= amount
            self.active_nodes[node_id] = self.active_nodes.get(node_id, 0) + amount
            self.wisdom += amount * 0.5
            
            print(f"  🎓 Обучение {node_id}: -{amount:.1f} из фонда, +{amount:.1f} узлу, +{amount*0.5:.1f} мудрости")
            return True
    
    def spend_social(self, node_ids) -> bool:
        """🏥 Расходование социалки на поддержку!"""
        with self.lock:
            if self.social_fund < 1.0:
                return False
            
            support = self.social_fund * 0.2
            per_node = support / max(1, len(node_ids))
            
            for node_id in node_ids:
                self.active_nodes[node_id] = self.active_nodes.get(node_id, 0) + per_node
            
            self.social_fund -= support
            
            
            return True
    
    def spend_science(self, amount: float) -> bool:
        """🔬 Расходование науки на открытия!"""
        with self.lock:
            if self.science < amount:
                print(f"  ❌ Мало науки! ({self.science:.1f})")
                return False
            
            self.science -= amount
            self.wisdom += amount * 2.0
            self.global_efficiency += 0.01
            
            print(f"  🔬 Открытие: -{amount:.1f} науки, +{amount*2:.1f} мудрости, эффективность +1%!")
            return True
    
    def verify_balance(self) -> bool:
        """⚖️ Универсальная проверка баланса!"""
        with self.lock:
            total_distributed = (
                sum(self.active_nodes.values()) +
                self.fat_reserves +
                self.bone_structure +
                self.blood_sugar +
                self.education +
                self.social_fund +
                self.science +
                self.wisdom +
                self.error_accounting.total_wisdom
            )
            
            discrepancy = self.total_energy - total_distributed
            
            if abs(discrepancy) > 0.5:
                print(f"  ⚠️ РАСХОЖДЕНИЕ: {discrepancy:+.2f}")
                if discrepancy > 0:
                    print(f"  🔥 УТЕЧКА! {discrepancy:.2f} исчезло!")
                else:
                    print(f"  💉 ВБРОС! {abs(discrepancy):.2f} из ниоткуда!")
                return False
            
            print(f"  ✅ Баланс = 0! Всё сходится!")
            return True            
    
    def record_node_error(self, node, error_type, cost):
        """Запись ошибки с уроком!"""
        lessons = {
            'resource_anomaly': 'Прозрачность происхождения!',
            'spam': 'Умеренность в действиях!',
            'concentration': 'Симбиоз вместо накопления!',
            'failed_task': 'Качество важнее количества!'
        }
        lesson = lessons.get(error_type, 'Опыт!')
        
        self.error_accounting.record_error(
            node_id=getattr(node, 'id', str(id(node))),
            error_type=error_type,
            cost=cost,
            lesson=lesson
        )
        
        self.wisdom += cost * 0.01
        print(f"  📚 Урок: {lesson}")

        # 🌀 Фрактальная память для ошибок!
        if self.error_memory is not None:
            self.error_memory.add({
                'node': node_id,
                'type': error_type,
                'cost': cost,
                'time': time.time()
            })
    
    def disconnect_node(self, node_id, reason):
        if node_id in self.active_nodes:
            self.disconnected_nodes[node_id] = {
                'balance': self.active_nodes[node_id],
                'time': time.time(),
                'reason': reason
            }
            # НЕ отнимаем из total_energy! Просто убираем!
            del self.active_nodes[node_id]
            print(f"  💧 Баланс частично переведён в жирок")
            print(f"  ⚡ {node_id} отключён! ({reason})")
    
    def get_balance(self, node) -> float:
        node_id = getattr(node, 'id', str(id(node)))
        return self.active_nodes.get(node_id, 0)
    
    def get_stats(self):
        fat_pct = self.fat_reserves / self.total_energy if self.total_energy > 0 else 0
        return {
            'total_energy': self.total_energy,
            'active_nodes': len(self.active_nodes),
            'fat_reserves': self.fat_reserves,
            'fat_percentage': fat_pct,
            'bone_structure': self.bone_structure,
            'blood_sugar': self.blood_sugar,
            'wisdom': self.wisdom,
            'education': self.education,
            'social_fund': self.social_fund,
            'science': self.science,
            'efficiency': self.global_efficiency,
            'metabolic_rates': self.metabolic_rates.copy(),
            'disconnected': len(self.disconnected_nodes),
            'scars': len(self.error_accounting.smart_scars),
            'wisdom_from_errors': self.error_accounting.total_wisdom,
            'fractal_depth': self.transaction_memory.get_depth() if self.transaction_memory else 0,
            'fractal_total': self.transaction_memory.get_total_memory() if self.transaction_memory else 0
        }


if __name__ == "__main__":
    print("💎 Монистическая экономика TEES — ТЕСТ ЗАЩИТЫ")
    print("=" * 50)
    
    economy = TEESEconomy()
    
    class TestNode:
        def __init__(self, node_id):
            self.id = node_id
            self.metrics = {
                'tasks_completed': 0,
                'heal_count': 0,
                'optimize_count': 0,
                'form_cluster_count': 0
            }
            self.neighbors = []
            self.storage_used = 0
    
    # ═══════════════════════════════
    # ТЕСТ 1: Честный узел
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 1: Честный узел работает")
    node_good = TestNode("good_node")
    
    for i in range(5):
        node_good.metrics['tasks_completed'] += 1
        economy.accrue(node_good, 'solve_task')
    
    print(f"  Баланс: {economy.get_balance(node_good):.1f}")
    
    # ═══════════════════════════════
    # ТЕСТ 2: Хитрый узел (вброс!)
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 2: Хитрый узел (вброс ресурса!)")
    node_bad = TestNode("bad_node")
    
    # Узел НЕ работал, но хочет получить ресурс!
    print(f"  Попытка начислить без работы:")
    economy.accrue(node_bad, 'solve_task')  # tasks_completed = 0!
    
    # ═══════════════════════════════
    # ТЕСТ 3: Подделка баланса!
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 3: Подделка баланса!")
    node_hacker = TestNode("hacker")
    
    # Хакер "нарисовал" себе баланс!
    economy.active_nodes["hacker"] = 1000.0
    print(f"  Хакер заявляет баланс: 1000.0")
    print(f"  Хакер выполнял задач: {node_hacker.metrics['tasks_completed']}")
    
    # Пытаемся начислить ещё — проверка должна поймать!
    node_hacker.metrics['tasks_completed'] = 1
    print(f"  Хакер пытается начислить:")
    result = economy.accrue(node_hacker, 'solve_task')
    print(f"  Результат: {result}")
    
    # ═══════════════════════════════
    # ТЕСТ 4: Спам контрактами!
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 4: Спам контрактами!")
    node_spammer = TestNode("spammer")
    node_spammer.metrics['tasks_completed'] = 10
    economy.accrue(node_spammer, 'solve_task')
    
    # Спамер создаёт 5 контрактов подряд!
    for i in range(5):
        contract = economy.create_contract(
            helper_id="spammer",
            receiver_id="good_node",
            task_type="optimization",
            aid_amount=1
        )
        if contract:
            print(f"  Контракт {i+1}: создан")

        # ═══════════════════════════════
    # ТЕСТ 5: Социалка — поддержка слабых!
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 5: Социалка!")
    node_weak = TestNode("weak_node")
    economy.active_nodes["weak_node"] = 0.5  # Очень слабый!
    
    print(f"  До социалки: weak_node = {economy.get_balance(node_weak):.1f}")
    print(f"  Соцфонд: {economy.social_fund:.1f}")
    
    economy.social_support()
    
    print(f"  После социалки: weak_node = {economy.get_balance(node_weak):.1f}")
    print(f"  Соцфонд: {economy.social_fund:.1f}")
    
    # ═══════════════════════════════
    # ТЕСТ 6: Образование — эффективность!
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 6: Образование!")
    print(f"  До: эффективность = {economy.global_efficiency:.2f}")
    print(f"  Образование: {economy.education:.1f}")
    
    # Ещё поработаем, чтобы образование выросло!
    for i in range(10):
        node_good.metrics['tasks_completed'] += 1
        economy.accrue(node_good, 'solve_task')
    
    print(f"  После: эффективность = {economy.global_efficiency:.2f}")
    print(f"  Образование: {economy.education:.1f}")
    
    # ═══════════════════════════════
    # ТЕСТ 7: Наука — открытие!
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 7: Наука!")
    print(f"  Наука: {economy.science:.1f}")
    
    # Копим науку!
    for i in range(30):
        node_good.metrics['tasks_completed'] += 1
        economy.accrue(node_good, 'solve_task')
    
    print(f"  Наука накоплена: {economy.science:.1f}")
    economy.invest_in_science()
    print(f"  После инвестиции: эффективность = {economy.global_efficiency:.2f}")

    # ═══════════════════════════════
    # ТЕСТ 8: Проверка баланса!
    # ═══════════════════════════════
    print(f"\n🧪 ТЕСТ 8: Универсальная проверка баланса!")
    economy.verify_balance()
    
    # Симулируем утечку!
    print(f"\n🧪 ТЕСТ 9: Симуляция утечки!")
    economy.fat_reserves -= 10.0  # Ресурс "исчез"!
    economy.verify_balance()
    
    # Симулируем вброс!
    print(f"\n🧪 ТЕСТ 10: Симуляция вброса!")
    economy.active_nodes["mystery_node"] = 50.0  # Ресурс "появился"!
    economy.verify_balance()
    
    # ═══════════════════════════════
    # ИТОГ
    # ═══════════════════════════════
    print(f"\n📊 ФИНАЛЬНАЯ СТАТИСТИКА:")
    stats = economy.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")        
        
    print(f"\n  Отключённые узлы: {economy.disconnected_nodes}")