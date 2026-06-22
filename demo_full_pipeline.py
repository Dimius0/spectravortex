#!/usr/bin/env python3
"""
demo_full_pipeline.py — Полная демонстрация пайплайна SpectraVortex.
От потоковой загрузки данных до нарративной интерпретации.
"""

import os
import sys
import tempfile
import hashlib
import numpy as np
from pathlib import Path

# Подключаем модули
from field_analyzer import CleanFieldStreamingAdapter
from field_interpreter import FieldInterpreter, NarrativeStyle, DataKnowledgeBase


def generate_test_file(size_mb: int = 5, filepath: str = None) -> str:
    """
    Генерирует тестовый файл со смешанными данными для демонстрации.
    """
    if filepath is None:
        filepath = os.path.join(tempfile.gettempdir(), "spectravortex_demo.dat")
    
    print(f"📦 Генерация тестового файла ({size_mb} МБ)...")
    
    with open(filepath, 'wb') as f:
        # 1. Текстовая часть (30%) — русский и английский
        text1 = b"Hello SpectraVortex! This is a demonstration file for the full analysis pipeline. " * 1000
        text2 = "Привет мир! Это демонстрационный файл для полного пайплайна анализа. ".encode('utf-8') * 1000
        f.write(text1 + text2)
        
        # 2. Структурированные данные (30%) — симуляция протокола
        protocol = b'\x01\x02\x03\x04\x05\x06\x07\x08' * 1000
        f.write(protocol)
        
        # 3. Криптографические данные (20%) — симуляция хешей
        hashes = b''.join([hashlib.sha256(str(i).encode()).digest() for i in range(100)])
        f.write(hashes * 20)
        
        # 4. Случайный шум (20%)
        random_data = np.random.bytes(int(size_mb * 0.2 * 1024 * 1024))
        f.write(random_data)
    
    print(f"✅ Файл создан: {filepath} ({os.path.getsize(filepath) / 1024 / 1024:.1f} МБ)")
    return filepath


def run_demo():
    """
    Основная демонстрация пайплайна.
    """
    print("╔═══════════════════════════════════════════════════╗")
    print("║   SPECTRAVORTEX — ПОЛНЫЙ ПАЙПЛАЙН АНАЛИЗА       ║")
    print("╚═══════════════════════════════════════════════════╝")
    
    # Шаг 1: Генерация тестового файла
    print("\n" + "="*60)
    print("ШАГ 1: ПОДГОТОВКА ДАННЫХ")
    print("="*60)
    
    test_file = generate_test_file(size_mb=2)
    
    # Шаг 2: Потоковый анализ
    print("\n" + "="*60)
    print("ШАГ 2: ПОТОКОВЫЙ АНАЛИЗ (field_analyzer)")
    print("="*60)
    
    adapter = CleanFieldStreamingAdapter(work_dir="./demo_work")
    
    print("\n🚀 Запуск анализа...")
    report = adapter.stream_load(
        test_file,
        n=8,                    # Размер n-граммы
        chunk_size=1024*1024,   # Чанки по 1 МБ
        num_workers=4,          # 4 потока
    )
    
    if report is None:
        print("❌ Анализ не удался")
        return
    
    print("\n📊 Отчёт анализа:")
    print(f"   Природа данных: {report.data_nature.value}")
    print(f"   Энтропия: {report.entropy:.2f} бит/байт")
    print(f"   Индекс структуры: {report.structure_index:.3f}")
    print(f"   Комплексность: {report.complexity_score:.3f}")
    print(f"   Уникальных n-грамм: {report.unique_grams}")
    print(f"   Грамматических правил: {report.total_rules}")
    print(f"   Обменных паттернов: {report.total_patterns}")
    
    # Шаг 3: Интерпретация
    print("\n" + "="*60)
    print("ШАГ 3: НАРРАТИВНАЯ ИНТЕРПРЕТАЦИЯ (field_interpreter)")
    print("="*60)
    
    # Интерпретатор в детективном стиле
    interpreter_detective = FieldInterpreter(style=NarrativeStyle.DETECTIVE)
    result_detective = interpreter_detective.interpret(report)
    
    print("\n🕵️ ДЕТЕКТИВНЫЙ СТИЛЬ:")
    print(f"   Вердикт: {result_detective.verdict}")
    print(f"   Уверенность: {result_detective.confidence.value}")
    print(f"   Лучшее совпадение: {result_detective.data_identity['best_match']} "
          f"({result_detective.data_identity['match_score']:.0%})")
    
    print("\n📖 Нарратив:")
    print(result_detective.narrative[:500] + "..." if len(result_detective.narrative) > 500 else result_detective.narrative)
    
    # Интерпретатор в научном стиле
    interpreter_scientific = FieldInterpreter(style=NarrativeStyle.SCIENTIFIC)
    result_scientific = interpreter_scientific.interpret(report)
    
    print("\n🔬 НАУЧНЫЙ СТИЛЬ:")
    print(f"   Вердикт: {result_scientific.verdict}")
    print(f"   Подзаголовок: {result_scientific.subtitle}")
    
    # Вывод доказательств
    if result_scientific.evidence:
        print("\n🔍 КЛЮЧЕВЫЕ ДОКАЗАТЕЛЬСТВА:")
        for ev in result_scientific.evidence[:5]:
            print(f"   • {ev.fact}")
            print(f"     → {ev.interpretation}")
    
    # Вывод рекомендаций
    if result_scientific.recommendations:
        print("\n💡 РЕКОМЕНДАЦИИ:")
        for rec in result_scientific.recommendations:
            print(f"   • [{rec['priority']}] {rec['action']}")
            print(f"     → {rec['detail']}")
    
    if result_scientific.next_steps:
        print("\n📋 СЛЕДУЮЩИЕ ШАГИ:")
        for step in result_scientific.next_steps:
            print(f"   • {step}")
    
    if result_scientific.warnings:
        print("\n⚠️ ПРЕДУПРЕЖДЕНИЯ:")
        for w in result_scientific.warnings:
            print(f"   • {w}")
    
    # Шаг 4: Очистка
    print("\n" + "="*60)
    print("ШАГ 4: ОЧИСТКА")
    print("="*60)
    
    os.remove(test_file)
    print(f"🧹 Удалён тестовый файл: {test_file}")
    
    import shutil
    shutil.rmtree("./demo_work", ignore_errors=True)
    print("🧹 Удалена рабочая директория: ./demo_work")
    
    print("\n" + "="*60)
    print("✅ ДЕМОНСТРАЦИЯ ЗАВЕРШЕНА")
    print("="*60)
    
    print("\n📌 Итоговый вывод:")
    print(f"   Тип данных: {report.data_nature.value}")
    print(f"   Структура: {report.structure_index:.3f} (наличие: {'да' if report.structure_index > 0.3 else 'нет'})")
    print(f"   Грамматика: {report.total_rules} правил (сложность: {'высокая' if report.total_rules > 10 else 'средняя' if report.total_rules > 3 else 'низкая'})")
    print(f"   Аномалии: {len(report.anomalies) if hasattr(report, 'anomalies') else 0}")
    
    return report, result_scientific


