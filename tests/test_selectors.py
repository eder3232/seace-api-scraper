"""
Tests para verificar que los selectores están correctamente definidos.
"""

import pytest
from src.selectors import regional, nomenclatura


class TestRegionalSelectors:
    """Tests para selectores regionales."""
    
    def test_selectors_dict_existe(self):
        """Test que verifica que SELECTORS existe."""
        assert hasattr(regional, 'SELECTORS')
        assert isinstance(regional.SELECTORS, dict)
    
    def test_selectors_requeridos(self):
        """Test que verifica que todos los selectores requeridos existen."""
        required_selectors = [
            'search_type',
            'advanced_search_container',
            'department_container',
            'department_panel',
            'department_item',
            'year_container',
            'year_panel',
            'year_item',
            'search_button',
            'results_container',
            'results_table_body',
            'results_table_row',
            'results_table_cell',
            'pagination_container',
            'pagination_next',
        ]
        
        for selector in required_selectors:
            assert selector in regional.SELECTORS, f"Selector '{selector}' no encontrado"
    
    def test_columnas_esperadas(self):
        """Test que verifica que COLUMNAS_ESPERADAS está definido."""
        assert hasattr(regional, 'COLUMNAS_ESPERADAS')
        assert isinstance(regional.COLUMNAS_ESPERADAS, list)
        assert len(regional.COLUMNAS_ESPERADAS) == 10
    
    def test_indices_columnas(self):
        """Test que verifica que INDICES_COLUMNAS está definido."""
        assert hasattr(regional, 'INDICES_COLUMNAS')
        assert isinstance(regional.INDICES_COLUMNAS, list)
        assert len(regional.INDICES_COLUMNAS) == 10
    
    def test_wait_selectors(self):
        """Test que verifica que WAIT_SELECTORS está definido."""
        assert hasattr(regional, 'WAIT_SELECTORS')
        assert isinstance(regional.WAIT_SELECTORS, dict)
        assert 'min_columns' in regional.WAIT_SELECTORS


class TestNomenclaturaSelectors:
    """Tests para selectores de nomenclatura."""
    
    def test_selectors_dict_existe(self):
        """Test que verifica que SELECTORS existe."""
        assert hasattr(nomenclatura, 'SELECTORS')
        assert isinstance(nomenclatura.SELECTORS, dict)
    
    def test_selectors_requeridos(self):
        """Test que verifica que todos los selectores requeridos existen."""
        required_selectors = [
            'search_type',
            'advanced_search_container',
            'nomenclatura_input',
            'search_button',
            'ficha_seleccion',
            'cronograma_table',
            'cronograma_rows',
            'cronograma_cells',
            'documentos_table',
            'documentos_rows',
            'documentos_cells',
            'documentos_download_link',
            'documentos_size_span',
        ]
        
        for selector in required_selectors:
            assert selector in nomenclatura.SELECTORS, f"Selector '{selector}' no encontrado"
    
    def test_cronograma_columns(self):
        """Test que verifica que CRONOGRAMA_COLUMNS está definido."""
        assert hasattr(nomenclatura, 'CRONOGRAMA_COLUMNS')
        assert isinstance(nomenclatura.CRONOGRAMA_COLUMNS, dict)
        assert 'etapa' in nomenclatura.CRONOGRAMA_COLUMNS
        assert 'fecha_inicio' in nomenclatura.CRONOGRAMA_COLUMNS
        assert 'fecha_fin' in nomenclatura.CRONOGRAMA_COLUMNS
    
    def test_documentos_columns(self):
        """Test que verifica que DOCUMENTOS_COLUMNS está definido."""
        assert hasattr(nomenclatura, 'DOCUMENTOS_COLUMNS')
        assert isinstance(nomenclatura.DOCUMENTOS_COLUMNS, dict)
        assert 'numero' in nomenclatura.DOCUMENTOS_COLUMNS
        assert 'etapa' in nomenclatura.DOCUMENTOS_COLUMNS
        assert 'documento' in nomenclatura.DOCUMENTOS_COLUMNS
        assert 'archivo' in nomenclatura.DOCUMENTOS_COLUMNS
    
    def test_min_constants(self):
        """Test que verifica constantes mínimas."""
        assert hasattr(nomenclatura, 'MIN_CRONOGRAMA_CELLS')
        assert hasattr(nomenclatura, 'MIN_DOCUMENTOS_CELLS')
        assert nomenclatura.MIN_CRONOGRAMA_CELLS == 3
        assert nomenclatura.MIN_DOCUMENTOS_CELLS == 5
