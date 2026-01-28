"""
Servicios de aplicación: orquestación de scrapers (src/) para la API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Tuple

from src.scrapers.nomenclatura import NomenclaturaScraper
from src.scrapers.regional import RegionalScraper


async def run_regional_scrape(
    *,
    departamento: str,
    anio: str,
    output_csv: str | None,
    debug: bool,
) -> Tuple[int, str | None]:
    """
    Ejecuta scraping regional completo.

    Returns:
        (total_registros, csv_path)
    
    Raises:
        ScrapingError: Si hay un error durante el scraping
        TableNotFoundError: Si no se encuentran resultados
    """
    from src.utils.logging import get_logger
    logger = get_logger(__name__)
    
    csv_name = output_csv or f"procesos_{departamento}_{anio}.csv"
    
    try:
        async with RegionalScraper(departamento=departamento, anio=anio, debug=debug) as scraper:
            logger.info(f"Iniciando scraping regional: departamento={departamento}, anio={anio}")
            
            await scraper.navigate_to_seace()
            await scraper.select_search_type()
            await scraper.click_busqueda_avanzada()
            
            # Orden actual: primero departamento, luego año
            await scraper.desplegar_boton_para_seleccionar_departamento()
            await scraper.seleccionar_departamento(departamento)
            await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
            await scraper.seleccionar_anio_de_convocatoria(anio)

            # Importante: la UI de SEACE no carga resultados hasta presionar "Buscar"
            await scraper.click_boton_de_buscar()
            
            logger.info("Parámetros seleccionados, iniciando búsqueda...")
            df = await scraper.obtener_todas_las_paginas_de_procesos(nombre_archivo_csv=csv_name)

            total_registros = int(len(df))
            csv_path = Path(scraper.config.DATA_OUTPUT_DIR) / csv_name
            
            if total_registros == 0:
                logger.warning(f"No se encontraron registros para departamento={departamento}, anio={anio}")
                # No lanzar excepción, solo loggear y retornar 0
                # Esto permite que el job se complete exitosamente pero con 0 registros
            else:
                logger.info(f"Scraping completado: {total_registros} registros encontrados")
            
            return total_registros, str(csv_path)
            
    except Exception as e:
        logger.error(f"Error en scraping regional: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise


async def run_nomenclatura_scrape(
    *,
    nomenclatura: str,
    debug: bool,
) -> Dict[str, Any]:
    """
    Ejecuta scraping por nomenclatura: cronograma + documentos.
    """
    async with NomenclaturaScraper(nomenclatura=nomenclatura, debug=debug) as scraper:
        await scraper.navigate_to_seace()
        await scraper.select_search_type()
        await scraper.click_busqueda_avanzada()
        await scraper.ingresar_nomenclatura(nomenclatura)
        await scraper.click_boton_de_buscar()
        await scraper.clickear_ficha_seleccion()
        cronograma = await scraper.obtener_cronograma()
        documentos = await scraper.scrapear_documentos_con_links()

        return {"cronograma": cronograma, "documentos": documentos}

