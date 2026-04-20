from __future__ import annotations

import argparse
import asyncio
import sys

import uvicorn

from creative_suite._port_check import format_port_busy_message, probe_port
from creative_suite.app import create_app
from creative_suite.config import Config


def _cmd_ingest(args: argparse.Namespace) -> int:
    from creative_suite.db.migrate import migrate
    from creative_suite.inventory.catalog import load_or_build_catalog
    from creative_suite.inventory.ingest import default_pk3_paths, ingest
    from creative_suite.inventory.thumbnails import generate_thumbnails

    cfg = Config()
    cfg.ensure_dirs()
    migrate(cfg)

    catalog_json = cfg.full_catalog_json if cfg.full_catalog_json.exists() else None
    entries = load_or_build_catalog(catalog_json, default_pk3_paths())
    print(f"[ingest] {len(entries)} entries from catalog / pk3s")

    n_new = ingest(cfg, entries)
    print(f"[ingest] {n_new} new rows inserted into assets table")

    if not args.no_thumbnails:
        limit = args.thumbnail_limit
        wrote = generate_thumbnails(cfg, limit=limit)
        print(f"[ingest] {wrote} thumbnails generated"
              f"{f' (limit={limit})' if limit else ''}")

    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    """Boot the FastAPI server with an atomic port probe + graceful-shutdown.

    Hardenings added 2026-04-19:
    - Port-busy detection BEFORE uvicorn.run — converts the generic
      WinError 10048 / EADDRINUSE traceback into a message naming the
      PID holding the port and the exact kill command. Prevents the
      "stale uvicorn from 5 hours ago" footgun.
    - Explicit uvicorn.Server + signal_handlers so Ctrl+C and SIGTERM
      trigger the lifespan shutdown path (which stops the render-worker
      job queue cleanly) instead of abandoning the worker and leaving
      the socket in TIME_WAIT.
    """
    cfg = Config()
    host = "127.0.0.1"
    port = cfg.port

    holder = probe_port(host, port)
    if holder is not None:
        # `holder` is either a positive PID or -1 ("busy, owner unknown").
        # Either way, refuse to start — printing a readable block to stderr
        # so the operator sees it without scrolling past a uvicorn banner.
        print(format_port_busy_message(host, port, holder), file=sys.stderr)
        return 2

    app = create_app()
    config = uvicorn.Config(
        app,
        host=host,
        port=port,
        log_level="info",
        # install_signal_handlers=True is the default, but we're being
        # explicit: Ctrl+C and SIGTERM set server.should_exit, which
        # drains in-flight requests and runs the "shutdown" lifespan
        # event — that's what stops the JobQueue worker (see app.py:31).
        # Without this, a render or preview mid-flight would be killed
        # by Python exiting and wolfcam/ffmpeg could orphan (Rule CS-4).
    )
    server = uvicorn.Server(config)

    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        # Secondary guard — uvicorn's own handler normally catches this
        # first, but if the first Ctrl+C arrives between asyncio.run
        # setup and the signal handler install, this prevents a noisy
        # traceback on what is a perfectly normal shutdown.
        print("\n[creative_suite] interrupted — server stopped.", file=sys.stderr)
        return 130  # conventional exit code for SIGINT

    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="creative_suite")
    # Flag shortcut for the top-level parser — `python -m creative_suite --ingest`
    # bypasses subcommand dispatch and runs the asset ingest pipeline.
    p.add_argument(
        "--ingest",
        action="store_true",
        help="Run asset catalog ingest + thumbnail bulk refresh, then exit",
    )
    p.add_argument(
        "--no-thumbnails", action="store_true",
        help="(with --ingest) skip thumbnail generation",
    )
    p.add_argument(
        "--thumbnail-limit", type=int, default=None,
        help="(with --ingest) cap the number of thumbnails to generate",
    )

    sub = p.add_subparsers(dest="cmd")

    serve = sub.add_parser("serve", help="Run the FastAPI app (default)")
    serve.set_defaults(func=_cmd_serve)

    ingest = sub.add_parser("ingest", help="Build asset catalog from Steam paks")
    ingest.add_argument("--no-thumbnails", action="store_true",
                        help="Skip thumbnail generation")
    ingest.add_argument("--thumbnail-limit", type=int, default=None,
                        help="Cap the number of thumbnails to generate")
    ingest.set_defaults(func=_cmd_ingest)

    args = p.parse_args(argv)
    if getattr(args, "ingest", False) and not hasattr(args, "func"):
        return _cmd_ingest(args)
    if not hasattr(args, "func"):
        return _cmd_serve(args)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
