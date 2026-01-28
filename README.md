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

### Probar endpoints (Postman)

Puedes probar la API con Postman creando una **Collection** y usando como base URL:

- `http://localhost:8000`

#### 1) Health

- **Method**: `GET`
- **URL**: `{{base_url}}/health`
- **Respuesta esperada**:

```json
{ "status": "ok" }
```

#### 2) Scrape Regional

- **Method**: `POST`
- **URL**: `{{base_url}}/scrape/regional`
- **Headers**:
  - `Content-Type: application/json`
- **Body (raw JSON)**:

```json
{
  "departamento": "AREQUIPA",
  "anio": "2025",
  "output_csv": null,
  "debug": false
}
```

**Respuesta esperada (modo async por jobs):**

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

#### 3) Scrape por Nomenclatura

- **Method**: `POST`
- **URL**: `{{base_url}}/scrape/nomenclatura`
- **Headers**:
  - `Content-Type: application/json`
- **Body (raw JSON)**:

```json
{
  "nomenclatura": "SIE-SIE-1-2026-SEDAPAR-1",
  "debug": false
}
```

**Respuesta esperada (modo async por jobs):**

```json
{
  "job_id": "uuid",
  "status": "queued"
}
```

#### 4) Consultar el Job

- **Method**: `GET`
- **URL**: `{{base_url}}/jobs/{{job_id}}`

#### 5) Obtener resultado del Job

- **Method**: `GET`
- **URL**: `{{base_url}}/jobs/{{job_id}}/result`

**Respuesta esperada:**

```json
{
  "job_id": "uuid",
  "status": "succeeded",
  "result": {
    "departamento": "AREQUIPA",
    "anio": "2025",
    "total_registros": 150,
    "csv_path": "/ruta/absoluta/data/procesos_AREQUIPA_2025.csv"
  },
  "error": null
}
```

#### 6) Descargar CSV del Job (solo para jobs regionales)

- **Method**: `GET`
- **URL**: `{{base_url}}/jobs/{{job_id}}/download`

**Descripción:** Descarga el archivo CSV generado por un job de tipo `regional`. El job debe estar completado (`status: "succeeded"`).

**Respuesta:** Archivo CSV descargable con el nombre del archivo original.

**Errores posibles:**
- `404`: Job no encontrado
- `400`: Job no completado o no es de tipo `regional`
- `404`: Archivo CSV no encontrado

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

## Herramientas de desarrollo (debug)

### Instalar navegadores de Playwright

En Windows (PowerShell), usa:

```bash
python -m playwright install chromium
```

### Scripts de debug

- `scripts/debug_regional.py`: ejecuta el scraper regional en modo `debug=True` y guarda CSV/artefactos en `debug/`.
- `scripts/debug_nomenclatura.py`: ejecuta el scraper de nomenclatura en modo `debug=True` y guarda JSON/artefactos en `debug/`.

Ejemplos:

```bash
python scripts/debug_regional.py --departamento AREQUIPA --anio 2025
python scripts/debug_nomenclatura.py --nomenclatura "SIE-SIE-1-2026-SEDAPAR-1"
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

### Deploy en Railway (mínimo, funcional)

**Modo recomendado:** Docker (para incluir Playwright/Chromium).

1) En Railway, crea un proyecto y conecta tu repo.
2) Asegúrate de que Railway detecte el `Dockerfile`.
3) Configura variables de entorno (si quieres):
   - `SEACE_HEADLESS=true` (recomendado en producción)
   - `LOG_LEVEL=INFO`
   - `SEACE_NETWORK_TIMEOUT=30000`
4) Railway expone `PORT` automáticamente; el contenedor usa `uvicorn` con `--port $PORT`.

**Endpoints (modo async por jobs):**
- `POST /scrape/regional` → devuelve `job_id`
- `POST /scrape/nomenclatura` → devuelve `job_id`
- `GET /jobs/{job_id}` → estado
- `GET /jobs/{job_id}/result` → resultado

**Nota importante:** los jobs son **in-memory**. Si Railway reinicia el contenedor, se pierden jobs en progreso/historial.

## Licencia

MIT
