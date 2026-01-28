"""
Clase base para todos los scrapers de SEACE.
Proporciona funcionalidad común y manejo de recursos.
"""

import asyncio
import inspect
from typing import Optional
from pathlib import Path

from playwright.async_api import async_playwright, Page, Browser, BrowserContext, Playwright

from ..config.settings import BaseConfig
from ..utils.exceptions import SeaceScraperError, ScrapingError
from ..utils.logging import setup_logging, get_logger
from ..utils.wait_strategies import WaitStrategy, ProductionWaitStrategy


class BaseScraper:
    """
    Clase base para scrapers de SEACE.
    
    Características:
    - Context manager async para manejo seguro de recursos
    - Estrategia de espera configurable (producción o desarrollo)
    - Logging profesional
    - Configuración flexible
    """
    
    def __init__(
        self,
        config: Optional[BaseConfig] = None,
        debug: bool = False,
        wait_strategy: Optional[WaitStrategy] = None
    ):
        """
        Inicializa el scraper base.
        
        Args:
            config: Configuración (opcional, usa BaseConfig por defecto)
            debug: Si True, habilita modo debug
            wait_strategy: Estrategia de espera (opcional, usa ProductionWaitStrategy por defecto)
        """
        # Configuración
        self.config = config or BaseConfig()
        self.debug = debug
        
        # Elegir estrategia de espera
        if wait_strategy:
            self.wait_strategy = wait_strategy
        elif debug:
            # En desarrollo, importar y usar DevelopmentWaitStrategy
            from ..utils.wait_strategies import DevelopmentWaitStrategy
            self.wait_strategy = DevelopmentWaitStrategy(debug_output_dir=self.config.DEBUG_DIR)
        else:
            # En producción, usar estrategia optimizada
            self.wait_strategy = ProductionWaitStrategy()
        
        # Recursos de Playwright
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
        # Estado del scraper
        self._started = False
        
        # Configurar logging
        log_file = f"scraper_{self.__class__.__name__.lower()}.log" if not debug else None
        setup_logging(
            log_level=self.config.LOG_LEVEL,
            log_file=log_file,
            log_dir=self.config.LOG_DIR
        )
        self.logger = get_logger(__name__)
        
        # Crear directorios necesarios
        self._setup_directories()
        
        self.logger.info(f"{self.__class__.__name__} inicializado")
    
    def _setup_directories(self):
        """Crea los directorios necesarios si no existen."""
        directories = [
            self.config.DATA_OUTPUT_DIR,
            self.config.DEBUG_DIR,
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
            self.logger.debug(f"Directorio verificado/creado: {directory}")
    
    async def start(self):
        """
        Inicia el navegador y configura el contexto.
        
        Raises:
            ScrapingError: Si hay un error al iniciar el navegador
        """
        if self._started:
            self.logger.warning("El scraper ya está iniciado")
            return
        
        try:
            self.logger.info("Iniciando navegador...")
            self.playwright = await async_playwright().start()
            
            viewport = self.config.browser_viewport
            timeouts = self.config.timeouts
            
            self.browser = await self.playwright.chromium.launch(
                headless=self.config.BROWSER_HEADLESS
            )
            
            self.context = await self.browser.new_context(
                viewport={
                    'width': viewport['width'],
                    'height': viewport['height']
                },
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            self.page = await self.context.new_page()
            
            # Configurar timeouts
            self.page.set_default_timeout(timeouts['element_wait'])
            self.page.set_default_navigation_timeout(timeouts['page_load'])
            
            self._started = True
            self.logger.info("Navegador iniciado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al iniciar el navegador: {e}")
            raise ScrapingError(f"Error al iniciar el navegador: {e}") from e
    
    async def navigate_to_seace(self):
        """
        Navega a la página principal de SEACE.
        
        Raises:
            ScrapingError: Si hay un error al navegar
        """
        self._ensure_started()
        
        try:
            url = self.config.SEACE_BASE_URL
            self.logger.info(f"Navegando a SEACE: {url}")
            await self.page.goto(url)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)  # Pequeño delay para estabilizar
            self.logger.info("Página de SEACE cargada correctamente")
        except Exception as e:
            self.logger.error(f"Error al navegar a SEACE: {e}")
            raise ScrapingError(f"Error al navegar a SEACE: {e}") from e
    
    async def select_search_type(self, search_type_text: str = "Buscador de Procedimientos de Selección"):
        """
        Selecciona el tipo de búsqueda.
        
        Args:
            search_type_text: Texto del tipo de búsqueda a seleccionar
        
        Raises:
            ScrapingError: Si hay un error al seleccionar
        """
        self._ensure_started()
        
        try:
            self.logger.info(f"Seleccionando tipo de búsqueda: {search_type_text}")
            search_type_locator = self.page.locator('#tbBuscador')
            search_type_button = search_type_locator.get_by_text(search_type_text)
            
            if not await search_type_button.is_visible(timeout=10000):
                raise ScrapingError(f"No se encontró el botón de tipo de búsqueda: {search_type_text}")
            
            await search_type_button.click()
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)  # Pequeño delay
            self.logger.info("Tipo de búsqueda seleccionado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al seleccionar tipo de búsqueda: {e}")
            raise ScrapingError(f"Error al seleccionar tipo de búsqueda: {e}") from e
    
    async def click_busqueda_avanzada(self):
        """
        Hace click en el botón de búsqueda avanzada.
        
        Raises:
            ScrapingError: Si hay un error al hacer click
        """
        self._ensure_started()
        
        try:
            self.logger.info("Buscando botón de búsqueda avanzada...")
            container = self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:pnlBuscarProceso")
            button = container.get_by_text("Búsqueda Avanzada")
            
            if not await button.is_visible(timeout=10000):
                raise ScrapingError("No se encontró el botón de búsqueda avanzada")
            
            await button.click()
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(1)  # Pequeño delay
            self.logger.info("Botón de búsqueda avanzada clickeado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al hacer click en búsqueda avanzada: {e}")
            raise ScrapingError(f"Error al hacer click en búsqueda avanzada: {e}") from e

    async def _maybe_await(self, value):
        """
        Compatibilidad con mocks async en tests.

        En Playwright real, métodos como page.locator(...) retornan un Locator inmediato.
        En tests, al usar AsyncMock, esos mismos métodos pueden retornar un coroutine.
        """
        if inspect.isawaitable(value):
            return await value
        return value

    async def _locator(self, selector: str):
        """Obtiene un locator, soportando retornos awaitables (tests)."""
        self._ensure_started()
        return await self._maybe_await(self.page.locator(selector))
    
    def _ensure_started(self):
        """Verifica que el scraper esté iniciado."""
        if not self._started:
            raise SeaceScraperError("El scraper no está iniciado. Llama a start() primero o usa el context manager.")
    
    async def close(self):
        """Cierra el navegador y libera recursos."""
        try:
            if self.browser:
                self.logger.info("Cerrando navegador...")
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            self._started = False
            self.logger.info("Recursos liberados correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al cerrar recursos: {e}")
    
    async def __aenter__(self):
        """Async context manager: inicia el scraper al entrar."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager: cierra el scraper al salir."""
        await self.close()
        return False  # No suprime excepciones
