"""
Estrategias de espera para los scrapers.
Permite diferentes comportamientos en producción vs desarrollo.
"""

import asyncio
import inspect
from typing import Optional

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
    
    async def prepare_wait(self, page) -> None:
        """
        Prepara la espera ANTES del click.
        Configura listeners y prepara el monitoreo de peticiones AJAX.
        
        Args:
            page: Página de Playwright
        """
        # Por defecto no hace nada, las subclases pueden sobrescribir
        pass
    
    async def click_and_wait_for_response(
        self,
        page,
        button_locator,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Hace click en el botón y espera la respuesta AJAX.
        Usa expect_response como context manager ANTES del click.
        
        Args:
            page: Página de Playwright
            button_locator: Locator del botón a clickear
            selectors: Diccionario con selectores necesarios
            timeout: Timeout máximo en milisegundos
        """
        # Por defecto solo hace click, las subclases pueden sobrescribir
        await button_locator.click()
    
    async def wait_for_search_results(
        self,
        page,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Espera a que los resultados de búsqueda estén listos.
        Se llama DESPUÉS del click en buscar.
        
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
    
    async def prepare_wait(self, page) -> None:
        """
        Prepara la espera ANTES del click.
        En producción no necesita hacer nada especial.
        """
        logger.debug("Preparando espera (producción - sin acción necesaria)")
    
    async def click_and_wait_for_response(
        self,
        page,
        button_locator,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Hace click en el botón y espera la respuesta AJAX usando expect_response.
        En Playwright Python, expect_response debe usarse ANTES del click.
        """
        try:
            logger.debug("Haciendo click y esperando respuesta AJAX (POST a buscadorPublico.xhtml)...")
            
            # Usar expect_response como context manager ANTES del click
            async with page.expect_response(
                lambda response: (
                    "buscadorPublico.xhtml" in response.url and
                    response.request.method == "POST" and
                    response.status == 200
                ),
                timeout=timeout
            ) as response_info:
                # Hacer click dentro del context manager
                await button_locator.click()
            
            # Obtener la respuesta después de que se complete
            response = await response_info.value
            logger.info(f"✓ Respuesta AJAX recibida: {response.url} (status: {response.status})")
            
        except Exception as e:
            logger.warning(f"No se detectó respuesta AJAX específica: {e}")
            # Fallback: hacer click sin esperar respuesta específica
            logger.debug("Usando fallback: haciendo click sin espera específica...")
            await button_locator.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=min(timeout, 15000))
            except Exception:
                logger.debug("networkidle timeout, continuando...")
    
    async def wait_for_search_results(
        self,
        page,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Espera a que termine de renderizar y valida los resultados.
        Se llama DESPUÉS de click_and_wait_for_response.
        """
        try:
            
            # 2. Esperar a que la página termine de renderizar completamente
            logger.debug("Esperando a que termine de renderizar la UI...")
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                logger.debug("networkidle timeout, continuando...")
            
            # 3. Esperar un tiempo adicional para que el DOM se actualice completamente
            # JSF puede necesitar tiempo adicional para actualizar la tabla después de la respuesta AJAX
            await asyncio.sleep(2)
            
            # 4. Validar que hay resultados en la tabla
            # Esto buscará las filas dentro del contenedor y validará la estructura
            logger.debug("Validando estructura de la tabla...")
            await self._validate_table_structure(page, selectors)
            
            logger.info("✓ Resultados cargados y validados correctamente")
            
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
        
        # Verificar si el contenedor existe
        container_count = await container_locator.count()
        if container_count == 0:
            raise TableNotFoundError("El contenedor de resultados no se encuentra")
        
        # Buscar filas dentro del contenedor
        rows_locator = await _maybe_await(container_locator.locator(table_selector))
        rows = await rows_locator.all()
        
        logger.debug(f"Filas encontradas en contenedor: {len(rows)}")
        
        if len(rows) == 0:
            # Fallback: algunos DOMs (o mocks) no encadenan locator() desde el contenedor
            # y exponen directamente las filas desde page.locator(table_selector).
            logger.debug("Intentando buscar filas directamente desde page...")
            page_rows_locator = await _maybe_await(page.locator(table_selector))
            page_rows = await page_rows_locator.all()
            if len(page_rows) > 0:
                logger.debug(f"Filas encontradas directamente: {len(page_rows)}")
                rows = page_rows
            else:
                # Verificar si hay mensaje de "no hay resultados"
                try:
                    container_text = (await container_locator.inner_text()).lower()
                    if any(msg in container_text for msg in ["no hay", "sin resultados", "no se encontraron"]):
                        raise TableNotFoundError("No hay resultados en la búsqueda")
                    else:
                        # Esperar un poco más y reintentar
                        logger.debug("Esperando más tiempo para que se carguen las filas...")
                        await asyncio.sleep(2)
                        rows_locator = await _maybe_await(container_locator.locator(table_selector))
                        rows = await rows_locator.all()
                        if len(rows) == 0:
                            raise TableNotFoundError("La tabla está vacía después de esperar")
                except Exception as e:
                    if isinstance(e, TableNotFoundError):
                        raise
                    logger.warning(f"Error al verificar mensaje de sin resultados: {e}")
                    raise TableNotFoundError("La tabla está vacía")
        
        # Verificar que la primera fila tiene columnas suficientes
        if len(rows) > 0:
            primera_fila = rows[0]
            celdas_locator = await _maybe_await(primera_fila.locator(cell_selector))
            celdas = await celdas_locator.all()
            
            if len(celdas) < min_columns:
                raise InvalidTableStructureError(
                    f"Tabla tiene {len(celdas)} columnas, se esperaban al menos {min_columns}"
                )
            
            logger.debug(f"Tabla validada: {len(rows)} filas, {len(celdas)} columnas")
        else:
            raise TableNotFoundError("No se encontraron filas en la tabla")


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
        # Devtool reutilizable para monitorear red (se adjunta una sola vez).
        from ..devtools.network_monitor import NetworkMonitor

        self._monitor = NetworkMonitor(output_dir=debug_output_dir, enabled=True)
        self._monitoring_enabled = False
    
    async def prepare_wait(self, page) -> None:
        """
        Prepara la espera ANTES del click.
        Configura el monitoreo de red y captura el estado inicial.
        """
        # Habilitar captura de red
        self._setup_network_capture(page)
        
        # Capturar estado ANTES del click
        self._network_before = self._monitor.snapshot()
        logger.info(f"Estado ANTES del click: {len(self._network_before.requests)} peticiones")
    
    async def click_and_wait_for_response(
        self,
        page,
        button_locator,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Hace click en el botón y espera la respuesta AJAX usando expect_response.
        También captura información de red para análisis.
        """
        try:
            logger.debug("Haciendo click y esperando respuesta AJAX (POST a buscadorPublico.xhtml)...")
            
            # Usar expect_response como context manager ANTES del click
            async with page.expect_response(
                lambda response: (
                    "buscadorPublico.xhtml" in response.url and
                    response.request.method == "POST"
                ),
                timeout=timeout
            ) as response_info:
                # Hacer click dentro del context manager
                await button_locator.click()
            
            # Obtener la respuesta después de que se complete
            response = await response_info.value
            logger.info(f"✓ Respuesta AJAX recibida: {response.url} (status: {response.status})")
            
        except Exception as e:
            logger.warning(f"No se detectó respuesta AJAX: {e}")
            # Fallback: hacer click sin esperar respuesta específica
            logger.debug("Usando fallback: haciendo click sin espera específica...")
            await button_locator.click()
            try:
                await page.wait_for_load_state("networkidle", timeout=min(timeout, 15000))
            except Exception:
                logger.debug("networkidle timeout, continuando...")
    
    async def wait_for_search_results(
        self,
        page,
        selectors: dict,
        timeout: int = 30000
    ) -> None:
        """
        Espera a que termine de renderizar y valida los resultados.
        También captura información de red para análisis.
        Se llama DESPUÉS de click_and_wait_for_response.
        """
        try:
            # 1. Esperar a que termine de renderizar
            logger.debug("Esperando a que termine de renderizar la UI...")
            try:
                await page.wait_for_load_state("networkidle", timeout=5000)
            except Exception:
                logger.debug("networkidle timeout, continuando...")
            
            # 3. Esperar tiempo adicional para actualización del DOM
            await asyncio.sleep(2)
            
            # 4. Validar estructura
            await self._validate_table_structure(page, selectors)
            
            # 5. Capturar estado DESPUÉS y analizar
            await asyncio.sleep(1)  # Dar tiempo a que lleguen todas las respuestas
            network_after = self._monitor.snapshot()
            logger.info(f"Estado DESPUÉS del click: {len(network_after.requests)} peticiones")

            # Analizar cambios
            if hasattr(self, '_network_before'):
                analysis = self._monitor.analyze(self._network_before, network_after)
                self._log_analysis(analysis)
                self._save_analysis(analysis, "network_analysis_search.json")
            
            logger.info("✓ Resultados cargados y análisis de red completado")
            
        except Exception as e:
            logger.error(f"Error esperando resultados: {e}")
            raise ScrapingError(f"Error esperando resultados de búsqueda: {e}") from e
    
    def _setup_network_capture(self, page):
        """Configura captura de red (solo en desarrollo)."""
        if self._monitoring_enabled:
            return

        self._monitor.attach(page)
        self._monitoring_enabled = True
        logger.info("Monitoreo de red habilitado")
    
    def _log_analysis(self, analysis: dict):
        """Loggea resumen del análisis."""
        logger.info("=" * 60)
        logger.info("ANÁLISIS DE RED - Resumen:")
        counts = analysis.get("counts", {})
        logger.info(f"  - Nuevas peticiones totales: {counts.get('new_requests')}")
        logger.info(f"  - Nuevas respuestas totales: {counts.get('new_responses')}")
        logger.info(f"  - Peticiones AJAX/XHR: {counts.get('ajax_requests')}")
        logger.info("=" * 60)

        ajax_details = analysis.get("ajax_requests", [])
        if ajax_details:
            logger.info("Peticiones AJAX/XHR detectadas:")
            for req in ajax_details:
                logger.info(f"  - {req.get('method')} {req.get('url')}")
    
    def _save_analysis(self, analysis: dict, filename: str):
        """Guarda análisis en archivo JSON."""
        try:
            self._monitor.save_json(analysis, filename)
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
