from fastapi import APIRouter

from ..models.schemas import (
    JobCreateResponse,
    NomenclaturaScrapeRequest,
    RegionalScrapeRequest,
)
from ..services.job_manager import job_manager
from ..services.scraper_service import run_nomenclatura_scrape, run_regional_scrape

router = APIRouter(prefix="/scrape", tags=["scrape"])


@router.post("/regional", response_model=JobCreateResponse)
async def scrape_regional(payload: RegionalScrapeRequest) -> JobCreateResponse:
    async def fn():
        total, csv_path = await run_regional_scrape(
            departamento=payload.departamento,
            anio=payload.anio,
            output_csv=payload.output_csv,
            debug=payload.debug,
        )
        return {
            "departamento": payload.departamento,
            "anio": payload.anio,
            "total_registros": total,
            "csv_path": csv_path,
        }

    job = await job_manager.create_job(
        job_type="regional",
        fn=fn,
        meta={"departamento": payload.departamento, "anio": payload.anio},
    )
    return JobCreateResponse(job_id=job.id, status=job.status)


@router.post("/nomenclatura", response_model=JobCreateResponse)
async def scrape_nomenclatura(payload: NomenclaturaScrapeRequest) -> JobCreateResponse:
    async def fn():
        result = await run_nomenclatura_scrape(nomenclatura=payload.nomenclatura, debug=payload.debug)
        return {
            "nomenclatura": payload.nomenclatura,
            "cronograma": result["cronograma"],
            "documentos": result["documentos"],
        }

    job = await job_manager.create_job(
        job_type="nomenclatura",
        fn=fn,
        meta={"nomenclatura": payload.nomenclatura},
    )
    return JobCreateResponse(job_id=job.id, status=job.status)

