# Arquitectura: Desarrollo vs Producción Optimizados

## Contexto del Problema

El monitoreo de red no es solo debugging, es una **solución técnica** para un problema real:

### Problema Real
- La página de SEACE es **inestable**
- Los tiempos de carga varían mucho (a veces 1 segundo, a veces 10 segundos)
- Un timeout fijo (`sleep(3)`) falla porque:
  - Si es rápido → espera innecesaria (lento)
  - Si es lento → timeout antes de que cargue (falla)

### Solución Actual
- **Detectar qué petición HTTP específica** se dispara al hacer click
- **Esperar a que esa petición termine** (en lugar de timeout fijo)
- Esto funciona porque la petición AJAX termina cuando los datos están listos

### Necesidad
- **Desarrollo:** Necesitas ver qué peticiones se hacen para entender la página y ajustar selectores
- **Producción:** No necesitas capturar todas las peticiones, solo esperar a la correcta

---

## Propuesta de Arquitectura

### Opción 1: Modo Debug Inteligente (Recomendada)

**Idea:** Mantener la lógica de detección de peticiones, pero hacerla eficiente según el modo.

#### Estructura

```
src/
├── scrapers/
│   ├── base.py                    # Clase base con lógica común
│   ├── regional.py                # Scraper regional (producción)
│   └── nomenclatura.py            # Scraper nomenclatura (producción)
├── scrapers_dev/                  # Solo para desarrollo
│   ├── __init__.py
│   ├── network_monitor.py         # Herramientas de monitoreo de red
│   └── debug_utils.py             # Utilidades de debugging
└── utils/
    ├── wait_strategies.py         # Estrategias de espera (dev y prod)
    └── exceptions.py
```

*(Documento original completo conservado; movido a `docs/completed/` al implementarse la arquitectura y las DevTools.)*

