# tees_symbiosis_tees.py
# 🔗 Калькулятор симбиоза и система редкости

import time


class SymbiosisCalculator:
    """Калькулятор симбиотической связи между маяками."""
    
    def __init__(self):
        self.resources = {
            'cpu': 100, 'memory': 512, 'storage': 1024,
            'peers': 0, 'data': 0, 'uptime': 0
        }
        self.needs = {'data': 100, 'peers': 50, 'validation': 10}
    
    def auto_measure(self):
        """Автоматический замер ресурсов устройства."""
        try:
            import psutil
            self.resources['cpu'] = max(1, 100 - psutil.cpu_percent(interval=0.1))
            self.resources['memory'] = int(psutil.virtual_memory().available / (1024 * 1024))
            self.resources['uptime'] = int(time.time() - psutil.boot_time())
        except ImportError:
            pass
    
    def calculate(self, my_passport, their_passport):
        """
        Расчёт взаимовыгодности симбиоза.
        Возвращает словарь с вердиктом и редкостью.
        """
        # Что мы можем предложить
        my_offer, my_total = {}, 0
        for need, weight in their_passport.get('needs', {}).items():
            if need in my_passport.get('resources', {}):
                offer = min(my_passport['resources'][need], weight)
                if offer > 0:
                    my_offer[need] = offer
                    my_total += offer
        
        # Что они могут предложить
        their_offer, their_total = {}, 0
        for need, weight in my_passport.get('needs', {}).items():
            if need in their_passport.get('resources', {}):
                offer = min(their_passport['resources'][need], weight)
                if offer > 0:
                    their_offer[need] = offer
                    their_total += offer
        
        # Стоимость моста
        bridge_cost = 0.01 * (
            my_passport.get('peers', 0) + their_passport.get('peers', 0)
        )
        
        # Итоговый счёт
        score = my_total + their_total - bridge_cost
        
        # Редкость по разнообразию обмена
        diversity = len(my_offer) + len(their_offer)
        if diversity >= 6:
            rarity = "shiny"
        elif diversity >= 4:
            rarity = "ultra_rare"
        elif diversity >= 2:
            rarity = "rare"
        else:
            rarity = "common"
        
        return {
            'score': score,
            'my_offer': my_offer,
            'their_offer': their_offer,
            'diversity': diversity,
            'rarity': rarity,
            'bridge_cost': bridge_cost,
            'verdict': 'symbiosis' if score > 0 else 'acquaintance'
        }


def calculate_symbiosis_reward(result, existing_connections):
    """
    Расчет награды за симбиоз.
    Чем больше существующих связей — тем меньше награда (убывающая отдача).
    """
    rarity_multipliers = {
        'shiny': 10.0,
        'ultra_rare': 5.0,
        'rare': 2.0,
        'common': 1.0
    }
    
    base = 5 * rarity_multipliers.get(result.get('rarity', 'common'), 1.0)
    decay = 1.0 / (1.0 + existing_connections / 100)
    
    reward = (
        base
        + result.get('diversity', 1) * 5
        + result.get('score', 0) * 0.5
    ) * decay
    
    return max(0.1, round(reward, 1))