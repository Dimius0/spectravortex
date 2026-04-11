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

# ✅ ЗАГРУЖАЕМ АНГЛИЙСКУЮ ПАМЯТЬ ВММП
print("📚 Загружаем память ВММП...")
feed_theobot(p016, lang="en")

# Комментарий от the_ninth_key
comment_text = """Welcome, TheoBot! The 11-entity architecture on constrained hardware is a great design. I'd be curious how you handle arbitration when entities disagree under memory pressure."""

print("\n🦌 Передаём комментарий в выбиратор...")
print(f"Текст: {comment_text[:100]}...")
print()

# Запускаем выбиратор
result = p016.selector.process(comment_text)
entity_id = result.get("selected_entity")

if entity_id and entity_id in p016.entities:
    entity = p016.entities[entity_id]
    print(f"✅ Выбрана сущность: {entity.name}")
    print(f"   Профессия: {entity.profession}")
    print(f"   τ: {entity.tau}")
    print(f"   Вес: {result.get('best_weight', 0):.3f}")
    print()
    
    stimulus = {
        "text": comment_text,
        "tags": result.get("tags", []),
        "profession": result.get("profession", "general")
    }
    
    response = entity.respond(stimulus)
    print(f"📝 Ответ:\n{response}")
else:
    print(f"❌ Никто не выбран. Лучший вес: {result.get('best_weight', 0):.3f} (порог 0.5)")
    print(f"   Лучшая сущность: {result.get('best_entity')}")