"""
Script rápido para verificar que todos los imports funcionan correctamente.
"""

def test_imports():
    """Verifica que todos los módulos se pueden importar."""
    print("Verificando imports...")
    
    # Configuración
    from src.config.settings import BaseConfig
    print("✅ BaseConfig importado")
    
    # Excepciones
    from src.utils.exceptions import (
        SeaceScraperError,
        ElementNotFoundError,
        ScrapingError,
    )
    print("✅ Excepciones importadas")
    
    # Logging
    from src.utils.logging import setup_logging, get_logger
    print("✅ Logging importado")
    
    # Estrategias
    from src.utils.wait_strategies import (
        WaitStrategy,
        ProductionWaitStrategy,
        DevelopmentWaitStrategy,
    )
    print("✅ Estrategias de espera importadas")
    
    # Selectores
    from src.selectors.regional import SELECTORS as REGIONAL_SELECTORS
    from src.selectors.nomenclatura import SELECTORS as NOMENCLATURA_SELECTORS
    print("✅ Selectores importados")
    
    # Scrapers
    from src.scrapers.base import BaseScraper
    from src.scrapers.regional import RegionalScraper
    from src.scrapers.nomenclatura import NomenclaturaScraper
    print("✅ Scrapers importados")
    
    # Verificar que se pueden instanciar
    config = BaseConfig()
    print(f"✅ Config creada: {config.SEACE_BASE_URL}")
    
    regional_scraper = RegionalScraper(departamento="AREQUIPA", anio="2025")
    print("✅ RegionalScraper instanciado")
    
    nomenclatura_scraper = NomenclaturaScraper(nomenclatura="TEST-123")
    print("✅ NomenclaturaScraper instanciado")
    
    print("\n🎉 Todos los imports funcionan correctamente!")


if __name__ == "__main__":
    test_imports()
