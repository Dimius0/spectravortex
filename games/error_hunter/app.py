#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask-сервер для "Охотника за ошибками"
Связывает HTML-интерфейс с лесом знаний
"""

from flask import Flask, request, jsonify, send_from_directory
import sys
import os
import random
import math
from pathlib import Path

# Добавляем путь к проекту
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

# Пытаемся импортировать лес знаний
try:
    from prototype_fractal.knowledge_forest import KnowledgeForest, KnowledgeTree, ErrorGenerator
    FOREST_AVAILABLE = True
    print("✅ Лес знаний загружен")
except ImportError as e:
    print(f"⚠️ Лес знаний не найден: {e}")
    print("⚠️ Работаем в демо-режиме")
    FOREST_AVAILABLE = False

app = Flask(__name__)

# Глобальные переменные
forest = None
generator = None
materials_db = []

def init_forest():
    """Инициализирует лес с материалами"""
    global forest, generator, materials_db
    
    if not FOREST_AVAILABLE:
        # Демо-режим
        materials_db = [
            {'id': 1, 'name': 'графен чистый', 'base_potential': 100},
            {'id': 2, 'name': 'графен с вакансиями', 'base_potential': 120},
            {'id': 3, 'name': 'MOF-цирконий', 'base_potential': 150},
            {'id': 4, 'name': 'Bi2Se3 (топоизол)', 'base_potential': 200},
            {'id': 5, 'name': 'осадок со свалки', 'base_potential': 50},
            {'id': 6, 'name': 'торф после пожара', 'base_potential': 80},
            {'id': 7, 'name': 'речной графен', 'base_potential': 300},
        ]
        return
    
    # Реальный лес
    forest = KnowledgeForest()
    
    # Этаж 3 — материалы
    materials_tree = KnowledgeTree(3, "materials", (0.5, 3.0))
    
    materials = [
        ("графен чистый", 0, 100),
        ("графен с вакансиями", 0.3, 120),
        ("графен с CuO", 0.5, 150),
        ("MOF-цирконий", 0.2, 130),
        ("MOF дефектный", 0.6, 160),
        ("Bi2Se3", 0.4, 200),
        ("Bi2Te3", 0.7, 220),
        ("осадок со свалки", 1.2, 50),
        ("торф после пожара", 1.5, 80),
        ("речной графен", 1.8, 300),
    ]
    
    for name, tau_shift, base_p in materials:
        node_id = materials_tree.add_node(materials_tree.root_id, name, tau_shift)
        # Сохраняем базовый потенциал для демо
        if not hasattr(materials_tree.nodes[node_id].params, 'base_potential'):
            materials_tree.nodes[node_id].params.base_potential = base_p
    
    forest.add_tree(materials_tree)
    
    # Этаж 1 — физические принципы (для связей)
    physics_tree = KnowledgeTree(1, "physics", (0.1, 1.0))
    physics_tree.add_node(physics_tree.root_id, "квантовое туннелирование", 0)
    physics_tree.add_node(physics_tree.root_id, "спиновая синхронизация", 0.2)
    physics_tree.add_node(physics_tree.root_id, "фазовый переход", 0.1)
    physics_tree.add_node(physics_tree.root_id, "вихревое накопление", 0.3)
    forest.add_tree(physics_tree)
    
    # Проращиваем начальные связи
    print("🌱 Проращиваем связи...")
    forest.grow_all(threshold=0.3)
    print(f"   Создано связей: {forest.total_connections()}")
    
    # Создаём генератор ошибок
    generator = ErrorGenerator(forest)
    
    # Собираем базу материалов
    materials_db = []
    for k, tree in forest.trees.items():
        if k == 3:
            for node_id, node in tree.nodes.items():
                base_p = getattr(node.params, 'base_potential', node.params.n * (1 + node.params.H))
                materials_db.append({
                    'id': node_id,
                    'name': node.name,
                    'base_potential': round(base_p, 1)
                })

# Инициализируем при старте
init_forest()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/materials')
def get_materials():
    return jsonify(materials_db)

@app.route('/api/experiment', methods=['POST'])
def run_experiment():
    data = request.json
    material_id = data.get('material_id')
    violations = data.get('violations', [])
    
    # Сила нарушений (случайная, но разная для разных типов)
    strength_map = {
        'temp': (0.3, 0.8),
        'pressure': (0.2, 0.7),
        'purity': (0.4, 1.0),
        'time': (0.1, 0.4),
        'field': (0.3, 0.6)
    }
    
    violation_list = []
    for v in violations:
        lo, hi = strength_map.get(v, (0.2, 0.5))
        violation_list.append(random.uniform(lo, hi))
    
    N = len(violation_list)
    
    # Ищем материал в базе
    material = next((m for m in materials_db if m['id'] == material_id), None)
    if not material:
        return jsonify({'error': 'Material not found'}), 404
    
    if generator and FOREST_AVAILABLE:
        # Режим с реальным лесом
        P, status = generator.experiment(material_id, violation_list)
        P0 = material['base_potential']
        
        # Определяем класс для CSS
        if status == "обычный":
            status_class = ""
        elif status == "аномальный":
            status_class = "anomaly"
        elif status == "прорывной":
            status_class = "breakthrough"
        else:
            status_class = "unknown"
    else:
        # Демо-режим
        P0 = material['base_potential']
        delta_sum = sum(violation_list)
        P = P0 * (1 + delta_sum) * math.exp(N)
        
        # Классификация
        ratio = P / P0
        if ratio < 2:
            status = "обычный"
            status_class = ""
        elif ratio < 5:
            status = "аномальный"
            status_class = "anomaly"
        elif ratio < 20:
            status = "прорывной"
            status_class = "breakthrough"
        else:
            status = "НЕИЗВЕСТНОЕ"
            status_class = "unknown"
    
    return jsonify({
        'material': material['name'],
        'violations': N,
        'P0': round(P0, 1),
        'P': round(P, 1),
        'status': status,
        'status_class': status_class
    })

@app.route('/api/suggest')
def suggest_experiment():
    if generator and FOREST_AVAILABLE:
        node_id, name, N = generator.suggest_experiment()
        return jsonify({
            'material_id': node_id,
            'name': name,
            'suggested_violations': N
        })
    else:
        # Демо-режим
        material = random.choice(materials_db)
        N = random.randint(1, 4)
        return jsonify({
            'material_id': material['id'],
            'name': material['name'],
            'suggested_violations': N
        })

if __name__ == '__main__':
    print("=" * 60)
    print("🦉 ОХОТНИК ЗА ОШИБКАМИ")
    print("=" * 60)
    print(f"📍 Режим: {'РЕАЛЬНЫЙ ЛЕС' if FOREST_AVAILABLE else 'ДЕМО'}")
    print("📍 Открой в браузере: http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)