# Análisis: Scrapers Experimentales vs Producción

**Fecha:** 2026-01-27  
**Objetivo:** Analizar los scrapers de producción en `legacy/src/` para identificar qué está bien, qué está mal, y qué mejoras aplicar al convertir los experimentales a producción.

---

## Resumen Ejecutivo

Los scrapers de producción (`legacy/src/`) tienen una arquitectura mucho más robusta que los experimentales, pero también tienen complejidad innecesaria y algunos problemas de diseño. Este análisis identifica los puntos clave para crear una versión mejorada.

---

## 1. Scraper Regional

### Archivos Analizados
- **Experimental:** `experiments/por_region/scraper_regional.py` (289 líneas)
- **Producción:** `legacy/src/regional/scraper.py` (1275 líneas)
- **Config:** `legacy/src/regional/config.py` (189 líneas)
- **Selectors:** `legacy/src/regional/selectors.py` (59 líneas)

### ✅ Lo que está BIEN en Producción

#### 1.1 Arquitectura Modular
- **Separación de responsabilidades:** Config, selectors y scraper están separados
- **Selectores centralizados:** Facilita mantenimiento cuando cambia la estructura del sitio
- **Configuración externa:** YAML + variables de entorno, muy flexible

#### 1.2 Manejo de Errores Robusto
- **Excepciones personalizadas:** `ElementNotFoundError`, `TableNotFoundError`, `InvalidTableStructureError`
- **Logging profesional:** Sistema de logging con niveles configurables
- **Validación de estructura:** Verifica que las tablas tengan el formato esperado antes de extraer

#### 1.3 Funcionalidades Avanzadas
- **Context manager async:** `async with SeaceScraper() as scraper:` - manejo seguro de recursos
- **Guardado incremental:** Sistema de checkpoints para reanudar scraping
- **Monitoreo de red:** En modo debug, captura peticiones AJAX para debugging
- **Espera inteligente:** Detecta respuestas AJAX de JSF antes de validar tabla

#### 1.4 Validación de Datos
- **Validación de estructura de tabla:** Verifica número de columnas antes de extraer
- **Manejo de casos edge:** Detecta "no hay resultados" vs "tabla vacía por error"
- **Retry con backoff exponencial:** En `_wait_for_table_ready()`

### ❌ Lo que está MAL en Producción

#### 1.1 Complejidad Excesiva
- **1275 líneas es demasiado:** Mucho código para debugging que no debería estar en producción
- **Monitoreo de red innecesario:** `_enable_network_monitoring()`, `_capture_network_snapshot()`, `_analyze_network_changes()` - esto debería ser opcional o estar en herramientas separadas
- **Múltiples métodos de espera:** `_wait_for_loading_indicators_to_disappear()`, `_wait_for_jsf_ajax_response()`, `_wait_for_table_ready()` - demasiada complejidad

#### 1.2 Problemas de Diseño
- **Dependencia de YAML:** Requiere `pyyaml` como dependencia adicional
- **Configuración duplicada:** `RegionalConfig` y `NomenclaturaConfig` tienen mucho código duplicado
- **Selectores hardcodeados:** Aunque están centralizados, algunos selectores son muy específicos y frágiles

#### 1.3 Código Problemático
- **Delays fijos:** `await asyncio.sleep(2)` en varios lugares - debería ser configurable
- **Manejo de errores inconsistente:** A veces continúa, a veces lanza excepción
- **Validación redundante:** Valida estructura de tabla múltiples veces

#### 1.4 Problemas de Performance
- **Espera excesiva:** `await asyncio.sleep(7)` después de buscar - demasiado tiempo
- **Múltiples esperas:** Espera networkidle + sleep + validación - podría optimizarse
- **Guardado incremental puede ser lento:** Escribe CSV después de cada página

### 🔧 Mejoras Sugeridas

#### 1.1 Simplificar Esperas
- **Una sola función de espera inteligente:** Combinar las múltiples funciones en una que detecte automáticamente cuando la página está lista
- **Usar eventos de Playwright:** En lugar de esperas fijas, usar `page.wait_for_response()` o `page.wait_for_selector()`
- **Timeout configurable:** Pero con valores razonables por defecto

#### 1.2 Reducir Complejidad
- **Eliminar monitoreo de red:** Moverlo a herramientas de debugging separadas
- **Simplificar validación:** Una sola validación antes de extraer, no múltiples
- **Código más limpio:** Reducir de 1275 a ~600-700 líneas manteniendo funcionalidad

