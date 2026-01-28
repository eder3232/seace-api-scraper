# Explicación: Reducción de Código y Monitoreo de Red

## 1. ¿Qué es el Monitoreo de Red?

### Concepto

El **monitoreo de red** es una funcionalidad de debugging que captura y analiza todas las peticiones HTTP que hace el navegador cuando interactúas con una página web.

### ¿Para qué sirve?

Cuando haces click en "Buscar" en SEACE, el navegador hace múltiples peticiones HTTP:
- Peticiones AJAX/XHR que cargan los datos de la tabla
- Recursos estáticos (CSS, imágenes, JavaScript)
- Peticiones de autenticación o validación

El monitoreo de red captura **todas** estas peticiones para entender:
- ¿Qué petición carga los datos de la tabla?
- ¿Cuánto tiempo tarda en responder?
- ¿Qué headers tiene?
- ¿Cuál es la URL exacta?

### Ejemplo del Código

En `legacy/src/regional/scraper.py`, líneas 599-740, hay ~140 líneas dedicadas a esto:

```python
def _enable_network_monitoring(self):
    """Habilita el monitoreo de peticiones de red para debugging."""
    # Captura TODAS las peticiones HTTP
    def on_request(request):
        request_info = {
            'url': request.url,
            'method': request.method,
            'headers': request.headers,
            # ... más información
        }
        self._network_requests.append(request_info)
    
    # Captura TODAS las respuestas HTTP
    def on_response(response):
        response_info = {
            'url': response.url,
            'status': response.status,
            'content_type': response.headers.get('content-type', ''),
            # ... más información
        }
        self._network_responses.append(response_info)
    
    # Escuchar todos los eventos de red
    self.page.on("request", on_request)
    self.page.on("response", on_response)
```

Luego, cuando haces click en buscar:

```python
async def click_boton_de_buscar(self):
    # 1. Capturar estado ANTES del click
    if self.debug:
        network_before = self._capture_network_snapshot()  # Línea 389
    
    await button.click()
    
    # 2. Esperar a que carguen los resultados
    await self._wait_for_table_ready()
    
    # 3. Capturar estado DESPUÉS del click
    if self.debug:
        network_after = self._capture_network_snapshot()  # Línea 408
        
        # 4. Analizar qué cambió
        analysis = self._analyze_network_changes(network_before, network_after)  # Línea 412
        
        # 5. Guardar análisis en JSON
        self._save_network_analysis(full_analysis, "network_analysis.json")  # Línea 443
```

### ¿Por qué es problemático en producción?

1. **Solo es útil para debugging:** En producción normal, no necesitas saber qué peticiones HTTP se hicieron
2. **Consume memoria:** Guarda todas las peticiones en listas que crecen indefinidamente
3. **Añade complejidad:** ~140 líneas de código que solo se usan cuando `debug=True`
4. **Ralentiza el código:** Procesar y analizar todas las peticiones toma tiempo

### Solución Recomendada

**Eliminar completamente** del código de producción. Si necesitas debugging de red:
- Usar las DevTools del navegador (F12 → Network tab)
- Crear una herramienta de debugging separada
- Usar `page.on("response")` solo cuando realmente lo necesites, no siempre

---

## 2. Cómo Reducir las Líneas de Código

### Análisis: ¿Dónde está el código extra?

Del scraper regional de producción (1275 líneas), podemos identificar:

#### 2.1 Monitoreo de Red (~140 líneas)
- `_enable_network_monitoring()`: ~50 líneas
- `_disable_network_monitoring()`: ~10 líneas
- `_capture_network_snapshot()`: ~10 líneas
- `_analyze_network_changes()`: ~50 líneas
- `_save_network_analysis()`: ~20 líneas
- **Total a eliminar: ~140 líneas**

#### 2.2 Múltiples Métodos de Espera (~200 líneas)
Hay 3 métodos diferentes para esperar a que la página cargue:

