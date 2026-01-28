"""
Herramientas de desarrollo: monitoreo de red para Playwright.

Objetivo:
- Usar en desarrollo para entender qué requests/responses se disparan tras acciones (ej. click "Buscar")
- Evitar timeouts fijos, detectando señales reales de carga (XHR/fetch/POSTs JSF)
- Guardar artefactos en JSON para depurar y documentar el comportamiento del sitio

Nota:
- En producción NO es necesario (y no debe ser obligatorio).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence

from ..utils.logging import get_logger

logger = get_logger(__name__)


def _now_iso() -> str:
    return datetime.now().isoformat()


def _safe_mkdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _is_static_asset(url: str) -> bool:
    static_extensions = (
        ".css",
        ".js",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".map",
    )
    lowered = url.lower()
    return any(lowered.endswith(ext) for ext in static_extensions)


@dataclass(frozen=True)
class NetworkSnapshot:
    timestamp: str
    requests: List[Dict[str, Any]]
    responses: List[Dict[str, Any]]


class NetworkMonitor:
    """
    Monitor simple para capturar requests/responses de una Page de Playwright.

    Uso típico (desarrollo):
    - monitor.attach(page)
    - before = monitor.snapshot()
    - ... acción (click) + waits ...
    - after = monitor.snapshot()
    - analysis = monitor.analyze(before, after)
    - monitor.save_json(analysis, "network_click_buscar.json")
    """

    def __init__(self, output_dir: str = "debug", enabled: bool = True):
        self.output_dir = Path(output_dir)
        self.enabled = enabled

        self._attached: bool = False
        self._requests: List[Dict[str, Any]] = []
        self._responses: List[Dict[str, Any]] = []

        self._on_request: Optional[Callable[..., None]] = None
        self._on_response: Optional[Callable[..., None]] = None

    def attach(self, page) -> None:
        """Adjunta listeners a la page. Idempotente."""
        if not self.enabled:
            return
        if self._attached:
            return

        def on_request(request) -> None:
            try:
                self._requests.append(
                    {
                        "url": request.url,
                        "method": request.method,
                        "resource_type": getattr(request, "resource_type", None),
                        "timestamp": _now_iso(),
                    }
                )
            except Exception as e:
                logger.debug(f"Error capturando request: {e}")

        def on_response(response) -> None:
            try:
                req = getattr(response, "request", None)
                self._responses.append(
                    {
                        "url": response.url,
                        "status": response.status,
                        "status_text": getattr(response, "status_text", None),
                        "method": getattr(req, "method", None),
                        "content_type": (response.headers or {}).get("content-type", ""),
                        "timestamp": _now_iso(),
                    }
                )
            except Exception as e:
                logger.debug(f"Error capturando response: {e}")

        page.on("request", on_request)
        page.on("response", on_response)

        self._on_request = on_request
        self._on_response = on_response
        self._attached = True

        logger.info("NetworkMonitor adjuntado (dev)")

    def reset(self) -> None:
        """Limpia el buffer de eventos capturados."""
        self._requests = []
        self._responses = []

    def snapshot(self) -> NetworkSnapshot:
        """Captura un snapshot del estado actual del buffer."""
        return NetworkSnapshot(
            timestamp=_now_iso(),
            requests=list(self._requests),
            responses=list(self._responses),
        )

    def analyze(
        self,
        before: NetworkSnapshot,
        after: NetworkSnapshot,
        *,
        include_static: bool = False,
        ajax_resource_types: Sequence[str] = ("xhr", "fetch"),
    ) -> Dict[str, Any]:
        """
        Analiza qué apareció entre before/after.
        Devuelve un dict listo para serializar.
        """
        before_urls = {r.get("url") for r in before.requests if r.get("url")}

        new_requests = [r for r in after.requests if r.get("url") not in before_urls]
        new_responses = [r for r in after.responses if r.get("url") not in before_urls]

        if not include_static:
            new_requests = [r for r in new_requests if not _is_static_asset(r.get("url", ""))]
            new_responses = [r for r in new_responses if not _is_static_asset(r.get("url", ""))]

        ajax_requests = [
            r
            for r in new_requests
            if (r.get("resource_type") in set(ajax_resource_types))
            or (r.get("method") == "POST")  # útil en JSF (aunque no sea xhr)
        ]

        ajax_urls = {r.get("url") for r in ajax_requests if r.get("url")}
        ajax_responses = [r for r in new_responses if r.get("url") in ajax_urls]

        analysis = {
            "meta": {
                "before_ts": before.timestamp,
                "after_ts": after.timestamp,
                "include_static": include_static,
                "ajax_resource_types": list(ajax_resource_types),
            },
            "counts": {
                "new_requests": len(new_requests),
                "new_responses": len(new_responses),
                "ajax_requests": len(ajax_requests),
                "ajax_responses": len(ajax_responses),
            },
            "new_requests": new_requests,
            "new_responses": new_responses,
            "ajax_requests": ajax_requests,
            "ajax_responses": ajax_responses,
        }
        return analysis

    def save_json(self, data: Dict[str, Any], filename: str) -> Path:
        """Guarda un JSON en output_dir y retorna la ruta."""
        _safe_mkdir(self.output_dir)
        path = self.output_dir / filename
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"NetworkMonitor guardó: {path}")
        return path

