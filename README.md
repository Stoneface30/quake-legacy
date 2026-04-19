<div align="center">

<table width="100%" cellpadding="0" cellspacing="0" style="background:#040c1f;border-radius:8px;border:1px solid #1e2a50;overflow:hidden;">
<tr><td style="border-left:4px solid #f5c518;padding:28px 32px;">

<p style="color:#8090b8;font-size:12px;letter-spacing:0.2em;margin:0 0 6px;">
⊕ &nbsp;PANTHEON / PTN &nbsp;·&nbsp; QUAKE LIVE
</p>

<h1 style="color:#f5c518;font-size:38px;font-weight:900;letter-spacing:-0.5px;margin:0 0 4px;">
QUAKE LEGACY
</h1>

<p style="color:#8090b8;margin:0 0 16px;font-size:14px;">
// fragmovie production system &nbsp;·&nbsp; id Tech 3
</p>

<p style="color:#c8d4e8;max-width:640px;margin:0;line-height:1.6;">
Ten years of competitive Quake Live Clan Arena — <strong style="color:#e8eef8;">6,465</strong> <code style="background:#1a3e9a22;color:#8090b8;padding:1px 5px;border-radius:3px;">.dm_73</code> demos, tens of thousands of frags — turned into a fully automated fragmovie pipeline. Parse the binary, score every kill, batch-render through WolfcamQL, assemble with beat-synced music. Human approves at each gate. Machine does the rest.
</p>

</td></tr>
</table>

</div>

&nbsp;

