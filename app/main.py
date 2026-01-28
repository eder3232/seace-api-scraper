from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.utils.exceptions import SeaceScraperError

from .routers.health import router as health_router
from .routers.jobs import router as jobs_router
from .routers.scrape import router as scrape_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="SEACE Scraper API",
        version="0.1.0",
        description="API para ejecutar scrapers de SEACE (Playwright) y exponer resultados.",
    )

    @app.exception_handler(SeaceScraperError)
    async def seace_error_handler(_, exc: SeaceScraperError):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    app.include_router(health_router)
    app.include_router(jobs_router)
    app.include_router(scrape_router)
    return app


app = create_app()

