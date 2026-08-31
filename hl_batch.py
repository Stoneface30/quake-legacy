"""Sequential highlight builds. Continues past a failed Part."""
import subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).parent
res = []
for part in [int(a) for a in sys.argv[1:]] or [5, 6]:
    log = ROOT / "output" / f"hl{part}.out"
    print(f"\n===== Part {part} =====", flush=True)
    t0 = time.time()
    with log.open("w", encoding="utf-8", errors="replace") as fh:
        p = subprocess.run([sys.executable, "-u", "-m",
                            "creative_suite.engine.render_highlight",
                            "--part", str(part), "--minutes", "5"],
                           cwd=str(ROOT), stdout=fh, stderr=subprocess.STDOUT)
    dt = (time.time() - t0) / 60
    res.append((part, p.returncode == 0, dt))
    print(f"Part {part}: {'OK' if p.returncode==0 else 'FAILED'} {dt:.1f} min", flush=True)
print("\n===== SUMMARY =====", flush=True)
for part, ok, dt in res:
    print(f"  Part {part}: {'OK    ' if ok else 'FAILED'} {dt:6.1f} min", flush=True)
