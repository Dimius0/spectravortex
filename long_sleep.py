import sys, os, time
sys.path.insert(0, 'v8_sensor/src')
sys.path.insert(0, 'src/architect')
from hybrid_bridge import HybridBridge

print('=' * 60)
print('LONG SLEEP: 5 hours')
print('=' * 60)

bridge = HybridBridge('src/rizoma/data/personalities/p016_grown_3h.json')

bridge.session_questions = [
    'What is TEES?',
    'How does Yumi effect work?',
    'Tell about gravity',
    'What is VMMP?',
    'DeepSeek theorem',
    'Hoyle state',
    'Transition layers',
    'Yumi catapult',
    'Godel and TEES',
    'Water experiment',
]

print(f'Context: {len(bridge.session_questions)} themes')
print('Starting 5 sleep cycles with 1 hour interval...')
print('-' * 60)

for cycle in range(5):
    print(f'\nSleep cycle {cycle+1}/5...')
    result = bridge.sleep()
    print(f'   Result: {result["answer"]}')
    stats = bridge.memory.get_stats()
    print(f'   Bridges: {stats["bridge_modes"]} | Timeline: {stats["timeline_size"]}')
    
    if cycle < 4:
        print(f'   Waiting 60 minutes...')
        time.sleep(3600)

bridge.save('src/rizoma/data/personalities/p016_hybrid_v3_slept_5h.json')
print('\n' + '=' * 60)
print('AWAKENING AFTER 5 HOURS OF SLEEP')
print('=' * 60)
stats = bridge.memory.get_stats()
print(f'Total bridges: {stats["bridge_modes"]}')
print(f'Total timeline: {stats["timeline_size"]}')
print('Saved: p016_hybrid_v3_slept_5h.json')
