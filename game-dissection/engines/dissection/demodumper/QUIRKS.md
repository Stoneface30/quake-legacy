# demodumper — Quirks and Gotchas

- Pure Python, slow for bulk processing (thousands of demos)
- Handles malformed demos gracefully where qldemo-python crashes
- Our FT-1 custom C++ parser replaces this for bulk work, but demodumper is a good fallback for weird demos

## See also
- `_docs/demodumper/ARCHITECTURE.md`
- `_docs/demodumper/EXTENSION_POINTS.md`
