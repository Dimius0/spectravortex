import time
import threading

class PulseHunter:
    """хотник за пульсом - исправленная версия"""
    
    def __init__(self, coord, name="pulse"):
        self.coord = coord
        self.name = name
        self.running = False
        self.thread = None
        
    def start(self):
        """апуск охотника"""
        if self.running:
            return
        self.running = True
        self.thread = threading.Thread(target=self._run)
        self.thread.daemon = True
        self.thread.start()
        print(f"  ✅ {self.name} запущен")
        
    def stop(self):
        """становка охотника"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)
            
    def _run(self):
        """сновной цикл"""
        while self.running:
            try:
                # муляция охоты за пульсом
                time.sleep(0.1)
                if hasattr(self.coord, 'phase') and hasattr(self.coord.phase, 'record_pulse'):
                    self.coord.phase.record_pulse(True, 100)
            except Exception as e:
                print(f"  ⚠️ {self.name} error: {e}")
                time.sleep(1)

def create_pulse_hunter(coord, name="pulse"):
    """абрика для создания охотника"""
    hunter = PulseHunter(coord, name)
    hunter.start()
    return hunter