#### 1.3 Mejorar Configuración
- **Configuración unificada:** Una sola clase base `BaseConfig` con herencia
- **Sin YAML obligatorio:** Usar valores por defecto sensatos, YAML opcional
- **Type hints mejorados:** Usar `TypedDict` o `pydantic` para validación de config

#### 1.4 Optimizar Performance
- **Esperas más inteligentes:** Detectar cuando la tabla está lista en lugar de esperas fijas
- **Guardado en batch:** Guardar cada N páginas en lugar de cada página
- **Paralelización opcional:** Para múltiples departamentos/años

---

## 2. Scraper por Nomenclatura

### Archivos Analizados
- **Experimental:** `experiments/por_nomenclatura/scraper_nomenclatura.py` (344 líneas)
- **Producción:** `legacy/src/nomenclatura/scraper.py` (629 líneas)
- **Config:** `legacy/src/nomenclatura/config.py` (173 líneas)
- **Selectors:** `legacy/src/nomenclatura/selectors.py` (63 líneas)

### ✅ Lo que está BIEN en Producción

#### 2.1 Extracción de Datos
- **Extracción de cronograma:** Bien estructurada con validación de columnas
- **Extracción de documentos:** Maneja links de descarga correctamente
- **Manejo de errores por fila:** Si una fila falla, continúa con las demás

#### 2.2 Validación
- **Validación de estructura:** Verifica número mínimo de celdas antes de extraer
- **Manejo de casos edge:** Detecta cuando no hay suficientes celdas

#### 2.3 Logging
- **Logging detallado:** Informa progreso de extracción
- **Debug opcional:** Guarda HTMLs cuando está en modo debug

### ❌ Lo que está MAL en Producción

#### 2.1 Problemas con Links de Descarga
- **Método complejo:** Intenta interceptar descarga, luego interceptar respuesta de red - demasiado complejo
- **Código duplicado:** El método experimental tiene mejor lógica para obtener links
- **No maneja bien errores:** Si falla obtener link, continúa pero no informa bien

#### 2.2 Esperas Excesivas
- **`await asyncio.sleep(7)` después de buscar:** Demasiado tiempo fijo
- **`await asyncio.sleep(3)` después de clickear ficha:** Podría ser más inteligente
- **Delays entre documentos:** Configurable pero valor por defecto puede ser optimizado

#### 2.3 Código Experimental Mejor en Algunos Aspectos
- **Método de obtener links:** El experimental tiene mejor lógica con `page.expect_download()`
- **Manejo de errores más simple:** El experimental es más directo

### 🔧 Mejoras Sugeridas

#### 2.1 Simplificar Obtención de Links
- **Usar método del experimental:** `page.expect_download()` es más simple y confiable
- **Fallback simple:** Si falla, intentar método alternativo una vez, luego continuar
- **No interceptar todas las respuestas:** Solo interceptar cuando sea necesario

#### 2.2 Optimizar Esperas
- **Esperar a que la tabla esté visible:** En lugar de sleep fijo
- **Detectar cuando cargó:** Usar `wait_for_selector()` con estado visible
- **Reducir delays:** Valores por defecto más agresivos pero seguros

#### 2.3 Mejorar Extracción
- **Validar estructura antes de iterar:** Una sola validación al inicio
- **Manejo de errores más claro:** Informar mejor qué falló y por qué

---

## 3. Comparación: Experimental vs Producción

### Aspectos donde el EXPERIMENTAL es mejor

1. **Simplicidad:** El código experimental es más fácil de entender
2. **Obtención de links:** El método con `expect_download()` es más directo
3. **Menos dependencias:** No requiere YAML, menos complejidad
4. **Código más directo:** Menos abstracciones innecesarias

### Aspectos donde la PRODUCCIÓN es mejor

1. **Arquitectura modular:** Separación clara de responsabilidades
2. **Manejo de errores:** Excepciones personalizadas y logging profesional
3. **Configuración flexible:** YAML + variables de entorno
4. **Validación robusta:** Verifica estructura antes de extraer
5. **Context manager:** Manejo seguro de recursos
6. **Guardado incremental:** Sistema de checkpoints (solo en regional)

---

## 4. Recomendaciones para Nueva Versión de Producción

