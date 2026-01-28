"""
Scraper por nomenclatura de SEACE - Versión modularizada y optimizada.
Busca un proceso específico por su nomenclatura y extrae cronograma y documentos.
"""

import asyncio
import re
from pathlib import Path
from typing import Dict, List, Optional

from .base import BaseScraper
from ..selectors.nomenclatura import (
    SELECTORS,
    CRONOGRAMA_COLUMNS,
    DOCUMENTOS_COLUMNS,
    MIN_CRONOGRAMA_CELLS,
    MIN_DOCUMENTOS_CELLS,
    WAIT_SELECTORS,
)
from ..utils.exceptions import ScrapingError, ElementNotFoundError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class NomenclaturaScraper(BaseScraper):
    """
    Scraper para buscar un proceso específico de SEACE por nomenclatura.
    
    Características:
    - Búsqueda por nomenclatura específica
    - Extracción de cronograma
    - Extracción de documentos con links de descarga
    - Usa estrategias de espera optimizadas (producción o desarrollo)
    """
    
    def __init__(
        self,
        nomenclatura: Optional[str] = None,
        **kwargs
    ):
        """
        Inicializa el scraper por nomenclatura.
        
        Args:
            nomenclatura: Nomenclatura a buscar (ej: "SIE-SIE-1-2026-SEDAPAR-1")
            **kwargs: Argumentos adicionales para BaseScraper (config, debug, wait_strategy)
        """
        super().__init__(**kwargs)
        self.nomenclatura = nomenclatura
    
    async def ingresar_nomenclatura(self, nomenclatura: Optional[str] = None):
        """
        Ingresa la nomenclatura en el campo de búsqueda.
        
        Args:
            nomenclatura: Nomenclatura a buscar (opcional, usa la del constructor si no se proporciona)
        
        Raises:
            ElementNotFoundError: Si no se encuentra el campo de entrada
            ValueError: Si no se proporciona nomenclatura
        """
        self._ensure_started()
        
        nomenclatura = nomenclatura or self.nomenclatura
        if not nomenclatura:
            raise ValueError("Debe proporcionar una nomenclatura")
        
        try:
            self.logger.info(f"Ingresando nomenclatura: {nomenclatura}")
            input_nomenclatura = await self._locator(SELECTORS['nomenclatura_input'])
            
            if not await input_nomenclatura.is_visible(timeout=10000):
                raise ElementNotFoundError("No se encontró el campo de nomenclatura")
            
            await input_nomenclatura.fill(nomenclatura)
            await asyncio.sleep(0.5)  # Pequeño delay para asegurar que se ingresó
            self.logger.info(f"Nomenclatura {nomenclatura} ingresada correctamente")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al ingresar nomenclatura: {e}")
            raise ScrapingError(f"Error al ingresar nomenclatura: {e}") from e
    
    async def click_boton_de_buscar(self):
        """
        Hace click en el botón de buscar y espera inteligentemente a que los resultados se carguen.
        Usa la estrategia de espera configurada (producción o desarrollo).
        
        El flujo es:
        1. Preparar la espera de la petición AJAX ANTES del click
        2. Hacer click en buscar
        3. Esperar a que se complete la petición AJAX específica
        4. Esperar a que termine de renderizar la UI
        5. Validar que hay resultados
        
        Raises:
            ElementNotFoundError: Si no se encuentra el botón
            ScrapingError: Si hay un error esperando los resultados
        """
        self._ensure_started()
        
        try:
            self.logger.info("Buscando botón de buscar...")
            button = self.page.locator(SELECTORS['search_button'])
            
            if not await button.is_visible(timeout=10000):
                raise ElementNotFoundError("No se encontró el botón de buscar")
            
            # Preparar la espera ANTES del click y hacer click dentro del context manager
            # La estrategia configurará expect_response antes del click
            self.logger.info("Preparando espera de resultados...")
            
            # Hacer click y esperar respuesta AJAX usando expect_response
            await self.wait_strategy.click_and_wait_for_response(
                self.page,
                button,
                WAIT_SELECTORS,
                timeout=self.config.timeouts['network']
            )
            
            self.logger.info("Botón de buscar clickeado, esperando resultados...")
            
            # Esperar a que termine de renderizar y validar resultados
            await self.wait_strategy.wait_for_search_results(
                self.page,
                WAIT_SELECTORS,
                timeout=self.config.timeouts['network']
            )
            
            self.logger.info("Resultados cargados correctamente")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al hacer click en buscar: {e}")
            raise ScrapingError(f"Error al hacer click en buscar: {e}") from e
    
    async def clickear_ficha_seleccion(self):
        """
        Hace click en la ficha de selección del primer resultado.
        
        Raises:
            ElementNotFoundError: Si no se encuentra la ficha de selección
        """
        self._ensure_started()
        
        try:
            self.logger.info("Buscando ficha de selección...")
            ficha_seleccion = self.page.locator(SELECTORS['ficha_seleccion'])
            
            timeout = self.config.timeouts['element_wait']
            if not await ficha_seleccion.is_visible(timeout=timeout):
                raise ElementNotFoundError("No se encontró la ficha de selección")
            
            await ficha_seleccion.click()
            self.logger.info("Ficha de selección clickeada, esperando carga...")
            
            # Esperar a que cargue la página (puede demorar mucho)
            await asyncio.sleep(2)  # Delay inicial
            await self.page.wait_for_load_state("networkidle")
            
            self.logger.info("Ficha de selección cargada correctamente")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al clickear ficha de selección: {e}")
            raise ScrapingError(f"Error al clickear ficha de selección: {e}") from e
    
    async def obtener_cronograma(self) -> List[Dict[str, str]]:
        """
        Obtiene el cronograma de la ficha de selección.
        
        Returns:
            Lista de diccionarios con los datos del cronograma (etapa, fecha_inicio, fecha_fin)
        
        Raises:
            ElementNotFoundError: Si no se encuentra la tabla de cronograma
            ScrapingError: Si hay un error al extraer los datos
        """
        self._ensure_started()
        
        try:
            self.logger.info("Extrayendo cronograma...")
            tabla_cronograma = self.page.locator(SELECTORS['cronograma_table'])
            
            if not await tabla_cronograma.is_visible(timeout=10000):
                raise ElementNotFoundError("No se encontró la tabla de cronograma")
            
            # Guardar HTML de debug si está habilitado
            if self.debug:
                html = await tabla_cronograma.evaluate("element => element.outerHTML")
                debug_path = Path(self.config.DEBUG_DIR) / "cronograma_table.html"
                debug_path.write_text(html, encoding="utf-8")
                self.logger.debug(f"HTML guardado en {debug_path}")
            
            # Extraer datos de las filas
            filas = await tabla_cronograma.locator(SELECTORS['cronograma_rows']).all()
            datos_cronograma = []
            
            self.logger.debug(f"Encontradas {len(filas)} filas en el cronograma")
            
            for indice, fila in enumerate(filas):
                try:
                    celdas = await fila.locator(SELECTORS['cronograma_cells']).all()
                    
                    if len(celdas) < MIN_CRONOGRAMA_CELLS:
                        self.logger.warning(f"Fila {indice + 1} del cronograma no tiene suficientes celdas, saltando...")
                        continue
                    
                    etapa = (await celdas[CRONOGRAMA_COLUMNS['etapa']].inner_text()).strip()
                    # Limpiar el texto de etapa (remover <br> y espacios extra)
                    etapa = ' '.join(etapa.split())
                    
                    fecha_inicio = (await celdas[CRONOGRAMA_COLUMNS['fecha_inicio']].inner_text()).strip()
                    fecha_fin = (await celdas[CRONOGRAMA_COLUMNS['fecha_fin']].inner_text()).strip()
                    # Limpiar fecha_fin (puede tener elementos adicionales)
                    fecha_fin = fecha_fin.split('\n')[0].strip() if '\n' in fecha_fin else fecha_fin
                    
                    datos_cronograma.append({
                        "etapa": etapa,
                        "fecha_inicio": fecha_inicio,
                        "fecha_fin": fecha_fin
                    })
                    
                except Exception as e:
                    self.logger.warning(f"Error procesando fila {indice + 1} del cronograma: {e}")
                    continue
            
            self.logger.info(f"✓ Cronograma extraído: {len(datos_cronograma)} registros")
            return datos_cronograma
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al obtener cronograma: {e}")
            raise ScrapingError(f"Error al obtener cronograma: {e}") from e
    
    async def scrapear_documentos_con_links(self) -> Dict[str, any]:
        """
        Scrapea la tabla de documentos y obtiene los links reales de descarga.
        Usa el método mejorado del experimental con expect_download().
        
        Returns:
            Diccionario con total_documentos y lista de documentos con sus links
        
        Raises:
            ElementNotFoundError: Si no se encuentra la tabla de documentos
            ScrapingError: Si hay un error al extraer los datos
        """
        self._ensure_started()
        
        try:
            self.logger.info("Extrayendo documentos con links...")
            tabla_documentos = self.page.locator(SELECTORS['documentos_table'])
            
            timeout = self.config.timeouts['element_wait']
            if not await tabla_documentos.is_visible(timeout=timeout):
                raise ElementNotFoundError("No se encontró la tabla de documentos")
            
            await asyncio.sleep(1)  # Pequeño delay para asegurar renderizado completo
            
            # Guardar HTML de debug si está habilitado
            if self.debug:
                html = await tabla_documentos.evaluate("element => element.outerHTML")
                debug_path = Path(self.config.DEBUG_DIR) / "documentos_table.html"
                debug_path.write_text(html, encoding="utf-8")
                self.logger.debug(f"HTML guardado en {debug_path}")
            
            # Obtener todas las filas de la tabla
            filas = await tabla_documentos.locator(SELECTORS['documentos_rows']).all()
            documentos = []
            
            self.logger.info(f"Encontradas {len(filas)} filas en la tabla de documentos")
            
            for indice, fila in enumerate(filas):
                try:
                    # Extraer datos de las celdas
                    celdas = await fila.locator(SELECTORS['documentos_cells']).all()
                    
                    if len(celdas) < MIN_DOCUMENTOS_CELLS:
                        self.logger.warning(f"Fila {indice + 1}: No tiene suficientes celdas, saltando...")
                        continue
                    
                    # Nro.
                    numero = (await celdas[DOCUMENTOS_COLUMNS['numero']].inner_text()).strip()
                    
                    # Etapa
                    etapa = (await celdas[DOCUMENTOS_COLUMNS['etapa']].inner_text()).strip()
                    
                    # Documento
                    documento = (await celdas[DOCUMENTOS_COLUMNS['documento']].inner_text()).strip()
                    
                    # Archivo - aquí está el enlace de descarga
                    celda_archivo = celdas[DOCUMENTOS_COLUMNS['archivo']]
                    
                    # Extraer el tamaño del archivo del span dentro del enlace
                    tamaño = ""
                    try:
                        span_tamaño = celda_archivo.locator(SELECTORS['documentos_size_span']).first
                        if await span_tamaño.count() > 0:
                            tamaño = (await span_tamaño.inner_text()).strip()
                    except Exception:
                        pass
                    
                    # Extraer el nombre del archivo del atributo onclick
                    nombre_archivo = ""
                    try:
                        enlace_descarga = celda_archivo.locator(SELECTORS['documentos_download_link']).first
                        if await enlace_descarga.count() > 0:
                            onclick_attr = await enlace_descarga.get_attribute("onclick") or ""
                            
                            # Extraer el nombre del archivo del onclick
                            # Formato: javascript:descargaDocGeneral('uuid','tipo','nombre_archivo.ext');
                            if "descargaDocGeneral" in onclick_attr:
                                matches = re.findall(
                                    r"descargaDocGeneral\('([^']+)','([^']+)','([^']+)'\)",
                                    onclick_attr
                                )
                                if matches:
                                    uuid_doc, tipo_doc, nombre_archivo = matches[0]
                    except Exception as e:
                        self.logger.debug(f"Error extrayendo nombre de archivo de la fila {indice + 1}: {e}")
                    
                    # Fecha y Hora de publicación
                    fecha_publicacion = ""
                    if len(celdas) > DOCUMENTOS_COLUMNS['fecha_publicacion']:
                        fecha_publicacion = (await celdas[DOCUMENTOS_COLUMNS['fecha_publicacion']].inner_text()).strip()
                    
                    # Obtener el link real de descarga usando expect_download() (método mejorado)
                    link_descarga = None
                    try:
                        enlace_descarga = celda_archivo.locator(SELECTORS['documentos_download_link']).first
                        if await enlace_descarga.count() > 0:
                            # Método mejorado: interceptar la descarga antes de hacer click
                            download_timeout = self.config.timeouts['network']
                            async with self.page.expect_download(timeout=download_timeout) as download_info:
                                await enlace_descarga.click()
                            
                            download = await download_info.value
                            link_descarga = download.url
                            # Cancelar la descarga real, solo queremos la URL
                            await download.cancel()
                            
                            self.logger.debug(f"✓ Fila {indice + 1}: Link obtenido - {nombre_archivo}")
                            
                    except Exception as e:
                        self.logger.debug(f"Error obteniendo link de la fila {indice + 1}: {e}")
                        # Si falla, continuar sin link (no crítico)
                    
                    # Construir el objeto del documento
                    documento_info = {
                        "numero": numero,
                        "etapa": etapa,
                        "documento": documento,
                        "nombre_archivo": nombre_archivo,
                        "tamaño": tamaño,
                        "fecha_publicacion": fecha_publicacion,
                        "link_descarga": link_descarga
                    }
                    
                    documentos.append(documento_info)
                    
                    # Pequeña pausa entre descargas para no sobrecargar el servidor
                    delay = self.config.DELAY_BETWEEN_DOCUMENTS
                    if delay > 0:
                        await asyncio.sleep(delay)
                    
                except Exception as e:
                    self.logger.warning(f"Error procesando fila {indice + 1}: {e}")
                    continue
            
            resultado = {
                "total_documentos": len(documentos),
                "documentos": documentos
            }
            
            documentos_con_link = sum(1 for doc in documentos if doc.get('link_descarga'))
            self.logger.info(f"✓ Documentos scrapeados: {len(documentos)} total, {documentos_con_link} con link")
            
            return resultado
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al scrapear documentos: {e}")
            raise ScrapingError(f"Error al scrapear documentos: {e}") from e
