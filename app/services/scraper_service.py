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
    """
    csv_name = output_csv or f"procesos_{departamento}_{anio}.csv"
    async with RegionalScraper(departamento=departamento, anio=anio, debug=debug) as scraper:
        await scraper.navigate_to_seace()
        await scraper.select_search_type()
        await scraper.click_busqueda_avanzada()
        await scraper.desplegar_boton_para_seleccionar_departamento()
        await scraper.seleccionar_departamento(departamento)
        await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
        await scraper.seleccionar_anio_de_convocatoria(anio)
        df = await scraper.obtener_todas_las_paginas_de_procesos(nombre_archivo_csv=csv_name)

        csv_path = Path(scraper.config.DATA_OUTPUT_DIR) / csv_name
        return int(len(df)), str(csv_path)


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

