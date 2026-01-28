"""
Excepciones personalizadas para los scrapers de SEACE.
"""


class SeaceScraperError(Exception):
    """Excepción base para todos los errores del scraper."""
    pass


class ElementNotFoundError(SeaceScraperError):
    """Excepción lanzada cuando un elemento no se encuentra en la página."""
    pass


class ScrapingError(SeaceScraperError):
    """Excepción lanzada cuando ocurre un error durante el scraping."""
    pass


class TableNotFoundError(SeaceScraperError):
    """Excepción lanzada cuando la tabla de resultados no se encuentra."""
    pass


class InvalidTableStructureError(SeaceScraperError):
    """Excepción lanzada cuando la estructura de la tabla no es la esperada."""
    pass


class ConfigurationError(SeaceScraperError):
    """Excepción lanzada cuando hay un error en la configuración."""
    pass


class NetworkTimeoutError(SeaceScraperError):
    """Excepción lanzada cuando hay un timeout esperando una petición de red."""
    pass
