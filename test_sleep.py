import sys, os
sys.path.insert(0, 'v8_sensor/src')
sys.path.insert(0, 'src/architect')
from hybrid_bridge import HybridBridge

print("Loading hybrid...")
bridge = HybridBridge('src/rizoma/data/personalities/p016_grown_3h.json')

# онтекст сессии
bridge.session_questions = [
    'What is TEES?',
    'How does the Yumi effect work?',
    'What is gravity?',
]

print("\nStarting sleep cycle...")
r = bridge.sleep()
print(f"\nResult: {r['answer']}")

stats = bridge.memory.get_stats()
print(f"\nBridges created: {stats['bridge_modes']}")
print(f"Timeline size: {stats['timeline_size']}")

# Тестируем поиск после сна
print("\nSearch after sleep: TEES")
results = bridge.memory.find_relevant_modes('TEES')
for mode_id, score, summary in results[:5]:
    print(f"  [{score:.2f}] {summary[:80]}...")
