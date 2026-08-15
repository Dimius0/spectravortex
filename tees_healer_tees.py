# tees_healer_tees.py
# 🧬 Self-Healing Mesh — самовосстанавливающаяся сеть

import time
import threading


class SelfHealingMesh:
    """
    Эритроцитарный морфогенез сети.
    Если маяк исчезает — соседи восстанавливают его из фрагментов TEES-триад.
    """
    
    # ✅ Константы вместо магических чисел
    HEARTBEAT_TIMEOUT = 30        # секунд без пульса до объявления потери
    MAX_FRAGMENTS = 3             # размер триады
    HEAL_REWARD = 5.0             # награда за восстановление
    MAX_WATCHLIST_SIZE = 200      # максимум наблюдаемых маяков
    MAX_REPLICATED_SIZE = 100     # максимум записей о восстановлении
    FRAGMENT_MAX_AGE = 300        # максимальный возраст фрагмента (5 минут)
    MAX_FRAGMENTS_PER_SHARE = 10  # максимум фрагментов при sharing
    
    def __init__(self, beacon):
        self.beacon = beacon
        self.watchlist = {}       # beacon_id -> время последнего heartbeat
        self.replicated = []      # список восстановленных маяков
        self.fragments = {}       # beacon_id -> список фрагментов
        self.lock = threading.Lock()  # ✅ Блокировка для потокобезопасности
    
    def heartbeat(self, beacon_id: str):
        """Зафиксировать пульс маяка."""
        # ✅ Игнорируем свой собственный ID
        if beacon_id == self.beacon.beacon_id:
            return
        
        with self.lock:
            self.watchlist[beacon_id] = time.time()
            
            # ✅ Если маяк был в "потерянных" — удаляем из фрагментов
            if beacon_id in self.fragments:
                del self.fragments[beacon_id]
                # Не награждаем, просто очищаем — маяк сам вернулся
    
    def check_pulse(self):
        """
        Проверить пульс всех наблюдаемых маяков.
        Возвращает список исчезнувших.
        """
        now = time.time()
        lost = []
        
        with self.lock:
            # ✅ Очистка старых записей из watchlist
            stale_ids = []
            for beacon_id, last_seen in self.watchlist.items():
                if now - last_seen > self.HEARTBEAT_TIMEOUT * 4:  # 2 минуты без пульса
                    stale_ids.append(beacon_id)
            
            for beacon_id in stale_ids:
                del self.watchlist[beacon_id]
                if beacon_id in self.fragments:
                    del self.fragments[beacon_id]
            
            # ✅ Ограничиваем размер watchlist
            if len(self.watchlist) > self.MAX_WATCHLIST_SIZE:
                # Удаляем самые старые записи
                sorted_ids = sorted(
                    self.watchlist.keys(),
                    key=lambda x: self.watchlist[x]
                )
                for beacon_id in sorted_ids[:len(sorted_ids) - self.MAX_WATCHLIST_SIZE]:
                    del self.watchlist[beacon_id]
            
            # Находим потерянные маяки
            for beacon_id, last_seen in self.watchlist.items():
                if now - last_seen > self.HEARTBEAT_TIMEOUT:
                    lost.append(beacon_id)
        
        # Исцеляем вне блокировки, чтобы не держать её долго
        for beacon_id in lost:
            self.heal(beacon_id)
        
        return lost
    
    def store_fragment(self, beacon_id: str, data: dict):
        """
        Сохранить фрагмент состояния маяка.
        Каждый фрагмент — часть TEES-триады (source/tees/receiver).
        """
        # ✅ Не храним фрагменты о себе
        if beacon_id == self.beacon.beacon_id:
            return
        
        # ✅ Валидация данных
        if not data or not isinstance(data, dict):
            return
        
        with self.lock:
            if beacon_id not in self.fragments:
                self.fragments[beacon_id] = []
            
            fragment = {
                'data': data,
                'triad_part': len(self.fragments[beacon_id]) % self.MAX_FRAGMENTS,
                'timestamp': time.time(),
                'stored_by': self.beacon.beacon_id
            }
            
            self.fragments[beacon_id].append(fragment)
            
            # Храним только последние N фрагментов (триаду)
            if len(self.fragments[beacon_id]) > self.MAX_FRAGMENTS:
                self.fragments[beacon_id] = self.fragments[beacon_id][-self.MAX_FRAGMENTS:]
            
            # ✅ Ограничиваем общее количество фрагментов
            total_fragments = sum(len(f) for f in self.fragments.values())
            if total_fragments > self.MAX_FRAGMENTS_PER_SHARE * 5:
                # Удаляем самые старые фрагменты
                oldest = None
                oldest_time = float('inf')
                oldest_beacon = None
                for bid, frags in self.fragments.items():
                    if frags and frags[0]['timestamp'] < oldest_time:
                        oldest_time = frags[0]['timestamp']
                        oldest_beacon = bid
                
                if oldest_beacon:
                    del self.fragments[oldest_beacon]
    
    def heal(self, lost_beacon_id: str):
        # ✅ Не пытаемся лечить себя
        if lost_beacon_id == self.beacon.beacon_id:
            return None
        
        with self.lock:
            if lost_beacon_id not in self.fragments:
                return None
            
            fragments = self.fragments[lost_beacon_id]
            if len(fragments) < 1:
                return None
            
            # ✅ Проверяем, не восстанавливали ли уже
            for prev in self.replicated[-10:]:  # проверяем последние 10
                if prev.get('beacon_id') == lost_beacon_id:
                    # Уже восстанавливали недавно
                    return None
            
            # ✅ Проверяем возраст фрагментов
            now = time.time()
            valid_fragments = [
                f for f in fragments
                if now - f['timestamp'] < self.FRAGMENT_MAX_AGE
            ]
            
            if len(valid_fragments) < 1:
                # Фрагменты просрочены
                del self.fragments[lost_beacon_id]
                return None
            
            source_data = tees_data = receiver_data = None
            
            for f in valid_fragments:
                if f['triad_part'] == 0:
                    source_data = f['data']
                elif f['triad_part'] == 1:
                    tees_data = f['data']
                elif f['triad_part'] == 2:
                    receiver_data = f['data']
            
            # ✅ Удаляем потерянный маяк из watchlist
            if lost_beacon_id in self.watchlist:
                del self.watchlist[lost_beacon_id]
            
            # Очищаем фрагменты
            del self.fragments[lost_beacon_id]
        
        recovered = {
            'beacon_id': lost_beacon_id,
            'recovered_at': time.time(),
            'recovered_by': self.beacon.beacon_id,
            'complete': all([source_data, tees_data, receiver_data])
        }
        
        with self.lock:
            self.replicated.append(recovered)
            
            # ✅ Ограничиваем размер истории
            if len(self.replicated) > self.MAX_REPLICATED_SIZE:
                self.replicated = self.replicated[-self.MAX_REPLICATED_SIZE:]
        
        # Награда только за полное восстановление
        if recovered['complete']:
            self.beacon.network_reward(self.HEAL_REWARD, reason="heal_reward")
            print(f"  🧬 Маяк восстановлен — помощь оказана! +{self.HEAL_REWARD} ресурса")
        
        return recovered
    
    def share_fragments_with_neighbors(self):
        """Поделиться фрагментами с соседями для распределённого хранения."""
        # ✅ Ограничиваем количество рассылаемых фрагментов
        fragments_to_share = []
        
        with self.lock:
            for lost_id, fragments in self.fragments.items():
                if fragments:
                    fragments_to_share.append((lost_id, fragments[-1]))
                    if len(fragments_to_share) >= self.MAX_FRAGMENTS_PER_SHARE:
                        break
        
        # ✅ Отправляем не всем, а случайным соседям
        import random
        neighbors = self.beacon.neighbors[:]
        random.shuffle(neighbors)
        
        for neighbor_id in neighbors[:5]:  # максимум 5 получателей
            for lost_id, fragment in fragments_to_share:
                if lost_id != neighbor_id:
                    self.beacon._broadcast({
                        'type': 'fragment_share',
                        'beacon_id': lost_id,
                        'fragment': fragment,
                        'from': self.beacon.beacon_id
                    })
    
    def get_stats(self) -> dict:
        """Статистика самовосстановления."""
        with self.lock:
            return {
                'watching': len(self.watchlist),
                'fragments_stored': sum(len(f) for f in self.fragments.values()),
                'beacons_healed': len(self.replicated)
            }
    
    # ✅ Новый метод для ручной очистки
    def cleanup(self):
        """Полная очистка устаревших данных."""
        now = time.time()
        with self.lock:
            # Чистим watchlist
            old_watch = [
                bid for bid, last in self.watchlist.items()
                if now - last > self.HEARTBEAT_TIMEOUT * 2
            ]
            for bid in old_watch:
                del self.watchlist[bid]
            
            # Чистим старые фрагменты
            old_frags = []
            for bid, frags in self.fragments.items():
                valid = [f for f in frags if now - f['timestamp'] < self.FRAGMENT_MAX_AGE]
                if valid:
                    self.fragments[bid] = valid
                else:
                    old_frags.append(bid)
            
            for bid in old_frags:
                del self.fragments[bid]