### 4.1 Arquitectura

```
src/
├── scrapers/
│   ├── base.py              # Clase base con funcionalidad común
│   ├── regional.py          # Scraper regional (simplificado)
│   └── nomenclatura.py      # Scraper nomenclatura (simplificado)
├── config/
│   ├── base.py              # Configuración base (sin YAML obligatorio)
│   └── settings.py          # Configuración compartida
├── selectors/
│   ├── regional.py          # Selectores regionales
│   └── nomenclatura.py      # Selectores nomenclatura
└── utils/
    ├── exceptions.py        # Excepciones personalizadas
    └── logging.py           # Utilidades de logging
```

### 4.2 Principios de Diseño

1. **Simplicidad sobre complejidad:** Menos código, más mantenible
2. **Configuración opcional:** Valores por defecto sensatos, configuración externa opcional
3. **Una responsabilidad:** Cada función hace una cosa bien
4. **Esperas inteligentes:** Detectar estado en lugar de esperas fijas
5. **Manejo de errores claro:** Excepciones específicas, logging útil

### 4.3 Características a Mantener

- ✅ Context manager async
- ✅ Logging profesional
- ✅ Excepciones personalizadas
- ✅ Validación de estructura
- ✅ Selectores centralizados
- ✅ Configuración flexible (pero opcional)

### 4.4 Características a Eliminar/Simplificar

- ❌ Monitoreo de red complejo (mover a herramientas de debug)
- ❌ Múltiples métodos de espera (unificar en uno inteligente)
- ❌ Dependencia de YAML (hacer opcional)
- ❌ Guardado incremental complejo (simplificar o hacer opcional)
- ❌ Delays fijos excesivos (usar esperas inteligentes)

### 4.5 Características a Mejorar

- 🔧 Obtención de links: Usar método del experimental mejorado
- 🔧 Esperas: Combinar múltiples métodos en uno inteligente
- 🔧 Configuración: Clase base con herencia, sin duplicación
- 🔧 Validación: Una sola validación eficiente
- 🔧 Performance: Reducir esperas innecesarias

---

## 5. Plan de Implementación

### Fase 1: Base Común
1. Crear `src/scrapers/base.py` con funcionalidad compartida
2. Crear `src/config/settings.py` con configuración unificada
3. Crear `src/utils/exceptions.py` y `src/utils/logging.py`

### Fase 2: Scraper Regional
1. Crear `src/scrapers/regional.py` basado en experimental pero con mejoras de producción
2. Crear `src/selectors/regional.py` con selectores centralizados
3. Implementar validación simplificada pero robusta

### Fase 3: Scraper Nomenclatura
1. Crear `src/scrapers/nomenclatura.py` mejorando ambos (experimental + producción)
2. Crear `src/selectors/nomenclatura.py` con selectores centralizados
3. Implementar obtención de links mejorada

### Fase 4: Optimización
1. Reducir complejidad innecesaria
2. Optimizar esperas y timeouts
3. Mejorar manejo de errores
4. Agregar tests

---

## 6. Checklist de Calidad

Para cada scraper de producción, verificar:

- [ ] Menos de 800 líneas de código
- [ ] Sin dependencias innecesarias (YAML opcional)
- [ ] Esperas inteligentes, no fijas
- [ ] Una sola función de validación eficiente
- [ ] Context manager async implementado
- [ ] Logging profesional configurado
- [ ] Excepciones personalizadas apropiadas
- [ ] Selectores centralizados y documentados
- [ ] Configuración con valores por defecto sensatos
- [ ] Manejo de errores claro y consistente
- [ ] Sin código de debugging en producción
- [ ] Type hints completos
- [ ] Docstrings claros y completos

---

## Conclusión

Los scrapers de producción tienen una base sólida pero están sobrecargados con complejidad innecesaria. La nueva versión debe:

1. **Mantener lo bueno:** Arquitectura modular, manejo de errores, logging
2. **Eliminar lo malo:** Complejidad excesiva, dependencias innecesarias, esperas fijas
3. **Mejorar lo existente:** Simplificar esperas, optimizar performance, mejorar obtención de links
4. **Aprender del experimental:** Simplicidad, código directo, menos abstracciones

El objetivo es crear scrapers que sean **robustos pero simples**, **flexibles pero con buenos defaults**, y **fáciles de mantener y extender**.

