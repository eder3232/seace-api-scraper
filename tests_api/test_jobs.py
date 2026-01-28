import asyncio

from fastapi.testclient import TestClient

from app.main import create_app
from app.services.job_manager import job_manager


def test_jobs_status_and_result_flow():
    client = TestClient(create_app())

    async def fn():
        await asyncio.sleep(0)
        return {"ok": True}

    # crear job directamente (unit test del flujo HTTP)
    rec = asyncio.run(job_manager.create_job(job_type="test", fn=fn))

    res_status = client.get(f"/jobs/{rec.id}")
    assert res_status.status_code == 200
    assert res_status.json()["job_id"] == rec.id

    # dar chance a que el task corra
    asyncio.run(asyncio.sleep(0))

    res_result = client.get(f"/jobs/{rec.id}/result")
    assert res_result.status_code == 200
    assert res_result.json()["job_id"] == rec.id