def run_single_file_demo(filepath: str):
    """
    Демонстрация на одном реальном файле.
    """
    print("╔═══════════════════════════════════════════════════╗")
    print("║   SPECTRAVORTEX — АНАЛИЗ ОДНОГО ФАЙЛА           ║")
    print("╚═══════════════════════════════════════════════════╝")
    
    if not os.path.exists(filepath):
        print(f"❌ Файл не найден: {filepath}")
        return
    
    print(f"\n📂 Файл: {filepath}")
    print(f"   Размер: {os.path.getsize(filepath) / 1024 / 1024:.2f} МБ")
    
    # Анализ
    adapter = CleanFieldStreamingAdapter(work_dir="./single_demo_work")
    report = adapter.stream_load(filepath, n=8, chunk_size=1024*1024, num_workers=4)
    
    if report is None:
        print("❌ Анализ не удался")
        return
    
    # Интерпретация
    interpreter = FieldInterpreter(style=NarrativeStyle.EDUCATIONAL)
    result = interpreter.interpret(report)
    
    print("\n" + "="*60)
    print("📖 ИНТЕРПРЕТАЦИЯ")
    print("="*60)
    
    print(f"\n🎯 ВЕРДИКТ: {result.verdict}")
    print(f"📊 Уверенность: {result.confidence.value}")
    
    print(f"\n📖 НАРРАТИВ:")
    print(result.narrative)
    
    if result.next_steps:
        print(f"\n💡 СЛЕДУЮЩИЕ ШАГИ:")
        for step in result.next_steps:
            print(f"   • {step}")
    
    # Очистка
    import shutil
    shutil.rmtree("./single_demo_work", ignore_errors=True)
    
    return report, result


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="SpectraVortex — полный пайплайн анализа")
    parser.add_argument("--file", type=str, help="Путь к файлу для анализа")
    parser.add_argument("--demo", action="store_true", default=True, 
                       help="Запустить демонстрацию на синтетическом файле")
    
    args = parser.parse_args()
    
    if args.file:
        run_single_file_demo(args.file)
    else:
        run_demo()