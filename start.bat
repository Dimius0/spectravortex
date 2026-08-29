@echo off
title 🌲 Лес Знаний — TEES
chcp 65001 >nul
color 0A

echo.
echo   🌲 Лес Знаний — TEES
echo   ====================
echo.

:: Проверяем Python
python --version >nul 2>&1
if errorlevel 1 (
    echo   ❌ Python не найден!
    echo   📥 Скачайте с https://python.org
    echo.
    pause
    exit
)

:: Показываем версию Python
echo   ✅ Python найден:
python --version
echo.

:: Устанавливаем зависимости
echo   📦 Устанавливаем зависимости...
pip install psutil --quiet 2>nul
echo   ✅ Зависимости готовы
echo.

:: Запускаем Лес Знаний
echo   🌲 Запускаю Лес Знаний...
echo   Откройте http://localhost:8080/forest.html
echo.

python forest_server.py

pause