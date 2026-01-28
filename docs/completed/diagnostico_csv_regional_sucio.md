# Diagnóstico: CSV “sucio” en scraper regional (headers/footers repetidos)

Fecha: 2026-01-28  
Contexto: Scraper regional (`src/scrapers/regional.py`) generando CSV con texto “pegado” del encabezado y del paginador (ej. `[ Mostrando de 1 a 15 ... ]`, `p`, `123`, etc.).

## Evidencia (basada en HTML capturado en `debug/`)

Con `debug=true` se guardaron:

- `debug/regional_resultados_container_p1.html`
- `debug/regional_resultados_tbody_p1.html`
- `debug/regional_resultados_paginador_p1.html`

### 1) El contenedor completo incluye **thead + tbody + paginator**

En `debug/regional_resultados_container_p1.html` se observa que el contenedor `#tbBuscador:idFormBuscarProceso:pnlGrdResultadosProcesos` contiene:

- Un `<thead id="...:dtProcesos_head">` con headers (incluye “Acciones”).
- Un `<tbody id="...:dtProcesos_data">` con las filas reales.
- Un `<div id="...:dtProcesos_paginator_bottom">` con el paginador, incluyendo:
  - `span.ui-paginator-current` con el texto `[ Mostrando de ... ]`
  - varios `span.ui-icon ...` cuyo texto es `p`
  - números de página (1,2,3)
  - opciones 10/15/20

### 2) El `tbody` real está limpio

En `debug/regional_resultados_tbody_p1.html` el elemento es:

- `<tbody id="tbBuscador:idFormBuscarProceso:dtProcesos_data" ...>`

y dentro solo existen `<tr ...>` de datos con `<td>` por columna.

Esto confirma que **los datos están bien en el DOM**, pero **la extracción está “scopiando” mal**.

## Causa raíz probable (en código)

En `src/selectors/regional.py` el selector actual es:

- `SELECTORS['results_table_body'] = '#...:dtProcesos_data'` (esto es correcto: ya apunta al `<tbody>` real)
- `SELECTORS['results_table_row'] = 'tbody tr'` (**esto es el problema** cuando se usa bajo el `<tbody>` real)

En `RegionalScraper._extraer_datos_pagina_actual()` se hace:

1) `tbody = container.locator(SELECTORS['results_table_body'])`  → esto devuelve el `<tbody id="...dtProcesos_data">`
2) `filas = await tbody.locator(SELECTORS['results_table_row']).all()`

Pero si `results_table_row` es `'tbody tr'`, entonces desde un `<tbody>` buscas un `<tbody>` descendiente (que no existe) y terminas con **0 filas**.

Luego entra el fallback:

3) `filas_directas = await container.locator(SELECTORS['results_table_row']).all()`

Aquí `container.locator('tbody tr')` sí encuentra **el `tr` del panelgrid externo** (el layout `ui-panelgrid`), cuya única celda contiene todo el texto: headers + datos + paginador.

Cuando el scraper extrae `td.inner_text()` de ese `tr`, genera una “fila” con texto gigante (incluyendo `[ Mostrando ... ]`, `p`, `1 2 3`, `10 15 20`), que es exactamente lo que aparece en `debug/resultados.csv`.

## Estrategia para devolver un CSV limpio (robusta y basada en datos)

### A) Corregir el selector de filas para que sea consistente con `dtProcesos_data`

**Cambiar `results_table_row` a `tr`** (filas directas del `<tbody>` real).

Propuesta:

- En `src/selectors/regional.py`:
  - `SELECTORS['results_table_row'] = 'tr'`
  - y en `WAIT_SELECTORS['results_table_row']` también usar `tr` (o un selector equivalente que apunte a filas reales del `dtProcesos_data`)

Con esto:

- `tbody.locator('tr')` devuelve **solo filas reales**
- el fallback `container.locator('tr')` (si se mantiene) ya no debería usarse, o debe apuntar a `dtProcesos_data tr` específicamente para evitar capturar layout externo

### B) Eliminar (o endurecer) el fallback de “filas directas”

Si el selector principal está bien, el fallback se vuelve innecesario y es la fuente del problema.

Recomendación:

- Si `len(filas) == 0`, en vez de buscar en todo el contenedor, buscar explícitamente dentro de `dtProcesos_data`:
  - `filas_directas = await self.page.locator(SELECTORS['results_table_body']).locator('tr').all()`

### C) Validación de fila por invariantes del dataset

Como segunda barrera (por si SEACE cambia DOM), filtrar filas antes de agregarlas:

- **Invariante 1**: la primera celda `N°` debe ser numérica (`isdigit()`).
- **Invariante 2**: la fila debe traer al menos \(n\) celdas (en el HTML actual son 13 tds, incluyendo SNIP/CUI/Acciones).
- **Invariante 3 (opcional)**: descartar filas que contengan textos de UI como `[ Mostrando` o `ui-icon`.

Con A + B + C, el CSV quedará:

- 1 header (el que escribe `pandas.to_csv`)
- solo filas reales del `tbody`
- sin headers/footers repetidos ni paginador contaminando la data.

## Próximo paso recomendado

Implementar primero (A) + (B), porque el HTML ya demuestra que el `tbody` real está limpio.  
Luego volver a correr con `debug=true` y validar que:

- `regional_resultados_tbody_p*.html` contiene solo `tr` de datos
- el CSV final ya no incluye líneas tipo `[ Mostrando ... ]` ni `p/123/10/15/20`.

