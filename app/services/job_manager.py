"""
JobManager in-memory para ejecutar scrapes en background.

Notas importantes (Railway):
- Esto NO persiste si el contenedor reinicia.
- Sirve para "async execution" evitando timeouts de request.
- Si luego necesitas persistencia/escala, migramos a Redis/DB + queue.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Awaitable, Callable, Dict, Optional
from uuid import uuid4


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


JobFn = Callable[[], Awaitable[Any]]


@dataclass
class JobRecord:
    id: str
    type: str
    status: str  # queued | running | succeeded | failed | cancelled
    created_at: str
    updated_at: str
    result: Any = None
    error: Optional[str] = None
    task: Optional[asyncio.Task] = None
    meta: Dict[str, Any] = field(default_factory=dict)


class JobManager:
    def __init__(self) -> None:
        self._jobs: Dict[str, JobRecord] = {}
        self._lock = asyncio.Lock()

    async def create_job(self, *, job_type: str, fn: JobFn, meta: Optional[Dict[str, Any]] = None) -> JobRecord:
        job_id = str(uuid4())
        now = _now_iso()
        record = JobRecord(
            id=job_id,
            type=job_type,
            status="queued",
            created_at=now,
            updated_at=now,
            meta=meta or {},
        )

        async with self._lock:
            self._jobs[job_id] = record

        async def runner() -> None:
            await self._set_status(job_id, "running")
            try:
                result = await fn()
                await self._set_result(job_id, result=result)
            except asyncio.CancelledError:
                await self._set_status(job_id, "cancelled")
                raise
            except Exception as e:  # pragma: no cover (varía según runtime)
                await self._set_error(job_id, error=str(e))

        task = asyncio.create_task(runner(), name=f"job:{job_type}:{job_id}")
        async with self._lock:
            self._jobs[job_id].task = task

        return record

    async def get(self, job_id: str) -> Optional[JobRecord]:
        async with self._lock:
            return self._jobs.get(job_id)

    async def cancel(self, job_id: str) -> bool:
        async with self._lock:
            rec = self._jobs.get(job_id)
            if not rec or not rec.task:
                return False
            if rec.status in {"succeeded", "failed", "cancelled"}:
                return False
            rec.task.cancel()
            rec.updated_at = _now_iso()
            rec.status = "cancelled"
            return True

    async def _set_status(self, job_id: str, status: str) -> None:
        async with self._lock:
            rec = self._jobs[job_id]
            rec.status = status
            rec.updated_at = _now_iso()

    async def _set_result(self, job_id: str, result: Any) -> None:
        async with self._lock:
            rec = self._jobs[job_id]
            rec.status = "succeeded"
            rec.result = result
            rec.updated_at = _now_iso()

    async def _set_error(self, job_id: str, error: str) -> None:
        async with self._lock:
            rec = self._jobs[job_id]
            rec.status = "failed"
            rec.error = error
            rec.updated_at = _now_iso()


job_manager = JobManager()

