# qldemo-python — Quirks and Gotchas

- Pure Python parsing is SLOW (~60 seconds per 3 MB demo on a modern CPU)
- Huffman decoder is the hot path; reimplemented in C it's 10-100x faster
- Missing some edge cases (proto-73 extensions past 2015 QL updates — FT-1 must handle)

## See also
- `_docs/qldemo-python/ARCHITECTURE.md`
- `_docs/qldemo-python/EXTENSION_POINTS.md`
