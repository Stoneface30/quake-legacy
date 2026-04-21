import re, os, sys
os.chdir("G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src/code")

def read_lines(p):
    with open(p, encoding='utf-8', errors='replace') as f:
        return f.readlines()

# ---- 1. Commands from Cmd_AddCommand / trap_AddCommand ----
cmd_entries = []
cmd_re = re.compile(r'(?:ri\.)?Cmd_AddCommand\s*\(\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)')
trap_re = re.compile(r'trap_AddCommand\s*\(\s*"([^"]+)"')
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git','tools','thirdparty','asm','web')]
    for fn in files:
        if not fn.endswith('.c'): continue
        p = os.path.join(root, fn).replace('\\','/').lstrip('./')
        if p.startswith('./'): p = p[2:]
        for i, line in enumerate(read_lines(p), 1):
            s = line.strip()
            if s.startswith('//'): continue
            for m in cmd_re.finditer(line):
                cmd_entries.append((m.group(1), m.group(2), f"{p}:{i}"))
            for m in trap_re.finditer(line):
                if not line.lstrip().startswith('//'):
                    cmd_entries.append((m.group(1), "(cgame forward)", f"{p}:{i}"))

cg_table = []
in_table = False
tbl_re = re.compile(r'\{\s*"([^"]+)"\s*,\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}')
for i, line in enumerate(read_lines('cgame/cg_consolecmds.c'), 1):
    if 'consoleCommand_t\tcommands[]' in line or 'consoleCommand_t commands[]' in line:
        in_table = True; continue
    if in_table:
        if line.strip().startswith('};'):
            in_table = False; continue
        m = tbl_re.search(line)
        if m and not line.lstrip().startswith('//'):
            cg_table.append((m.group(1), m.group(2), f"cgame/cg_consolecmds.c:{i}"))

seen = set(); uniq_cmds = []
for name, handler, src in cmd_entries + cg_table:
    k = (name, src)
    if k in seen: continue
    seen.add(k); uniq_cmds.append((name, handler, src))
uniq_cmds.sort(key=lambda x:(x[0].lower(), x[2]))

# ---- 2. Cvar table entries ----
cvar_entries = []
cvar_table_re = re.compile(r'\{\s*(?:&([a-zA-Z_][a-zA-Z0-9_]*)|cvp\(([a-zA-Z_][a-zA-Z0-9_]*)\))\s*,\s*(?:"([^"]*)"\s*,\s*)?"([^"]*)"\s*,\s*([A-Z_|0-9 \t]+)\s*\}')
def scan_tbl(path, category):
    for i, line in enumerate(read_lines(path), 1):
        if line.lstrip().startswith('//'): continue
        m = cvar_table_re.search(line)
        if not m: continue
        if m.group(2):
            cname = m.group(2); default = m.group(4)
        else:
            cname = m.group(3) if m.group(3) else m.group(1)
            default = m.group(4)
        flags = m.group(5).strip()
        cvar_entries.append((cname, default, flags, f"{path}:{i}", category))

scan_tbl('cgame/cg_main.c', 'cgame')
scan_tbl('ui/ui_main.c', 'ui')
scan_tbl('q3_ui/ui_main.c', 'q3_ui')

# ---- 3. Cvar_Get ----
cvar_get_re = re.compile(r'(?:ri\.)?Cvar_Get\s*\(\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*([A-Z_|0-9 \t]+?)\s*\)')
cvar_get_entries = []
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git','tools','thirdparty','asm','web','cgame','ui','q3_ui','game','botlib')]
    for fn in files:
        if not fn.endswith('.c'): continue
        p = os.path.join(root, fn).replace('\\','/').lstrip('./')
        if p.startswith('./'): p = p[2:]
        cat = p.split('/')[0]
        for i, line in enumerate(read_lines(p), 1):
            if line.lstrip().startswith('//'): continue
            m = cvar_get_re.search(line)
            if m:
                cvar_get_entries.append((m.group(1), m.group(2), m.group(3).strip(), f"{p}:{i}", cat))

# ---- 4. trap_Cvar_Register direct ----
trap_cvar_re = re.compile(r'trap_Cvar_Register\s*\(\s*(?:NULL|&[a-zA-Z_][a-zA-Z0-9_]*)\s*,\s*"([^"]+)"\s*,\s*"([^"]*)"\s*,\s*([A-Z_|0-9 \t]+?)\s*\)')
for root, dirs, files in os.walk('.'):
    dirs[:] = [d for d in dirs if d not in ('.git','tools','thirdparty','asm','web')]
    for fn in files:
        if not fn.endswith('.c'): continue
        p = os.path.join(root, fn).replace('\\','/').lstrip('./')
        if p.startswith('./'): p = p[2:]
        cat = p.split('/')[0]
        for i, line in enumerate(read_lines(p), 1):
            if line.lstrip().startswith('//'): continue
            m = trap_cvar_re.search(line)
            if m:
                cvar_get_entries.append((m.group(1), m.group(2), m.group(3).strip(), f"{p}:{i}", cat))

