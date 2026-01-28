"""
Tests unitarios para el scraper regional.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.scrapers.regional import RegionalScraper
from src.config.settings import BaseConfig
from src.utils.exceptions import ElementNotFoundError, ScrapingError


class TestRegionalScraper:
    """Tests para RegionalScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Fixture que crea un scraper para testing."""
        return RegionalScraper(
            departamento="AREQUIPA",
            anio="2025",
            debug=False
        )
    
    @pytest.fixture
    def mock_page(self):
        """Fixture que crea un mock de página de Playwright."""
        # En Playwright, page.locator(...) es síncrono y retorna un Locator (cuyos métodos sí son async).
        page = MagicMock()
        page.locator = MagicMock(return_value=AsyncMock())
        return page
    
    def test_init(self):
        """Test que verifica la inicialización del scraper."""
        scraper = RegionalScraper(departamento="AREQUIPA", anio="2025")
        
        assert scraper.departamento == "AREQUIPA"
        assert scraper.anio == "2025"
        assert scraper.config is not None
        assert scraper.wait_strategy is not None
    
    def test_init_sin_parametros(self):
        """Test que verifica inicialización sin parámetros."""
        scraper = RegionalScraper()
        
        assert scraper.departamento is None
        assert scraper.anio is None
    
    @pytest.mark.asyncio
    async def test_desplegar_boton_departamento_elemento_no_encontrado(self, scraper, mock_page):
        """Test que verifica error cuando no se encuentra el botón de departamento."""
        scraper.page = mock_page
        scraper._started = True
        
        container_mock = AsyncMock()
        button_mock = AsyncMock()
        button_mock.is_visible.return_value = False
        
        mock_page.locator.return_value = container_mock
        container_mock.locator.return_value = button_mock
        
        with pytest.raises(ElementNotFoundError):
            await scraper.desplegar_boton_para_seleccionar_departamento()
    
    @pytest.mark.asyncio
    async def test_seleccionar_departamento_sin_parametro(self, scraper):
        """Test que verifica error cuando no se proporciona departamento."""
        scraper._started = True
        scraper.departamento = None
        
        with pytest.raises(ValueError, match="Debe proporcionar un departamento"):
            await scraper.seleccionar_departamento()
    
    @pytest.mark.asyncio
    async def test_seleccionar_anio_sin_parametro(self, scraper):
        """Test que verifica error cuando no se proporciona año."""
        scraper._started = True
        scraper.anio = None
        
        with pytest.raises(ValueError, match="Debe proporcionar un año"):
            await scraper.seleccionar_anio_de_convocatoria()
    
    @pytest.mark.asyncio
    async def test_click_boton_buscar_sin_iniciar(self, scraper):
        """Test que verifica error cuando se intenta buscar sin iniciar."""
        scraper._started = False
        
        with pytest.raises(Exception):  # SeaceScraperError
            await scraper.click_boton_de_buscar()
    
    def test_scraper_hereda_de_base(self):
        """Test que verifica que RegionalScraper hereda de BaseScraper."""
        from src.scrapers.base import BaseScraper
        
        assert issubclass(RegionalScraper, BaseScraper)
