"""
Tests para la configuración.
"""

import pytest
import os
from src.config.settings import BaseConfig


class TestBaseConfig:
    """Tests para BaseConfig."""
    
    def test_default_values(self):
        """Test que verifica valores por defecto."""
        config = BaseConfig()
        
        assert config.SEACE_BASE_URL is not None
        assert config.PAGE_LOAD_TIMEOUT == 30000
        assert config.ELEMENT_WAIT_TIMEOUT == 10000
        assert config.BROWSER_HEADLESS == False
        assert config.BROWSER_VIEWPORT_WIDTH == 1920
        assert config.BROWSER_VIEWPORT_HEIGHT == 1080
    
    def test_browser_viewport_property(self):
        """Test que verifica la propiedad browser_viewport."""
        config = BaseConfig()
        viewport = config.browser_viewport
        
        assert isinstance(viewport, dict)
        assert viewport['width'] == 1920
        assert viewport['height'] == 1080
    
    def test_timeouts_property(self):
        """Test que verifica la propiedad timeouts."""
        config = BaseConfig()
        timeouts = config.timeouts
        
        assert isinstance(timeouts, dict)
        assert 'page_load' in timeouts
        assert 'element_wait' in timeouts
        assert 'network' in timeouts
        assert timeouts['page_load'] == 30000
        assert timeouts['element_wait'] == 10000
    
    def test_get_method(self):
        """Test que verifica el método get."""
        config = BaseConfig()
        
        # Debería retornar el valor del atributo
        assert config.get('SEACE_BASE_URL') is not None
        
        # Debería retornar default si no existe
        assert config.get('NONEXISTENT', 'default') == 'default'
