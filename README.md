# SEACE Scraper API

API para scraper de la plataforma SEACE desarrollada con FastAPI.

## Estructura del Proyecto

Este proyecto sigue un flujo de desarrollo iterativo:

1. **Experimentos** (`experiments/`) - Pruebas empíricas y scrapers simples
2. **Código de Producción** (`src/`) - Scrapers modularizados y async
3. **Tests** (`tests/`) - Tests unitarios
4. **API** (`app/`) - Endpoints FastAPI

## Instalación

### Requisitos

- Python 3.10 o superior
- pip

### Instalación de dependencias

```bash
# Instalar dependencias de producción
make install

# O instalar dependencias de desarrollo (incluye herramientas de testing)
make install-dev
```

## Uso

### Desarrollo

```bash
# Ejecutar servidor de desarrollo
make dev

# O directamente con uvicorn
uvicorn app.main:app --reload
```

La API estará disponible en `http://localhost:8000`

Documentación automática disponible en:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Tests

```bash
# Ejecutar tests
make test

# Tests con cobertura
make test-cov
```

### Linting y Formateo

```bash
# Ejecutar linters
make lint

# Formatear código
make format
```

## Documentación

La documentación del proyecto se encuentra en `docs/`:

- `docs/active/` - Trabajo en progreso
- `docs/completed/` - Tareas completadas
- `docs/reference/` - Documentación de referencia
- `docs/ideas/` - Ideas futuras
- `docs/archived/` - Ideas descartadas

Para más detalles sobre la arquitectura y el plan de desarrollo, ver `docs/reference/plan.md`.

## Docker

```bash
# Construir imagen
make docker-build

# Ejecutar con docker-compose
make docker-run

# Detener
make docker-down
```

## Despliegue

Este proyecto está configurado para desplegarse en Railway. Ver `docs/reference/plan.md` para más detalles.

## Licencia

MIT
