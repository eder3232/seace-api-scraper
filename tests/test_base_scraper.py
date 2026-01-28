"""
Tests unitarios para la clase base BaseScraper.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.scrapers.base import BaseScraper
from src.config.settings import BaseConfig
from src.utils.exceptions import SeaceScraperError


class TestBaseScraper:
    """Tests para BaseScraper."""
    
    @pytest.fixture
    def scraper(self):
        """Fixture que crea un scraper base."""
        return BaseScraper(debug=False)
    
    def test_init(self, scraper):
        """Test que verifica inicialización."""
        assert scraper.config is not None
        assert scraper.debug == False
        assert scraper.wait_strategy is not None
        assert scraper._started == False
    
    def test_init_con_debug(self):
        """Test que verifica inicialización con debug=True."""
        scraper = BaseScraper(debug=True)
        
        assert scraper.debug == True
        # En modo debug debería usar DevelopmentWaitStrategy
        assert scraper.wait_strategy is not None
    
    def test_ensure_started_raise_error(self, scraper):
        """Test que verifica que _ensure_started lanza error si no está iniciado."""
        scraper._started = False
        
        with pytest.raises(SeaceScraperError):
            scraper._ensure_started()
    
    def test_ensure_started_ok(self, scraper):
        """Test que verifica que _ensure_started no lanza error si está iniciado."""
        scraper._started = True
        
        # No debería lanzar excepción
        scraper._ensure_started()
    
    @pytest.mark.asyncio
    async def test_start(self, scraper):
        """Test que verifica inicio del scraper."""
        with patch('playwright.async_api.async_playwright') as mock_playwright:
            mock_playwright_instance = AsyncMock()
            mock_playwright.return_value.start = AsyncMock(return_value=mock_playwright_instance)
            
            mock_browser = AsyncMock()
            mock_context = AsyncMock()
            mock_page = AsyncMock()
            
            mock_playwright_instance.chromium.launch = AsyncMock(return_value=mock_browser)
            mock_browser.new_context = AsyncMock(return_value=mock_context)
            mock_context.new_page = AsyncMock(return_value=mock_page)
            
            await scraper.start()
            
            assert scraper._started == True
            assert scraper.playwright is not None
            assert scraper.browser is not None
            assert scraper.page is not None
    
    @pytest.mark.asyncio
    async def test_start_ya_iniciado(self, scraper):
        """Test que verifica que start no hace nada si ya está iniciado."""
        scraper._started = True
        
        # No debería lanzar error ni hacer nada
        await scraper.start()
    
    @pytest.mark.asyncio
    async def test_navigate_to_seace_sin_iniciar(self, scraper):
        """Test que verifica error al navegar sin iniciar."""
        scraper._started = False
        
        with pytest.raises(SeaceScraperError):
            await scraper.navigate_to_seace()
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test que verifica que funciona como context manager."""
        scraper = BaseScraper()
        
        with patch.object(scraper, 'start', new_callable=AsyncMock) as mock_start, \
             patch.object(scraper, 'close', new_callable=AsyncMock) as mock_close:
            
            async with scraper:
                mock_start.assert_called_once()
            
            mock_close.assert_called_once()
