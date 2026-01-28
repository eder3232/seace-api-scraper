"""
Tests unitarios para las estrategias de espera.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from src.utils.wait_strategies import ProductionWaitStrategy, DevelopmentWaitStrategy
from src.utils.exceptions import TableNotFoundError, InvalidTableStructureError


class TestProductionWaitStrategy:
    """Tests para ProductionWaitStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Fixture que crea una estrategia de producción."""
        return ProductionWaitStrategy()
    
    @pytest.fixture
    def mock_page(self):
        """Fixture que crea un mock de página."""
        page = MagicMock()
        # APIs async de Playwright
        page.wait_for_response = AsyncMock()
        page.wait_for_selector = AsyncMock()
        # locator(...) es sync
        page.locator = MagicMock()
        return page
    
    @pytest.fixture
    def selectors(self):
        """Fixture con selectores de ejemplo."""
        return {
            'results_container': '#results',
            'results_table_row': 'tbody tr',
            'results_table_cell': 'td',
            'min_columns': 12,
        }
    
    @pytest.mark.asyncio
    async def test_wait_for_search_results_exitoso(self, strategy, mock_page, selectors):
        """Test que verifica espera exitosa de resultados."""
        # Mock de respuesta AJAX
        mock_response = MagicMock()
        mock_response.url = "https://prod2.seace.gob.pe/seacebus-uiwd-pub/buscadorPublico/buscadorPublico.xhtml"
        mock_response.request.method = "POST"
        mock_response.status = 200
        
        mock_page.wait_for_response = AsyncMock(return_value=mock_response)
        
        # Mock de tabla: page.locator(table_selector).all() -> [row]
        row_locator = AsyncMock()
        cell_locators = [AsyncMock() for _ in range(12)]
        row_locator.locator.return_value.all = AsyncMock(return_value=cell_locators)

        table_locator = AsyncMock()
        table_locator.all = AsyncMock(return_value=[row_locator])

        # Mock del contenedor: page.locator(results_container).inner_text()
        container_locator = AsyncMock()
        container_locator.inner_text = AsyncMock(return_value="contenido")

        def locator_side_effect(selector: str):
            if selector == selectors["results_table_row"]:
                return table_locator
            if selector == selectors["results_container"]:
                return container_locator
            # fallback
            return AsyncMock()

        mock_page.locator.side_effect = locator_side_effect
        
        # Ejecutar
        await strategy.wait_for_search_results(mock_page, selectors, timeout=5000)
        
        # Verificar que se llamaron los métodos esperados
        mock_page.wait_for_response.assert_called_once()
        mock_page.wait_for_selector.assert_called_once()


class TestDevelopmentWaitStrategy:
    """Tests para DevelopmentWaitStrategy."""
    
    @pytest.fixture
    def strategy(self):
        """Fixture que crea una estrategia de desarrollo."""
        return DevelopmentWaitStrategy(debug_output_dir="test_debug")
    
    def test_init(self, strategy):
        """Test que verifica inicialización."""
        assert strategy.debug_output_dir == "test_debug"
        assert strategy._monitor is not None
        assert strategy._monitoring_enabled == False
    
    def test_capture_snapshot(self, strategy):
        """Test que verifica captura de snapshot."""
        strategy._monitor.reset()
        # Simular eventos ya capturados (evitamos attach real en tests unitarios)
        strategy._monitor._requests = [{"url": "http://test.com", "method": "GET"}]
        strategy._monitor._responses = [{"url": "http://test.com", "status": 200}]

        snapshot = strategy._monitor.snapshot()

        assert len(snapshot.requests) == 1
        assert len(snapshot.responses) == 1
        assert snapshot.timestamp
    
    def test_analyze_changes(self, strategy):
        """Test que verifica análisis de cambios."""
        from src.devtools.network_monitor import NetworkSnapshot

        before = NetworkSnapshot(
            timestamp="t0",
            requests=[{"url": "http://test.com/old"}],
            responses=[{"url": "http://test.com/old"}],
        )

        after = NetworkSnapshot(
            timestamp="t1",
            requests=[
                {"url": "http://test.com/old"},
                {"url": "http://test.com/new", "resource_type": "xhr", "method": "GET"},
            ],
            responses=[
                {"url": "http://test.com/old"},
                {"url": "http://test.com/new", "status": 200},
            ],
        )

        analysis = strategy._monitor.analyze(before, after)

        assert analysis["counts"]["new_requests"] == 1
        assert analysis["counts"]["ajax_requests"] == 1
