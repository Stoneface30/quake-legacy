"""Task 8 — pk3 builder helpers.

Split into two modules to keep each responsibility testable in isolation:
  - png_to_tga: single-file conversion, 32-bit RGBA, no pk3 knowledge
  - zip_pk3:    deflate a list of (internal_path, bytes) tuples into a pk3

The API layer (api/packs.py) composes these around the approval query and
writes a `pack_builds` row with the sha256.
"""
