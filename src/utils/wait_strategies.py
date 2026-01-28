"""
Estrategias de espera para los scrapers.
Permite diferentes comportamientos en producción vs desarrollo.
"""

import asyncio
import json
import inspect
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from ..utils.exceptions import ScrapingError, TableNotFoundError, InvalidTableStructureError
from ..utils.logging import get_logger

logger = get_logger(__name__)

async def _maybe_await(value):
    """Compatibilidad con AsyncMock en tests (locator puede ser awaitable)."""
    if inspect.isawaitable(value):
        return await value
    return value


class WaitStrategy:
    """Estrategia base para esperar a que la página cargue."""
    
    async def wait_for_search_results(
        self,
        page,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Espera a que los resultados de búsqueda estén listos.
        
        Args:
            page: Página de Playwright
            selectors: Diccionario con selectores necesarios
            timeout: Timeout máximo en milisegundos
        
        Raises:
            ScrapingError: Si hay un error esperando los resultados
            TableNotFoundError: Si la tabla no se encuentra
        """
        raise NotImplementedError


class ProductionWaitStrategy(WaitStrategy):
    """
    Estrategia optimizada para producción.
    Solo espera la petición necesaria, sin capturar ni guardar información.
    """
    
    async def wait_for_search_results(
        self,
        page,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Espera SOLO a la petición AJAX que carga los resultados.
        No captura ni guarda nada, solo espera eficientemente.
        """
        try:
            # 1. Esperar específicamente a la petición POST que carga datos
            # Esta es la petición AJAX de JSF que actualiza la tabla
            logger.debug("Esperando respuesta AJAX de búsqueda...")
            
            try:
                await page.wait_for_response(
                    lambda response: (
                        "buscadorPublico.xhtml" in response.url and
                        response.request.method == "POST" and
                        response.status == 200
                    ),
                    timeout=timeout
                )
                logger.debug("Respuesta AJAX recibida")
            except Exception as e:
                logger.warning(f"No se detectó respuesta AJAX específica: {e}")
                # Continuar con espera de tabla como fallback
            
            # 2. Esperar a que la tabla sea visible
            logger.debug("Esperando a que la tabla sea visible...")
            table_selector = selectors.get('results_table_row', 'tbody tr')
            
            await page.wait_for_selector(
                table_selector,
                state="visible",
                timeout=10000
            )
            
            # 3. Validación rápida: verificar que tiene estructura correcta
            await self._validate_table_structure(page, selectors)
            
            logger.info("Resultados cargados y validados correctamente")
            
        except Exception as e:
            logger.error(f"Error esperando resultados: {e}")
            raise ScrapingError(f"Error esperando resultados de búsqueda: {e}") from e
    
    async def _validate_table_structure(
        self,
        page,
        selectors: dict
    ) -> None:
        """
        Valida rápidamente que la tabla tiene la estructura esperada.
        
        Raises:
            TableNotFoundError: Si la tabla no se encuentra
            InvalidTableStructureError: Si la estructura no es válida
        """
        table_selector = selectors.get('results_table_row', 'tbody tr')
        cell_selector = selectors.get('results_table_cell', 'td')
        min_columns = selectors.get('min_columns', 12)
        container_selector = selectors.get('results_container', 'body')

        # Buscar filas dentro del contenedor de resultados (más robusto y coincide con los tests)
        container_locator = await _maybe_await(page.locator(container_selector))
        rows_locator = await _maybe_await(container_locator.locator(table_selector))
        rows = await rows_locator.all()
        
        if len(rows) == 0:
            # Fallback: algunos DOMs (o mocks) no encadenan locator() desde el contenedor
            # y exponen directamente las filas desde page.locator(table_selector).
            page_rows_locator = await _maybe_await(page.locator(table_selector))
            page_rows = await page_rows_locator.all()
            if len(page_rows) > 0:
                rows = page_rows
            else:
            # Verificar si hay mensaje de "no hay resultados"
                container_text = (await container_locator.inner_text()).lower()
                if any(msg in container_text for msg in ["no hay", "sin resultados", "no se encontraron"]):
                    raise TableNotFoundError("No hay resultados en la búsqueda")
                else:
                    raise TableNotFoundError("La tabla está vacía")
        
        # Verificar que la primera fila tiene columnas suficientes
        primera_fila = rows[0]
        celdas_locator = await _maybe_await(primera_fila.locator(cell_selector))
        celdas = await celdas_locator.all()
        
        if len(celdas) < min_columns:
            raise InvalidTableStructureError(
                f"Tabla tiene {len(celdas)} columnas, se esperaban al menos {min_columns}"
            )
        
        logger.debug(f"Tabla validada: {len(rows)} filas, {len(celdas)} columnas")


class DevelopmentWaitStrategy(WaitStrategy):
    """
    Estrategia para desarrollo con monitoreo de red.
    Captura y analiza peticiones para debugging.
    """
    
    def __init__(self, debug_output_dir: str = "debug"):
        """
        Inicializa la estrategia de desarrollo.
        
        Args:
            debug_output_dir: Directorio donde guardar análisis de red
        """
        self.debug_output_dir = debug_output_dir
        self._network_requests = []
        self._network_responses = []
        self._monitoring_enabled = False
    
    async def wait_for_search_results(
        self,
        page,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Espera a los resultados PERO también captura información de red.
        """
        # Habilitar captura de red
        self._setup_network_capture(page)
        
        # Capturar estado ANTES del click (si ya se hizo)
        network_before = self._capture_snapshot()
        logger.info(f"Estado ANTES: {len(network_before['requests'])} peticiones")
        
        try:
            # Esperar respuesta AJAX (igual que producción)
            logger.debug("Esperando respuesta AJAX...")
            try:
                await page.wait_for_response(
                    lambda response: (
                        "buscadorPublico.xhtml" in response.url and
                        response.request.method == "POST"
                    ),
                    timeout=timeout
                )
                logger.debug("Respuesta AJAX recibida")
            except Exception as e:
                logger.warning(f"No se detectó respuesta AJAX: {e}")
            
            # Esperar tabla (igual que producción)
            table_selector = selectors.get('results_table_row', 'tbody tr')
            await page.wait_for_selector(
                table_selector,
                state="visible",
                timeout=10000
            )
            
            # Validar estructura
            await self._validate_table_structure(page, selectors)
            
            # Capturar estado DESPUÉS y analizar
            await asyncio.sleep(1)  # Dar tiempo a que lleguen todas las respuestas
            network_after = self._capture_snapshot()
            logger.info(f"Estado DESPUÉS: {len(network_after['requests'])} peticiones")
            
            # Analizar cambios
            analysis = self._analyze_changes(network_before, network_after)
            self._log_analysis(analysis)
            self._save_analysis(analysis, "network_analysis_search.json")
            
            logger.info("Resultados cargados y análisis de red completado")
            
        except Exception as e:
            logger.error(f"Error esperando resultados: {e}")
            raise ScrapingError(f"Error esperando resultados de búsqueda: {e}") from e
    
    def _setup_network_capture(self, page):
        """Configura captura de red (solo en desarrollo)."""
        if self._monitoring_enabled:
            return
        
        def on_request(request):
            self._network_requests.append({
                'url': request.url,
                'method': request.method,
                'resource_type': request.resource_type,
                'timestamp': datetime.now().isoformat(),
            })
            logger.debug(f"Request: {request.method} {request.url}")
        
        def on_response(response):
            try:
                self._network_responses.append({
                    'url': response.url,
                    'status': response.status,
                    'status_text': response.status_text,
                    'content_type': response.headers.get('content-type', ''),
                    'timestamp': datetime.now().isoformat(),
                })
                logger.debug(f"Response: {response.status} {response.url}")
            except Exception as e:
                logger.warning(f"Error capturando respuesta: {e}")
        
        page.on("request", on_request)
        page.on("response", on_response)
        self._monitoring_enabled = True
        logger.info("Monitoreo de red habilitado")
    
    def _capture_snapshot(self) -> dict:
        """Captura snapshot actual del estado de red."""
        return {
            'requests': self._network_requests.copy(),
            'responses': self._network_responses.copy(),
            'timestamp': datetime.now().isoformat(),
        }
    
    def _analyze_changes(self, before: dict, after: dict) -> dict:
        """Analiza cambios entre snapshots."""
        before_urls = {req['url'] for req in before['requests']}
        
        new_requests = [req for req in after['requests'] if req['url'] not in before_urls]
        new_responses = [resp for resp in after['responses'] if resp['url'] not in before_urls]
        
        # Filtrar recursos estáticos
        static_extensions = {'.css', '.js', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.ico', '.woff', '.woff2', '.ttf'}
        relevant_requests = [
            req for req in new_requests
            if not any(req['url'].lower().endswith(ext) for ext in static_extensions)
        ]
        
        # Identificar peticiones AJAX/XHR
        ajax_requests = [req for req in relevant_requests if req['resource_type'] in ['xhr', 'fetch']]
        ajax_responses = [
            resp for resp in new_responses
            if any(resp['url'] == req['url'] for req in ajax_requests)
        ]
        
        return {
            'total_new_requests': len(new_requests),
            'total_new_responses': len(new_responses),
            'relevant_requests': len(relevant_requests),
            'ajax_requests': len(ajax_requests),
            'ajax_requests_details': ajax_requests,
            'ajax_responses_details': ajax_responses,
        }
    
    def _log_analysis(self, analysis: dict):
        """Loggea resumen del análisis."""
        logger.info("=" * 60)
        logger.info("ANÁLISIS DE RED - Resumen:")
        logger.info(f"  - Nuevas peticiones totales: {analysis['total_new_requests']}")
        logger.info(f"  - Peticiones relevantes: {analysis['relevant_requests']}")
        logger.info(f"  - Peticiones AJAX/XHR: {analysis['ajax_requests']}")
        logger.info("=" * 60)
        
        if analysis['ajax_requests_details']:
            logger.info("Peticiones AJAX/XHR detectadas:")
            for req in analysis['ajax_requests_details']:
                logger.info(f"  - {req['method']} {req['url']}")
    
    def _save_analysis(self, analysis: dict, filename: str):
        """Guarda análisis en archivo JSON."""
        try:
            from pathlib import Path
            import json
            
            debug_path = Path(self.debug_output_dir)
            debug_path.mkdir(parents=True, exist_ok=True)
            
            file_path = debug_path / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(analysis, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Análisis de red guardado en {file_path}")
        except Exception as e:
            logger.warning(f"No se pudo guardar análisis de red: {e}")
    
    async def _validate_table_structure(
        self,
        page,
        selectors: dict
    ) -> None:
        """Valida estructura de tabla (igual que producción)."""
        table_selector = selectors.get('results_table_row', 'tbody tr')
        cell_selector = selectors.get('results_table_cell', 'td')
        min_columns = selectors.get('min_columns', 12)
        container_selector = selectors.get('results_container', 'body')

        container_locator = await _maybe_await(page.locator(container_selector))
        rows_locator = await _maybe_await(container_locator.locator(table_selector))
        rows = await rows_locator.all()
        
        if len(rows) == 0:
            page_rows_locator = await _maybe_await(page.locator(table_selector))
            page_rows = await page_rows_locator.all()
            if len(page_rows) > 0:
                rows = page_rows
            else:
                container_text = (await container_locator.inner_text()).lower()
                if any(msg in container_text for msg in ["no hay", "sin resultados", "no se encontraron"]):
                    raise TableNotFoundError("No hay resultados en la búsqueda")
                else:
                    raise TableNotFoundError("La tabla está vacía")
        
        primera_fila = rows[0]
        celdas_locator = await _maybe_await(primera_fila.locator(cell_selector))
        celdas = await celdas_locator.all()
        
        if len(celdas) < min_columns:
            raise InvalidTableStructureError(
                f"Tabla tiene {len(celdas)} columnas, se esperaban al menos {min_columns}"
            )
