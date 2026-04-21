from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from creative_suite.api.forge import router as forge_router
from creative_suite.config import Config
from creative_suite.db.migrate import migrate

VERSION = "0.1.0"

_FRONTEND_DIR = Path(__file__).parent / "frontend"
_ENGINE_GRAPH_DIR = Path(__file__).parent.parent / "engine" / "graphify-out"


def create_app() -> FastAPI:
    cfg = Config()
    migrate(cfg)
    app = FastAPI(title="Creative Suite v2", version=VERSION)
    app.state.cfg = cfg

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True, "version": VERSION}

    @app.get("/", response_class=RedirectResponse, status_code=307)
    def root():
        return RedirectResponse(url="/studio", status_code=307)

    @app.get("/studio")
    def studio():
        return FileResponse(_FRONTEND_DIR / "studio.html")

    app.include_router(forge_router)

    if _ENGINE_GRAPH_DIR.exists():
        app.mount(
            "/engine-graph",
            StaticFiles(directory=str(_ENGINE_GRAPH_DIR), html=True),
            name="engine-graph",
        )

    app.mount(
        "/static",
        StaticFiles(directory=str(_FRONTEND_DIR)),
        name="static",
    )

    return app
