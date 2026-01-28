"""
Script de debug detallado para el scraper regional.
Compara diferentes enfoques y captura información para diagnóstico.

Ejemplo:
    python scripts/debug_regional_detallado.py --departamento AREQUIPA --anio 2026
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Agregar el directorio raíz del proyecto al path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.scrapers.regional import RegionalScraper
from src.utils.logging import get_logger

logger = get_logger(__name__)


async def debug_con_orden_produccion(departamento: str, anio: str, output_dir: Path):
    """Prueba con el orden usado en producción: primero departamento, luego año."""
    logger.info("=" * 80)
    logger.info("DEBUG: Orden PRODUCCIÓN (departamento -> año)")
    logger.info("=" * 80)
    
    try:
        async with RegionalScraper(departamento=departamento, anio=anio, debug=True) as scraper:
            await scraper.navigate_to_seace()
            
            # Capturar screenshot después de navegar
            screenshot_path = output_dir / "01_navegacion.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            logger.info(f"Screenshot guardado: {screenshot_path}")
            
            await scraper.select_search_type()
            screenshot_path = output_dir / "02_tipo_busqueda.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            await scraper.click_busqueda_avanzada()
            screenshot_path = output_dir / "03_busqueda_avanzada.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            # ORDEN PRODUCCIÓN: primero departamento
            logger.info(">>> Seleccionando DEPARTAMENTO primero...")
            await scraper.desplegar_boton_para_seleccionar_departamento()
            screenshot_path = output_dir / "04_departamento_desplegado.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            await scraper.seleccionar_departamento(departamento)
            screenshot_path = output_dir / "05_departamento_seleccionado.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            # Guardar HTML del panel de departamento
            panel = scraper.page.locator("#tbBuscador\\:idFormBuscarProceso\\:departamento")
            html = await panel.evaluate("element => element.outerHTML")
            html_path = output_dir / "departamento_seleccionado.html"
            html_path.write_text(html, encoding="utf-8")
            logger.info(f"HTML guardado: {html_path}")
            
            # Luego año
            logger.info(">>> Seleccionando AÑO después...")
            await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
            screenshot_path = output_dir / "06_anio_desplegado.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            await scraper.seleccionar_anio_de_convocatoria(anio)
            screenshot_path = output_dir / "07_anio_seleccionado.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            # Guardar HTML del panel de año
            panel_anio = scraper.page.locator("#tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria")
            html_anio = await panel_anio.evaluate("element => element.outerHTML")
            html_path_anio = output_dir / "anio_seleccionado.html"
            html_path_anio.write_text(html_anio, encoding="utf-8")
            logger.info(f"HTML guardado: {html_path_anio}")
            
            # Capturar HTML completo antes de buscar
            html_completo = await scraper.page.content()
            html_completo_path = output_dir / "antes_de_buscar.html"
            html_completo_path.write_text(html_completo, encoding="utf-8")
            logger.info(f"HTML completo guardado: {html_completo_path}")
            
            # Buscar
            logger.info(">>> Haciendo click en buscar...")
            await scraper.click_boton_de_buscar()
            
            # Esperar un poco más para asegurar que cargue
            await asyncio.sleep(3)
            
            screenshot_path = output_dir / "08_despues_de_buscar.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            logger.info(f"Screenshot guardado: {screenshot_path}")
            
            # Capturar HTML después de buscar
            html_despues = await scraper.page.content()
            html_despues_path = output_dir / "despues_de_buscar.html"
            html_despues_path.write_text(html_despues, encoding="utf-8")
            logger.info(f"HTML después de buscar guardado: {html_despues_path}")
            
            # Intentar extraer datos de TODAS las páginas
            logger.info(">>> Intentando extraer datos de todas las páginas...")
            try:
                csv_name = f"resultados_orden_produccion.csv"
                df = await scraper.obtener_todas_las_paginas_de_procesos(nombre_archivo_csv=csv_name)
                total_registros = len(df)
                logger.info(f"✓ Datos extraídos: {total_registros} registros totales")
                
                # También guardar en el directorio de debug
                csv_path = output_dir / csv_name
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                logger.info(f"CSV guardado: {csv_path}")
                
                return total_registros
            except Exception as e:
                logger.error(f"Error al extraer datos: {e}")
                # Capturar HTML del contenedor de resultados
                try:
                    container = scraper.page.locator("#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos")
                    html_container = await container.evaluate("element => element.outerHTML")
                    container_path = output_dir / "contenedor_resultados_error.html"
                    container_path.write_text(html_container, encoding="utf-8")
                    logger.info(f"HTML del contenedor guardado: {container_path}")
                    
                    # Verificar si hay mensaje de "sin resultados"
                    texto_container = await container.inner_text()
                    logger.info(f"Texto del contenedor: {texto_container[:500]}")
                except Exception as e2:
                    logger.error(f"Error al capturar contenedor: {e2}")
                
                raise
            
    except Exception as e:
        logger.error(f"Error en debug con orden producción: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0


async def debug_con_orden_experimental(departamento: str, anio: str, output_dir: Path):
    """Prueba con el orden usado en experimental: primero año, luego departamento."""
    logger.info("=" * 80)
    logger.info("DEBUG: Orden EXPERIMENTAL (año -> departamento)")
    logger.info("=" * 80)
    
    try:
        async with RegionalScraper(departamento=departamento, anio=anio, debug=True) as scraper:
            await scraper.navigate_to_seace()
            await scraper.select_search_type()
            await scraper.click_busqueda_avanzada()
            
            # ORDEN EXPERIMENTAL: primero año
            logger.info(">>> Seleccionando AÑO primero...")
            await scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
            await scraper.seleccionar_anio_de_convocatoria(anio)
            
            # Luego departamento
            logger.info(">>> Seleccionando DEPARTAMENTO después...")
            await scraper.desplegar_boton_para_seleccionar_departamento()
            await scraper.seleccionar_departamento(departamento)
            
            screenshot_path = output_dir / "09_orden_experimental_antes_buscar.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            # Buscar
            logger.info(">>> Haciendo click en buscar...")
            await scraper.click_boton_de_buscar()
            await asyncio.sleep(3)
            
            screenshot_path = output_dir / "10_orden_experimental_despues_buscar.png"
            await scraper.page.screenshot(path=str(screenshot_path))
            
            # Intentar extraer datos de TODAS las páginas
            logger.info(">>> Intentando extraer datos de todas las páginas...")
            try:
                csv_name = f"resultados_orden_experimental.csv"
                df = await scraper.obtener_todas_las_paginas_de_procesos(nombre_archivo_csv=csv_name)
                total_registros = len(df)
                logger.info(f"✓ Datos extraídos: {total_registros} registros totales")
                
                # También guardar en el directorio de debug
                csv_path = output_dir / csv_name
                df.to_csv(csv_path, index=False, encoding="utf-8-sig")
                logger.info(f"CSV guardado: {csv_path}")
                
                return total_registros
            except Exception as e:
                logger.error(f"Error al extraer datos: {e}")
                raise
            
    except Exception as e:
        logger.error(f"Error en debug con orden experimental: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 0


async def main():
    parser = argparse.ArgumentParser(description="Debug detallado del scraper regional")
    parser.add_argument("--departamento", required=True, help="Departamento a buscar")
    parser.add_argument("--anio", required=True, help="Año de convocatoria")
    parser.add_argument("--orden", choices=["produccion", "experimental", "ambos"], 
                       default="ambos", help="Orden a probar")
    args = parser.parse_args()
    
    # Crear directorio de salida con timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path("debug") / f"regional_{args.departamento}_{args.anio}_{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Directorio de debug: {output_dir}")
    
    resultados = {}
    
    if args.orden in ["produccion", "ambos"]:
        resultados["produccion"] = await debug_con_orden_produccion(
            args.departamento, args.anio, output_dir
        )
    
    if args.orden in ["experimental", "ambos"]:
        resultados["experimental"] = await debug_con_orden_experimental(
            args.departamento, args.anio, output_dir
        )
    
    # Resumen
    logger.info("=" * 80)
    logger.info("RESUMEN DE RESULTADOS")
    logger.info("=" * 80)
    for orden, cantidad in resultados.items():
        logger.info(f"Orden {orden}: {cantidad} registros")
    logger.info(f"Archivos guardados en: {output_dir}")


if __name__ == "__main__":
    asyncio.run(main())
