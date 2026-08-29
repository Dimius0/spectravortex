#!/bin/bash

echo "🌲 Лес Знаний — TEES"
echo "===================="
echo

# Проверяем Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python не найден!"
    echo "📥 Установите: sudo apt install python3"
    exit 1
fi

echo "✅ Python найден:"
python3 --version
echo

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip3 install psutil --quiet
echo "✅ Зависимости готовы"
echo

# Запускаем Лес Знаний
echo "🌲 Запускаю Лес Знаний..."
echo "Откройте http://localhost:8080/forest.html"
echo

python3 forest_server.py