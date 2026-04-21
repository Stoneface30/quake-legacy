from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from creative_suite.config import Config
from creative_suite.db.migrate import migrate

VERSION = "0.1.0"
WEB_ROOT = Path(__file__).parent / "web"
FRONTEND_ROOT = Path(__file__).parent / "frontend"

_FRONTEND_DIR = Path(__file__).parent / "frontend"
_ENGINE_GRAPH_DIR = Path(__file__).parent.parent / "engine" / "graphify-out"


def create_app() -> FastAPI:
    cfg = Config()
    migrate(cfg)
    from creative_suite.database.nle_db import init_db as _nle_init
    _nle_init(cfg.nle_db_path)
    app = FastAPI(title="Creative Suite v2", version=VERSION)
    app.state.cfg = cfg

    from creative_suite.api._render_worker import JobQueue

    app.state.job_queue = JobQueue()

    @app.on_event("startup")  # pyright: ignore[reportDeprecated]
    async def _cinema_startup() -> None:  # pyright: ignore[reportUnusedFunction]
        await app.state.job_queue.start()

    @app.on_event("shutdown")  # pyright: ignore[reportDeprecated]
    async def _cinema_shutdown() -> None:  # pyright: ignore[reportUnusedFunction]
        await app.state.job_queue.stop()

    from creative_suite.api import (
        annotations,
        assets,
        capture,
        clips,
        comfy,
        editor,
        forge,
        md3,
        ollama,
        packs,
        parts,
        phase1,
        studio,
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
    app.include_router(phase1.router)
    app.include_router(ollama.router)
    app.include_router(capture.router)
    app.include_router(editor.router)
    app.include_router(studio.router)
    app.include_router(forge.router)

    # Spec §11.3 mitigation: check img2img workflow placeholders at boot.
    # This only logs — it never aborts startup, so a ComfyUI update that
    # renames nodes leaves the rest of the app usable.
    from creative_suite.comfy.client import validate_workflow_file
    validate_workflow_file(
        Path(__file__).parent / "comfy" / "workflows" / "img2img_sdxl.json"
    )

    @app.get("/")
    def index() -> RedirectResponse:  # pyright: ignore[reportUnusedFunction]
        return RedirectResponse(url="/studio", status_code=307)

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

    @app.get("/cinema")
    def cinema_page() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        path = FRONTEND_ROOT / "cinema.html"
        if path.exists():
            return FileResponse(path)
        return FileResponse(WEB_ROOT / "annotate.html")

    @app.get("/editor")
    def editor_page() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        path = FRONTEND_ROOT / "editor.html"
        if path.exists():
            return FileResponse(path)
        return FileResponse(WEB_ROOT / "annotate.html")

    @app.get("/studio")
    def studio_page() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        return FileResponse(FRONTEND_ROOT / "studio.html")

    PHOTOREAL_DIR = Path(__file__).parent / "comfy" / "photoreal"

    @app.get("/gallery")
    def gallery_page() -> FileResponse:  # pyright: ignore[reportUnusedFunction]
        return FileResponse(PHOTOREAL_DIR / "gallery.html")

    if PHOTOREAL_DIR.exists():
        app.mount("/photoreal", StaticFiles(directory=str(PHOTOREAL_DIR)), name="photoreal")

    if WEB_ROOT.exists():
        app.mount("/web", StaticFiles(directory=str(WEB_ROOT)), name="web")
    if cfg.phase1_output_dir.exists():
        app.mount(
            "/media",
            StaticFiles(directory=str(cfg.phase1_output_dir)),
            name="media",
        )
    if FRONTEND_ROOT.exists():
        app.mount("/cinema-static", StaticFiles(directory=str(FRONTEND_ROOT)), name="cinema-static")
        # /static → frontend root (studio.css, studio-store.js, studio-app.js, …)
        app.mount("/static", StaticFiles(directory=str(FRONTEND_ROOT)), name="static")
        # /vendor → frontend/vendor/ (wavesurfer, litegraph, tweakpane, etc.)
        vendor_dir = FRONTEND_ROOT / "vendor"
        if vendor_dir.exists():
            app.mount("/vendor", StaticFiles(directory=str(vendor_dir)), name="vendor")
    if cfg.phase1_output_dir.exists():
        app.mount("/media/phase1", StaticFiles(directory=str(cfg.phase1_output_dir)), name="media-phase1")

    _engine_graph = _ENGINE_GRAPH_DIR
    if _engine_graph.exists():
        app.mount("/engine-graph", StaticFiles(directory=str(_engine_graph), html=True), name="engine-graph")

    return app
