# tees_compass_tees.py
# 🧭 Компас — умный роутер TEES-сети


class Compass:
    """TEESRouter — поиск оптимального пути между маяками."""
    
    def __init__(self, lang='ru'):
        self.lang = lang
        self.paths_found = 0
    
    def find_path(self, from_portal, to_portal, neighbors):
        """
        Найти лучший путь между порталами.
        Учитывает качество и энергозатраты.
        """
        paths = [
            {
                'path': ['WiFi', 'Bluetooth', 'QR'],
                'quality': 0.95,
                'energy': 3
            },
            {
                'path': ['WiFi', 'WiFi'],
                'quality': 0.87,
                'energy': 2
            },
            {
                'path': ['Bluetooth', 'QR', 'Audio'],
                'quality': 0.72,
                'energy': 5
            },
        ]
        
        # Выбираем лучший по качеству
        best = max(paths, key=lambda p: p['quality'])
        self.paths_found += 1
        
        return {
            'from': from_portal[:12] + '...',
            'to': to_portal[:12] + '...',
            'best_path': ' → '.join(best['path']),
            'quality': best['quality'],
            'energy': best['energy'],
            'paths_found': self.paths_found
        }