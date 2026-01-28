"""
Schemas (Pydantic) para requests/responses de la API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(default="ok")


class JobCreateResponse(BaseModel):
    job_id: str
    status: str


class JobStatusResponse(BaseModel):
    job_id: str
    type: str
    status: str
    created_at: str
    updated_at: str
    error: Optional[str] = None


class JobResultResponse(BaseModel):
    job_id: str
    status: str
    result: Any = None
    error: Optional[str] = None


class RegionalScrapeRequest(BaseModel):
    departamento: str = Field(..., min_length=2, description="Ej: AREQUIPA")
    anio: str = Field(..., min_length=4, max_length=4, description="Ej: 2025")
    output_csv: Optional[str] = Field(default=None, description="Nombre del CSV (opcional)")
    debug: bool = Field(default=False, description="Habilita modo debug (más artefactos/logs)")


class RegionalScrapeResponse(BaseModel):
    departamento: str
    anio: str
    total_registros: int
    csv_path: Optional[str] = None


class NomenclaturaScrapeRequest(BaseModel):
    nomenclatura: str = Field(..., min_length=3, description="Ej: SIE-SIE-1-2026-SEDAPAR-1")
    debug: bool = Field(default=False)


class NomenclaturaScrapeResponse(BaseModel):
    nomenclatura: str
    cronograma: List[Dict[str, str]]
    documentos: Dict[str, Any]


class ErrorResponse(BaseModel):
    detail: str

