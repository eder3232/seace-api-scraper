"""
Configuración compartida para tests.
"""

import pytest
from pathlib import Path

# Ruta base del proyecto
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture
def fixtures_dir():
    """Directorio con fixtures (HTMLs de ejemplo)."""
    return PROJECT_ROOT / "tests" / "fixtures"
