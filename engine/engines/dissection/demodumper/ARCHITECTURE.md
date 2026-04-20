# demodumper — Architecture

**Upstream:** https://github.com/syncore/demodumper
**Size (original):** 0.2 MB
**Role in our project:** Python companion to qldemo-python. Handles score-format edge cases.

## Module map
demodumper.py     — main entry, handles score format variants
qldemo/           — may include patches to base qldemo-python
NOTE              — quirks and limitations (read first)

## Key files
- `demodumper.py` — Main entry — handles all score command format variants
- `NOTE` — Known quirks and limitations — read first

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `engine/engines/demodumper/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