**Método 1:** `_wait_for_loading_indicators_to_disappear()` (~45 líneas)
```python
async def _wait_for_loading_indicators_to_disappear(self, timeout: int = 30000):
    """Espera a que desaparezcan los indicadores de carga."""
    loading_selectors = [
        '.ui-state-loading',
        '.ui-progressbar',
        '[class*="loading"]',
        # ... 8 selectores más
    ]
    for selector in loading_selectors:
        # ... código para cada selector
```

**Método 2:** `_wait_for_jsf_ajax_response()` (~75 líneas)
```python
async def _wait_for_jsf_ajax_response(self, timeout: int = 30000):
    """Espera específicamente a que se complete la petición AJAX de JSF."""
    def is_jsf_ajax_response(response):
        # Verifica URL, método POST, headers AJAX, content-type XML
        # ... 30 líneas de validación
    
    response = await self.page.wait_for_response(is_jsf_ajax_response, timeout=timeout)
```

**Método 3:** `_wait_for_table_ready()` (~80 líneas)
```python
async def _wait_for_table_ready(self, max_retries: int = 10):
    """Espera inteligentemente a que la tabla esté completamente cargada."""
    await self._wait_for_loading_indicators_to_disappear()  # Llama al método 1
    await self.page.wait_for_load_state("networkidle")
    
    for attempt in range(max_retries):
        # Verifica contenedor, tbody, filas, columnas
        # ... 60 líneas de lógica
```

**Problema:** Estos 3 métodos hacen cosas similares y se llaman entre sí. Podemos unificarlos.

**Solución:** Un solo método inteligente (~50 líneas)
```python
async def _wait_for_table_ready(self, timeout: int = 30000):
    """Espera a que la tabla esté lista usando el método más eficiente."""
    # 1. Esperar respuesta AJAX (más rápido)
    try:
        await self.page.wait_for_response(
            lambda r: "buscadorPublico.xhtml" in r.url and r.request.method == "POST",
            timeout=timeout
        )
    except:
        pass  # Si no hay AJAX, continuar
    
    # 2. Esperar a que la tabla tenga contenido
    await self.page.wait_for_selector(SELECTORS['results_table_row'], timeout=10000)
    
    # 3. Verificar que tiene columnas correctas (una sola verificación)
    filas = await self.page.locator(SELECTORS['results_table_row']).all()
    if len(filas) > 0:
        celdas = await filas[0].locator('td').all()
        if len(celdas) >= 12:
            return True
    
    raise TableNotFoundError("Tabla no tiene estructura válida")
```

**Ahorro: ~150 líneas** (de 200 a 50)

#### 2.3 Validación Redundante (~100 líneas)

Hay validación de tabla en múltiples lugares:

1. `_validar_estructura_tabla()`: ~75 líneas - valida estructura completa
2. `_wait_for_table_ready()`: ~30 líneas - también valida estructura
3. `_extraer_datos_pagina_actual()`: ~10 líneas - llama a `_validar_estructura_tabla()`

**Problema:** Se valida 3 veces la misma cosa.

**Solución:** Validar una sola vez antes de extraer
```python
async def _extraer_datos_pagina_actual(self):
    """Extrae datos validando UNA VEZ antes de empezar."""
    # Validación simple y rápida
    await self._wait_for_table_ready()  # Ya valida estructura
    
    # Extraer datos directamente
    filas = await self.page.locator(SELECTORS['results_table_row']).all()
    # ... resto del código
```

**Ahorro: ~75 líneas** (eliminar `_validar_estructura_tabla()` duplicada)

#### 2.4 Guardado Incremental Complejo (~150 líneas)

El sistema de checkpoints tiene:
- `_load_checkpoint()`: ~25 líneas
- `_save_checkpoint()`: ~20 líneas
- `_append_to_csv()`: ~25 líneas
- Lógica en `obtener_todas_las_paginas_de_procesos()`: ~80 líneas

**Problema:** Mucha lógica para algo que puede ser más simple.

