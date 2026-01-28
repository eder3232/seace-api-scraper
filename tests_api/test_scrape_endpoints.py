from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import create_app


def test_scrape_regional_mocked():
    client = TestClient(create_app())

    with patch(
        "app.routers.scrape.run_regional_scrape",
        new=AsyncMock(return_value=(10, "data/procesos_AREQUIPA_2025.csv")),
    ):
        res = client.post(
            "/scrape/regional",
            json={"departamento": "AREQUIPA", "anio": "2025", "output_csv": None, "debug": False},
        )

    assert res.status_code == 200
    body = res.json()
    assert "job_id" in body
    assert body["status"] in {"queued", "running"}


def test_scrape_nomenclatura_mocked():
    client = TestClient(create_app())

    mocked_result = {
        "cronograma": [{"etapa": "X", "fecha_inicio": "01/01/2026", "fecha_fin": "02/01/2026"}],
        "documentos": {"total_documentos": 0, "documentos": []},
    }

    with patch("app.routers.scrape.run_nomenclatura_scrape", new=AsyncMock(return_value=mocked_result)):
        res = client.post(
            "/scrape/nomenclatura",
            json={"nomenclatura": "SIE-SIE-1-2026-SEDAPAR-1", "debug": False},
        )

    assert res.status_code == 200
    body = res.json()
    assert "job_id" in body
    assert body["status"] in {"queued", "running"}

