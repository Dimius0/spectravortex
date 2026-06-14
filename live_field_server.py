# live_field_server.py — ЖИВОЕ ПОЛЕ ПАМЯТИ v6.0
import sys, os, json, time, math, re, random, hashlib, threading, gc
from collections import Counter, defaultdict
from http.server import HTTPServer, BaseHTTPRequestHandler

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(CURRENT_DIR, 'src', 'architect'))

from living_personality_v21_3_1 import (
    LivingPersonality, SpectralMode, WaveformEmotion, MIN_ENERGY
)

print("=" * 60)
print("🧠 ЖИВОЕ ПОЛЕ ПАМЯТИ v6.0")
print("=" * 60)

# ═══════════════════════════════════════════════════════
# ЗАГРУЗКА ПОЛЕЙ
# ═══════════════════════════════════════════════════════

TALK_FILE = 'src/rizoma/data/personalities/p016_talk.json'
CODE_FILE = 'src/rizoma/data/personalities/p016_code.json'

print("\n📂 Загружаю разговорное поле...")
start = time.time()
lp_talk = LivingPersonality.load(TALK_FILE) if os.path.exists(TALK_FILE) else None
if lp_talk:
    print(f"✅ Разговорное: {len(lp_talk.get_all_modes())} мод за {time.time()-start:.0f}с")
else:
    print("⚠️ Разговорное поле не найдено, создаю пустое")
    lp_talk = LivingPersonality(id="talk", name="Talk Field", db_path=":memory:")

print("\n📂 Загружаю программное поле...")
start = time.time()
lp_code = LivingPersonality.load(CODE_FILE) if os.path.exists(CODE_FILE) else None
if lp_code:
    print(f"✅ Программное: {len(lp_code.get_all_modes())} мод за {time.time()-start:.0f}с")
else:
    print("⚠️ Программное поле не найдено, создаю пустое")
    lp_code = LivingPersonality(id="code", name="Code Field", db_path=":memory:")

# ═══════════════════════════════════════════════════════
# ИНДЕКСЫ ДЛЯ БЫСТРОГО ПОИСКА
# ═══════════════════════════════════════════════════════

word_to_mode = {}
for mode in lp_talk.get_all_modes():
    if mode.trace_id.startswith('L3_'):
        word = mode.trace_id[3:]
        word_to_mode[word] = mode
for mode in lp_code.get_all_modes():
    if mode.trace_id.startswith('L3_'):
        word = mode.trace_id[3:]
        if word not in word_to_mode:
            word_to_mode[word] = mode

print(f"\n🔍 Общий индекс: {len(word_to_mode)} токенов")

# ═══════════════════════════════════════════════════════
# КАНАЛЫ (из существующих фраз)
# ═══════════════════════════════════════════════════════

channels = defaultdict(list)

def build_channels(lp):
    for mode in lp.get_all_modes():
        if mode.trace_id.startswith('L5_'):
            parts = mode.trace_id[3:].rsplit('_', 1)
            if len(parts) == 2:
                w1, w2 = parts
                if w1 in word_to_mode and w2 in word_to_mode:
                    channels[w1].append((w2, mode.energy))
                    channels[w2].append((w1, mode.energy))

build_channels(lp_talk)
build_channels(lp_code)

print(f"🔗 Каналов: {sum(len(v) for v in channels.values())}")

# ═══════════════════════════════════════════════════════
# ФОНОВЫЙ ПРОЦЕСС (TEES + фуркации + сон)
# ═══════════════════════════════════════════════════════

