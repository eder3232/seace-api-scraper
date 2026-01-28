from fastapi import APIRouter, HTTPException

from ..models.schemas import JobResultResponse, JobStatusResponse
from ..services.job_manager import job_manager

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str) -> JobStatusResponse:
    rec = await job_manager.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobStatusResponse(
        job_id=rec.id,
        type=rec.type,
        status=rec.status,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        error=rec.error,
    )


@router.get("/{job_id}/result", response_model=JobResultResponse)
async def get_job_result(job_id: str) -> JobResultResponse:
    rec = await job_manager.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResultResponse(job_id=rec.id, status=rec.status, result=rec.result, error=rec.error)


@router.post("/{job_id}/cancel", response_model=JobStatusResponse)
async def cancel_job(job_id: str) -> JobStatusResponse:
    rec = await job_manager.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    await job_manager.cancel(job_id)
    rec = await job_manager.get(job_id)
    return JobStatusResponse(
        job_id=rec.id,
        type=rec.type,
        status=rec.status,
        created_at=rec.created_at,
        updated_at=rec.updated_at,
        error=rec.error,
    )

