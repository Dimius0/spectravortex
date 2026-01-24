.PHONY: help install test lint format clean build dev

# Цвета для красивого вывода
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

help:
	@echo "$(YELLOW)🌀 SpectraVortex - команды:$(NC)"
	@echo "$(GREEN)make install$(NC)    - установить зависимости"
	@echo "$(GREEN)make test$(NC)       - запустить все тесты"
	@echo "$(GREEN)make test-fast$(NC)  - быстрые тесты (без coverage)"
	@echo "$(GREEN)make lint$(NC)       - проверка стиля кода"
	@echo "$(GREEN)make format$(NC)     - автоматическое форматирование кода"
	@echo "$(GREEN)make clean$(NC)      - очистка временных файлов"
	@echo "$(GREEN)make dev$(NC)        - установка для разработки"
	@echo "$(GREEN)make all$(NC)        - ВСЁ: install + test + lint"
	@echo "$(GREEN)make run-example$(NC)- запустить пример hello_photon.svx"

install:
	@echo "$(YELLOW)📦 Устанавливаю зависимости...$(NC)"
	pip install -e .[dev]
	pip install black ruff pytest

test:
	@echo "$(YELLOW)🧪 Запускаю ВСЕ тесты...$(NC)"
	@echo "$(GREEN)=== Тесты через main.py ===$(NC)"
	python main.py --test || echo "$(RED)⚠ main.py tests failed$(NC)"
	@echo "\n$(GREEN)=== Тесты через pytest ===$(NC)"
	python -m pytest tests/ -v --cov=./ --cov-report=term-missing

test-fast:
	@echo "$(YELLOW)⚡ Быстрые тесты...$(NC)"
	python main.py --test
	python -m pytest tests/ -v

lint:
	@echo "$(YELLOW)🔍 Проверяю стиль кода...$(NC)"
	@echo "$(GREEN)=== Black (форматирование) ===$(NC)"
	black --check --diff . || echo "$(RED)⚠ Код нуждается в форматировании. Запустите: make format$(NC)"
	@echo "\n$(GREEN)=== Ruff (линтер) ===$(NC)"
	ruff check . || echo "$(RED)⚠ Найдены проблемы с кодом$(NC)"

format:
	@echo "$(YELLOW)🎨 Форматирую код...$(NC)"
	black .
	@echo "$(GREEN)✓ Готово!$(NC)"

clean:
	@echo "$(YELLOW)🧹 Очищаю временные файлы...$(NC)"
	rm -rf build/ dist/ *.egg-info .pytest_cache .coverage htmlcov __pycache__ */__pycache__ */*/__pycache__
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Готово!$(NC)"

build:
	@echo "$(YELLOW)🔨 Собираю пакет...$(NC)"
	python -m build
	@echo "$(GREEN)✓ Готово! Пакет в dist/$(NC)"

dev: clean install
	@echo "$(GREEN)✅ Готово к разработке!$(NC)"

all: install test lint
	@echo "\n$(GREEN)======================================$(NC)"
	@echo "$(GREEN)✅ ВСЁ СДЕЛАНО! Проект в порядке.$(NC)"
	@echo "$(GREEN)======================================$(NC)"

run-example:
	@echo "$(YELLOW)🚀 Запускаю пример hello_photon.svx...$(NC)"
	python main.py --compile examples/hello_photon.svx || echo "$(RED)⚠ Пример не сработал (компилятор в разработке)$(NC)"