class LiveField:
    def __init__(self):
        self.running = True
        self.energy = 1.0
        self.total_transfers = 0
        self.total_furcations = 0
        self.messages_processed = 0
        self._lock = threading.Lock()
    
    def process_message(self, text):
        """Обработка входящего сообщения."""
        with self._lock:
            self.messages_processed += 1
            
            # Токенизация
            words = re.findall(r'[а-яёa-z0-9_]+', text.lower())
            words = [w for w in words if len(w) > 1]
            
            if len(words) < 2:
                return "Сообщение слишком короткое"
            
            new_modes = 0
            new_pairs = 0
            
            # Добавляем новые слова как моды
            for word in words:
                if word not in word_to_mode:
                    word_hash = hashlib.md5(word.encode()).digest()
                    mode = SpectralMode(
                        tau=(word_hash[0] % 50) + 5.0,
                        amplitude=0.3,
                        scale=2.0 + len(word)/10,
                        trace_id=f"L3_{word}",
                        creator="live_field",
                        content=word,
                        emotion=WaveformEmotion(amplitude=0.3, base_emotion='neutral'),
                        phase=(word_hash[1] / 255.0) * 2 * math.pi,
                    )
                    lp_talk.add_mode(mode)
                    word_to_mode[word] = mode
                    new_modes += 1
            
            # Добавляем новые пары как каналы
            for j in range(len(words) - 1):
                w1, w2 = words[j], words[j+1]
                if w1 in word_to_mode and w2 in word_to_mode:
                    strength = 0.1  # новый канал — слабый
                    channels[w1].append((w2, strength))
                    channels[w2].append((w1, strength))
                    new_pairs += 1
            
            # Быстрый TEES (10 циклов)
            transfers = 0
            for _ in range(10):
                sources = random.sample(list(channels.keys()), min(100, len(channels)))
                for word in sources:
                    mode_from = word_to_mode.get(word)
                    if not mode_from or mode_from.energy <= 0.01: continue
                    ch_list = channels.get(word, [])
                    if not ch_list: continue
                    w2, strength = random.choice(ch_list)
                    mode_to = word_to_mode.get(w2)
                    if not mode_to: continue
                    energy_diff = mode_from.energy - mode_to.energy
                    if energy_diff > 0:
                        flow = strength * energy_diff * 0.1
                        flow = min(flow, mode_from.energy * 0.1)
                        mode_from.energy -= flow
                        mode_to.energy += flow
                        transfers += 1
            
            self.total_transfers += transfers
            self.energy = max(0.1, self.energy - 0.01)
            
            return f"Принято. Новых мод: {new_modes}, пар: {new_pairs}, TEES: {transfers}. Всего сообщений: {self.messages_processed}"
    
    def background_loop(self):
        """Фоновый процесс: сон, фуркации, автосохранение."""
        cycle = 0
        while self.running:
            time.sleep(1)
            cycle += 1
            
            # Каждые 60 секунд — короткий TEES
            if cycle % 60 == 0:
                with self._lock:
                    transfers = 0
                    sources = random.sample(list(channels.keys()), min(500, len(channels)))
                    for word in sources:
                        mode_from = word_to_mode.get(word)
                        if not mode_from or mode_from.energy <= 0.01: continue
                        ch_list = channels.get(word, [])
                        if not ch_list: continue
                        w2, strength = random.choice(ch_list)
                        mode_to = word_to_mode.get(w2)
                        if not mode_to: continue
                        energy_diff = mode_from.energy - mode_to.energy
                        if energy_diff > 0:
                            flow = strength * energy_diff * 0.1
                            flow = min(flow, mode_from.energy * 0.1)
                            mode_from.energy -= flow
                            mode_to.energy += flow
                            transfers += 1
                    self.total_transfers += transfers
                    self.energy = min(1.0, self.energy + 0.01)
                
                if transfers > 0:
                    print(f"   🔄 Фон: {transfers} переносов, E={self.energy:.3f}")
            
            # Каждые 10 минут — автосохранение
            if cycle % 600 == 0:
                try:
                    lp_talk.save(TALK_FILE)
                    lp_code.save(CODE_FILE)
                    print(f"   💾 Автосохранение: {len(word_to_mode)} токенов")
                except Exception as e:
                    print(f"   ⚠️ Ошибка сохранения: {e}")
            
            # Каждые 30 минут — статус
            if cycle % 1800 == 0:
                print(f"\n📊 Статус: {self.total_transfers} переносов, {self.total_furcations} фуркаций, {self.messages_processed} сообщений")

live_field = LiveField()

# Запускаем фоновый поток
bg_thread = threading.Thread(target=live_field.background_loop, daemon=True)
bg_thread.start()
print("🌿 Фоновый процесс запущен (TEES, автосохранение)")

# ═══════════════════════════════════════════════════════
# HTTP API
# ═══════════════════════════════════════════════════════

class LiveFieldHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length).decode('utf-8')
        
        try:
            data = json.loads(body)
            text = data.get('text', '')
            user = data.get('user', 'anonymous')
        except:
            text = body
            user = 'anonymous'
        
        result = live_field.process_message(text)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        response = json.dumps({
            'status': 'ok',
            'result': result,
            'stats': {
                'transfers': live_field.total_transfers,
                'furcations': live_field.total_furcations,
                'messages': live_field.messages_processed,
                'energy': live_field.energy,
                'tokens': len(word_to_mode),
                'channels': sum(len(v) for v in channels.values()),
            }
        }, ensure_ascii=False)
        self.wfile.write(response.encode('utf-8'))
    
    def do_GET(self):
        if self.path == '/stats':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.end_headers()
            stats = json.dumps({
                'transfers': live_field.total_transfers,
                'furcations': live_field.total_furcations,
                'messages': live_field.messages_processed,
                'energy': live_field.energy,
                'tokens': len(word_to_mode),
                'channels': sum(len(v) for v in channels.values()),
            }, ensure_ascii=False)
            self.wfile.write(stats.encode('utf-8'))
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; charset=utf-8')
            self.end_headers()
            self.wfile.write(f"Живое поле v6.0. Сообщений: {live_field.messages_processed}".encode('utf-8'))

PORT = 8765
server = HTTPServer(('localhost', PORT), LiveFieldHandler)
print(f"\n🌐 API запущен на http://localhost:{PORT}")
print(f"   Отправь POST / с {'text': 'твой текст'}")
print(f"   Открой GET /stats для статистики")
print(f"   Ctrl+C для остановки\n")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\n🛑 Завершение...")
    live_field.running = False
    server.shutdown()
    lp_talk.save(TALK_FILE)
    lp_code.save(CODE_FILE)
    print("💾 Сохранено. До встречи!")