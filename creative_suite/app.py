from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from creative_suite.config import Config
from creative_suite.db.migrate import migrate

VERSION = "0.1.0"
WEB_ROOT = Path(__file__).parent / "web"


def create_app() -> FastAPI:
    cfg = Config()
    migrate(cfg)
    app = FastAPI(title="Creative Suite v2", version=VERSION)
    app.state.cfg = cfg

    from creative_suite.api import (
        annotations,
        assets,
        capture,
        clips,
        comfy,
        md3,
        ollama,
        packs,
        parts,
        variants,
    )
    app.include_router(annotations.router)
    app.include_router(clips.router)
    app.include_router(parts.router)
    app.include_router(assets.router)
    app.include_router(comfy.router)
    app.include_router(variants.router)
    app.include_router(md3.router)
    app.include_router(packs.router)
    app.include_router(ollama.router)
    app.include_router(capture.router)

    # Spec §11.3 mitigation: check img2img workflow placeholders at boot.
    # This only logs — it never aborts startup, so a ComfyUI update that
    # renames nodes leaves the rest of the app usable.
    from creative_suite.comfy.client import validate_workflow_file
    validate_workflow_file(
        Path(__file__).parent / "comfy" / "workflows" / "img2img_sdxl.json"
    )

    @app.get("/")
    def index() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        return FileResponse(WEB_ROOT / "annotate.html")

    @app.get("/health")
    def health() -> dict[str, object]:  # pyright: ignore[reportUnusedFunction]
        return {"ok": True, "version": VERSION}

    @app.get("/annotate")
    def annotate_page() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        return FileResponse(WEB_ROOT / "annotate.html")

    @app.get("/creative")
    def creative_page() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        # creative.html lands in Step 4 — gracefully degrade until then.
        path = WEB_ROOT / "creative.html"
        if path.exists():
            return FileResponse(path)
        return FileResponse(WEB_ROOT / "annotate.html")

    if WEB_ROOT.exists():
        app.mount("/web", StaticFiles(directory=str(WEB_ROOT)), name="web")
    if cfg.phase1_output_dir.exists():
        app.mount(
            "/media",
            StaticFiles(directory=str(cfg.phase1_output_dir)),
            name="media",
        )
    return app
