from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

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


@router.get("/{job_id}/download")
async def download_job_csv(job_id: str) -> FileResponse:
    """
    Descarga el archivo CSV generado por un job de tipo 'regional'.
    
    El job debe estar completado (status: 'succeeded') y ser de tipo 'regional'.
    """
    rec = await job_manager.get(job_id)
    if not rec:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if rec.type != "regional":
        raise HTTPException(
            status_code=400,
            detail=f"Este endpoint solo está disponible para jobs de tipo 'regional'. Job tipo: {rec.type}"
        )
    
    if rec.status != "succeeded":
        raise HTTPException(
            status_code=400,
            detail=f"El job aún no está completado. Estado actual: {rec.status}"
        )
    
    if not rec.result or "csv_path" not in rec.result:
        raise HTTPException(
            status_code=404,
            detail="No se encontró el archivo CSV en el resultado del job"
        )
    
    csv_path = Path(rec.result["csv_path"])
    if not csv_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"El archivo CSV no existe en la ruta: {csv_path}"
        )
    
    # Obtener el nombre del archivo para el header Content-Disposition
    filename = csv_path.name
    
    return FileResponse(
        path=str(csv_path),
        filename=filename,
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


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

