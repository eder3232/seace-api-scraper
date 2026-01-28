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

#### Implementación

**1. Estrategia de Espera Inteligente (Producción)**

```python
# src/utils/wait_strategies.py

class WaitStrategy:
    """Estrategia base para esperar a que la página cargue."""
    
    async def wait_for_search_results(self, page, timeout: int = 30000):
        """Espera a que los resultados de búsqueda estén listos."""
        raise NotImplementedError

class ProductionWaitStrategy(WaitStrategy):
    """Estrategia optimizada para producción: solo espera la petición necesaria."""
    
    async def wait_for_search_results(self, page, timeout: int = 30000):
        """
        Espera SOLO a la petición AJAX que carga los resultados.
        No captura ni guarda nada, solo espera.
        """
        try:
            # Esperar específicamente a la petición POST que carga datos
            await page.wait_for_response(
                lambda response: (
                    "buscadorPublico.xhtml" in response.url and
                    response.request.method == "POST" and
                    response.status == 200
                ),
                timeout=timeout
            )
            # Luego esperar a que la tabla sea visible
            await page.wait_for_selector(
                SELECTORS['results_table_row'],
                state="visible",
                timeout=10000
            )
        except Exception as e:
            raise ScrapingError(f"Timeout esperando resultados: {e}")

class DevelopmentWaitStrategy(WaitStrategy):
    """Estrategia para desarrollo: captura y analiza todas las peticiones."""
    
    def __init__(self, debug_output_dir: str = "debug"):
        self.debug_output_dir = debug_output_dir
        self._network_requests = []
        self._network_responses = []
    
    async def wait_for_search_results(self, page, timeout: int = 30000):
        """
        Espera a los resultados PERO también captura información de red.
        """
        # Habilitar captura de red
        self._setup_network_capture(page)
        
        # Capturar estado ANTES
        network_before = self._capture_snapshot()
        
        # Esperar respuesta AJAX (igual que producción)
        try:
            await page.wait_for_response(
                lambda response: (
                    "buscadorPublico.xhtml" in response.url and
                    response.request.method == "POST"
                ),
                timeout=timeout
            )
        except Exception as e:
            self.logger.warning(f"No se detectó respuesta AJAX: {e}")
        
        # Capturar estado DESPUÉS
        network_after = self._capture_snapshot()
        
        # Analizar y guardar (solo en desarrollo)
        analysis = self._analyze_changes(network_before, network_after)
        self._save_analysis(analysis, "network_analysis_search.json")
        
        # Esperar tabla (igual que producción)
        await page.wait_for_selector(
            SELECTORS['results_table_row'],
            state="visible",
            timeout=10000
        )
    
    def _setup_network_capture(self, page):
        """Configura captura de red (solo en desarrollo)."""
        def on_request(request):
            self._network_requests.append({
                'url': request.url,
                'method': request.method,
                'timestamp': datetime.now().isoformat(),
            })
        
        def on_response(response):
            self._network_responses.append({
                'url': response.url,
                'status': response.status,
                'content_type': response.headers.get('content-type', ''),
                'timestamp': datetime.now().isoformat(),
            })
        
        page.on("request", on_request)
        page.on("response", on_response)
    
    def _capture_snapshot(self):
        """Captura snapshot actual."""
        return {
            'requests': self._network_requests.copy(),
            'responses': self._network_responses.copy(),
        }
    
    def _analyze_changes(self, before, after):
        """Analiza cambios entre snapshots."""
        # Lógica de análisis (igual que antes)
        return {
            'new_requests': [...],
            'ajax_requests': [...],
            # ...
        }
    
    def _save_analysis(self, analysis, filename):
        """Guarda análisis en archivo."""
        debug_path = Path(self.debug_output_dir) / filename
        with open(debug_path, 'w') as f:
            json.dump(analysis, f, indent=2)
```

**2. Scraper Base con Estrategia Configurable**

```python
# src/scrapers/base.py

class BaseScraper:
    """Clase base para scrapers con estrategia de espera configurable."""
    
    def __init__(self, debug: bool = False, wait_strategy: Optional[WaitStrategy] = None):
        self.debug = debug
        
        # Elegir estrategia según modo
        if wait_strategy:
            self.wait_strategy = wait_strategy
        elif debug:
            # En desarrollo, usar estrategia con monitoreo
            from scrapers_dev.network_monitor import DevelopmentWaitStrategy
            self.wait_strategy = DevelopmentWaitStrategy(debug_output_dir="debug")
        else:
            # En producción, usar estrategia optimizada
            from utils.wait_strategies import ProductionWaitStrategy
            self.wait_strategy = ProductionWaitStrategy()
    
    async def click_boton_de_buscar(self):
        """Hace click y espera usando la estrategia configurada."""
        button = self.page.locator(SELECTORS['search_button'])
        
        if not await button.is_visible(timeout=10000):
            raise ElementNotFoundError("No se encontró el botón de buscar")
        
        await button.click()
        self.logger.info("Botón clickeado, esperando resultados...")
        
        # Usar estrategia configurada (dev o prod)
        await self.wait_strategy.wait_for_search_results(self.page)
        
        self.logger.info("Resultados cargados correctamente")
```

