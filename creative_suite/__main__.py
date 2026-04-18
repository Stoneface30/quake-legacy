from __future__ import annotations

import uvicorn

from creative_suite.app import create_app
from creative_suite.config import Config


def main() -> None:
    cfg = Config()
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=cfg.port, log_level="info")


if __name__ == "__main__":
    main()
