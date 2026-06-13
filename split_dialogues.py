# split_dialogues.py — разделение диалогов на разговорные и программные
import json

INPUT = 'dialogue_texts.json'
OUTPUT_TALK = 'talk_texts.json'
OUTPUT_CODE = 'code_texts.json'

with open(INPUT, 'r', encoding='utf-8') as f:
    all_texts = json.load(f)

talk = []
code = []

code_markers = [
    'def ', 'import ', 'class ', 'return ', 'self.', 'print(',
    'pip install', 'git ', 'python', '```', '{', '}',
    'except ', 'try:', 'from ', 'import ', ' as ',
    ' = ', ' += ', ' -= ', ' *= ', ' /= ',
    'def __init__', 'lambda ', 'yield ', 'raise ',
]

for item in all_texts:
    text = item.get('text', '')
    if not text:
        continue
    
    # Считаем признаки кода
    code_score = 0
    for marker in code_markers:
        if marker in text:
            code_score += 1
    
    # Считаем признаки разговора
    talk_score = 0
    if '?' in text:
        talk_score += 1
    if any(w in text.lower() for w in ['привет', 'как дела', 'что такое', 'расскажи', 'объясни', 'спасибо']):
        talk_score += 1
    
    if code_score > talk_score:
        code.append(item)
    else:
        talk.append(item)

print(f'Всего: {len(all_texts)}')
print(f'Разговоры: {len(talk)}')
print(f'Код: {len(code)}')

with open(OUTPUT_TALK, 'w', encoding='utf-8') as f:
    json.dump(talk, f, ensure_ascii=False)
print(f'✅ {OUTPUT_TALK}')

with open(OUTPUT_CODE, 'w', encoding='utf-8') as f:
    json.dump(code, f, ensure_ascii=False)
print(f'✅ {OUTPUT_CODE}')