"""
Selectores centralizados para el scraper por nomenclatura de SEACE.
Facilita el mantenimiento cuando cambie la estructura del sitio.
"""

# Selectores principales
SELECTORS = {
    # Buscador principal
    'search_type': '#tbBuscador',
    'search_type_text': 'Buscador de Procedimientos de Selección',
    
    # Búsqueda avanzada
    'advanced_search_container': '#tbBuscador\\:idFormBuscarProceso\\:pnlBuscarProceso',
    'advanced_search_button_text': 'Búsqueda Avanzada',
    
    # Input de nomenclatura
    'nomenclatura_input': '#tbBuscador\\:idFormBuscarProceso\\:siglasEntidad',
    
    # Botón de buscar
    'search_button': '#tbBuscador\\:idFormBuscarProceso\\:btnBuscarSelToken',
    
    # Ficha de selección
    'ficha_seleccion': 'a:has(img[src*="fichaSeleccion.gif"])',
    
    # Cronograma
    'cronograma_table': 'xpath=//thead[@id="tbFicha:dtCronograma_head"]/parent::table',
    'cronograma_thead': 'thead',
    'cronograma_headers': 'thead th',
    'cronograma_tbody': 'tbody',
    'cronograma_rows': 'tbody tr',
    'cronograma_cells': 'td',
    
    # Documentos
    'documentos_table': '#tbFicha\\:dtDocumentos',
    'documentos_tbody': 'tbody',
    'documentos_rows': 'tbody tr',
    'documentos_cells': 'td',
    'documentos_download_link': 'a:has(span)',
    'documentos_size_span': 'a span',
}

# Índices de columnas en la tabla de cronograma
CRONOGRAMA_COLUMNS = {
    'etapa': 0,
    'fecha_inicio': 1,
    'fecha_fin': 2,
}

# Índices de columnas en la tabla de documentos
DOCUMENTOS_COLUMNS = {
    'numero': 0,
    'etapa': 1,
    'documento': 2,
    'archivo': 3,
    'fecha_publicacion': 4,
}

# Número mínimo esperado de celdas en cronograma
MIN_CRONOGRAMA_CELLS = 3

# Número mínimo esperado de celdas en documentos
MIN_DOCUMENTOS_CELLS = 5

# Selectores para estrategia de espera (después de buscar)
WAIT_SELECTORS = {
    'results_container': '#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos',
    'results_table_row': '#tbBuscador\\:idFormBuscarProceso\\:dtProcesos_data tbody tr',
    'results_table_cell': 'td',
    'min_columns': 12,  # Para validar tabla de resultados de búsqueda
}