**3. Herramientas de Desarrollo Separadas**

```python
# scrapers_dev/network_monitor.py

class NetworkMonitor:
    """
    Herramienta de desarrollo para monitorear peticiones de red.
    Se usa cuando necesitas entender qué peticiones se hacen.
    """
    
    def __init__(self, page):
        self.page = page
        self.requests = []
        self.responses = []
    
    def start_monitoring(self):
        """Inicia monitoreo de red."""
        self.page.on("request", self._on_request)
        self.page.on("response", self._on_response)
    
    def stop_monitoring(self):
        """Detiene monitoreo de red."""
        # Remover listeners
        pass
    
    def get_ajax_requests(self):
        """Obtiene solo peticiones AJAX/XHR."""
        return [r for r in self.requests if r['resource_type'] in ['xhr', 'fetch']]
    
    def analyze_search_click(self):
        """
        Analiza qué peticiones se hacen al hacer click en buscar.
        Útil para entender la página y ajustar selectores.
        """
        # Lógica de análisis
        pass
```

---

### Opción 2: Configuración por Entorno

**Idea:** Usar variables de entorno o configuración para elegir comportamiento.

```python
# En .env o configuración
SCRAPER_MODE=production  # o 'development'

# En el código
class BaseScraper:
    def __init__(self):
        mode = os.getenv('SCRAPER_MODE', 'production')
        
        if mode == 'development':
            self.enable_network_monitoring = True
            self.save_debug_html = True
            self.wait_strategy = DevelopmentWaitStrategy()
        else:
            self.enable_network_monitoring = False
            self.save_debug_html = False
            self.wait_strategy = ProductionWaitStrategy()
```

---

### Opción 3: Herramientas de Desarrollo Completamente Separadas

**Idea:** Crear scripts/módulos separados solo para desarrollo.

```
scrapers_dev/
├── network_analyzer.py      # Script para analizar peticiones
├── selector_tester.py        # Script para probar selectores
└── debug_scraper.py          # Wrapper del scraper con debugging
```

**Uso:**
```python
# En desarrollo, usar:
from scrapers_dev.debug_scraper import DebugRegionalScraper

scraper = DebugRegionalScraper()  # Tiene monitoreo de red

# En producción, usar:
from src.scrapers.regional import RegionalScraper

scraper = RegionalScraper()  # Sin monitoreo de red
```

---

## Comparación de Opciones

| Aspecto | Opción 1: Estrategias | Opción 2: Config | Opción 3: Separado |
|---------|----------------------|------------------|-------------------|
| **Código producción** | Limpio ✅ | Limpio ✅ | Limpio ✅ |
| **Código desarrollo** | Disponible ✅ | Disponible ✅ | Separado ✅✅ |
| **Flexibilidad** | Alta ✅✅ | Media | Alta ✅✅ |
| **Complejidad** | Media | Baja ✅ | Baja ✅ |
| **Mantenibilidad** | Buena ✅ | Buena ✅ | Excelente ✅✅ |
| **Performance prod** | Óptimo ✅✅ | Óptimo ✅✅ | Óptimo ✅✅ |

---

## Recomendación: Opción 1 (Estrategias) + Opción 3 (Herramientas)

### Por qué esta combinación:

1. **Estrategias de Espera (Opción 1):**
   - Mantiene la lógica de detección de peticiones (fundamental)
   - Permite optimizar producción vs desarrollo
   - Código claro y mantenible

2. **Herramientas Separadas (Opción 3):**
   - Scripts específicos para debugging profundo
   - No contamina código de producción
   - Fácil de usar cuando lo necesites

### Estructura Final Recomendada

