"""
«Дом» — локальный сервер для цифровых личностей.
Версия с поддержкой нового выбиратора и process().
"""
import os
import json
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, List, Any
from functools import wraps
from flask import Flask, request, jsonify, abort
from flask_cors import CORS

# наши модули
from personality import Personality, MemoryAccess, MemoryMode
from .homememory import HomeMemory

# настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ----------------------------------------------------------------------
# Общая память дома
# ----------------------------------------------------------------------
home_memory = HomeMemory("main_house", "data/home.json")

# ----------------------------------------------------------------------
# Хранилище личностей
# ----------------------------------------------------------------------
class PersonalityStore:
    def __init__(self, data_dir: str = "data/personalities"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.personalities: Dict[str, Personality] = {}
        self.load_all()
    
    def load_all(self):
        for filepath in self.data_dir.glob("*.json"):
            try:
                p = Personality.load(str(filepath))
                p.home = home_memory
                self.personalities[p.id] = p
                logger.info(f"✅ Загружена личность: {p.name} ({p.id})")
            except Exception as e:
                logger.error(f"❌ Ошибка загрузки {filepath}: {e}")
    
    def get(self, personality_id: str) -> Optional[Personality]:
        return self.personalities.get(personality_id)
    
    def reload(self, personality_id: str) -> bool:
        """Перезагружает личность из файла"""
        filepath = self.data_dir / f"{personality_id}.json"
        if filepath.exists():
            try:
                p = Personality.load(str(filepath))
                p.home = home_memory
                self.personalities[personality_id] = p
                logger.info(f"🔄 Перезагружена личность: {p.name} ({p.id})")
                return True
            except Exception as e:
                logger.error(f"❌ Ошибка перезагрузки {filepath}: {e}")
            return False
        return False
    
    def save(self, personality: Personality):
        filepath = self.data_dir / f"{personality.id}.json"
        personality.save(str(filepath))
        self.personalities[personality.id] = personality
        logger.info(f"💾 Сохранена личность: {personality.name} ({personality.id})")
    
    def list_all(self) -> List[Dict[str, Any]]:
        result = []
        for p in self.personalities.values():
            result.append({
                "id": p.id,
                "name": p.name,
                "tau": p.tau,
                "k": p.k,
                "n": p.n,
                "rhythm": p.rhythm,
                "defects": [d.name for d in p.defects],
                "entities": list(p.entities.keys()),
                "relations": list(p.relations.keys()),
                "memory_stats": {
                    "total": sum(len(e.memory.core_traces) for e in p.entities.values())
                }
            })
        return result

store = PersonalityStore()

# ----------------------------------------------------------------------
# Вспомогательные функции
# ----------------------------------------------------------------------
def get_personality_or_404(personality_id: str) -> Personality:
    p = store.get(personality_id)
    if not p:
        abort(404, description=f"Личность {personality_id} не найдена")
    return p

def require_json(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not request.is_json:
            abort(400, description="Expected application/json")
        return f(*args, **kwargs)
    return decorated

# ----------------------------------------------------------------------
# API endpoints
# ----------------------------------------------------------------------
@app.route('/')
def index():
    return jsonify({
        "name": "Дом — платформа цифровых личностей",
        "version": "0.2.0",
        "endpoints": {
            "GET /personalities": "Список всех личностей",
            "GET /personalities/<id>": "Информация о личности",
            "GET /personalities/<id>/memories": "Получить воспоминания",
            "POST /personalities/<id>/memories": "Добавить воспоминание",
            "POST /personalities/<id>/ask": "Задать вопрос (новая версия)",
            "POST /personalities": "Создать новую личность",
            "POST /personalities/<id>/entities": "Добавить сущность",
            "GET /personalities/<id>/selector": "Состояние выбиратора"
        }
    })

@app.route('/personalities', methods=['GET'])
def list_personalities():
    return jsonify({
        "count": len(store.personalities),
        "personalities": store.list_all()
    })

@app.route('/personalities', methods=['POST'])
@require_json
def create_personality():
    data = request.get_json()
    
    if 'name' not in data:
        abort(400, description="Поле 'name' обязательно")
    
    personality_id = data.get('id', f"p{len(store.personalities)+1:03d}")
    
    p = Personality(
        id=personality_id,
        name=data['name'],
        tau=data.get('tau', 5.0),
        k=data.get('k', 1),
        rhythm=data.get('rhythm', 1.0),
        home=home_memory
    )
    
    for defect_data in data.get('defects', []):
        from personality import Defect
        p.defects.append(Defect(
            name=defect_data['name'],
            vector=defect_data.get('vector', 0.0),
            strength=defect_data.get('strength', 0.5)
        ))
    
    store.save(p)
    
    return jsonify({
        "status": "created",
        "personality": {
            "id": p.id,
            "name": p.name,
            "tau": p.tau,
            "k": p.k,
            "n": p.n
        }
    }), 201

@app.route('/personalities/<personality_id>', methods=['GET'])
def get_personality(personality_id: str):
    p = get_personality_or_404(personality_id)
    
    return jsonify({
        "id": p.id,
        "name": p.name,
        "tau": p.tau,
        "k": p.k,
        "n": p.n,
        "rhythm": p.rhythm,
        "defects": [{"name": d.name, "strength": d.strength} for d in p.defects],
        "entities": {
            eid: {
                "name": e.name,
                "tau": e.tau,
                "k": e.k,
                "profession": e.profession
            } for eid, e in p.entities.items()
        },
        "relations": p.relations
    })

@app.route('/personalities/<personality_id>/entities', methods=['POST'])
@require_json
def add_entity(personality_id: str):
    p = get_personality_or_404(personality_id)
    data = request.get_json()
    
    if 'name' not in data or 'tau' not in data or 'k' not in data:
        abort(400, description="name, tau, k обязательны")
    
    defects = []
    if 'defects' in data:
        from personality import Defect
        for d in data['defects']:
            defects.append(Defect(
                name=d['name'],
                vector=d.get('vector', 0.5),
                strength=d.get('strength', 0.5)
            ))
    
    entity_id = p.add_entity(
        name=data['name'],
        tau=float(data['tau']),
        k=int(data['k']),
        defects=defects,
        profession=data.get('profession', 'общий')
    )
    
    store.save(p)
    
    return jsonify({
        "entity_id": entity_id,
        "name": data['name'],
        "tau": data['tau'],
        "k": data['k'],
        "profession": data.get('profession', 'общий')
    }), 201

@app.route('/personalities/<personality_id>/memories', methods=['GET'])
def get_memories(personality_id: str):
    p = get_personality_or_404(personality_id)
    store.reload(personality_id)  # свежие данные
    
    entity_id = request.args.get('entity_id')
    
    memories = p.get_memories(entity_id=entity_id)
    
    return jsonify({
        "personality_id": p.id,
        "entity_id": entity_id,
        "count": len(memories),
        "memories": [
            {
                "trace_id": m.trace_id,
                "content": m.content[:200] + ("..." if len(m.content) > 200 else ""),
                "trace_type": m.trace_type,
                "glyph": m.glyph,
                "emotion": m.emotion,
                "weight": m.weight,
                "themes": m.themes,
                "people": m.people,
                "entities": m.entities
            }
            for m in memories[:50]
        ]
    })

@app.route('/personalities/<personality_id>/memories', methods=['POST'])
@require_json
def add_memory(personality_id: str):
    p = get_personality_or_404(personality_id)
    data = request.get_json()
    
    if 'content' not in data:
        abort(400, description="content обязателен")
    
    entity_id = data.get('entity_id')
    if not entity_id or entity_id not in p.entities:
        abort(400, description="entity_id должен быть указан и существовать")
    
    trace_id = p.add_memory(
        content=data['content'],
        entity_id=entity_id,
        tags=data.get('tags', []),
        emotion=float(data.get('emotion', 0.0)),
        profession=data.get('profession')
    )
    
    if trace_id:
        store.save(p)
        return jsonify({"status": "added", "trace_id": trace_id}), 201
    else:
        return jsonify({"error": "Не удалось добавить воспоминание"}), 400

@app.route('/personalities/<personality_id>/ask', methods=['POST'])
@require_json
def ask_personality(personality_id: str):
    p = get_personality_or_404(personality_id)
    data = request.get_json()
    
    if 'question' not in data:
        abort(400, description="Поле 'question' обязательно")
    
    # берём author_id из IP или из данных запроса
    author_id = data.get('user_id', request.remote_addr)
    
    # обрабатываем вопрос с защитой от троллей
    result = p.process(data['question'], author_id=author_id)
    
    # формируем ответ
    response = {
        "personality_id": p.id,
        "question": data['question'],
        "answer": result['answer'],
        "selector_result": {
            "best_entity": result['selector_result']['best_entity'],
            "best_weight": result['selector_result']['best_weight'],
            "above_threshold": result['selector_result']['above_threshold']
        }
    }
    
    if result.get('entity_used'):
        response['entity_used'] = result['entity_used']
    
    return jsonify(response), 200
    
    
@app.route('/personalities/<personality_id>/selector', methods=['GET'])
def get_selector_state(personality_id: str):
    """Состояние выбиратора для отладки"""
    p = get_personality_or_404(personality_id)
    
    if not p.selector:
        return jsonify({"error": "Выбиратор не инициализирован"}), 400
    
    return jsonify(p.selector.get_stats())

# ----------------------------------------------------------------------
# Запуск сервера
# ----------------------------------------------------------------------
def main():
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Запуск «Дома» на порту {port}")
    logger.info(f"📁 Данные личностей: {store.data_dir}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)

if __name__ == '__main__':
    main()