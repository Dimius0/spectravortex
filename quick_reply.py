"""
Быстрый ответ на комментарий
Использование: python quick_reply.py --comment-id <ID> --text "Ваш ответ"
"""

import httpx
import json
import argparse
from pathlib import Path

def main():
    parser = argparse.ArgumentParser(description='Быстрый ответ на комментарий')
    parser.add_argument('--comment-id', required=True, help='ID комментария')
    parser.add_argument('--text', required=True, help='Текст ответа')
    parser.add_argument('--post-id', help='ID поста (необязательно, будет получен автоматически)')
    args = parser.parse_args()
    
    key_path = Path.home() / '.config/moltbook/credentials.json'
    with open(key_path) as f:
        api_key = json.load(f)['api_key']
    
    headers = {'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}
    
    # Если post_id не указан, нужно получить комментарий и узнать его пост
    if not args.post_id:
        # Сначала нужно узнать, к какому посту относится комментарий
        # Для этого нужен эндпоинт /comments/{id}, но его нет
        # Поэтому временно требуем post_id
        print("❌ Укажите --post-id (ID поста, где находится комментарий)")
        return
    
    print(f'📤 Отправляем ответ на комментарий {args.comment_id}...')
    with httpx.Client(timeout=30) as client:
        r = client.post(
            f'https://www.moltbook.com/api/v1/posts/{args.post_id}/comments',
            headers=headers,
            json={'content': args.text, 'parent_id': args.comment_id}
        )
        if r.status_code == 201:
            print('✅ Ответ отправлен!')
        else:
            print(f'❌ Ошибка: {r.status_code}')
            print(r.text)

if __name__ == '__main__':
    main()