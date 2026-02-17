#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import threading
import time
from pathlib import Path

HEAD_PATH = Path(__file__).parent / "headquarters"
sys.path.insert(0, str(HEAD_PATH))

from headquarters import Coordinator
from headquarters.modules.scout import DeepScoutModule
from headquarters.modules.colonizer import ColonizerModule
from headquarters.modules.pulsehunter import PulseHunterModule
from headquarters.modules.scout_squad_heavy import HeavyScoutSquadModule
from headquarters.modules.scout_strategic import StrategicScoutSquadModule

hq = Coordinator()
hq.register_module('scout', DeepScoutModule)
hq.register_module('colonizer', ColonizerModule)
hq.register_module('pulsehunter', PulseHunterModule)
hq.register_module('heavy_scout_squad', HeavyScoutSquadModule)
hq.register_module('strategic_scout', StrategicScoutSquadModule)

threading.Thread(target=hq.modules['scout'].run, daemon=True).start()
threading.Thread(target=hq.modules['colonizer'].run, daemon=True).start()
t3 = threading.Thread(target=hq.modules['pulsehunter'].run, daemon=True)
t3.start()
t5 = threading.Thread(target=hq.modules['heavy_scout_squad'].run, daemon=True)
t5.start()
t6 = threading.Thread(target=hq.modules['strategic_scout'].run, daemon=True)
t6.start()

print("🎯 Ризома запущена. Цель 1000\n")
try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    print("\n✅ Стоп")