```
src/
├── scrapers/
│   ├── base.py                    # Clase base con estrategia configurable
│   ├── regional.py                # Scraper regional (producción)
│   └── nomenclatura.py            # Scraper nomenclatura (producción)
├── utils/
│   ├── wait_strategies.py         # ProductionWaitStrategy (optimizada)
│   └── exceptions.py
└── scrapers_dev/                   # Solo para desarrollo (opcional)
    ├── network_monitor.py          # Herramientas de monitoreo
    ├── debug_wait_strategy.py      # DevelopmentWaitStrategy (con monitoreo)
    └── scripts/
        ├── analyze_network.py     # Script para analizar peticiones
        └── test_selectors.py      # Script para probar selectores
```

---

## Ventajas de Esta Arquitectura

### Para Producción:
- ✅ **Código limpio:** Solo espera la petición necesaria, sin capturar nada
- ✅ **Performance óptimo:** No procesa ni guarda información innecesaria
- ✅ **Sin dependencias de debug:** No importa módulos de desarrollo

### Para Desarrollo:
- ✅ **Herramientas disponibles:** Puedes usar `DevelopmentWaitStrategy` cuando necesites
- ✅ **Scripts útiles:** Scripts separados para análisis profundo
- ✅ **Fácil de activar:** Solo cambiar `debug=True` o usar estrategia de desarrollo

### Para Mantenimiento:
- ✅ **Separación clara:** Código de producción vs desarrollo bien separado
- ✅ **Fácil de entender:** Cada estrategia tiene un propósito claro
- ✅ **Extensible:** Fácil agregar nuevas estrategias si es necesario

---

## Ejemplo de Uso

### Producción (por defecto)
```python
from src.scrapers.regional import RegionalScraper

async with RegionalScraper(departamento="AREQUIPA", anio="2025") as scraper:
    await scraper.navigate_to_seace()
    await scraper.select_search_type()
    await scraper.click_busqueda_avanzada()
    await scraper.seleccionar_departamento("AREQUIPA")
    await scraper.seleccionar_anio("2025")
    await scraper.click_boton_de_buscar()  # Usa ProductionWaitStrategy
    df = await scraper.obtener_todas_las_paginas()
```

### Desarrollo (cuando necesitas debugging)
```python
from src.scrapers.regional import RegionalScraper
from scrapers_dev.debug_wait_strategy import DevelopmentWaitStrategy

# Usar estrategia de desarrollo
dev_strategy = DevelopmentWaitStrategy(debug_output_dir="debug")

async with RegionalScraper(
    departamento="AREQUIPA",
    anio="2025",
    wait_strategy=dev_strategy  # Pasar estrategia de desarrollo
) as scraper:
    await scraper.navigate_to_seace()
    # ... resto del código
    await scraper.click_boton_de_buscar()  # Usa DevelopmentWaitStrategy
    # Ahora tienes network_analysis.json en debug/
```

### Desarrollo Profundo (scripts separados)
```python
# scrapers_dev/scripts/analyze_network.py
from scrapers_dev.network_monitor import NetworkMonitor

async def analyze_search_click():
    """Script para analizar qué peticiones se hacen al buscar."""
    monitor = NetworkMonitor(page)
    monitor.start_monitoring()
    
    # Hacer click en buscar
    await button.click()
    
    # Esperar a que termine
    await page.wait_for_load_state("networkidle")
    
    # Analizar
    ajax_requests = monitor.get_ajax_requests()
    print(f"Peticiones AJAX detectadas: {len(ajax_requests)}")
    for req in ajax_requests:
        print(f"  - {req['method']} {req['url']}")
    
    monitor.stop_monitoring()
```

---

## Resumen

### Lo que se mantiene:
- ✅ **Lógica de detección de peticiones:** Fundamental para esperas inteligentes
- ✅ **Funcionalidad completa:** Todo lo necesario para scraping robusto

### Lo que se optimiza:
- ✅ **Producción:** Solo espera la petición, sin capturar ni guardar
- ✅ **Desarrollo:** Herramientas disponibles cuando las necesites
- ✅ **Separación:** Código de producción limpio, herramientas de desarrollo separadas

### Resultado:
- **Producción:** Código limpio, rápido, sin overhead
- **Desarrollo:** Herramientas poderosas disponibles cuando las necesites
- **Mantenibilidad:** Separación clara, fácil de entender y extender

---

## Próximos Pasos

1. **Implementar estrategias de espera:** `ProductionWaitStrategy` y `DevelopmentWaitStrategy`
2. **Refactorizar scrapers:** Usar estrategias en lugar de código inline
3. **Crear herramientas de desarrollo:** Scripts y utilidades separadas
4. **Documentar uso:** Cómo usar cada modo según necesidad

¿Te parece bien esta arquitectura? ¿Algún ajuste o preocupación?
