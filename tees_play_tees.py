# tees_play_tees.py
# 🎮 Игровой интерфейс (консоль)

import threading
import time
import uuid

from tees_core_tees import VERSION
from tees_scroll_tees import (
    create_scroll, validate_scroll, scroll_to_portal,
    mine_child_portals
)
from tees_beacon_tees import Beacon
from tees_stranger_tees import Stranger
from tees_compass_tees import Compass
from tees_box_tees import TEESBox


# ═══════════════════════════════════════════════════════════════
# 📜 ИГРОВЫЕ ТЕРМИНЫ
# ═══════════════════════════════════════════════════════════════

GAME_WORDS = {
    'ru': {
        'help_text': '''
╔════════════════════════════════════════════════════════════╗
║                 🌀 TEES WORLD — Помощь                     ║
╠════════════════════════════════════════════════════════════╣
║  портал       — Показать свой портал (адрес)               ║
║  ресурс         — Проверить ресурс                         ║
║  поделиться   — Отправить ресурс другу                     ║
║  копать [n]   — Создать n дочерних порталов                ║
║  маяк         — Поставить маяк (помогать сети)             ║
║  деревня      — Пригласить друга (код)                     ║
║  компас       — Найти путь (роутер)                        ║
║  симбиоз      — Сканировать соседей                        ║
║  пещера       — Исследовать пещеру (модуль)                ║
║  странник     — Спросить Странника (LLM)                   ║
║  карта        — Показать карту приключений                 ║
║  свиток       — Показать свой свиток (мнемонику)           ║
║  чат          — P2P чат с другим игроком                   ║
║  mesh         — Сеть без интернета (WiFi/BT/QR)            ║
║  здоровье      — Статус самовосстановления сети             ║
║  выйти        — Покинуть мир                                ║
╚══════════════════════════════════════════════════════════════╝
''',
        'welcome': 'Добро пожаловать в TEES-мир!',
        'goodbye': 'До новых приключений!',
        'new_player': '🆕 Новый игрок появился в мире!',
        'beacon_placed': '🔥 Маяк поставлен! Свет распространяется...',
        'village_grows': '🏘️ Деревня растёт!',
        'help_cmd': 'помощь',
        'exit_cmd': 'выйти',
        'portal': 'Портал',
        'world': 'TEES-мир',
        'block': 'Глыб',
    },
    'en': {
        'help_text': '''
╔═════════════════════════════════════════════════════════════╗
║                 🌀 TEES WORLD — Help                        ║
╠═════════════════════════════════════════════════════════════╣
║  portal       — Show your portal (address)                  ║
║  power        — Check your resource                         ║
║  share        — Send resource to a friend                   ║
║  mine [n]     — Create n child portals                      ║
║  beacon       — Place a beacon (help the network)           ║
║  village      — Invite a friend (code)                      ║
║  compass      — Find a path (router)                        ║
║  symbiosis    — Scan neighbors                              ║
║  cave         — Explore a cave (module)                     ║
║  stranger     — Ask the Stranger (LLM)                      ║
║  map          — Show the adventure map                      ║
║  scroll       — Show your scroll (mnemonic)                 ║
║  chat         — P2P chat with another player                ║
║  mesh         — Offline network (WiFi/BT/QR)                ║
║  health       — Self-healing status                         ║
║  exit         — Leave the world                             ║
╚═════════════════════════════════════════════════════════════╝
''',
        'welcome': 'Welcome to TEES World!',
        'goodbye': 'Until the next adventure!',
        'new_player': '🆕 A new player appeared in the world!',
        'beacon_placed': '🔥 Beacon placed! Light spreads...',
        'village_grows': '🏘️ Village grows!',
        'help_cmd': 'help',
        'exit_cmd': 'exit',
        'portal': 'Portal',
        'world': 'TEES World',
        'block': 'Blocks',
    }
}


def w(key: str, lang: str = 'en') -> str:
    return GAME_WORDS.get(lang, GAME_WORDS['en']).get(key, key)


# ═══════════════════════════════════════════════════════════════
# 🎮 ИГРОВОЙ ЦИКЛ
# ═══════════════════════════════════════════════════════════════

