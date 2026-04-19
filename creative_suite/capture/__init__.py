"""Task 9.3 — max-quality wolfcam capture config writer.

Phase 2's wolfcam re-render launcher consumes a `gamestart.cfg` with the
§4.4 cvar block: 4K resolution, 16x aniso, mipmap LOD bias -2, subdivisions
1, HUD off, com_maxfps 125. This module is the single source of truth for
that block so Phase 2 launchers and the /api/capture/gamestart endpoint
both agree.
"""
