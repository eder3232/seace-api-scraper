"""
Tests para las excepciones personalizadas.
"""

import pytest
from src.utils.exceptions import (
    SeaceScraperError,
    ElementNotFoundError,
    ScrapingError,
    TableNotFoundError,
    InvalidTableStructureError,
    ConfigurationError,
    NetworkTimeoutError,
)


class TestExceptions:
    """Tests para verificar que las excepciones funcionan correctamente."""
    
    def test_seace_scraper_error_base(self):
        """Test que verifica que SeaceScraperError es la excepción base."""
        assert issubclass(ElementNotFoundError, SeaceScraperError)
        assert issubclass(ScrapingError, SeaceScraperError)
        assert issubclass(TableNotFoundError, SeaceScraperError)
        assert issubclass(InvalidTableStructureError, SeaceScraperError)
        assert issubclass(ConfigurationError, SeaceScraperError)
        assert issubclass(NetworkTimeoutError, SeaceScraperError)
    
    def test_element_not_found_error(self):
        """Test que verifica ElementNotFoundError."""
        error = ElementNotFoundError("Elemento no encontrado")
        assert str(error) == "Elemento no encontrado"
        assert isinstance(error, SeaceScraperError)
    
    def test_scraping_error(self):
        """Test que verifica ScrapingError."""
        error = ScrapingError("Error durante scraping")
        assert str(error) == "Error durante scraping"
        assert isinstance(error, SeaceScraperError)
    
    def test_table_not_found_error(self):
        """Test que verifica TableNotFoundError."""
        error = TableNotFoundError("Tabla no encontrada")
        assert str(error) == "Tabla no encontrada"
        assert isinstance(error, SeaceScraperError)
    
    def test_invalid_table_structure_error(self):
        """Test que verifica InvalidTableStructureError."""
        error = InvalidTableStructureError("Estructura inválida")
        assert str(error) == "Estructura inválida"
        assert isinstance(error, SeaceScraperError)
    
    def test_configuration_error(self):
        """Test que verifica ConfigurationError."""
        error = ConfigurationError("Error de configuración")
        assert str(error) == "Error de configuración"
        assert isinstance(error, SeaceScraperError)
    
    def test_network_timeout_error(self):
        """Test que verifica NetworkTimeoutError."""
        error = NetworkTimeoutError("Timeout de red")
        assert str(error) == "Timeout de red"
        assert isinstance(error, SeaceScraperError)