**Solución:** Simplificar o hacer opcional
```python
async def obtener_todas_las_paginas_de_procesos(self, csv_file: str = "procesos.csv"):
    """Extrae todas las páginas y guarda al final (más simple)."""
    todos_los_datos = []
    
    # Primera página
    datos = await self._extraer_datos_pagina_actual()
    todos_los_datos.extend(datos)
    
    # Siguientes páginas
    while await self._avanzar_pagina():
        datos = await self._extraer_datos_pagina_actual()
        todos_los_datos.extend(datos)
    
    # Guardar TODO al final (más simple)
    df = pd.DataFrame(todos_los_datos, columns=COLUMNAS_ESPERADAS)
    df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    return df
```

**Ahorro: ~100 líneas** (si no necesitas guardado incremental)

#### 2.5 Código de Debug Mezclado (~50 líneas)

Hay código de debug mezclado en varios métodos:
```python
if self.debug:
    await self._save_debug_html(element, "filename.html")
    network_before = self._capture_network_snapshot()
    # ... más código de debug
```

**Solución:** Mover a método separado o eliminar
```python
# En lugar de esto en cada método:
if self.debug:
    await self._save_debug_html(...)

# Hacer esto solo cuando realmente necesites debug
async def _debug_save_page_state(self, name: str):
    """Guarda estado de la página para debug (opcional)."""
    if not self.debug:
        return
    # ... código de debug aquí
```

**Ahorro: ~30 líneas** (código más limpio)

#### 2.6 Delays y Sleeps Excesivos (~20 líneas)

Hay muchos `await asyncio.sleep()` fijos:
```python
await asyncio.sleep(2)  # Después de navegar
await asyncio.sleep(1)  # Después de click
await asyncio.sleep(7)  # Después de buscar (¡demasiado!)
await asyncio.sleep(0.5)  # Entre acciones
```

**Solución:** Usar esperas inteligentes en lugar de sleeps fijos
```python
# En lugar de:
await asyncio.sleep(7)

# Hacer:
await self.page.wait_for_selector(SELECTORS['results_table'], timeout=10000)
```

**Ahorro: ~10 líneas** (pero mejora performance significativamente)

### Resumen de Reducción

| Categoría | Líneas Actuales | Líneas Optimizadas | Ahorro |
|-----------|------------------|-------------------|--------|
| Monitoreo de red | 140 | 0 (eliminar) | -140 |
| Múltiples esperas | 200 | 50 (unificar) | -150 |
| Validación redundante | 100 | 25 (simplificar) | -75 |
| Guardado incremental | 150 | 50 (simplificar) | -100 |
| Código debug mezclado | 50 | 20 (limpiar) | -30 |
| Delays excesivos | 20 | 5 (optimizar) | -15 |
| **TOTAL** | **660** | **150** | **-510 líneas** |

### Resultado Final

- **Código actual:** 1275 líneas
- **Código optimizado:** ~765 líneas (1275 - 510)
- **Reducción:** ~40% menos código
- **Beneficios:**
  - Más fácil de entender
  - Más rápido (menos procesamiento)
  - Más mantenible
  - Misma funcionalidad esencial

---

## 3. Ejemplo Concreto: Antes vs Después

### Antes (Código de Producción - 1275 líneas)

```python
async def click_boton_de_buscar(self):
    # Habilitar monitoreo de red si está en modo debug
    if self.debug:
        self._enable_network_monitoring()  # 50 líneas de código
        self.logger.info("Monitoreo de red activado")
    
    button = self.page.locator(SELECTORS['search_button'])
    if not await self._wait_for_element(button, "Botón de buscar"):
        raise ElementNotFoundError("No se encontró el botón de buscar")
    
    # Capturar snapshot ANTES
    if self.debug:
        network_before = self._capture_network_snapshot()  # 10 líneas
    
    await button.click()
    
    # Esperar respuesta AJAX
    if await self._wait_for_jsf_ajax_response(timeout=30000):  # 75 líneas
        self.logger.debug("Respuesta AJAX recibida")
    
    # Esperar indicadores de carga
    await self._wait_for_loading_indicators_to_disappear()  # 45 líneas
    
    # Esperar tabla lista
    await self._wait_for_table_ready()  # 80 líneas
    
    # Capturar snapshot DESPUÉS y analizar
    if self.debug:
        network_after = self._capture_network_snapshot()
        analysis = self._analyze_network_changes(network_before, network_after)  # 50 líneas
        self._save_network_analysis(analysis, "network_analysis.json")  # 20 líneas
    
    # Guardar HTML de debug
    if self.debug:
        await self._save_debug_html(results_container, "results.html")
    
    self.logger.info("Resultados cargados")
```