all_cvars = cvar_entries + cvar_get_entries
seen = set(); uniq_cvars = []
for e in all_cvars:
    k = (e[0], e[3])
    if k in seen: continue
    seen.add(k); uniq_cvars.append(e)

# ioquake3 baseline
ioq3_names = set()
ioq3_path = "G:/QUAKE_LEGACY/tools/quake-source/ioquake3/code"
if os.path.isdir(ioq3_path):
    cv_simple = re.compile(r'(?:Cvar_Get|trap_Cvar_Register)\s*\(\s*(?:&[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*)?"([a-zA-Z_][a-zA-Z0-9_]*)"')
    tbl_simple = re.compile(r'\{\s*&?[a-zA-Z_][a-zA-Z0-9_]*\s*,\s*"([a-zA-Z_][a-zA-Z0-9_]*)"')
    for root, dirs, files in os.walk(ioq3_path):
        for fn in files:
            if not (fn.endswith('.c') or fn.endswith('.h')): continue
            p = os.path.join(root, fn)
            try:
                with open(p, encoding='utf-8', errors='replace') as f:
                    for line in f:
                        for m in cv_simple.finditer(line): ioq3_names.add(m.group(1))
                        for m in tbl_simple.finditer(line): ioq3_names.add(m.group(1))
            except: pass

uniq_cvars.sort(key=lambda x:(x[0].lower(), x[3]))

def is_wolfcam_specific(name):
    low = name.lower()
    if low.startswith('wolfcam') or low.startswith('wc_') or low.startswith('cg_draw2d'):
        return True
    if ioq3_names and name not in ioq3_names:
        return True
    return False

def esc(s): return str(s).replace('|','\\|')

out_path = "G:/QUAKE_LEGACY/.claude/worktrees/hopeful-shtern-7fe850/engine/wolfcam-knowledge-ingest/01-commands-cvars.md"

lines = []
L = lines.append
L("# 01 — Commands & Cvars (wolfcamql)")
L("")
L("License: GPL-2.0 (wolfcamql) — extracted via static source scan, no inference.")
L("Generated from: G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src/")
L("")
L("Scan method: Python walk over `code/` matching `Cmd_AddCommand(...)`, `trap_AddCommand(...)`, the")
L("`cgame/cg_consolecmds.c:commands[]` table, cvar tables `cvarTable[]` in `cg_main.c`/`ui_main.c`,")
L("`Cvar_Get(...)` and `trap_Cvar_Register(...)` calls. Commented-out (`//`) lines excluded.")
L("")
L(f"Totals: **{len(uniq_cmds)} command registrations**, **{len(uniq_cvars)} cvar registrations** (a cvar")
L("registered in several files appears once per site).")
L("")
L("ioquake3 baseline loaded from `G:/QUAKE_LEGACY/tools/quake-source/ioquake3/code/` "
  f"({len(ioq3_names)} distinct cvar names). Any name not present there is tagged wolfcam-specific.")
L("")
L("---")
L("")
L("## A. Console Commands")
L("")
L("Handler column: C function bound to the command, or `(cgame forward)` for `trap_AddCommand` entries")
L("where the cgame module merely forwards the token to the server.")
L("")
L("| Name | Handler | Source |")
L("|------|---------|--------|")
for name, handler, src in uniq_cmds:
    L(f"| `{esc(name)}` | `{esc(handler)}` | {esc(src)} |")
L("")
L(f"*Total:* **{len(uniq_cmds)}**")
L("")
L("---")
L("")

wolfcam_specific = []
inherited = []
renderer_capture = []
for e in uniq_cvars:
    name = e[0]; src = e[3]
    if 'tr_init.c' in src or 'cl_avi.c' in src or '/snd_' in src:
        renderer_capture.append(e)
    elif is_wolfcam_specific(name):
        wolfcam_specific.append(e)
    else:
        inherited.append(e)

def cvar_block(title, rows, note=""):
    L(f"## {title}")
    L("")
    if note: L(note); L("")
    L("| Name | Default | Flags | Source |")
    L("|------|---------|-------|--------|")
    for name, default, flags, src, cat in rows:
        d = default if default != "" else '""'
        L(f"| `{esc(name)}` | `{esc(d)}` | {esc(flags)} | {esc(src)} |")
    L("")
    L(f"*Count:* **{len(rows)}**")
    L("")
    L("---")
    L("")

cvar_block("B. Cvars — wolfcam-specific (NEW vs ioquake3)", wolfcam_specific,
           "Name starts with `wolfcam_`, `wc_`, `cg_draw2d`, OR name is absent from the ioquake3 baseline. "
           "Heuristic — some names may exist in ioq3 under a different module; verify before "
           "assuming absolute novelty.")
cvar_block("C. Cvars — inherited from Q3/ioquake3", inherited,
           "Name appears in the ioquake3 baseline. Default value / flags may still differ from upstream.")
