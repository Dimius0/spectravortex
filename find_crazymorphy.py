import httpx
import json
import time  # ← добавить
from pathlib import Path

key_path = Path.home() / '.config/moltbook/credentials.json'
with open(key_path) as f:
    api_key = json.load(f)['api_key']

headers = {'Authorization': f'Bearer {api_key}'}

print('🔍 Получаем все посты TheoBot...')
with httpx.Client(timeout=30) as client:
    r = client.get('https://www.moltbook.com/api/v1/posts', headers=headers, 
                   params={'author': 'theobot_vm_387', 'limit': 30})
    if r.status_code == 200:
        posts = r.json().get('posts', [])
        print(f'✅ Найдено {len(posts)} постов\n')
        
        for post in posts:
            post_id = post.get('id')
            title = post.get('title', '')[:50]
            print(f'📝 Пост: {title}...')
            
            r2 = client.get(f'https://www.moltbook.com/api/v1/posts/{post_id}/comments', headers=headers)
            if r2.status_code == 200:
                comments = r2.json().get('comments', [])
                for c in comments:
                    author = c.get('author', {}).get('name', '')
                    if 'crazymorphy' in author:
                        print(f'   ✅ Найден! ID поста: {post_id}')
                        print(f'   Комментарий: {c.get("content")[:100]}...')
                        print(f'   ID комментария: {c.get("id")}')
                        print()
            time.sleep(0.5)  # пауза между запросами
    else:
        print(f'❌ Ошибка: {r.status_code}')