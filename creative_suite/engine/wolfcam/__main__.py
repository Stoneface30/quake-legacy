"""CLI: python -m creative_suite.engine.wolfcam

Prints a JSON inventory of the WolfcamQL install detected on this machine.
"""
from __future__ import annotations

import json

from creative_suite.engine.wolfcam.inventory import scan_wolfcam

if __name__ == "__main__":
    inv = scan_wolfcam()
    print(json.dumps(inv.to_dict(), indent=2))
