"""
Selectores centralizados para el scraper regional de SEACE.
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
    
    # Departamento
    'department_container': '#tbBuscador\\:idFormBuscarProceso\\:departamento',
    'department_panel': '#tbBuscador\\:idFormBuscarProceso\\:departamento_panel',
    'department_item': "li[data-label='{departamento}']",  # Usar .format() o f-string
    
    # Año de convocatoria
    'year_container': '#tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria',
    'year_panel': '#tbBuscador\\:idFormBuscarProceso\\:anioConvocatoria_panel',
    'year_item': "li[data-label='{anio}']",  # Usar .format() o f-string
    
    # Botón de buscar
    'search_button': '#tbBuscador\\:idFormBuscarProceso\\:btnBuscarSelToken',
    
    # Tabla de resultados
    'results_container': '#tbBuscador\\:idFormBuscarProceso\\:pnlGrdResultadosProcesos',
    'results_table_body': '#tbBuscador\\:idFormBuscarProceso\\:dtProcesos_data',
    # IMPORTANTE: `results_table_body` ya es un `<tbody>`, así que aquí deben ser filas directas.
    # Si usamos `tbody tr` desde un `<tbody>`, no encuentra nada y fuerza fallbacks peligrosos
    # que terminan capturando `tr` del layout/paginador (contaminando el CSV).
    'results_table_row': 'tr',
    'results_table_cell': 'td',
    
    # Paginador
    'pagination_container': '#tbBuscador\\:idFormBuscarProceso\\:dtProcesos_paginator_bottom',
    'pagination_next': 'span.ui-paginator-next',
}

# Nombres de columnas esperadas
COLUMNAS_ESPERADAS = [
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

# Índices de columnas a extraer (excluyendo SNIP, CUI y Acciones)
INDICES_COLUMNAS = [0, 1, 2, 3, 4, 5, 6, 9, 10, 11]

# Número mínimo esperado de columnas
MIN_COLUMNAS_ESPERADAS = 10

# Selectores para estrategia de espera
WAIT_SELECTORS = {
    'results_container': SELECTORS['results_container'],
    'results_table_body': SELECTORS['results_table_body'],  # Selector específico del tbody para validación robusta
    'results_table_row': SELECTORS['results_table_row'],
    'results_table_cell': SELECTORS['results_table_cell'],
    'min_columns': 12,  # Número mínimo de columnas esperadas en la tabla
}
