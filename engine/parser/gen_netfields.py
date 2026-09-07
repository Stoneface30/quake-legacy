"""Generate the protocol netfield schemas from the engine source.

WHY THIS EXISTS. The field indices were hand-maintained in two places and
audited by eye. An audit regex that required a NUMERIC bit width silently
skipped `{ PSF(groundEntityNum), GENTITYNUM_BITS }` -- one entry -- which
shifted every later index down by one and produced a confident, wrong
conclusion that protocol 73 used a different playerstate table. It does not:
msg.c selects `playerStateFieldsQ3` for 73, and every index the parser already
used was correct.

So the table is no longer transcribed or eyeballed. It is read out of the
engine source, and a test regenerates it and fails if the two ever diverge.

    python -m engine.parser.gen_netfields --check
    python -m engine.parser.gen_netfields --write
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

SRC = Path("G:/QUAKE_LEGACY/engine/pantheon_renderer/wolfcamql-11.3-src/"
           "wolfcamql-src/code/qcommon/msg.c")
OUT = Path(__file__).with_name("netfields_generated.py")

# Deliberately permissive on the bit width: it may be a number, a negative
# number, or a macro such as GENTITYNUM_BITS. Requiring digits is the exact
# mistake this module exists to prevent.
ENTRY = re.compile(r"\{\s*(PSF|NETF)\(\s*([A-Za-z0-9_\[\]\.]+)\s*\)\s*,"
                   r"\s*([A-Za-z0-9_\-]+)\s*\}")

TABLES = {
    # python name              C array name              protocols that use it
    "PLAYERSTATE_Q3":          ("playerStateFieldsQ3", "Q3, 73"),
    "PLAYERSTATE_QLDM90":      ("playerStateFieldsQldm90", "90"),
    "PLAYERSTATE_QLDM91":      ("playerStateFieldsQldm91", "91"),
    "ENTITYSTATE_Q3":          ("entityStateFieldsQ3", "Q3"),
    "ENTITYSTATE_QLDM73":      ("entityStateFieldsQldm73", "73"),
}


def parse_table(src: str, c_name: str) -> list[tuple[str, str]]:
    i = src.index(c_name + "[]")
    j = src.index("};", i)
    rows = []
    for line in src[i:j].splitlines():
        line = line.split("//")[0]
        m = ENTRY.search(line)
        if m:
            rows.append((m.group(2), m.group(3)))
    return rows


def render(src: str) -> str:
    out = ['"""Generated from msg.c by engine/parser/gen_netfields.py.',
           "",
           "DO NOT EDIT. Regenerate instead. A test asserts this file still",
           "matches the engine source, so hand-editing it will fail loudly.",
           '"""',
           ""]
    for py_name, (c_name, protos) in TABLES.items():
        try:
            rows = parse_table(src, c_name)
        except ValueError:
            continue
        out.append("# %s -- used by protocol(s): %s -- %d fields"
                   % (c_name, protos, len(rows)))
        out.append("%s = [" % py_name)
        for n, (name, bits) in enumerate(rows):
            out.append("    (%3d, %-24r, %r)," % (n, name, bits))
        out.append("]")
        out.append("")
        out.append("%s_INDEX = {name: idx for idx, name, _bits in %s}"
                   % (py_name, py_name))
        out.append("")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not SRC.exists():
        print("engine source not present: %s" % SRC, file=sys.stderr)
        return 2
    text = render(SRC.read_text(errors="replace"))

    if args.write:
        OUT.write_text(text, encoding="utf-8")
        print("wrote %s" % OUT)
        return 0
    if args.check:
        if not OUT.exists():
            print("%s missing; run --write" % OUT, file=sys.stderr)
            return 1
        if OUT.read_text(encoding="utf-8") != text:
            print("%s is STALE -- the engine source disagrees with it"
                  % OUT, file=sys.stderr)
            return 1
        print("netfield schema matches the engine source")
        return 0
    print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
