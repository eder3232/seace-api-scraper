# Debug del Scraper Regional - AREQUIPA 2026

## Problema Reportado

- **Versión experimental**: Funciona correctamente, encuentra 32 registros para AREQUIPA y 2026
- **Versión producción**: No scrapea ningún proceso (debería encontrar al menos 10)
- **Tests**: Pasan correctamente

## Diferencias Identificadas

### 1. Orden de Selección
- **Experimental**: Primero selecciona **año**, luego **departamento**
- **Producción**: Primero selecciona **departamento**, luego **año**

### 2. Estrategia de Espera
- **Experimental**: Usa delays fijos largos (2000ms, 5000ms)
- **Producción**: Usa `ProductionWaitStrategy` que espera respuesta AJAX específica

### 3. Manejo de Tablas Vacías
- La validación lanza `TableNotFoundError` cuando no hay resultados
- Puede estar fallando silenciosamente si la tabla existe pero está vacía

## Mejoras Implementadas

### 1. Script de Debug Detallado
- `scripts/debug_regional_detallado.py`: Compara ambos órdenes de selección
- Captura screenshots en cada paso
- Guarda HTML para análisis
- Compara resultados entre ambos enfoques

### 2. Correcciones en `wait_strategies.py`
- Corregido problema de indentación en línea 130
- Mejorada espera: primero verifica contenedor, luego filas
- Mejor logging para diagnóstico

### 3. Mejoras en `regional.py`
- Mejor manejo de tablas vacías en `_extraer_datos_pagina_actual`
- Verificación de mensajes "sin resultados"
- Mejor logging y manejo de errores

## Próximos Pasos para Debug

### Paso 1: Ejecutar Script de Debug
```bash
python scripts/debug_regional_detallado.py --departamento AREQUIPA --anio 2026 --orden ambos
```

Esto generará:
- Screenshots en cada paso
- HTML de los paneles y contenedores
- Comparación de ambos órdenes
- CSV con resultados de cada enfoque

### Paso 2: Revisar Logs
Los logs mostrarán:
- Si la respuesta AJAX se detecta correctamente
- Si la tabla se encuentra pero está vacía
- Mensajes de error específicos

### Paso 3: Verificar en Railway
1. Revisar logs de Railway para ver errores específicos
2. Verificar si el problema es solo en producción o también localmente
3. Comparar configuración de entorno (headless, timeouts, etc.)

### Paso 4: Posibles Soluciones

#### Opción A: Cambiar Orden de Selección
Si el orden experimental funciona mejor, actualizar `scraper_service.py`:
```python
# Cambiar de:
await scraper.desplegar_boton_para_seleccionar_departamento()
await scraper.seleccionar_departamento(departamento)
await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
await scraper.seleccionar_anio_de_convocatoria(anio)

# A:
await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
await scraper.seleccionar_anio_de_convocatoria(anio)
await scraper.desplegar_boton_para_seleccionar_departamento()
await scraper.seleccionar_departamento(departamento)
```

#### Opción B: Ajustar Estrategia de Espera
Si la respuesta AJAX no se detecta correctamente:
- Aumentar timeout
- Cambiar criterio de detección de respuesta AJAX
- Agregar delay adicional después del click

#### Opción C: Manejar Tabla Vacía
Si la tabla existe pero está vacía:
- Retornar DataFrame vacío en lugar de lanzar excepción
- Mejorar mensaje de error para diagnóstico

## Comandos Útiles

### Ejecutar debug local
```bash
python scripts/debug_regional_detallado.py --departamento AREQUIPA --anio 2026
```

### Ejecutar solo orden producción
```bash
python scripts/debug_regional_detallado.py --departamento AREQUIPA --anio 2026 --orden produccion
```

### Ejecutar solo orden experimental
```bash
python scripts/debug_regional_detallado.py --departamento AREQUIPA --anio 2026 --orden experimental
```

### Ver logs
```bash
tail -f logs/scraper_regionalscraper.log
```

## Archivos Modificados

1. `src/utils/wait_strategies.py` - Correcciones y mejoras
2. `src/scrapers/regional.py` - Mejor manejo de tablas vacías
3. `scripts/debug_regional_detallado.py` - Nuevo script de debug
