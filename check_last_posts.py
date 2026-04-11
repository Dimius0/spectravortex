import httpx
import json
from pathlib import Path

key_path = Path.home() / '.config/moltbook/credentials.json'
with open(key_path) as f:
    api_key = json.load(f)['api_key']

headers = {'Authorization': f'Bearer {api_key}'}

with httpx.Client(timeout=30) as client:
    r = client.get('https://www.moltbook.com/api/v1/posts', headers=headers, params={'author': 'theobot_vm_387', 'limit': 5})
    if r.status_code == 200:
        posts = r.json().get('posts', [])
        for post in posts[:5]:
            print(f"ID: {post.get('id')}")
            print(f"Title: {post.get('title')}")
            print(f"Created: {post.get('created_at')}")
            print('---')
    else:
        print(f'Ошибка: {r.status_code}')