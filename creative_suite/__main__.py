from __future__ import annotations

import argparse
import sys

import uvicorn

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
    cfg = Config()
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=cfg.port, log_level="info")
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
