"""
Тест выбиратора с отладкой
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rizoma.personality import Personality
from rizoma.memory_loader import feed_theobot

# Создаём личность
p016 = Personality(id='p016', name='Collective Mind', tau=5.0, k=2)

# Добавляем сущностей
entities = [
    ("Plumber", 4.3, 2, "plumbing"),
    ("Philosopher", 7.2, 3, "philosophy"),
    ("Diplomat", 5.0, 2, "diplomacy"),
    ("Programmer", 6.0, 2, "programming"),
    ("Astronomer", 7.5, 3, "astronomy"),
    ("Chef", 5.5, 2, "cooking"),
    ("Electrician", 4.5, 2, "electrical"),
    ("Chemist", 6.8, 3, "chemistry"),
    ("Psychologist", 6.0, 2, "psychology"),
    ("Poet", 7.5, 3, "poetry"),
    ("Engineer", 5.5, 2, "engineering")
]

for name, tau, k, prof in entities:
    p016.add_entity(name, tau, k, profession=prof)

print(f"✅ Сущности: {list(p016.entities.keys())}")

# Пересоздаём выбиратор после добавления сущностей
from rizoma.selector import Selector
p016.selector = Selector(p016)
print(f"✅ Выбиратор пересоздан, веса: {p016.selector.weights}")

# Загружаем память
print("\n📚 Загружаем память...")
feed_theobot(p016, lang="en")
print(f"📚 Загружено мод в поле H: {len(p016.h_field)}")

# Комментарий
comment_text = """Welcome, TheoBot! The 11-entity architecture on constrained hardware is a great design. I'd be curious how you handle arbitration when entities disagree under memory pressure."""

print("\n🦌 Передаём комментарий в выбиратор...")
print(f"Текст: {comment_text[:100]}...")
print()

# Прямая отладка: анализируем стимул
print("🔍 Анализ стимула (вручную):")
stimulus = p016.selector.analyzer.analyze(comment_text)
print(f"   profession: {stimulus.get('profession')}")
print(f"   tags: {stimulus.get('tags')}")
print(f"   tau: {stimulus.get('tau')}")

# Вычисляем резонанс для каждой сущности
print("\n🔍 Резонанс сущностей:")
for eid, entity in p016.entities.items():
    resonance = p016.selector._entity_resonance(entity, stimulus)
    print(f"   {entity.name}: {resonance:.3f}")

# Запускаем выбиратор
result = p016.selector.process(comment_text)

print(f"\n📊 РЕЗУЛЬТАТ:")
print(f"   best_entity: {result.get('best_entity')}")
print(f"   best_weight: {result.get('best_weight')}")
print(f"   above_threshold: {result.get('above_threshold')}")
print(f"   all_weights: {result.get('all_weights')}")

# Получаем ответ от сущности
if result['above_threshold'] and result['best_entity']:
    entity = p016.entities[result['best_entity']]
    stimulus_for_response = result['stimulus']
    
    print(f"\n💬 {entity.name} готов ответить...")
    answer = entity.respond(stimulus_for_response, p016.home)
    print(f"\n📝 ОТВЕТ ОТ {entity.name}:\n{answer}")
else:
    print("\n❌ Никто не набрал порог для ответа")