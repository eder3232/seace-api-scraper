# Checklist: Verificación de Scrapers Completos

## Scraper Regional (`src/scrapers/regional.py`)

### Métodos del Experimental vs Producción

| Método Experimental | Método Producción | Estado |
|---------------------|-------------------|--------|
| `start()` | Heredado de `BaseScraper.start()` | ✅ |
| `navigate_to_seace()` | Heredado de `BaseScraper.navigate_to_seace()` | ✅ |
| `select_search_type()` | Heredado de `BaseScraper.select_search_type()` | ✅ |
| `click_busqueda_avanzada()` | Heredado de `BaseScraper.click_busqueda_avanzada()` | ✅ |
| `desplegar_boton_para_seleccionar_departamento()` | `desplegar_boton_para_seleccionar_departamento()` | ✅ |
| `seleccionar_departamento()` | `seleccionar_departamento()` | ✅ |
| `desplegar_boton_para_seleccionar_anio_de_convocatoria()` | `desplegar_boton_para_seleccionar_anio_de_convocatoria()` | ✅ |
| `seleccionar_anio_de_convocatoria()` | `seleccionar_anio_de_convocatoria()` | ✅ |
| `click_boton_de_buscar()` | `click_boton_de_buscar()` - Usa estrategia | ✅ |
| `_extraer_datos_pagina_actual()` | `_extraer_datos_pagina_actual()` | ✅ |
| `obtener_tabla_de_procesos()` | `obtener_tabla_de_procesos()` | ✅ |
| `clickear_en_siguiente_pagina()` | `clickear_en_siguiente_pagina()` | ✅ |
| `obtener_todas_las_paginas_de_procesos()` | `obtener_todas_las_paginas_de_procesos()` | ✅ |
| `close()` | Heredado de `BaseScraper.close()` | ✅ |

**Estado:** ✅ Completo

---

## Scraper Nomenclatura (`src/scrapers/nomenclatura.py`)

### Métodos del Experimental vs Producción

| Método Experimental | Método Producción | Estado |
|---------------------|-------------------|--------|
| `start()` | Heredado de `BaseScraper.start()` | ✅ |
| `navigate_to_seace()` | Heredado de `BaseScraper.navigate_to_seace()` | ✅ |
| `select_search_type()` | Heredado de `BaseScraper.select_search_type()` | ✅ |
| `click_busqueda_avanzada()` | Heredado de `BaseScraper.click_busqueda_avanzada()` | ✅ |
| `ingresar_nomenclatura()` | `ingresar_nomenclatura()` | ✅ |
| `click_boton_de_buscar()` | `click_boton_de_buscar()` - Usa estrategia | ✅ |
| `clickear_ficha_seleccion()` | `clickear_ficha_seleccion()` | ✅ |
| `obtener_cronograma()` | `obtener_cronograma()` | ✅ |
| `ver_documentos_por_etapa()` | No implementado (solo debug) | ⚠️ Opcional |
| `scrapear_documentos_con_links()` | `scrapear_documentos_con_links()` - Mejorado | ✅ |
| `close()` | Heredado de `BaseScraper.close()` | ✅ |

**Estado:** ✅ Completo (método `ver_documentos_por_etapa` es solo para debug, no crítico)

---

## Dependencias Necesarias

### Verificación en `pyproject.toml`

| Dependencia | Necesaria para | Estado |
|-------------|----------------|--------|
| `playwright` | Navegador automatizado | ✅ Agregada |
| `pandas` | Manejo de DataFrames y CSV | ✅ Agregada |
| `fastapi` | API (futuro) | ✅ Ya estaba |
| `uvicorn` | Servidor ASGI (futuro) | ✅ Ya estaba |
| `beautifulsoup4` | Parsing HTML (opcional) | ✅ Ya estaba |
| `lxml` | Parser HTML rápido | ✅ Ya estaba |

**Estado:** ✅ Todas las dependencias necesarias agregadas

---

## Verificaciones Finales

### ✅ Código
- [x] Todos los métodos del experimental implementados
- [x] Código async/await correcto
- [x] Manejo de errores robusto
- [x] Logging profesional
- [x] Type hints completos
- [x] Docstrings claros

### ✅ Arquitectura
- [x] Herencia de `BaseScraper`
- [x] Uso de selectores centralizados
- [x] Estrategias de espera implementadas
- [x] Configuración flexible

### ✅ Dependencias
- [x] `playwright` agregado
- [x] `pandas` agregado
- [x] Otras dependencias verificadas

