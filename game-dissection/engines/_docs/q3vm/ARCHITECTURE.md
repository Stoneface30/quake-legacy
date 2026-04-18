# q3vm — Architecture

**Upstream:** https://github.com/jnz/q3vm
**Size (original):** 1.8 MB
**Role in our project:** Standalone Q3 VM (virtual machine) interpreter. Useful for sandboxed game-logic analysis.

## Module map
src/vm_*.c        — VM core (stack, opcodes, syscalls)
src/tools/        — q3asm, q3lcc for compiling to .qvm
examples/         — small VM programs

## Key files
- `src/vm_*.c` — VM interpreter core
- `src/tools/q3asm/` — q3asm assembler
- `src/tools/q3lcc/` — q3lcc C-to-VM compiler

## See also
- `_canonical/` — canonical copy of files from this tree that are unique or authority-winners
- `game-dissection/engines/q3vm/` — near-duplicate variants preserved for diff
- `_diffs/` — per-file diffs where this tree differs from canonical
