import pandas as pd
from playwright.sync_api import sync_playwright
import logging
from typing import Dict, List, Optional

region_a_scraper='AREQUIPA'


class SeaceScraper:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
    
    def start(self):
        """Inicia el navegador y abre la página de SEACE"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context()
        self.page = self.context.new_page()

    def navigate_to_seace(self):
        """Navega a la página de SEACE"""
        self.page.goto("https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def select_search_type(self, search_type: str):
        """Selecciona el tipo de búsqueda"""
        self.page.locator('#tbBuscador').get_by_text("Buscador de Procedimientos de Selección").click()
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(2000)

    def click_busqueda_avanzada(self):
        """Click en el botón de buscar entidad"""
        table=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:pnlBuscarProceso")
        boton_busqueda_avanzada=table.get_by_text("Búsqueda Avanzada")

        if boton_busqueda_avanzada.is_visible():
            boton_busqueda_avanzada.click()
            print("Botón de busqueda avanzada encontrado y clickado")
        else:
            raise Exception("No se encontró el botón de busqueda avanzada")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(1000)

    def desplegar_boton_para_seleccionar_departamento(self,):
        """Selecciona el departamento"""
        padre=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:departamento")
        button_desplegable=padre.locator("> :last-child")
        if button_desplegable.is_visible():
            button_desplegable.click()
            print('Botón de departamento encontrado y clickado')
        else:
            raise Exception("No se encontró el botón de departamento")
        self.page.wait_for_timeout(1000)

    def seleccionar_departamento(self, departamento: str):
        """Selecciona el departamento"""
        padre=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:departamento_panel")
        
        html_to_save=padre.evaluate("element => element.outerHTML")
        with open("departamento_panel.html", "w", encoding="utf-8") as f:
            f.write(html_to_save)
        
        # Seleccionar el li específico usando el atributo data-label para mayor precisión
        region = padre.locator(f"li[data-label='{departamento}']")
        region.click()
        self.page.wait_for_timeout(1000)

    def desplegar_boton_para_seleccionar_anio_de_convocatoria(self):
        """Despliega el botón para seleccionar el año de convocatoria"""
        padre=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria")
        button_desplegable=padre.locator("> :last-child")
        if button_desplegable.is_visible():
            button_desplegable.click()
            print("Botón de anio de convocatoria encontrado y clickado")
        else:
            raise Exception("No se encontró el botón de anio de convocatoria")
        self.page.wait_for_timeout(1000)

    def seleccionar_anio_de_convocatoria(self, anio: str):
        """Selecciona el año de convocatoria"""
        padre=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria_panel")

        html_to_save=padre.evaluate("element => element.outerHTML")
        with open("anio_de_convocatoria.html", "w", encoding="utf-8") as f:
            f.write(html_to_save)
        # Seleccionar el li específico usando el atributo data-label para mayor precisión
        anio_elemento = padre.locator(f"li[data-label='{anio}']")
        anio_elemento.click()
        self.page.wait_for_timeout(1000)
    
    def click_boton_de_buscar(self):
        boton_buscar=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:btnBuscarSelToken")
        if boton_buscar.is_visible():
            boton_buscar.click()
            print("Botón de buscar encontrado y clickado")
        else:
            raise Exception("No se encontró el botón de buscar")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(5000)

    def _extraer_datos_pagina_actual(self) -> List[List[str]]:
        """
        Extrae los datos de la página actual sin guardar.
        Retorna una lista de listas con los datos de cada fila.
        """
        contenedor_resultados = self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos")
        tbody = contenedor_resultados.locator("#tbBuscador\\:idFormBuscarProceso\\:dtProcesos_data")
        
        # Obtener todas las filas del tbody
        filas = tbody.locator("tr").all()
        
        # Columnas a extraer (excluyendo índices 7, 8 y 12: Código SNIP, Código Único de Inversión, Acciones)
        # Índices: 0=N°, 1=Entidad, 2=Fecha, 3=Nomenclatura, 4=Reiniciado, 5=Objeto, 6=Descripción, 
        #          7=SNIP (excluir), 8=CUI (excluir), 9=Cuantía, 10=Moneda, 11=Versión, 12=Acciones (excluir)
        indices_a_extraer = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11]
        
        datos = []
        
        for fila in filas:
            celdas = fila.locator("td").all()
            fila_datos = []
            
            for indice in indices_a_extraer:
                if indice < len(celdas):
                    # Extraer el texto de la celda, limpiando espacios en blanco
                    texto = celdas[indice].inner_text().strip()
                    fila_datos.append(texto)
                else:
                    fila_datos.append("")
            
            datos.append(fila_datos)
        
        return datos

    def obtener_tabla_de_procesos(self, nombre_archivo_csv: str = "procesos_seace.csv"):
        """
        Extrae los datos de la tabla de procesos y los guarda en un CSV.
        Excluye: Código SNIP, Código Único de Inversión y Acciones.
        """
        nombres_columnas = [
            "N°",
            "Nombre o Sigla de la Entidad",
            "Fecha y Hora de Publicacion",
            "Nomenclatura",
            "Reiniciado Desde",
            "Objeto de Contratación",
            "Descripción de Objeto",
            "VR / VE / Cuantía de la contratación",
            "Moneda",
            "Versión SEACE"
        ]
        
        datos = self._extraer_datos_pagina_actual()
        
        print(f"Extrayendo datos de {len(datos)} filas...")
        
        # Crear DataFrame y guardar en CSV
        df = pd.DataFrame(datos, columns=nombres_columnas)
        df.to_csv(nombre_archivo_csv, index=False, encoding="utf-8-sig")
        
        print(f"✓ Datos guardados en {nombre_archivo_csv}")
        print(f"✓ Total de registros: {len(datos)}")
        
        return df

    def obtener_todas_las_paginas_de_procesos(self, nombre_archivo_csv: str = "procesos_seace.csv"):
        """
        Extrae los datos de todas las páginas de procesos y los guarda en un CSV.
        Itera sobre todas las páginas disponibles hasta que no haya más páginas.
        """
        nombres_columnas = [
            "N°",
            "Nombre o Sigla de la Entidad",
            "Fecha y Hora de Publicacion",
            "Nomenclatura",
            "Reiniciado Desde",
            "Objeto de Contratación",
            "Descripción de Objeto",
            "VR / VE / Cuantía de la contratación",
            "Moneda",
            "Versión SEACE"
        ]
        
        todos_los_datos = []
        numero_pagina = 1
        
        # Scrapear la primera página
        print(f"\n{'='*60}")
        print(f"Scrapeando página {numero_pagina}...")
        print(f"{'='*60}")
        datos_pagina = self._extraer_datos_pagina_actual()
        todos_los_datos.extend(datos_pagina)
        print(f"✓ Página {numero_pagina}: {len(datos_pagina)} registros extraídos")
        
        # Intentar ir a la siguiente página y scrapear
        while True:
            puede_avanzar = self.clickear_en_siguiente_pagina()
            
            if not puede_avanzar:
                print(f"\n{'='*60}")
                print("No hay más páginas. Proceso completado.")
                print(f"{'='*60}")
                break
            
            numero_pagina += 1
            print(f"\n{'='*60}")
            print(f"Scrapeando página {numero_pagina}...")
            print(f"{'='*60}")
            datos_pagina = self._extraer_datos_pagina_actual()
            todos_los_datos.extend(datos_pagina)
            print(f"✓ Página {numero_pagina}: {len(datos_pagina)} registros extraídos")
        
        # Crear DataFrame con todos los datos y guardar en CSV
        df = pd.DataFrame(todos_los_datos, columns=nombres_columnas)
        df.to_csv(nombre_archivo_csv, index=False, encoding="utf-8-sig")
        
        print(f"\n{'='*60}")
        print(f"✓ Todos los datos guardados en {nombre_archivo_csv}")
        print(f"✓ Total de páginas scrapeadas: {numero_pagina}")
        print(f"✓ Total de registros: {len(todos_los_datos)}")
        print(f"{'='*60}\n")
        
        return df


    def clickear_en_siguiente_pagina(self):
        """Clickea en el botón de siguiente página"""
        contenedor_paginador=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:dtProcesos_paginator_bottom")

        # Guardar el elemento contenedor_paginador en un archivo HTML
        html_to_save=contenedor_paginador.evaluate("element => element.outerHTML")
        with open("paginador_seace.html", "w", encoding="utf-8") as f:
            f.write(html_to_save)
        print("✓ Elemento paginador guardado en paginador_seace.html")

        # Localizar el botón de siguiente página (span con clase ui-paginator-next)
        boton_siguiente = contenedor_paginador.locator("span.ui-paginator-next")
        
        # Verificar que el botón existe y no está deshabilitado
        if boton_siguiente.is_visible():
            # Verificar si tiene la clase ui-state-disabled
            tiene_disabled = boton_siguiente.evaluate("element => element.classList.contains('ui-state-disabled')")
            
            if tiene_disabled:
                print("⚠ El botón de siguiente página está deshabilitado (ya estás en la última página)")
                return False
            else:
                boton_siguiente.click()
                print("✓ Click realizado en el botón de siguiente página")
                # Esperar a que la página se cargue después del click
                self.page.wait_for_load_state("networkidle")
                self.page.wait_for_timeout(2000)
                return True
        else:
            raise Exception("No se encontró el botón de siguiente página")

    def close(self):
        self.page.wait_for_timeout(30000)
        """Cierra el navegador"""
        self.page.wait_for_timeout(1000)
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

scraper = SeaceScraper()
try:
    scraper.start()
    scraper.navigate_to_seace()
    scraper.select_search_type("Buscador de Procedimientos de Selección")
    scraper.click_busqueda_avanzada()

    scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
    scraper.seleccionar_anio_de_convocatoria("2026")

    scraper.desplegar_boton_para_seleccionar_departamento()
    scraper.seleccionar_departamento(region_a_scraper)

    scraper.click_boton_de_buscar()
    # scraper.obtener_tabla_de_procesos()
    # scraper.clickear_en_siguiente_pagina()
    scraper.obtener_todas_las_paginas_de_procesos()
    # ... más operaciones ...
finally:
    scraper.close()