**Total: ~330 líneas de código ejecutado (aunque mucho está en métodos separados)**

### Después (Código Optimizado - ~50 líneas)

```python
async def click_boton_de_buscar(self):
    """Hace click en buscar y espera a que los resultados estén listos."""
    button = self.page.locator(SELECTORS['search_button'])
    
    if not await button.is_visible(timeout=10000):
        raise ElementNotFoundError("No se encontró el botón de buscar")
    
    await button.click()
    self.logger.info("Botón clickeado, esperando resultados...")
    
    # Espera inteligente: primero AJAX, luego tabla
    try:
        # Esperar respuesta AJAX (más rápido)
        await self.page.wait_for_response(
            lambda r: "buscadorPublico.xhtml" in r.url and r.request.method == "POST",
            timeout=30000
        )
    except:
        pass  # Si no hay AJAX, continuar con espera de tabla
    
    # Esperar a que la tabla tenga contenido válido
    await self.page.wait_for_selector(
        SELECTORS['results_table_row'],
        state="visible",
        timeout=10000
    )
    
    # Validación rápida: verificar que tiene columnas correctas
    primera_fila = self.page.locator(SELECTORS['results_table_row']).first
    celdas = await primera_fila.locator('td').all()
    
    if len(celdas) < 12:
        raise InvalidTableStructureError(f"Tabla tiene {len(celdas)} columnas, se esperaban 12")
    
    self.logger.info("Resultados cargados correctamente")
```

**Total: ~30 líneas de código directo**

### Comparación

| Aspecto | Antes | Después | Mejora |
|---------|-------|---------|--------|
| Líneas de código | ~330 | ~30 | 90% menos |
| Métodos auxiliares | 6 métodos | 0 métodos | Más directo |
| Monitoreo de red | Sí (140 líneas) | No | Eliminado |
| Esperas | 3 métodos diferentes | 1 espera inteligente | Simplificado |
| Debug mezclado | Sí | No | Separado |
| Performance | Lento (múltiples esperas) | Rápido (espera directa) | Mejor |

---

## 4. Principios para Reducir Código

### 4.1 Eliminar Código que Solo se Usa en Debug
- **Regla:** Si solo se usa cuando `debug=True`, moverlo a herramienta separada
- **Ejemplo:** Monitoreo de red → DevTools del navegador

### 4.2 Unificar Funcionalidad Similar
- **Regla:** Si 3 métodos hacen lo mismo, crear 1 método que haga todo
- **Ejemplo:** 3 métodos de espera → 1 método inteligente

### 4.3 Eliminar Validación Redundante
- **Regla:** Validar una sola vez, en el lugar correcto
- **Ejemplo:** Validar tabla antes de extraer, no en 3 lugares

### 4.4 Usar Funcionalidades Nativas
- **Regla:** Usar métodos de Playwright directamente en lugar de wrappers complejos
- **Ejemplo:** `page.wait_for_selector()` en lugar de método custom con retries

### 4.5 Simplificar Lógica Compleja
- **Regla:** Si algo es opcional y complejo, hacerlo más simple o eliminarlo
- **Ejemplo:** Guardado incremental complejo → Guardado simple al final

---

## Conclusión

El código de producción tiene **buena arquitectura** pero **demasiada complejidad innecesaria**. Reduciendo:

1. **Eliminando monitoreo de red:** -140 líneas
2. **Unificando esperas:** -150 líneas  
3. **Simplificando validación:** -75 líneas
4. **Simplificando guardado:** -100 líneas
5. **Limpiando debug:** -30 líneas
6. **Optimizando delays:** -15 líneas

**Total: ~510 líneas menos (40% de reducción)** manteniendo toda la funcionalidad esencial.

El código resultante será:
- ✅ Más fácil de entender
- ✅ Más rápido de ejecutar
- ✅ Más fácil de mantener
- ✅ Con la misma robustez
