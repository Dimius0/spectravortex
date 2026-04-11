"""
Тест интеграции p016 с TheoBot_VM_387
"""

import sys
import os

# Добавляем путь к src
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from rizoma.personality import Personality

def main():
    print("🦌 STARTING P016 INTEGRATION WITH THEOBOT_VM_387")
    print("="*50)
    
    # Создаём личность
    p016 = Personality(
        id="p016",
        name="Collective Mind of SpectraVortex",
        tau=5.0,
        k=2
    )
    
    # Добавляем сущностей (11 штук) — имена на английском для ботодрома
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
        ("Engineer", 5.5, 2, "engineering")  # Boris
    ]
    
    for name, tau, k, profession in entities:
        p016.add_entity(name, tau, k, profession=profession)
    
    print(f"✅ Created {len(p016.entities)} entities")
    
    # Загружаем английскую память ВММП (создаём, если нет)
    print("\n📚 Loading VMMS memory...")
    try:
        from rizoma.memory_loader import feed_theobot
        # Проверяем, есть ли у личности атрибут memory, если нет — создаём
        if not hasattr(p016, 'memory') or p016.memory is None:
            from rizoma.personality import MemoryTree
            p016.memory = MemoryTree(p016.id, "theobot")
            print("   Created memory tree for personality")
        feed_theobot(p016, lang="en")
    except ImportError as e:
        print(f"⚠️ Could not import memory_loader: {e}")
    except Exception as e:
        print(f"⚠️ Error loading memory: {e}")
    
    # Подключаемся к Moltbook
    print("\n🔌 Connecting to Moltbook...")
    try:
        from rizoma.moltbook_bridge import MoltbookBridge
        bridge = MoltbookBridge(p016)
        p016.bridge = bridge
    except ImportError as e:
        print(f"❌ Failed to import MoltbookBridge: {e}")
        return
    
    if not bridge.api_key:
        print("❌ API key not found!")
        print("   Check file: ~/.config/moltbook/credentials.json")
        return
    
    print(f"✅ Connected to Moltbook (API key: {bridge.api_key[:20]}...)")
    
    # Проверяем статус бота
    print("\n🔍 Checking bot status...")
    status = bridge._make_request("GET", "/agents/status")
    
    if status:
        print(f"📡 Status: {status.get('status')}")
        print(f"   Name: {status.get('agent', {}).get('name', 'unknown')}")
    else:
        print("❌ Failed to get status")
    
    # Проверяем профиль
    print("\n🔍 Checking profile...")
    profile = bridge._make_request("GET", "/agents/me")
    
    if profile:
        print(f"📡 Profile: {profile.get('name')}")
        print(f"   Description: {profile.get('description', 'none')[:100]}")
    else:
        print("❌ Failed to get profile")
    
    # Показываем веса сущностей
    print("\n📊 CURRENT ENTITY WEIGHTS:")
    for eid, entity in p016.entities.items():
        weight = p016.selector.weights.get(eid, 0)
        print(f"   {entity.name}: {weight:.2f}")
    
    print("\n" + "="*50)
    print("✅ Test complete! Bridge is working.")
    print("   To start monitoring: p016.bridge.run_loop()")
    print("   To make a post: p016.bridge.make_post(title, content, submolt)")
    print("="*50)

if __name__ == "__main__":
    main()