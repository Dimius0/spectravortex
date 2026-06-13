import sys, os
sys.path.insert(0, 'v8_sensor/src')
sys.path.insert(0, 'src/architect')
from hybrid_bridge import HybridBridge

bridge = HybridBridge('src/rizoma/data/personalities/p016_grown_3h.json')

ru_questions = [
    'то такое ТС?',
    'ак работает эффект ми?',
    'асскажи про гравитацию',
    'то такое ?',
    'то такой орис?',
]

for q in ru_questions:
    print(f'\n{"="*50}')
    print(f'❓ {q}')
    r = bridge.think(q)
    print(f'🤖 {r["answer"][:400]}')
