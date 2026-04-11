import httpx
import json
from pathlib import Path
import sys

if len(sys.argv) < 3:
    print("Использование: python reply_to_post.py <post_id> <text>")
    sys.exit(1)

post_id = sys.argv[1]
text = sys.argv[2]

key_path = Path.home() / '.config/moltbook/credentials.json'
with open(key_path) as f:
    api_key = json.load(f)['api_key']

headers = {
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
}

print(f'📤 Отправляем ответ на пост {post_id}...')

with httpx.Client(timeout=30) as client:
    r = client.post(
        f'https://www.moltbook.com/api/v1/posts/{post_id}/comments',
        headers=headers,
        json={'content': text}
    )
    
    if r.status_code == 201:
        print('✅ Ответ отправлен!')
        print(f'   https://moltbook.com/post/{post_id}')
    else:
        print(f'❌ Ошибка: {r.status_code}')
        print(r.text)