"""
Script de debug: scraper por nomenclatura (modo desarrollo).

Ejemplo:
    python scripts/debug_nomenclatura.py --nomenclatura "SIE-SIE-1-2026-SEDAPAR-1"
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path

# Agregar el directorio raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.nomenclatura import NomenclaturaScraper


async def run(nomenclatura: str) -> None:
    async with NomenclaturaScraper(nomenclatura=nomenclatura, debug=True) as scraper:
        await scraper.navigate_to_seace()
        await scraper.select_search_type()
        await scraper.click_busqueda_avanzada()

        await scraper.ingresar_nomenclatura(nomenclatura)
        await scraper.click_boton_de_buscar()

        await scraper.clickear_ficha_seleccion()
        cronograma = await scraper.obtener_cronograma()
        documentos = await scraper.scrapear_documentos_con_links()

        out = Path(scraper.config.DEBUG_DIR) / "debug_nomenclatura_resultado.json"
        out.write_text(
            json.dumps(
                {"nomenclatura": nomenclatura, "cronograma": cronograma, "documentos": documentos},
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
        print(f"Resultado guardado en: {out}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--nomenclatura", required=True)
    args = parser.parse_args()

    asyncio.run(run(args.nomenclatura))


if __name__ == "__main__":
    main()

