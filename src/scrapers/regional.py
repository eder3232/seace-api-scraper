"""
Scraper regional de SEACE - Versión modularizada y optimizada.
Busca procesos por departamento y año, con paginación automática.
"""

import asyncio
from pathlib import Path
from typing import List, Optional
import pandas as pd

from .base import BaseScraper
from ..selectors.regional import SELECTORS, COLUMNAS_ESPERADAS, INDICES_COLUMNAS, WAIT_SELECTORS
from ..utils.exceptions import ScrapingError, ElementNotFoundError
from ..utils.logging import get_logger

logger = get_logger(__name__)


class RegionalScraper(BaseScraper):
    """
    Scraper para buscar procesos de SEACE por departamento y año.
    
    Características:
    - Búsqueda por departamento y año de convocatoria
    - Paginación automática
    - Extracción de datos estructurada
    - Usa estrategias de espera optimizadas (producción o desarrollo)
    """
    
    def __init__(
        self,
        departamento: Optional[str] = None,
        anio: Optional[str] = None,
        **kwargs
    ):
        """
        Inicializa el scraper regional.
        
        Args:
            departamento: Nombre del departamento a buscar (ej: "AREQUIPA")
            anio: Año de convocatoria (ej: "2025")
            **kwargs: Argumentos adicionales para BaseScraper (config, debug, wait_strategy)
        """
        super().__init__(**kwargs)
        self.departamento = departamento
        self.anio = anio
    
    async def desplegar_boton_para_seleccionar_departamento(self):
        """
        Despliega el menú para seleccionar departamento.
        
        Raises:
            ElementNotFoundError: Si no se encuentra el botón
        """
        self._ensure_started()
        
        try:
            self.logger.info("Desplegando menú de departamento...")
            container = await self._locator(SELECTORS['department_container'])
            button = await self._maybe_await(container.locator("> :last-child"))
            
            if not await button.is_visible(timeout=10000):
                raise ElementNotFoundError("No se encontró el botón de departamento")
            
            await button.click()
            await asyncio.sleep(0.5)  # Pequeño delay para que se abra el menú
            self.logger.info("Menú de departamento desplegado")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al desplegar menú de departamento: {e}")
            raise ScrapingError(f"Error al desplegar menú de departamento: {e}") from e
    
    async def seleccionar_departamento(self, departamento: Optional[str] = None):
        """
        Selecciona un departamento del menú desplegable.
        
        Args:
            departamento: Nombre del departamento a seleccionar
        
        Raises:
            ElementNotFoundError: Si no se encuentra el departamento
        """
        self._ensure_started()
        
        departamento = departamento or self.departamento
        if not departamento:
            raise ValueError("Debe proporcionar un departamento")
        
        try:
            self.logger.info(f"Seleccionando departamento: {departamento}")
            panel = self.page.locator(SELECTORS['department_panel'])
            
            # Guardar HTML de debug si está habilitado
            if self.debug:
                html = await panel.evaluate("element => element.outerHTML")
                debug_path = Path(self.config.DEBUG_DIR) / f"departamento_panel_{departamento}.html"
                debug_path.write_text(html, encoding="utf-8")
                self.logger.debug(f"HTML guardado en {debug_path}")
            
            # Seleccionar el departamento usando data-label
            selector = SELECTORS['department_item'].format(departamento=departamento)
            departamento_element = panel.locator(selector)
            
            if not await departamento_element.is_visible(timeout=10000):
                raise ElementNotFoundError(f"No se encontró el departamento: {departamento}")
            
            await departamento_element.click()
            await asyncio.sleep(0.5)  # Pequeño delay para que se cierre el menú
            self.logger.info(f"Departamento {departamento} seleccionado correctamente")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al seleccionar departamento: {e}")
            raise ScrapingError(f"Error al seleccionar departamento: {e}") from e
    
    async def desplegar_boton_para_seleccionar_anio_de_convocatoria(self):
        """
        Despliega el menú para seleccionar año de convocatoria.
        
        Raises:
            ElementNotFoundError: Si no se encuentra el botón
        """
        self._ensure_started()
        
        try:
            self.logger.info("Desplegando menú de año de convocatoria...")
            container = self.page.locator(SELECTORS['year_container'])
            button = container.locator("> :last-child")
            
            if not await button.is_visible(timeout=10000):
                raise ElementNotFoundError("No se encontró el botón de año de convocatoria")
            
            await button.click()
            await asyncio.sleep(0.5)  # Pequeño delay para que se abra el menú
            self.logger.info("Menú de año de convocatoria desplegado")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al desplegar menú de año: {e}")
            raise ScrapingError(f"Error al desplegar menú de año: {e}") from e
    
    async def seleccionar_anio_de_convocatoria(self, anio: Optional[str] = None):
        """
        Selecciona un año de convocatoria del menú desplegable.
        
        Args:
            anio: Año a seleccionar (ej: "2025")
        
        Raises:
            ElementNotFoundError: Si no se encuentra el año
        """
        self._ensure_started()
        
        anio = anio or self.anio
        if not anio:
            raise ValueError("Debe proporcionar un año")
        
        try:
            self.logger.info(f"Seleccionando año de convocatoria: {anio}")
            panel = self.page.locator(SELECTORS['year_panel'])
            
            # Guardar HTML de debug si está habilitado
            if self.debug:
                html = await panel.evaluate("element => element.outerHTML")
                debug_path = Path(self.config.DEBUG_DIR) / f"anio_convocatoria_{anio}.html"
                debug_path.write_text(html, encoding="utf-8")
                self.logger.debug(f"HTML guardado en {debug_path}")
            
            # Seleccionar el año usando data-label
            selector = SELECTORS['year_item'].format(anio=anio)
            anio_element = panel.locator(selector)
            
            if not await anio_element.is_visible(timeout=10000):
                raise ElementNotFoundError(f"No se encontró el año: {anio}")
            
            await anio_element.click()
            await asyncio.sleep(0.5)  # Pequeño delay para que se cierre el menú
            self.logger.info(f"Año {anio} seleccionado correctamente")
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al seleccionar año: {e}")
            raise ScrapingError(f"Error al seleccionar año: {e}") from e
    
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
    
    async def _extraer_datos_pagina_actual(self) -> List[List[str]]:
        """
        Extrae los datos de la página actual.
        
        Returns:
            Lista de listas con los datos de cada fila
        
        Raises:
            ScrapingError: Si hay un error al extraer los datos
        """
        self._ensure_started()
        
        try:
            container = self.page.locator(SELECTORS['results_container'])
            
            # Verificar si el contenedor existe y es visible
            if not await container.is_visible(timeout=5000):
                self.logger.warning("El contenedor de resultados no es visible")
                return []
            
            # Obtener el texto del contenedor para verificar si hay mensaje de "sin resultados"
            container_text = (await container.inner_text()).lower()
            if any(msg in container_text for msg in ["no hay", "sin resultados", "no se encontraron"]):
                self.logger.info("No se encontraron resultados en la búsqueda")
                return []
            
            tbody = container.locator(SELECTORS['results_table_body'])
            filas = await tbody.locator(SELECTORS['results_table_row']).all()
            
            if len(filas) == 0:
                # Intentar buscar filas directamente desde el contenedor
                filas_directas = await container.locator(SELECTORS['results_table_row']).all()
                if len(filas_directas) > 0:
                    filas = filas_directas
                else:
                    self.logger.warning("No se encontraron filas en la tabla")
                    return []
            
            datos = []
            
            for fila in filas:
                celdas = await fila.locator(SELECTORS['results_table_cell']).all()
                
                # Verificar que la fila tenga contenido válido (al menos algunas celdas con texto)
                if len(celdas) == 0:
                    continue
                
                fila_datos = []
                
                for indice in INDICES_COLUMNAS:
                    if indice < len(celdas):
                        texto = (await celdas[indice].inner_text()).strip()
                        fila_datos.append(texto)
                    else:
                        fila_datos.append("")
                
                # Solo agregar si la fila tiene algún contenido válido
                if any(fila_datos):  # Si al menos un campo tiene contenido
                    datos.append(fila_datos)
            
            self.logger.info(f"Extraídos {len(datos)} registros de la página actual")
            return datos
            
        except Exception as e:
            self.logger.error(f"Error al extraer datos: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
            raise ScrapingError(f"Error al extraer datos: {e}") from e
    
    async def obtener_tabla_de_procesos(self, nombre_archivo_csv: Optional[str] = None) -> pd.DataFrame:
        """
        Extrae los datos de la tabla de procesos de la página actual y los guarda en CSV.
        
        Args:
            nombre_archivo_csv: Nombre del archivo CSV (opcional)
        
        Returns:
            DataFrame con los datos extraídos
        """
        self._ensure_started()
        
        nombre_archivo_csv = nombre_archivo_csv or "procesos_seace.csv"
        
        datos = await self._extraer_datos_pagina_actual()
        
        self.logger.info(f"Extrayendo datos de {len(datos)} filas...")
        
        # Crear DataFrame y guardar en CSV
        df = pd.DataFrame(datos, columns=COLUMNAS_ESPERADAS)
        csv_path = Path(self.config.DATA_OUTPUT_DIR) / nombre_archivo_csv
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        self.logger.info(f"✓ Datos guardados en {csv_path}")
        self.logger.info(f"✓ Total de registros: {len(datos)}")
        
        return df
    
    async def clickear_en_siguiente_pagina(self) -> bool:
        """
        Hace click en el botón de siguiente página.
        
        Returns:
            True si se pudo avanzar, False si ya está en la última página
        
        Raises:
            ElementNotFoundError: Si no se encuentra el paginador
        """
        self._ensure_started()
        
        try:
            container = self.page.locator(SELECTORS['pagination_container'])
            
            # Guardar HTML de debug si está habilitado
            if self.debug:
                html = await container.evaluate("element => element.outerHTML")
                debug_path = Path(self.config.DEBUG_DIR) / "paginador_seace.html"
                debug_path.write_text(html, encoding="utf-8")
                self.logger.debug(f"HTML guardado en {debug_path}")
            
            boton_siguiente = container.locator(SELECTORS['pagination_next'])
            
            if not await boton_siguiente.is_visible(timeout=10000):
                raise ElementNotFoundError("No se encontró el botón de siguiente página")
            
            # Verificar si está deshabilitado
            tiene_disabled = await boton_siguiente.evaluate(
                "element => element.classList.contains('ui-state-disabled')"
            )
            
            if tiene_disabled:
                self.logger.info("Ya estás en la última página")
                return False
            
            await boton_siguiente.click()
            self.logger.info("Click realizado en el botón de siguiente página")
            
            # Esperar a que la nueva página cargue usando la estrategia
            await self.wait_strategy.wait_for_search_results(
                self.page,
                WAIT_SELECTORS,
                timeout=self.config.timeouts['network']
            )
            
            return True
            
        except ElementNotFoundError:
            raise
        except Exception as e:
            self.logger.error(f"Error al avanzar a siguiente página: {e}")
            raise ScrapingError(f"Error al avanzar a siguiente página: {e}") from e
    
    async def obtener_todas_las_paginas_de_procesos(
        self,
        nombre_archivo_csv: str = "procesos_seace.csv"
    ) -> pd.DataFrame:
        """
        Extrae los datos de todas las páginas de procesos y los guarda en un CSV.
        
        Args:
            nombre_archivo_csv: Nombre del archivo CSV de salida
        
        Returns:
            DataFrame con todos los datos extraídos
        """
        self._ensure_started()
        
        todos_los_datos = []
        numero_pagina = 1
        
        # Scrapear primera página
        self.logger.info(f"{'='*60}")
        self.logger.info(f"Scrapeando página {numero_pagina}...")
        self.logger.info(f"{'='*60}")
        
        datos_pagina = await self._extraer_datos_pagina_actual()
        todos_los_datos.extend(datos_pagina)
        self.logger.info(f"✓ Página {numero_pagina}: {len(datos_pagina)} registros extraídos")
        
        # Continuar con las siguientes páginas
        while True:
            puede_avanzar = await self.clickear_en_siguiente_pagina()
            
            if not puede_avanzar:
                self.logger.info(f"\n{'='*60}")
                self.logger.info("No hay más páginas. Proceso completado.")
                self.logger.info(f"{'='*60}")
                break
            
            numero_pagina += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"Scrapeando página {numero_pagina}...")
            self.logger.info(f"{'='*60}")
            
            datos_pagina = await self._extraer_datos_pagina_actual()
            todos_los_datos.extend(datos_pagina)
            self.logger.info(f"✓ Página {numero_pagina}: {len(datos_pagina)} registros extraídos")
            
            # Delay entre páginas
            if self.config.DELAY_BETWEEN_PAGES > 0:
                await asyncio.sleep(self.config.DELAY_BETWEEN_PAGES)
        
        # Crear DataFrame con todos los datos y guardar en CSV
        df = pd.DataFrame(todos_los_datos, columns=COLUMNAS_ESPERADAS)
        csv_path = Path(self.config.DATA_OUTPUT_DIR) / nombre_archivo_csv
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        
        self.logger.info(f"\n{'='*60}")
        self.logger.info(f"✓ Todos los datos guardados en {csv_path}")
        self.logger.info(f"✓ Total de páginas scrapeadas: {numero_pagina}")
        self.logger.info(f"✓ Total de registros: {len(todos_los_datos)}")
        self.logger.info(f"{'='*60}\n")
        
        return df