def play(scroll=None, lang='ru'):
    lt = lang
    
    print(f"""
╔══════════════════════════════════════════════════════════╗
║               {w('world', lt)} v{VERSION}                     ║
║              {w('welcome', lt)}                          ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    if not scroll:
        box = TEESBox()
        if box.exists():
            print("🔐 Обнаружен TEES Box. Введи пароль.")
            pwd = input("🔑 Пароль: ").strip()
            scroll = box.unlock_scroll(pwd)
            if scroll:
                print("✅ Свиток восстановлен из TEES Box")
            else:
                print("❌ Неверный пароль. Создаю новый свиток.")
                scroll = create_scroll()
        else:
            scroll = create_scroll()
            print(w('new_player', lt))
    
    # Предложить запереть новый свиток
    if not TEESBox().exists():
        print("\n🔐 Хочешь запереть свиток в TEES Box? (не будет храниться открыто)")
        choice = input("   Запереть? (да/нет): ").strip().lower()
        if choice in ['да', 'yes', 'y', 'д']:
            pwd = input("🔑 Придумай пароль: ").strip()
            pwd2 = input("🔑 Повтори пароль: ").strip()
            if pwd == pwd2 and pwd:
                box = TEESBox()
                box.lock_scroll(scroll, pwd)
                print("✅ Свиток надёжно заперт!")
                print("⚠️ Не забудь пароль! Без него свиток не восстановить.")
            else:
                print("❌ Пароли не совпадают.")
    
    portal = scroll_to_portal(scroll)
    print(f"  {w('portal', lt)}: {portal}")
    print(f"  {w('help_cmd', lt)}: '{w('help_cmd', lt)}', {w('exit_cmd', lt)}: '{w('exit_cmd', lt)}'\n")
    
    beacon = None
    stranger = None
    compass = None
    
    while True:
        try:
            cmd = input(f"🌍> ").strip().split()
            if not cmd:
                continue
            
            action = cmd[0].lower()
            
            if action in ['помощь', 'help']:
                print(w('help_text', lt))
            
            elif action in ['портал', 'portal']:
                print(f"  {portal}")
            
            elif action in ['свиток', 'scroll']:
                print(f"  📜 {scroll}")
                print(f"  {'✅ Свиток настоящий' if validate_scroll(scroll) else '❌ Свиток повреждён'}")
            
            elif action in ['ресурс', 'power']:
                print(f"  💪 Ресурс: {beacon.get_power() if beacon else 0}")
            
            elif action in ['поделиться', 'share']:
                if not beacon:
                    print("  ❌ Сначала поставь маяк")
                elif len(cmd) < 3:
                    print("  🤝 Использование: поделиться <портал> <сколько>")
                else:
                    try:
                        amount = float(cmd[2])
                        trade = beacon.share_ores(cmd[1], amount)
                        print(f"  🤝 Отправлено {amount} → {cmd[1][:12]}..." if trade else "  ❌ Недостаточно ресурса")
                    except ValueError:
                        print("  ❌ Число нужно")
            
            elif action in ['копать', 'mine']:
                n = int(cmd[1].strip('[]()')) if len(cmd) > 1 else 5
                print(f"  ⛏️ Копаю {n} порталов...")
                for child in mine_child_portals(scroll, n):
                    print(f"  {child['path']}: {child['portal']}")
            
            elif action in ['маяк', 'beacon']:
                if beacon is None:
                    beacon = Beacon(scroll, lang=lt)
                    threading.Thread(target=beacon.light, daemon=True).start()
                    time.sleep(0.5)
                else:
                    print("  🔥 Маяк уже горит!")
            
            elif action in ['деревня', 'village']:
                code = str(uuid.uuid4())[:8]
                print(f"  🏘️ Код приглашения: {code}")
                print(f"  Друг может войти: python tees_world.py --join {code}")
                if beacon:
                    print(f"  {w('village_grows', lt)}")
            
            elif action in ['войти', 'join']:
                if len(cmd) < 2:
                    print("  🏘️ Использование: войти <код>")
                else:
                    code = cmd[1]
                    print(f"  🏘️ Вход по коду: {code}")
                    print(f"  🎁 Добро пожаловать! +100 ресурса!")
                    if beacon:
                        beacon.share_ores(beacon.portal, 100)
            
            elif action in ['компас', 'compass']:
                if compass is None:
                    compass = Compass(lang=lt)
                    print("  🧭 Компас готов")
                if beacon and len(cmd) > 1:
                    path = compass.find_path(beacon.portal, cmd[1], beacon.neighbors)
                    print(f"  🧭 {path['best_path']}\n  ✨ {path['quality']:.2f} | 🔋 {path['energy']}")
            
            elif action in ['симбиоз', 'symbiosis']:
                if not beacon:
                    print("  ❌ Сначала поставь маяк")
                elif not beacon.neighbors:
                    print("  🔍 Нет соседей")
                else:
                    for n in beacon.neighbors[:3]:
                        r = beacon.propose_symbiosis(n)
                        if r['verdict'] == 'already_connected':
                            print(f"  🤝 Маяк {n[:12]}... — уже в симбиозе")
                            continue
                        if r['verdict'] == 'symbiosis':
                            em = {'shiny': '⭐', 'ultra_rare': '💎', 'rare': '🔷', 'common': '🔹'}
                            print(f"  {em.get(r['rarity'], '🔹')} {r['rarity']}! +{r['reward']} ресурса")
            
            elif action in ['пещера', 'cave']:
                cave_type = cmd[1] if len(cmd) > 1 else 'science'
                print(f"  🕳️ Пещера: {cave_type}")
                if cave_type in ['oracle', 'stranger']:
                    if stranger is None:
                        stranger = Stranger(lang=lt)
                    print("  🔮 Странник здесь. Спроси: странник <вопрос>")
            
            elif action in ['странник', 'stranger']:
                if stranger is None:
                    stranger = Stranger(lang=lt)
                q = ' '.join(cmd[1:]) or 'Как мир?'
                state = {
                    'glow': beacon.glow if beacon else 0.99,
                    'warmth': beacon.warmth if beacon else 30,
                    'neighbors': len(beacon.neighbors) if beacon else 0,
                    'map_blocks': len(beacon.adventure_map) if beacon else 0
                }
                answer = stranger.ask(q, state)
                print(f"  🔮 Странник: '{answer}'")
            
            elif action in ['чат', 'chat']:
                if not beacon:
                    print("  ❌ Сначала поставь маяк")
                elif len(cmd) < 3:
                    print("  💬 Использование: чат <портал> <сообщение>")
                else:
                    trade = beacon.share_ores(cmd[1], 0, chat_msg=' '.join(cmd[2:]))
                    print(f"  💬 Отправлено!" if trade else "  ❌ Ошибка")
            
            elif action in ['карта', 'map']:
                if beacon and beacon.adventure_map:
                    print(f"  🗺️ Глыб: {len(beacon.adventure_map)} | ⛏️ {beacon.blocks_mined} | 🤝 {beacon.ores_shared}")
                else:
                    print("  🗺️ Карта пуста. Поставь маяк.")
            
            elif action in ['здоровье', 'heal', 'health']:
                if beacon:
                    stats = beacon.healer.get_stats()
                    print(f"  🧬 Самовосстановление:")
                    print(f"     Наблюдаем: {stats['watching']} маяков")
                    print(f"     Фрагментов: {stats['fragments_stored']}")
                    print(f"     Восстановлено: {stats['beacons_healed']}")
                else:
                    print("  ❌ Сначала поставь маяк")
            
            elif action in ['mesh', 'меш']:
                mesh_cmd = cmd[1] if len(cmd) > 1 else 'scan'
                if mesh_cmd in ['scan', 'скан']:
                    print(f"  🔍 Сканировать...\n  ✅ WiFi, Bluetooth, QR, Audio, USB")
                elif mesh_cmd in ['hotspot', 'точка']:
                    print(f"  📶 Точка доступа: TEES_Mesh")
                elif mesh_cmd in ['qr', 'кьюар']:
                    print(f"  📱 QR-код: готов")
                else:
                    print("  mesh: scan, hotspot, qr, audio, usb")
            
            elif action in ['выйти', 'exit', 'quit']:
                if beacon:
                    beacon.extinguish()
                print(w('goodbye', lt))
                break
            
            else:
                print(f"  ❓ {action}? Введи '{w('help_cmd', lt)}'")
        
        except KeyboardInterrupt:
            if beacon:
                beacon.extinguish()
            print(f"\n{w('goodbye', lt)}")
            break
        except Exception as e:
            print(f"  ❌ {e}")