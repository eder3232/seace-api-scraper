from playwright.sync_api import sync_playwright
import logging
import json
import re
from typing import Dict, List, Optional

nomenclatura='SIE-SIE-1-2026-SEDAPAR-1'


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

    def ingresar_nomenclatura(self, nomenclatura: str):
        """Ingresa la nomenclatura"""
        input_nomenclatura=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:siglasEntidad")
        input_nomenclatura.fill(nomenclatura)
        self.page.wait_for_timeout(1000)

    def clickear_ficha_seleccion(self):
        """Clickea en la ficha de selección"""
        ficha_seleccion=self.page.locator('a:has(img[src*="fichaSeleccion.gif"])')
        ficha_seleccion.click()
        # se debe esperar que cargue la pagina, porque aca demora mucho
        self.page.wait_for_timeout(3000)

    def obtener_cronograma(self):
        """Obtiene el cronograma y lo guarda en formato JSON"""
        tabla_cronograma = self.page.locator('xpath=//thead[@id="tbFicha:dtCronograma_head"]/parent::table')
        
        # Extraer encabezados
        headers = tabla_cronograma.locator('thead th').all()
        columnas = []
        for header in headers:
            texto = header.inner_text().strip()
            if texto:
                columnas.append(texto)
        
        # Extraer datos de las filas
        filas = tabla_cronograma.locator('tbody tr').all()
        datos_cronograma = []
        
        for fila in filas:
            celdas = fila.locator('td').all()
            if len(celdas) >= 3:
                etapa = celdas[0].inner_text().strip()
                # Limpiar el texto de etapa (remover <br> y espacios extra)
                etapa = ' '.join(etapa.split())
                
                fecha_inicio = celdas[1].inner_text().strip()
                fecha_fin = celdas[2].inner_text().strip()
                # Limpiar fecha_fin (puede tener elementos adicionales)
                fecha_fin = fecha_fin.split('\n')[0].strip() if '\n' in fecha_fin else fecha_fin
                
                datos_cronograma.append({
                    "etapa": etapa,
                    "fecha_inicio": fecha_inicio,
                    "fecha_fin": fecha_fin
                })
        
        # Guardar en JSON
        with open("cronograma.json", "w", encoding="utf-8") as f:
            json.dump(datos_cronograma, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Cronograma guardado en cronograma.json ({len(datos_cronograma)} registros)")
        
        self.page.wait_for_timeout(1000)


    
    def click_boton_de_buscar(self):
        boton_buscar=self.page.locator("#tbBuscador\\:idFormBuscarProceso\\:btnBuscarSelToken")
        if boton_buscar.is_visible():
            boton_buscar.click()
            print("Botón de buscar encontrado y clickado")
        else:
            raise Exception("No se encontró el botón de buscar")
        self.page.wait_for_load_state("networkidle")
        self.page.wait_for_timeout(7000)

    def ver_documentos_por_etapa(self):
        """Ver documentos por etapa"""
        selector = "#tbFicha\\:dtDocumentos"
        contenedor_documentos = self.page.locator(selector)
        
        # Esperar a que el elemento esté visible y estable antes de evaluarlo
        contenedor_documentos.wait_for(state="visible", timeout=10000)
        # Esperar un poco más para asegurar que el contenido esté completamente renderizado
        self.page.wait_for_timeout(1000)
        
        # Obtener el contenido HTML del div y guardarlo en un archivo
        # Usar first() para asegurar que solo se evalúe el primer elemento si hay múltiples
        try:
            html_content = contenedor_documentos.first.evaluate("el => el.outerHTML")
        except Exception as e:
            # Si falla, intentar con page.evaluate() directamente usando getElementById
            print(f"⚠ Error con locator.evaluate(): {e}")
            print("Intentando con page.evaluate() usando getElementById como alternativa...")
            # Usar getElementById que no requiere escape de dos puntos
            element_id = "tbFicha:dtDocumentos"  # ID sin el símbolo #
            html_content = self.page.evaluate(f"""
                () => {{
                    const el = document.getElementById('{element_id}');
                    return el ? el.outerHTML : null;
                }}
            """)
            if not html_content:
                raise Exception(f"No se pudo obtener el HTML del elemento con ID: {element_id}")
        
        with open("documentos_por_etapa.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        print("✓ Contenido del div documentos guardado en documentos_por_etapa.html")

    def scrapear_documentos_con_links(self, nombre_archivo_json: str = "documentos_por_etapa.json"):
        """
        Scrapea la tabla de documentos y obtiene los links reales de descarga.
        Guarda los resultados en un archivo JSON.
        
        Args:
            nombre_archivo_json: Nombre del archivo JSON donde guardar los resultados
        """
        selector_tabla = "#tbFicha\\:dtDocumentos"
        tabla_documentos = self.page.locator(selector_tabla)
        
        # Esperar a que la tabla esté visible
        tabla_documentos.wait_for(state="visible", timeout=10000)
        self.page.wait_for_timeout(1000)
        
        # Obtener todas las filas de la tabla
        filas = tabla_documentos.locator("tbody tr").all()
        documentos = []
        
        print(f"📄 Encontradas {len(filas)} filas en la tabla de documentos")
        
        for indice, fila in enumerate(filas):
            try:
                # Extraer datos de las celdas
                celdas = fila.locator("td").all()
                
                if len(celdas) < 5:
                    print(f"⚠ Fila {indice + 1}: No tiene suficientes celdas, saltando...")
                    continue
                
                # Nro.
                numero = celdas[0].inner_text().strip()
                
                # Etapa
                etapa = celdas[1].inner_text().strip()
                
                # Documento
                documento = celdas[2].inner_text().strip()
                
                # Archivo - aquí está el enlace de descarga
                celda_archivo = celdas[3]
                
                # Extraer el tamaño del archivo del span dentro del enlace
                try:
                    span_tamaño = celda_archivo.locator("a span").first
                    tamaño = span_tamaño.inner_text().strip() if span_tamaño.count() > 0 else ""
                except:
                    tamaño = ""
                
                # Extraer el nombre del archivo del atributo onclick
                try:
                    enlace_descarga = celda_archivo.locator("a:has(span)").first
                    onclick_attr = enlace_descarga.get_attribute("onclick") or ""
                    
                    # Extraer el nombre del archivo del onclick
                    # Formato: javascript:descargaDocGeneral('uuid','tipo','nombre_archivo.ext');
                    nombre_archivo = ""
                    if "descargaDocGeneral" in onclick_attr:
                        # Buscar el tercer parámetro entre comillas simples
                        matches = re.findall(r"descargaDocGeneral\('([^']+)','([^']+)','([^']+)'\)", onclick_attr)
                        if matches:
                            uuid_doc, tipo_doc, nombre_archivo = matches[0]
                except Exception as e:
                    print(f"⚠ Error extrayendo nombre de archivo de la fila {indice + 1}: {e}")
                    nombre_archivo = ""
                
                # Fecha y Hora de publicación
                fecha_publicacion = celdas[4].inner_text().strip() if len(celdas) > 4 else ""
                
                # Obtener el link real de descarga haciendo click
                link_descarga = None
                
                # Localizar el enlace de descarga (el que contiene el span con el tamaño)
                enlace_descarga = celda_archivo.locator("a:has(span)").first
                
                if enlace_descarga.count() > 0:
                    try:
                        # Método 1: Interceptar la descarga antes de hacer click
                        with self.page.expect_download(timeout=30000) as download_info:
                            enlace_descarga.click()
                        
                        download = download_info.value
                        link_descarga = download.url
                        # Cancelar la descarga real, solo queremos la URL
                        download.cancel()
                        
                        print(f"✓ Fila {indice + 1}: Link obtenido - {nombre_archivo}")
                        
                    except Exception as e:
                        print(f"⚠ Error obteniendo link de la fila {indice + 1} (método 1): {e}")
                        # Método alternativo: interceptar respuesta de red
                        try:
                            response_url = None
                            
                            def handle_response(response):
                                nonlocal response_url
                                content_type = response.headers.get("content-type", "")
                                # Buscar respuestas que sean descargas (archivos binarios)
                                if any(x in content_type.lower() for x in ["application", "octet-stream", "zip", "rar", "pdf"]):
                                    response_url = response.url
                            
                            self.page.on("response", handle_response)
                            enlace_descarga.click()
                            self.page.wait_for_timeout(3000)  # Esperar a que se complete la petición
                            self.page.remove_listener("response", handle_response)
                            
                            if response_url:
                                link_descarga = response_url
                                print(f"✓ Fila {indice + 1}: Link obtenido por interceptación - {nombre_archivo}")
                            else:
                                print(f"⚠ Fila {indice + 1}: No se pudo obtener el link por ningún método")
                        except Exception as e2:
                            print(f"⚠ Error en método alternativo para fila {indice + 1}: {e2}")
                else:
                    print(f"⚠ Fila {indice + 1}: No se encontró enlace de descarga")
                
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
                self.page.wait_for_timeout(500)
                
            except Exception as e:
                print(f"❌ Error procesando fila {indice + 1}: {e}")
                continue
        
        # Guardar en JSON
        resultado = {
            "total_documentos": len(documentos),
            "documentos": documentos
        }
        
        with open(nombre_archivo_json, "w", encoding="utf-8") as f:
            json.dump(resultado, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*60}")
        print(f"✓ Documentos scrapeados y guardados en {nombre_archivo_json}")
        print(f"✓ Total de documentos procesados: {len(documentos)}")
        print(f"✓ Documentos con link: {sum(1 for doc in documentos if doc['link_descarga'])}")
        print(f"{'='*60}\n")
        
        return resultado

        

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
    scraper.ingresar_nomenclatura(nomenclatura)




    # scraper.desplegar_boton_para_seleccionar_anio_de_convocatoria()
    # scraper.seleccionar_anio_de_convocatoria("2026")

    # scraper.desplegar_boton_para_seleccionar_departamento()
    # scraper.seleccionar_departamento(region_a_scraper)

    scraper.click_boton_de_buscar()
    scraper.clickear_ficha_seleccion()

    # scraper.obtener_cronograma()

    # scraper.ver_documentos_por_etapa()  # Método para guardar HTML
    scraper.scrapear_documentos_con_links()  # Método para scrapear tabla y obtener links

    # scraper.obtener_tabla_de_procesos()
    # scraper.clickear_en_siguiente_pagina()
    # scraper.obtener_todas_las_paginas_de_procesos()
    # ... más operaciones ...
finally:
    scraper.close()