[![python 3.11+](https://img.shields.io/badge/python-3.11+-002B7F?style=flat&labelColor=002B7F&color=1a3e9a)](https://www.python.org/)
[![ffmpeg 8.1](https://img.shields.io/badge/ffmpeg-8.1-002B7F?style=flat&labelColor=002B7F&color=1a3e9a)](https://ffmpeg.org/)
[![tests 132 passing](https://img.shields.io/badge/tests-132%20passing-002B7F?style=flat&labelColor=002B7F&color=1a3e9a)](#)
[![engine id Tech 3](https://img.shields.io/badge/engine-id%20Tech%203-002B7F?style=flat&labelColor=002B7F&color=1a3e9a)](https://github.com/id-Software/Quake-III-Arena)
[![clan Pantheon / pTn](https://img.shields.io/badge/clan-Pantheon%20%2F%20pTn-b8890a?style=flat&labelColor=b8890a&color=c99a10)](https://en.wikipedia.org/wiki/Flag_of_Nauru)
[![license GPL-2.0](https://img.shields.io/badge/license-GPL--2.0-002B7F?style=flat&labelColor=002B7F&color=1a3e9a)](./LICENSE)

<div align="center">

| **6,465** | **13.2 GB** | **107** | **3,200+** | **132** |
|:---:|:---:|:---:|:---:|:---:|
| `.dm_73` demos | corpus on disk | remastered assets | lines of pipeline | tests passing |

</div>

---

## What This Is

Two problems, one codebase:

- **Fragmovie automation** — parse every demo as binary, score every kill by weapon/airtime/multi-kill, batch-render approved clips through WolfcamQL, assemble through FFmpeg with beat-synced music. The human is the creative director, not the editor.
- **Engine ownership** — Quake Live's closed renderer is reverse-engineered with Ghidra, every console command inventoried, and a protocol-73-capable open-source engine fork planned for Phase 3.5. When we change a bit, we know it will make the rail pink.

Everything downstream — AI cinematography, photorealistic weapon skins, automated render approval — runs on those two foundations.

---

## Project Status

| PHASE | WHAT | STATUS | OUTPUT |
|---|---|---|---|
| **1 — FFmpeg pipeline** | Hard-cut concat assembler · beat-sync · PANTHEON intro · game audio mix | ▶ SHIPPING | Parts 4/5/6 rendered · Parts 7–12 queued |
| **1.5 — Cinema Suite** | FastAPI web UI — clip sequencing, seam drag, music swap, Tier A/B preview | ▶ SHIPPED | 132 tests · 8 panels · branch `creative-suite-v2-step2` |
| **2 — Demo intelligence** | C++ dm_73 parser · WolfcamQL batch renderer · frag scoring | ◉ IN PROGRESS | 222 frags parsed · 6,465 demo corpus unblocked |
| **3 — AI cinematography** | Auto camera angles · bullet cam · slow-mo triggers from entity trajectories | ○ PLANNED | Blocked on Phase 2 data |
| **5 — Graphics overhaul** | Real-ESRGAN + ControlNet-Tile · 107-asset pk3 · drop-in, no engine patch | ▶ SHIPPED | `zzz_photorealistic.pk3` · 30 MB · 1024² |
| **4 — Public CLI** | `pip install quake-legacy` — give it demos, get a fragmovie | ◇ VISION | Post-Phase-3 · community give-back |

---

## Pipeline

<div align="center">

<table cellpadding="0" cellspacing="0" style="border:1px solid #d0d7de;border-radius:6px;overflow:hidden;font-family:monospace;font-size:13px;">
<tr><td style="padding:20px 24px;background:#f6f8fa;">

<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
<span style="background:#1a3e9a;color:#fff;padding:5px 10px;border-radius:4px;">.dm_73 demos</span>
<span style="color:#656d76;">→</span>
<span style="background:#1a3e9a;color:#fff;padding:5px 10px;border-radius:4px;">C++ parser</span>
<span style="color:#656d76;">→</span>
<span style="background:#1a3e9a;color:#fff;padding:5px 10px;border-radius:4px;">frag DB (anon)</span>
<span style="color:#656d76;">→</span>
<span style="background:#1a3e9a;color:#fff;padding:5px 10px;border-radius:4px;">scorer</span>
<span style="color:#656d76;">→</span>
<span style="background:#c99a10;color:#fff;padding:5px 10px;border-radius:4px;font-weight:700;">HUMAN GATE</span>
</div>

<div style="margin:8px 0 8px 228px;color:#656d76;">↓</div>

<div style="margin-left:228px;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
<span style="background:#1a3e9a;color:#fff;padding:5px 10px;border-radius:4px;">WolfcamQL render</span>
<span style="color:#656d76;">→</span>
<span style="background:#1a3e9a;color:#fff;padding:5px 10px;border-radius:4px;">FFmpeg assembly</span>
<span style="color:#656d76;">→</span>
<span style="background:#1a6640;color:#fff;padding:5px 10px;border-radius:4px;font-weight:700;">Part N.mp4</span>
</div>

<p style="margin:12px 0 0;color:#656d76;font-size:12px;">
PANTHEON intro (7s) + beat-sync cuts + game audio at full · music at 50%
</p>

</td></tr>
</table>

</div>

---

## Cinema Suite — Web UI

> `git checkout creative-suite-v2-step2` &nbsp;·&nbsp; `cd creative_suite && python -m uvicorn app:app`

FastAPI + vanilla JS interface that replaces text-file editing for the entire Phase 1 pipeline. Eight panels covering the full creative workflow:

| Panel | Function |
|:---:|---|
| 1–2 | Part picker + clip sequence |
| 3 | Per-clip slow / trim / section-role overrides |
| 4 | Waveform + flow plan timeline |
| 5 | Seam drag → downbeat snapping |
| 6 | Music track swap |
| 7 | Tier A draft preview (wolfcam→ffmpeg mp4, ~45s) |
| 8 | Tier B live engine scrub (WebSocket + JPEG @ 4 Hz) |

---

## Graphics Overhaul

107 stock Quake Live weapon, icon, and HUD textures run through **Real-ESRGAN 4x-UltraSharp + SD1.5 ControlNet-Tile img2img**. UV layout preserved (denoise hard-capped at 0.35 — above 0.40 barrel/stock seams drift). Output ships as `zzz_photorealistic.pk3` — alphabetical load-order wins over stock, no config change, no engine patch.

![Phase 5 texture pipeline — original pak00 shotgun skin vs 4x-UltraSharp + ControlNet Tile photorealistic version](docs/visual-record/github-readme/textures/shotgun_after.png)

<details>
<summary><strong>Before / After — Rocket Launcher</strong></summary>

| Original (pak00, 256²) | Photorealistic (Phase 5, 1024²) |
|:---:|:---:|
| ![](docs/visual-record/github-readme/textures/rocket_before.png) | ![](docs/visual-record/github-readme/textures/rocket_after.png) |

</details>

<details>
<summary><strong>Full weapon grid (5 weapons)</strong></summary>

| Weapon | Original (pak00, 256²) | Photorealistic (Phase 5, 1024²) |
|---|:---:|:---:|
| Rocket Launcher | ![](docs/visual-record/github-readme/textures/rocket_before.png) | ![](docs/visual-record/github-readme/textures/rocket_after.png) |
| Railgun | ![](docs/visual-record/github-readme/textures/railgun_before.png) | ![](docs/visual-record/github-readme/textures/railgun_after.png) |
| Lightning Gun | ![](docs/visual-record/github-readme/textures/lightning_before.png) | ![](docs/visual-record/github-readme/textures/lightning_after.png) |
| Plasma Gun | ![](docs/visual-record/github-readme/textures/plasma_before.png) | ![](docs/visual-record/github-readme/textures/plasma_after.png) |
| Shotgun | ![](docs/visual-record/github-readme/textures/shotgun_before.png) | ![](docs/visual-record/github-readme/textures/shotgun_after.png) |

</details>

---

## How It Works

<details>
<summary><strong>Demo parsing — protocol 73 binary format</strong></summary>

Quake Live demos are Huffman-compressed server-to-client message streams. Each snapshot holds a delta-compressed entity array. The parser walks entities looking for `event & ~0x300 == EV_OBITUARY` (the top 2 bits toggle on re-fire and must be masked). Kill triples are `(otherEntityNum2=killer, otherEntityNum=victim, eventParm=MOD_*)` with millisecond-accurate `server_time`. Player identities stored as `anon_hash = sha256(raw_name)` — no handles, no Steam IDs, ever.

Full format reference: [`docs/reference/dm73-format-deep-dive.md`](docs/reference/dm73-format-deep-dive.md) (1,337 lines).

</details>

<details>
<summary><strong>WolfcamQL automation</strong></summary>

`trap_AddAt` is disabled in the shipped WolfcamQL build. Every scripted action goes through a generated `gamestart.cfg`:

```
seekclock 8:52
video avi name demo_name
at 9:05 quit
```

Launched headless: `wolfcamql.exe +set fs_homepath <out_dir> +exec gamestart.cfg +demo <path>`. With 8s pre-roll / 5s post-roll per frag, the recording window is tight enough to batch thousands of clips overnight.

60+ console commands catalogued from `wolfcam_consolecmds.c`: [`docs/reference/wolfcam-commands.md`](docs/reference/wolfcam-commands.md).

</details>

<details>
<summary><strong>FFmpeg assembly — the edit rules</strong></summary>

- **Hard cuts only.** No xfade, no dissolve, no dip-to-black. Every join is a raw concat.
- **Audio:** game sound at `1.0` (rail cracks, rocket impacts, grenade hits), music at `0.5` via `amix inputs=2:weights=1.0 0.5`. Game audio is the texture of the sport — muting it was tried and rejected.
- **Beat sync:** `librosa.onset.onset_detect` run once per track, cached as `*.beats.json`. Clip boundaries snap to nearest beat. T1 peaks snap to section drops.
- **Clip contract:** every clip plays its full post-trim duration (1s head / 2s tail). No sub-second cutaways. "Filler" means full-length atmospheric T3, not 0.5s flash.
- **PANTHEON intro:** first 7s of `IntroPart2.mp4` prepended to every Part, always.

</details>

---

## Quickstart

```bash
git clone https://github.com/Stoneface30/quake-legacy
cd quake-legacy
python -m venv venv && source venv/Scripts/activate
pip install -r requirements.txt

# Phase 1: preview render for a Part
python phase1/experiment.py --part 4 --style punchy --preview

# Phase 5: install the photorealistic texture pack
cp phase5/04_pk3/zzz_photorealistic.pk3 "$QUAKE_LIVE_BASEQ3"

# Cinema Suite
cd creative_suite && python -m uvicorn app:app --reload
```

FFmpeg 8.1 expected at `tools/ffmpeg/ffmpeg.exe`. WolfcamQL at `tools/wolfcamql/wolfcamql.exe`.

---

## Privacy

> ⚠️ **Public repo — privacy-hard by design.** Player names, handles, nicknames, and Steam IDs are never committed. Demo files, renders, and the frag DB never leave local disk. All analysis uses `anon_hash = sha256(raw_name)`.

---

## Credits & License

**Produced by [Pantheon / pTn](https://en.wikipedia.org/wiki/Flag_of_Nauru)** — Quake Live Clan Arena. Built on id Tech 3, open source since 2005.

- [WolfcamQL](https://github.com/brugal/wolfcamql) (GPL) — headless `.dm_73` renderer
- [UberDemoTools](https://github.com/mightycow/uberdemotools) — dm_73 format reference
- [Q3MME](https://github.com/q3mme/q3mme) — camera pathing inspiration
- [ioquake3](https://github.com/ioquake/ioq3) — engine branch
- id Software — Q3/QL source assets (GPL-2.0 since 2005)

This repo is **GPL-2.0**. Everything here is open source and homemade — a gift back to the community.
