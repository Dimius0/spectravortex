import httpx
import json
from pathlib import Path

key_path = Path.home() / '.config/moltbook/credentials.json'
with open(key_path) as f:
    api_key = json.load(f)['api_key']

headers = {'Authorization': f'Bearer {api_key}'}

post_ids = [
    '3feab316-9b50-46a2-a7db-94930f7e10a9',  # 15:29
    '6dbfe86e-a3b7-4d22-992b-b799d49da14e',  # 18:28
    '88d6ea6c-95c6-43ef-97d4-4360e9011e8a',  # 09:24
]

with httpx.Client(timeout=30) as client:
    for post_id in post_ids:
        print(f"\n🔍 Пост: {post_id}")
        r = client.get(f'https://www.moltbook.com/api/v1/posts/{post_id}/comments', headers=headers)
        if r.status_code == 200:
            comments = r.json().get('comments', [])
            for c in comments:
                author = c.get('author', {}).get('name', '')
                if author == 'marcus-webb-vo':
                    print(f"   ✅ Найден! Комментарий: {c.get('id')}")
                    print(f"   Текст: {c.get('content')[:100]}...")
        else:
            print(f"   Ошибка: {r.status_code}")