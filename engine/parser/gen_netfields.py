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

# From the code root (HL-9), not a drive letter: the tree is the pinned,
# bootstrapped WolfcamQL source (third_party/wolfcamql/SOURCE.json).
SRC = (Path(__file__).resolve().parents[2] / "engine" / "pantheon_renderer" /
       "wolfcamql-11.3-src" / "wolfcamql-src" / "code" / "qcommon" / "msg.c")
OUT = Path(__file__).with_name("netfields_generated.py")
# The same tables for the C side of gate G1: --dump-snapshots prints every
# field by name through them.
OUT_C = (Path(__file__).resolve().parents[2] / "engine" / "pantheon_renderer" /
         "host" / "pantheon_netfields.inc")
C_TABLES = {
    # C array emitted          (source table,               struct)
    "pantheon_es73": ("entityStateFieldsQldm73", "entityState_t"),
    "pantheon_psQ3": ("playerStateFieldsQ3", "playerState_t"),
}

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


# What the tables MUST contain. A generator that silently skips an entry it
# does not recognise recreates, in automated form, exactly the bug it exists to
# prevent -- so the counts are asserted and anything unparseable is fatal.
EXPECTED_COUNT = {
    "playerStateFieldsQ3": 48,
    "entityStateFieldsQldm73": 53,
}


class SchemaError(RuntimeError):
    pass


def parse_table(src: str, c_name: str) -> list[tuple[str, str]]:
    i = src.index(c_name + "[]")
    j = src.index("};", i)
    rows, skipped = [], []
    for lineno, line in enumerate(src[i:j].splitlines(), 1):
        code = line.split("//")[0]
        if "{" not in code or "}" not in code:
            continue                    # not an entry line at all
        m = ENTRY.search(code)
        if m:
            rows.append((m.group(2), m.group(3)))
        else:
            # An entry-shaped line we could not read. NEVER skip this: the
            # original bug was one such line, `{ PSF(groundEntityNum),
            # GENTITYNUM_BITS }`, quietly dropped by a regex that demanded a
            # numeric width. One missing row shifts every later index by one.
            skipped.append((lineno, code.strip()))
    if skipped:
        raise SchemaError(
            "%s: %d entry-shaped line(s) could not be parsed -- refusing to "
            "emit a table with holes in it:%s%s"
            % (c_name, len(skipped), NL,
               NL.join("    line %d: %s" % x for x in skipped)))

    want = EXPECTED_COUNT.get(c_name)
    if want is not None and len(rows) != want:
        raise SchemaError("%s: expected %d fields, parsed %d"
                          % (c_name, want, len(rows)))
    return rows


def is_signed(bits: str) -> bool:
    """A negative declared width means the field is signed (MSG_ReadBits).

    Signedness is per-field. Blanket sign-extending every 8-bit field would
    turn a perfectly good weapon slot or animation number negative.
    """
    return bits.lstrip().startswith("-")


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
            out.append("    (%3d, %-24r, %r, %s),"
                       % (n, name, bits, is_signed(bits)))
        out.append("]")
        out.append("")
        out.append("%s_INDEX = {name: idx for idx, name, _b, _s in %s}"
                   % (py_name, py_name))
        out.append("%s_SIGNED = {name for _i, name, _b, sgn in %s if sgn}"
                   % (py_name, py_name))
        out.append("")
    return "\n".join(out) + "\n"


def render_c(src: str) -> str:
    """The C tables: name, offsetof, float flag -- in msg.c's own order."""
    out = ["/* Generated from msg.c by engine/parser/gen_netfields.py.",
           " * DO NOT EDIT. Regenerate: python -m engine.parser.gen_netfields --write",
           " * Include after q_shared.h and <stddef.h>; the includer defines",
           " * pantheonNetField_t { const char *name; int offset; int isFloat; }. */",
           ""]
    for c_arr, (c_name, struct) in C_TABLES.items():
        rows = parse_table(src, c_name)
        out.append("static const pantheonNetField_t %s[] = {  /* %s, %d fields */"
                   % (c_arr, c_name, len(rows)))
        for name, bits in rows:
            out.append('    { "%s", (int)offsetof(%s, %s), %d },'
                       % (name, struct, name, 1 if bits.strip() == "0" else 0))
        out.append("};")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    if not SRC.exists():
        print("engine source not present: %s" % SRC, file=sys.stderr)
        return 2
    src = SRC.read_text(errors="replace")
    outputs = {OUT: render(src), OUT_C: render_c(src)}

    if args.write:
        for path, text in outputs.items():
            path.write_text(text, encoding="utf-8", newline="\n")
            print("wrote %s" % path)
        return 0
    if args.check:
        for path, text in outputs.items():
            if not path.exists():
                print("%s missing; run --write" % path, file=sys.stderr)
                return 1
            if path.read_text(encoding="utf-8") != text:
                print("%s is STALE -- the engine source disagrees with it"
                      % path, file=sys.stderr)
                return 1
        print("netfield schema matches the engine source")
        return 0
    print(outputs[OUT])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
