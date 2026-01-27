# ============================================
# SpectraVortex Makefile
# Optimized for fast testing
# ============================================

.PHONY: help install dev test test-fast test-all test-ci lint format clean build

# Colors for output
GREEN = \033[0;32m
YELLOW = \033[1;33m
RED = \033[0;31m
NC = \033[0m # No Color

help:
	@echo "$(GREEN)SpectraVortex - Quantum Chip Management System$(NC)"
	@echo ""
	@echo "$(YELLOW)Available commands:$(NC)"
	@echo "  $(GREEN)make help$(NC)       - Show this help message"
	@echo "  $(GREEN)make install$(NC)    - Install dependencies"
	@echo "  $(GREEN)make dev$(NC)        - Install dev dependencies"
	@echo ""
	@echo "$(YELLOW)Testing:$(NC)"
	@echo "  $(GREEN)make test$(NC)       - Run fast tests (default)"
	@echo "  $(GREEN)make test-fast$(NC)  - Fast tests only (< 10 sec)"
	@echo "  $(GREEN)make test-all$(NC)   - All tests (< 30 sec)"
	@echo "  $(GREEN)make test-ci$(NC)    - CI/CD tests (< 70 sec)"
	@echo ""
	@echo "$(YELLOW)Code Quality:$(NC)"
	@echo "  $(GREEN)make lint$(NC)       - Run linter"
	@echo "  $(GREEN)make format$(NC)     - Format code"
	@echo ""
	@echo "$(YELLOW)Cleanup:$(NC)"
	@echo "  $(GREEN)make clean$(NC)      - Clean temporary files"
	@echo "  $(GREEN)make build$(NC)      - Build project"

# ============================================
# Installation
# ============================================

install:
	@echo "$(YELLOW)Installing main dependencies...$(NC)"
	@pip install -e .

dev:
	@echo "$(YELLOW)Installing dev dependencies...$(NC)"
	@pip install -e ".[dev]"

# ============================================
# Testing
# ============================================

test-fast:
	@echo "$(YELLOW)Running FAST tests (timeout: 10 seconds)...$(NC)"
	@echo "$(GREEN)=== Tests via pytest (fast) ===$(NC)"
	@python -m pytest tests/test_adaptive_router_fast.py \
		-v \
		--tb=short \
		--disable-warnings \
		--timeout=10 \
		--cov=router \
		--cov-report=term-missing
	@echo "$(GREEN)✅ Fast tests completed$(NC)"

test-all:
	@echo "$(YELLOW)Running ALL tests (timeout: 30 seconds)...$(NC)"
	@echo "$(GREEN)=== Tests via main.py ===$(NC)"
	@python main.py --test || echo "$(RED)▲ main.py tests failed$(NC)"
	@echo ""
	@echo "$(GREEN)=== Tests via pytest ===$(NC)"
	@python -m pytest tests/ \
		-v \
		--tb=short \
		--disable-warnings \
		--timeout=30 \
		--cov=. \
		--cov-report=term-missing
	@echo "$(GREEN)✅ All tests completed$(NC)"

test-ci:
	@echo "$(YELLOW)Running CI/CD tests (optimized)...$(NC)"
	@echo "$(GREEN)=== PHASE 1: Fast tests (timeout: 10 seconds) ===$(NC)"
	@python -m pytest tests/ \
		-v \
		-m "not slow and not performance" \
		--tb=short \
		--disable-warnings \
		--timeout=10 \
		--cov=router \
		--cov-report=term-missing || (echo "$(RED)❌ Fast tests failed$(NC)" && exit 1)
	@echo "$(GREEN)✅ Fast tests passed$(NC)"
	@echo ""
	@echo "$(GREEN)=== PHASE 2: Slow tests (timeout: 60 seconds) ===$(NC)"
	@python -m pytest tests/ \
		-v \
		-m "slow or performance" \
		--tb=short \
		--disable-warnings \
		--timeout=60 \
		--cov=router \
		--cov-report=term-missing || (echo "$(RED)❌ Slow tests failed$(NC)" && exit 1)
	@echo "$(GREEN)✅ All CI tests passed$(NC)"

# Alias for make test (fast tests by default)
test: test-fast

# ============================================
# Code Quality
# ============================================

lint:
	@echo "$(YELLOW)Running code checks...$(NC)"
	@echo "$(GREEN)=== Flake8 ===$(NC)"
	@flake8 router/ tests/ --count --max-complexity=10 --max-line-length=127 --statistics
	@echo "$(GREEN)=== MyPy (type checking) ===$(NC)"
	@mypy router/ --ignore-missing-imports
	@echo "$(GREEN)✅ Code checks completed$(NC)"

format:
	@echo "$(YELLOW)Formatting code...$(NC)"
	@black router/ tests/
	@isort router/ tests/
	@echo "$(GREEN)✅ Formatting completed$(NC)"

# ============================================
# Cleanup and Build
# ============================================

clean:
	@echo "$(YELLOW)Cleaning temporary files...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type f -name "*.pyd" -delete
	@find . -type f -name ".coverage" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".coverage" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .eggs/ htmlcov/ coverage.xml .ruff_cache/
	@echo "$(GREEN)✅ Cleanup completed$(NC)"

build:
	@echo "$(YELLOW)Building project...$(NC)"
	@python setup.py sdist bdist_wheel
	@echo "$(GREEN)✅ Build completed$(NC)"

# ============================================
# Helper Commands
# ============================================

run-router-demo:
	@echo "$(YELLOW)Running router demo...$(NC)"
	@python -c "
from router.adaptive_router import create_adaptive_router

router = create_adaptive_router(grid_size=0.1)

# Simple test
start = (0.0, 0.0)
end = (1.0, 1.0)

print('Adaptive router demo:')
print(f'Routing from {start} to {end}')

result = router.find_path(start, end)

if result.success:
    print(f'✅ Success! Algorithm: {result.algorithm.value}')
    print(f'   Time: {result.time_spent:.3f} sec')
    print(f'   Path length: {len(result.path)} points')
    # Show first and last points
    if len(result.path) > 4:
        print(f'   First points: {result.path[:3]}...')
        print(f'   Last points: ...{result.path[-3:]}')
    else:
        print(f'   Full path: {result.path}')
else:
    print(f'❌ Error: {result.error_message}')
"

coverage:
	@echo "$(YELLOW)Generating coverage report...$(NC)"
	@python -m pytest tests/test_adaptive_router_fast.py \
		--cov=router \
		--cov-report=html \
		--cov-report=term-missing
	@echo "$(GREEN)Coverage report: file://$(shell pwd)/htmlcov/index.html$(NC)"

# Aliases for convenience
quick-test: test-fast
full-test: test-all
ci: test-ci
check: lint
fmt: format