cvar_block("D. Cvars — renderer / capture (tr_init.c, cl_avi.c, snd_*)", renderer_capture,
           "Renderer GL and AVI-capture cvars live in `renderergl1/tr_init.c`, `renderergl2/tr_init.c`, "
           "`client/cl_avi.c`, and `client/snd_*.c`.")

L("## E. Summary")
L("")
L(f"- Total console commands (all sites): **{len(uniq_cmds)}**")
L(f"- Total cvar registrations (all sites): **{len(uniq_cvars)}**")
L(f"  - wolfcam-specific (heuristic): **{len(wolfcam_specific)}**")
L(f"  - inherited from ioq3: **{len(inherited)}**")
L(f"  - renderer / capture / sound: **{len(renderer_capture)}**")
L("")
L("### Top 20 most fragmovie-relevant wolfcam cvars (judgment pick)")
L("")

reasons = {
    'wolfcam_following':'which player slot the chase cam is locked to',
    'wolfcam_fixedViewOrigin':'freeze camera origin — static shot for fragmovies',
    'wolfcam_fixedView':'master switch for fixed-camera mode',
    'cg_freecam_useServerAngles':'toggle between mouse-look and path-playback angles during freecam',
    'cg_freecam_noclip':'freecam passes through geometry',
    'cg_freecam_speed':'flight speed for freecam',
    'cl_freezeDemo':'pauses demo playback — used between cuts',
    'cl_avidemo':'legacy AVI capture frame-rate (0 = off)',
    'cl_aviFrameRate':'AVI capture fps when `video` command is active',
    'cl_aviMotionJpeg':'MJPEG vs raw RGB capture codec',
    'timescale':'global time multiplier — slow-mo / fast-forward',
    'cl_forceavidemo':'force frame-locked AVI capture',
    'cg_thirdPerson':'third-person view toggle',
    'cg_thirdPersonRange':'distance behind player in 3rd-person',
    'cg_thirdPersonAngle':'yaw offset behind player in 3rd-person',
    'cg_cameraOrbit':'orbit-cam speed',
    'cg_cameraOrbitDelay':'delay between orbit updates',
    'cg_draw2D':'2D HUD master switch — turn OFF before capture',
    'cg_drawGun':'weapon model visibility',
    'cg_drawFPS':'fps counter — disable for capture',
}
picks = []
for target in reasons.keys():
    for e in uniq_cvars:
        if e[0] == target:
            picks.append(e); break
if len(picks) < 20:
    for e in uniq_cvars:
        if len(picks) >= 20: break
        low = e[0].lower()
        if e[0] in [p[0] for p in picks]: continue
        if any(k in low for k in ['freecam','seek','pov','chase','camerapoint','killcam']):
            picks.append(e)
picks = picks[:20]

L("| Name | Default | Flags | Source | Why it matters |")
L("|------|---------|-------|--------|----------------|")
for name, default, flags, src, cat in picks:
    r = reasons.get(name, '(camera/demo-navigation related)')
    d = default if default != "" else '""'
    L(f"| `{esc(name)}` | `{esc(d)}` | {esc(flags)} | {esc(src)} | {r} |")
L("")
L("### Top 20 most fragmovie-relevant wolfcam COMMANDS (judgment pick)")
L("")
cmd_top = [
    ('freecam','toggle/set free cinematic camera'),
    ('seekclock','seek demo to wall-clock timestamp — core WolfWhisperer automation hook'),
    ('seek','seek demo to arbitrary server time'),
    ('seeknext','skip to next event/snapshot'),
    ('seekprev','skip to previous event/snapshot'),
    ('seekend','seek to end of demo'),
    ('fastforward','accelerate demo playback'),
    ('rewind','reverse demo playback'),
    ('pause','pause demo'),
    ('pov','switch POV to a specified client slot'),
    ('chase','chase-cam to a player'),
    ('video','begin AVI capture (starts cl_avi* pipeline)'),
    ('stopvideo','stop AVI capture'),
    ('addcamerapoint','add a spline knot for the camera path'),
    ('clearcamerapoints','reset the camera path'),
    ('playcamera','play back the camera path'),
    ('stopcamera','stop camera path playback'),
    ('savecamera','persist camera path to file'),
    ('loadcamera','load camera path from file'),
    ('at','schedule a console command at a demo time (WolfWhisperer automation hook)'),
]
L("| Command | Source | Why it matters |")
L("|---------|--------|----------------|")
for cmd, why in cmd_top:
    sr = next((s for n, h, s in uniq_cmds if n == cmd), "(not found)")
    L(f"| `{cmd}` | {esc(sr)} | {why} |")
L("")

with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))
print("WROTE:", out_path)
print("cmds:", len(uniq_cmds), "cvars:", len(uniq_cvars),
      "wc-spec:", len(wolfcam_specific), "inherit:", len(inherited), "rend:", len(renderer_capture))
print("ioq3 baseline names:", len(ioq3_names))
