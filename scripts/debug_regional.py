"""
Script de debug: scraper regional (modo desarrollo).

Ejemplo:
    python scripts/debug_regional.py --departamento AREQUIPA --anio 2025
"""

import argparse
import asyncio

from src.scrapers.regional import RegionalScraper


async def run(departamento: str, anio: str) -> None:
    async with RegionalScraper(departamento=departamento, anio=anio, debug=True) as scraper:
        await scraper.navigate_to_seace()
        await scraper.select_search_type()
        await scraper.click_busqueda_avanzada()

        await scraper.desplegar_boton_para_seleccionar_departamento()
        await scraper.seleccionar_departamento(departamento)

        await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
        await scraper.seleccionar_anio_de_convocatoria(anio)

        await scraper.click_boton_de_buscar()
        await scraper.obtener_todas_las_paginas_de_procesos(nombre_archivo_csv="debug_regional.csv")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--departamento", required=True)
    parser.add_argument("--anio", required=True)
    args = parser.parse_args()

    asyncio.run(run(args.departamento, args.anio))


if __name__ == "__main__":
    main()

