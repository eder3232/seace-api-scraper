"""
Tests unitarios para el scraper por nomenclatura.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.scrapers.nomenclatura import NomenclaturaScraper
from src.config.settings import BaseConfig
from src.utils.exceptions import ElementNotFoundError, ScrapingError


class TestNomenclaturaScraper:
    """Tests para NomenclaturaScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Fixture que crea un scraper para testing."""
        return NomenclaturaScraper(
            nomenclatura="SIE-SIE-1-2026-SEDAPAR-1",
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
        scraper = NomenclaturaScraper(nomenclatura="SIE-SIE-1-2026-SEDAPAR-1")
        
        assert scraper.nomenclatura == "SIE-SIE-1-2026-SEDAPAR-1"
        assert scraper.config is not None
        assert scraper.wait_strategy is not None
    
    def test_init_sin_parametros(self):
        """Test que verifica inicialización sin parámetros."""
        scraper = NomenclaturaScraper()
        
        assert scraper.nomenclatura is None
    
    @pytest.mark.asyncio
    async def test_ingresar_nomenclatura_sin_parametro(self, scraper):
        """Test que verifica error cuando no se proporciona nomenclatura."""
        scraper._started = True
        scraper.nomenclatura = None
        
        with pytest.raises(ValueError, match="Debe proporcionar una nomenclatura"):
            await scraper.ingresar_nomenclatura()
    
    @pytest.mark.asyncio
    async def test_ingresar_nomenclatura_elemento_no_encontrado(self, scraper, mock_page):
        """Test que verifica error cuando no se encuentra el campo de nomenclatura."""
        scraper.page = mock_page
        scraper._started = True
        
        input_mock = AsyncMock()
        input_mock.is_visible.return_value = False
        
        mock_page.locator.return_value = input_mock
        
        with pytest.raises(ElementNotFoundError):
            await scraper.ingresar_nomenclatura("TEST-123")
    
    @pytest.mark.asyncio
    async def test_click_boton_buscar_sin_iniciar(self, scraper):
        """Test que verifica error cuando se intenta buscar sin iniciar."""
        scraper._started = False
        
        with pytest.raises(Exception):  # SeaceScraperError
            await scraper.click_boton_de_buscar()
    
    def test_scraper_hereda_de_base(self):
        """Test que verifica que NomenclaturaScraper hereda de BaseScraper."""
        from src.scrapers.base import BaseScraper
        
        assert issubclass(NomenclaturaScraper, BaseScraper)
