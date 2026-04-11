import json
import re
import os

BROKEN_FILE = 'src/rizoma/data/personalities/p016_fractal_v16_1.json'
RECOVERED_FILE = 'src/rizoma/data/personalities/p016_fractal_v16_1_recovered.json'

print("=" * 60)
print("🔧 ЫТ ССТЯ Т JSON")
print("=" * 60)

if not os.path.exists(BROKEN_FILE):
    print(f"❌ айл не найден: {BROKEN_FILE}")
    exit(1)

size_mb = os.path.getsize(BROKEN_FILE) / 1024 / 1024
print(f"📁 сходный файл: {BROKEN_FILE}")
print(f"   азмер: {size_mb:.1f} ")

# итаем файл как текст
with open(BROKEN_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"📄 рочитано символов: {len(content)}")

# 1. робуем найти и исправить пропущенные запятые
# Типичная ошибка: } { → }, {
fixed = re.sub(r'}\s*{', '},{', content)

# 2. робуем найти и исправить пропущенные запятые в массивах
# ] [ → ], [
fixed = re.sub(r'\]\s*\[', '],[', fixed)

# 3. робуем обрезать до последнего валидного места
# (если файл обрезан в конце)
try:
    # робуем найти последнюю完整的 запись
    last_valid = fixed.rfind('}')
    if last_valid > 0:
        # щем начало последней完整的 записи
        start_valid = fixed.rfind('{', 0, last_valid)
        if start_valid > 0:
            fixed = fixed[:last_valid+1]
            print(f"✂️ брезано до последней完整 записи")
except:
    pass

# робуем загрузить исправленный вариант
try:
    data = json.loads(fixed)
    modes_count = len(data.get('h_field', []))
    print(f"\n✅ СХ! JSON восстановлен!")
    print(f"   оды: {modes_count}")
    
    # Сохраняем восстановленный файл
    with open(RECOVERED_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"💾 Сохранено: {RECOVERED_FILE}")
    
except json.JSONDecodeError as e:
    print(f"\n❌ е удалось восстановить полностью")
    print(f"   шибка: {e}")
    print(f"   озиция: {e.pos}")
    
    # робуем обрезать до позиции ошибки
    try:
        truncated = fixed[:e.pos]
        # щем последнюю完整 запись
        last_brace = truncated.rfind('}')
        if last_brace > 0:
            truncated = truncated[:last_brace+1] + ']}'
            data = json.loads(truncated)
            modes_count = len(data.get('h_field', []))
            print(f"\n⚠️ астичное восстановление (обрезано до ошибки)")
            print(f"   оды: {modes_count}")
            
            with open(RECOVERED_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"💾 Сохранено: {RECOVERED_FILE}")
    except:
        print("   е удалось восстановить даже частично")

print("\n" + "=" * 60)
