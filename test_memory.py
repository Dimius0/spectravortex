import json
from pathlib import Path

def find_memory_file():
    """Ищет core_traces.json во всех возможных местах"""
    
    possible_paths = [
        Path("memory_trees/theobot_vm_387/core_traces.json"),
        Path("src/memory_trees/theobot_vm_387/core_traces.json"),
        Path("../memory_trees/theobot_vm_387/core_traces.json"),
        Path("./theobot_vm_387/core_traces.json"),
        Path("C:/Users/Dim/source/repos/spectravortex/memory_trees/theobot_vm_387/core_traces.json"),
    ]
    
    for path in possible_paths:
        if path.exists():
            print(f"✅ Файл найден: {path}")
            return path
    
    print("❌ Файл не найден ни в одном из ожидаемых мест")
    return None

def test_memory():
    memory_file = find_memory_file()
    
    if not memory_file:
        return False
    
    with open(memory_file, 'r', encoding='utf-8') as f:
        traces = json.load(f)
    
    print(f"\n📊 ЗАГРУЖЕНО ТРАСС: {len(traces)}")
    print("="*50)
    
    discoveries = [t for t in traces if t.get("trace_type") == "discovery"]
    alchemy = [t for t in traces if t.get("trace_type") == "alchemy"]
    predictions = [t for t in traces if t.get("trace_type") == "prediction"]
    
    print(f"📁 discoveries: {len(discoveries)} трасс")
    print(f"📁 alchemy: {len(alchemy)} трасс")
    print(f"📁 predictions: {len(predictions)} трасс")
    print("="*50)
    
    if traces:
        print("\n🔍 ПРОВЕРКА ПЕРВОЙ ТРАССЫ:")
        first = traces[0]
        print(f"trace_id: {first.get('trace_id')}")
        print(f"trace_type: {first.get('trace_type')}")
        print(f"themes: {first.get('themes')}")
        print(f"_base_weight: {first.get('_base_weight')}")
        print(f"link: {first.get('link')}")
        print(f"content: {first.get('content', '')[:100]}...")
    
    print("\n✅ Тест завершён!")
    return True

if __name__ == "__main__":
    test_memory()