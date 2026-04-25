"""
API сервер для VMMS Workstation.
Обрабатывает запросы на ПИД-автоподбор P/T, расчёт стабильности и т.д.
"""

import sys
import os
import json
import numpy as np
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

# Добавляем пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src'))
sys.path.insert(0, os.path.join(PROJECT_ROOT, 'src', 'architect'))

from thermodynamics import ThermodynamicState, check_phonon_stability, compute_cluster_energy
from biharmonic_3d import TopologicalArchitect3D

app = Flask(__name__, static_folder='.')
CORS(app)  # Разрешаем кросс-доменные запросы

# Загружаем данные элементов при старте
elements_data = None

def load_elements():
    global elements_data
    if elements_data is None:
        with open('data/field_H_elements_complete.json', 'r', encoding='utf-8') as f:
            elements_data = json.load(f)
    return elements_data

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/results/<path:filename>')
def serve_results(filename):
    return send_from_directory('results', filename)

@app.route('/api/pid_autotune', methods=['POST'])
def pid_autotune():
    """
    Автоматический подбор давления для стабилизации кластера.
    
    Ожидает JSON:
    {
        "cluster": [{"symbol": "Mg", "pos": [0,0,0]}, ...],
        "T": 300,
        "P_min": 0.1,
        "P_max": 500.0
    }
    """
    data = request.json
    cluster = data['cluster']
    T = data.get('T', 300.0)
    P_min = data.get('P_min', 0.1)
    P_max = data.get('P_max', 500.0)
    
    # Формируем positions и elements
    positions = np.array([item['pos'] for item in cluster])
    elements = []
    elem_config = load_elements()
    
    for item in cluster:
        symbol = item['symbol']
        # Ищем элемент в конфиге
        elem = next((e for e in elem_config['vortex_components'] if e['symbol'] == symbol), None)
        if elem:
            elements.append({
                'Z': elem['Z'],
                'symmetry_group': elem.get('symmetry_group', 'C∞v'),
                'vortex_number': elem.get('vortex_number', 1),
                'mass': elem.get('mass', elem['Z'] * 2)
            })
        else:
            elements.append({
                'Z': 1, 'symmetry_group': 'C∞v', 'vortex_number': 1, 'mass': 1
            })
    
    # Функция энергии для check_phonon_stability
    def energy_function(pos, elems, state):
        return compute_cluster_energy(pos, elems, state)
    
    # Бинарный поиск P_crit
    def is_stable(P):
        state = ThermodynamicState(T, P)
        return check_phonon_stability(positions, elements, energy_function, state)
    
    # Проверяем, стабильно ли уже при P_min
    if is_stable(P_min):
        return jsonify({
            'status': 'stable',
            'P_crit': P_min,
            'message': f'Структура стабильна уже при {P_min} GPa'
        })
    
    # Проверяем, стабильно ли при P_max
    if not is_stable(P_max):
        return jsonify({
            'status': 'unstable',
            'P_crit': None,
            'message': f'Структура нестабильна даже при {P_max} GPa'
        })
    
    # Бинарный поиск
    P_low, P_high = P_min, P_max
    while P_high - P_low > 1.0:
        P_mid = (P_low + P_high) / 2
        if is_stable(P_mid):
            P_high = P_mid
        else:
            P_low = P_mid
    
    P_crit = P_high
    
    return jsonify({
        'status': 'found',
        'P_crit': round(P_crit, 1),
        'message': f'P_crit = {P_crit:.1f} GPa'
    })

@app.route('/api/check_stability', methods=['POST'])
def check_stability():
    """
    Проверка стабильности кластера при заданных T и P.
    """
    data = request.json
    cluster = data['cluster']
    T = data.get('T', 300.0)
    P = data.get('P', 0.1)
    
    positions = np.array([item['pos'] for item in cluster])
    elements = []
    elem_config = load_elements()
    
    for item in cluster:
        symbol = item['symbol']
        elem = next((e for e in elem_config['vortex_components'] if e['symbol'] == symbol), None)
        if elem:
            elements.append({
                'Z': elem['Z'],
                'symmetry_group': elem.get('symmetry_group', 'C∞v'),
                'vortex_number': elem.get('vortex_number', 1),
                'mass': elem.get('mass', elem['Z'] * 2)
            })
        else:
            elements.append({'Z': 1, 'symmetry_group': 'C∞v', 'vortex_number': 1, 'mass': 1})
    
    state = ThermodynamicState(T, P)
    
    def energy_function(pos, elems, st):
        return compute_cluster_energy(pos, elems, st)
    
    is_stable = check_phonon_stability(positions, elements, energy_function, state)
    energy = compute_cluster_energy(positions, elements, state)
    
    return jsonify({
        'is_stable': is_stable,
        'energy': round(energy, 3),
        'T': T,
        'P': P
    })

@app.route('/api/cluster_from_selection', methods=['POST'])
def cluster_from_selection():
    """
    Формирует кластер из выбранных элементов (центр + соседи в радиусе).
    """
    data = request.json
    center_symbol = data['center']
    radius = data.get('radius', 6.0)
    
    # Загружаем координаты из финального файла
    with open('results/autosave_T300.0_P0.1_128_local_final.json', 'r') as f:
        results = json.load(f)
    
    elements = results['elements']
    
    # Находим центр
    center = next((e for e in elements if e['symbol'] == center_symbol), None)
    if not center:
        return jsonify({'error': f'Элемент {center_symbol} не найден'}), 404
    
    center_pos = np.array([float(x) for x in center['position']])
    
    # Находим соседей
    cluster = [{
        'symbol': center['symbol'],
        'pos': center_pos.tolist()
    }]
    
    for e in elements:
        if e['symbol'] == center_symbol:
            continue
        pos = np.array([float(x) for x in e['position']])
        dist = np.linalg.norm(center_pos - pos)
        if dist < radius:
            cluster.append({
                'symbol': e['symbol'],
                'pos': pos.tolist()
            })
    
    return jsonify({
        'center': center_symbol,
        'radius': radius,
        'cluster': cluster,
        'count': len(cluster)
    })

if __name__ == '__main__':
    print("=" * 60)
    print("🚀 VMMS API Server запущен")
    print("=" * 60)
    print("Откройте http://localhost:5000 в браузере")
    print("Для остановки нажмите Ctrl+C")
    app.run(host='0.0.0.0', port=5000, debug=True)