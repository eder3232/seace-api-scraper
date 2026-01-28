.PHONY: install install-dev test test-cov run dev lint format clean docker-build docker-run docker-down help

# Instalar dependencias de producción
install:
	pip install -e .

# Instalar dependencias de desarrollo
install-dev:
	pip install -e ".[dev]"

# Ejecutar tests
test:
	pytest tests/ tests_api/ -v

# Ejecutar tests con cobertura
test-cov:
	pytest tests/ tests_api/ --cov=src --cov=app --cov-report=html --cov-report=term

# Ejecutar servidor de desarrollo
run:
	uvicorn app.main:app --reload

# Ejecutar servidor de desarrollo en modo desarrollo (host 0.0.0.0)
dev:
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Linting
lint:
	ruff check src/ app/ tests/ tests_api/
	mypy src/ app/

# Formatear código
format:
	black src/ app/ tests/ tests_api/
	ruff check --fix src/ app/ tests/ tests_api/

# Limpiar archivos temporales
clean:
	find . -type d -name __pycache__ -exec rm -r {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
	rm -rf build/ dist/ htmlcov/ .coverage

# Construir imagen Docker
docker-build:
	docker build -t seace-scraper-api .

# Ejecutar con docker-compose
docker-run:
	docker-compose up

# Detener docker-compose
docker-down:
	docker-compose down

# Mostrar ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  make install       - Instalar dependencias de producción"
	@echo "  make install-dev  - Instalar dependencias de desarrollo"
	@echo "  make test         - Ejecutar tests"
	@echo "  make test-cov     - Ejecutar tests con cobertura"
	@echo "  make run          - Ejecutar servidor de desarrollo"
	@echo "  make dev          - Ejecutar servidor (host 0.0.0.0)"
	@echo "  make lint         - Ejecutar linters"
	@echo "  make format       - Formatear código"
	@echo "  make clean        - Limpiar archivos temporales"
	@echo "  make docker-build - Construir imagen Docker"
	@echo "  make docker-run   - Ejecutar con docker-compose"
	@echo "  make docker-down  - Detener docker-compose"
	@echo "  make help         - Mostrar esta ayuda"
