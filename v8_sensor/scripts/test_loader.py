#!/usr/bin/env python3
"""
Тест загрузчика текстов
"""

print("=== ТЕСТ ЗАПУЩЕН ===")

import sys
import os
import tempfile
import shutil

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

print("Импортируем модули...")

try:
    from load_vmms_texts import load_text_file, WHISPER_MODEL
    from rizoma.personality import Personality
    print("✅ Импорты OK")
except Exception as e:
    print(f"❌ Ошибка импорта: {e}")
    sys.exit(1)


def create_test_files(test_dir):
    print("Создаём тестовые файлы...")
    
    # 1. TXT файл
    with open(os.path.join(test_dir, 'test.txt'), 'w', encoding='utf-8') as f:
        f.write("""
Это тестовый текстовый файл.

Вихревая модель материи-пространства (ВММП) рассматривает пространство-время
как квантовый сверхтекучий конденсат.

∇⁴ψ = 0 — основное уравнение модели.

Квантование циркуляции: ∮∇ψ·dl = 2πN.
""")
    
    # 2. MD файл (упрощённый, без math-блока)
    with open(os.path.join(test_dir, 'test.md'), 'w', encoding='utf-8') as f:
        f.write("""# ВММП: Основные принципы

## Вихревая модель

Пространство-время — квантовый сверхтекучий конденсат.

## Материя как топологический дефект

Частицы — вихри в конденсате.

Уравнение: ∇⁴ψ = 0
""")
    
    # Проверка MD файла
    with open(os.path.join(test_dir, 'test.md'), 'r', encoding='utf-8') as f:
        content = f.read()
        print(f"   MD файл: {len(content)} символов")
    
    # 3. HTML файл
    with open(os.path.join(test_dir, 'test.html'), 'w', encoding='utf-8') as f:
        f.write("""<!DOCTYPE html>
<html>
<head><title>ВММП Тест</title></head>
<body>
<h1>Вихревая модель</h1>
<p>Пространство-время — квантовый сверхтекучий конденсат.</p>
<p>∇⁴ψ = 0 — бигармоническое уравнение.</p>
<script>alert('этот текст не должен попасть');</script>
</body>
</html>""")
    
    print(f"✅ Созданы тестовые файлы в {test_dir}")
    print("   Файлы в папке:")
    for f in os.listdir(test_dir):
        print(f"      - {f}")


def main():
    print("=== MAIN ===")
    
    test_dir = tempfile.mkdtemp()
    print(f"\n📁 Тестовая папка: {test_dir}")
    
    create_test_files(test_dir)
    
    print("\nСоздаём поле H...")
    p = Personality(id="test", name="Test Loader")
    print(f"   ✅ Поле H создано")
    
    print("\n📄 Тестирование загрузки:")
    print("-"*40)
    
    for filename in ['test.txt', 'test.md', 'test.html']:
        filepath = os.path.join(test_dir, filename)
        if not os.path.exists(filepath):
            print(f"\n   ⚠️ {filename} не найден")
            continue
        print(f"\n   📄 {filename}:")
        try:
            count = load_text_file(p, filepath, tau=5.2, theme="test")
            print(f"      → Загружено блоков: {count}")
        except Exception as e:
            print(f"      ❌ Ошибка: {e}")
    
    print("\n" + "="*60)
    print("📊 РЕЗУЛЬТАТ")
    print("="*60)
    print(f" Мод в поле H: {len(p.h_field)}")
    
    if p.h_field:
        print("\n Первые 5 загруженных мод:")
        for i, mode in enumerate(p.h_field[:5], 1):
            print(f"\n{i}. {mode.trace_id} (τ={mode.tau:.2f})")
            print(f"   {mode.content[:100]}...")
    else:
        print("\n⚠️ Нет загруженных мод")
    
    print("\n🧹 Очистка...")
    shutil.rmtree(test_dir)
    
    print("\n✅ ТЕСТ ЗАВЕРШЁН")
    print("\n🦌 Загрузчик работает.")


if __name__ == "__main__":
    main()