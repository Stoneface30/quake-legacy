from __future__ import annotations

from fastapi import FastAPI

from creative_suite.config import Config
from creative_suite.db.migrate import migrate

VERSION = "0.1.0"


def create_app() -> FastAPI:
    cfg = Config()
    migrate(cfg)
    app = FastAPI(title="Creative Suite v2", version=VERSION)
    app.state.cfg = cfg

    @app.get("/health")
    def health() -> dict[str, object]:
        return {"ok": True, "version": VERSION}

    return app
