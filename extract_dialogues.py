# extract_dialogues.py — извлечение текстов из conversations.json
import json
import sys

INPUT = 'brain_dump/dialogues_json/conversations.json'
OUTPUT = 'dialogue_texts.json'

print(f"📂 Читаю {INPUT}...")
with open(INPUT, 'r', encoding='utf-8') as f:
    data = json.load(f)

print(f"Диалогов: {len(data)}")

texts = []
total_messages = 0

for conv in data:
    title = conv.get('title', '')[:100]
    mapping = conv.get('mapping', {})
    
    for key, msg in mapping.items():
        if msg.get('message') is None:
            continue
        
        m = msg['message']
        fragments = m.get('fragments', [])
        
        for frag in fragments:
            content = frag.get('content', '')
            if isinstance(content, str) and len(content) > 10:
                texts.append({
                    'title': title,
                    'text': content,
                    'role': 'user' if 'user' in str(msg.get('author', '')).lower() else 'assistant',
                })
                total_messages += 1

print(f"Сообщений: {total_messages}")

# Сохраняем
with open(OUTPUT, 'w', encoding='utf-8') as f:
    json.dump(texts, f, ensure_ascii=False, indent=2)

print(f"✅ Сохранено в {OUTPUT}: {len(texts)} текстов")
size_kb = __import__('os').path.getsize(OUTPUT) / 1024
print(f"   Размер: {size_kb:.0f} КБ")