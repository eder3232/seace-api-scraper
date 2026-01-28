"""
Configuración base para los scrapers de SEACE.
Usa valores por defecto sensatos, sin requerir YAML.
"""

import os
from typing import Dict, Any, Optional


class BaseConfig:
    """Configuración base con valores por defecto sensatos."""
    
    # URL base de SEACE
    SEACE_BASE_URL: str = os.getenv(
        'SEACE_BASE_URL',
        'https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml'
    )
    
    # Timeouts (en milisegundos)
    PAGE_LOAD_TIMEOUT: int = int(os.getenv('SEACE_PAGE_LOAD_TIMEOUT', '30000'))
    ELEMENT_WAIT_TIMEOUT: int = int(os.getenv('SEACE_ELEMENT_WAIT_TIMEOUT', '10000'))
    NETWORK_TIMEOUT: int = int(os.getenv('SEACE_NETWORK_TIMEOUT', '30000'))
    
    # Configuración del navegador
    BROWSER_HEADLESS: bool = os.getenv('SEACE_HEADLESS', 'false').lower() == 'true'
    BROWSER_VIEWPORT_WIDTH: int = int(os.getenv('SEACE_VIEWPORT_WIDTH', '1920'))
    BROWSER_VIEWPORT_HEIGHT: int = int(os.getenv('SEACE_VIEWPORT_HEIGHT', '1080'))
    
    # Delays entre acciones (en segundos)
    DELAY_BETWEEN_PAGES: float = float(os.getenv('SEACE_DELAY_BETWEEN_PAGES', '2.0'))
    DELAY_BETWEEN_DOCUMENTS: float = float(os.getenv('SEACE_DELAY_BETWEEN_DOCUMENTS', '0.5'))
    
    # Logging
    LOG_LEVEL: str = os.getenv('LOG_LEVEL', 'INFO')
    LOG_DIR: str = os.getenv('LOG_DIR', 'logs')
    
    # Directorios de datos
    DATA_OUTPUT_DIR: str = os.getenv('DATA_OUTPUT_DIR', 'data')
    DEBUG_DIR: str = os.getenv('DEBUG_DIR', 'debug')
    
    @property
    def browser_viewport(self) -> Dict[str, int]:
        """Viewport del navegador."""
        return {
            'width': self.BROWSER_VIEWPORT_WIDTH,
            'height': self.BROWSER_VIEWPORT_HEIGHT
        }
    
    @property
    def timeouts(self) -> Dict[str, int]:
        """Diccionario con todos los timeouts."""
        return {
            'page_load': self.PAGE_LOAD_TIMEOUT,
            'element_wait': self.ELEMENT_WAIT_TIMEOUT,
            'network': self.NETWORK_TIMEOUT,
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Método de compatibilidad para acceso estilo diccionario.
        
        Args:
            key: Clave a obtener
            default: Valor por defecto si no se encuentra
        
        Returns:
            Valor de la configuración o default
        """
        return getattr(self, key.upper(), default)
