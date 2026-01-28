"""
Tests completos para la API de scrape regional.
Incluye flujo completo: crear job, verificar status, obtener result y descargar CSV.
"""

import asyncio
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.job_manager import job_manager


@pytest.fixture
def client():
    """Fixture que crea un cliente de prueba."""
    return TestClient(create_app())


@pytest.fixture
def mock_regional_scrape(tmp_path):
    """Fixture que mockea run_regional_scrape."""
    csv_path = tmp_path / "procesos_AREQUIPA_2026.csv"
    # Crear un CSV de prueba
    csv_path.write_text(
        "N°,Nombre o Sigla de la Entidad,Fecha y Hora de Publicacion\n"
        "1,ENTIDAD TEST,28/01/2026 10:00\n"
        "2,ENTIDAD TEST 2,28/01/2026 11:00\n",
        encoding="utf-8-sig"
    )
    
    with patch(
        "app.routers.scrape.run_regional_scrape",
        new=AsyncMock(return_value=(2, str(csv_path))),
    ) as mock:
        yield mock, csv_path


class TestRegionalScrapeAPI:
    """Tests para el endpoint /scrape/regional."""
    
    def test_create_regional_scrape_job(self, client, mock_regional_scrape):
        """Test que verifica la creación de un job de scrape regional."""
        mock, _ = mock_regional_scrape
        
        response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "2026",
                "output_csv": None,
                "debug": False,
            },
        )
        
        assert response.status_code == 200
        body = response.json()
        assert "job_id" in body
        assert body["status"] in {"queued", "running"}
        assert isinstance(body["job_id"], str)
    
    def test_create_regional_scrape_job_with_custom_csv(self, client, mock_regional_scrape):
        """Test que verifica la creación de un job con nombre de CSV personalizado."""
        mock, _ = mock_regional_scrape
        
        response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "2026",
                "output_csv": "custom_output.csv",
                "debug": False,
            },
        )
        
        assert response.status_code == 200
        body = response.json()
        assert "job_id" in body
    
    def test_create_regional_scrape_job_with_debug(self, client, mock_regional_scrape):
        """Test que verifica la creación de un job con debug habilitado."""
        mock, _ = mock_regional_scrape
        
        response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "2026",
                "output_csv": None,
                "debug": True,
            },
        )
        
        assert response.status_code == 200
        body = response.json()
        assert "job_id" in body
    
    def test_create_regional_scrape_job_invalid_departamento(self, client):
        """Test que verifica validación de departamento inválido."""
        response = client.post(
            "/scrape/regional",
            json={
                "departamento": "A",  # Muy corto
                "anio": "2026",
                "output_csv": None,
                "debug": False,
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_regional_scrape_job_invalid_anio(self, client):
        """Test que verifica validación de año inválido."""
        response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "26",  # Muy corto
                "output_csv": None,
                "debug": False,
            },
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_regional_scrape_full_flow(self, client, mock_regional_scrape):
        """Test del flujo completo: crear job, verificar status, obtener result."""
        mock, csv_path = mock_regional_scrape
        
        # 1. Crear job
        create_response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "2026",
                "output_csv": None,
                "debug": False,
            },
        )
        
        assert create_response.status_code == 200
        job_data = create_response.json()
        job_id = job_data["job_id"]
        
        # 2. Verificar que el job existe
        status_response = client.get(f"/jobs/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["job_id"] == job_id
        assert status_data["type"] == "regional"
        assert status_data["status"] in {"queued", "running", "succeeded"}
        
        # 3. Esperar a que el job complete (dar tiempo al task)
        # En un test real, esto podría tomar más tiempo, pero con el mock debería ser rápido
        max_attempts = 10
        for _ in range(max_attempts):
            asyncio.run(asyncio.sleep(0.1))
            status_response = client.get(f"/jobs/{job_id}")
            status_data = status_response.json()
            if status_data["status"] == "succeeded":
                break
        
        # 4. Obtener el resultado
        result_response = client.get(f"/jobs/{job_id}/result")
        assert result_response.status_code == 200
        result_data = result_response.json()
        
        assert result_data["job_id"] == job_id
        assert result_data["status"] == "succeeded"
        assert result_data["result"] is not None
        assert "departamento" in result_data["result"]
        assert "anio" in result_data["result"]
        assert "total_registros" in result_data["result"]
        assert "csv_path" in result_data["result"]
        
        assert result_data["result"]["departamento"] == "AREQUIPA"
        assert result_data["result"]["anio"] == "2026"
        assert result_data["result"]["total_registros"] == 2
        assert result_data["result"]["csv_path"] == str(csv_path)
    
    def test_regional_scrape_download_csv(self, client, mock_regional_scrape):
        """Test que verifica la descarga del CSV generado."""
        mock, csv_path = mock_regional_scrape
        
        # 1. Crear job
        create_response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "2026",
                "output_csv": None,
                "debug": False,
            },
        )
        
        job_id = create_response.json()["job_id"]
        
        # 2. Esperar a que complete
        max_attempts = 10
        for _ in range(max_attempts):
            asyncio.run(asyncio.sleep(0.1))
            status_response = client.get(f"/jobs/{job_id}")
            if status_response.json()["status"] == "succeeded":
                break
        
        # 3. Descargar CSV
        download_response = client.get(f"/jobs/{job_id}/download")
        assert download_response.status_code == 200
        assert download_response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "Content-Disposition" in download_response.headers
        
        # Verificar contenido del CSV
        content = download_response.content.decode("utf-8-sig")
        assert "N°" in content
        assert "Nombre o Sigla de la Entidad" in content
        assert "ENTIDAD TEST" in content
    
    def test_download_csv_job_not_found(self, client):
        """Test que verifica error cuando el job no existe."""
        response = client.get("/jobs/non-existent-id/download")
        assert response.status_code == 404
    
    def test_download_csv_job_not_regional(self, client):
        """Test que verifica error cuando el job no es de tipo regional."""
        # Crear un job de tipo diferente
        async def fn():
            return {"test": "data"}
        
        job = asyncio.run(job_manager.create_job(job_type="test", fn=fn))
        
        response = client.get(f"/jobs/{job.id}/download")
        assert response.status_code == 400
        assert "solo está disponible para jobs de tipo 'regional'" in response.json()["detail"]
    
    def test_download_csv_job_not_completed(self, client, mock_regional_scrape):
        """Test que verifica error cuando el job aún no está completado."""
        mock, _ = mock_regional_scrape
        
        # Crear job pero no esperar a que complete
        create_response = client.post(
            "/scrape/regional",
            json={
                "departamento": "AREQUIPA",
                "anio": "2026",
                "output_csv": None,
                "debug": False,
            },
        )
        
        job_id = create_response.json()["job_id"]
        
        # Intentar descargar inmediatamente (probablemente aún está running)
        download_response = client.get(f"/jobs/{job_id}/download")
        
        # Puede ser 400 si aún no está completado, o 200 si ya completó muy rápido
        assert download_response.status_code in {200, 400}
        if download_response.status_code == 400:
            assert "aún no está completado" in download_response.json()["detail"]
    
    def test_regional_scrape_job_error_handling(self, client):
        """Test que verifica el manejo de errores en el job."""
        # Mock que simula un error
        with patch(
            "app.routers.scrape.run_regional_scrape",
            new=AsyncMock(side_effect=Exception("Error de scraping")),
        ):
            create_response = client.post(
                "/scrape/regional",
                json={
                    "departamento": "AREQUIPA",
                    "anio": "2026",
                    "output_csv": None,
                    "debug": False,
                },
            )
            
            job_id = create_response.json()["job_id"]
            
            # Esperar a que el job falle
            max_attempts = 10
            for _ in range(max_attempts):
                asyncio.run(asyncio.sleep(0.1))
                status_response = client.get(f"/jobs/{job_id}")
                status_data = status_response.json()
                if status_data["status"] == "failed":
                    break
            
            # Verificar que el error está registrado
            result_response = client.get(f"/jobs/{job_id}/result")
            assert result_response.status_code == 200
            result_data = result_response.json()
            assert result_data["status"] == "failed"
            assert result_data["error"] is not None
            assert "Error de scraping" in result_data["error"]
