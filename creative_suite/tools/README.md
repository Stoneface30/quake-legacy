# Tools

All project dependencies. Run `download_tools.py` to fetch everything automatically.

## Required Tools

| Tool | Version | Source | Purpose | Status |
|---|---|---|---|---|
| FFmpeg | Latest (7.x) | https://ffmpeg.org/download.html | Video encode/decode/filter | ⬜ Download |
| UberDemoTools | Latest | https://github.com/mightycow/uberdemotools | Demo parsing (C++, binary) | ⬜ Download |
| qldemo-python | Latest | https://github.com/Quakecon/qldemo-python | Python demo parser | ⬜ Download |
| f0e/blur | Latest | https://github.com/f0e/blur | Cinematic motion blur | ⬜ Download |
| WolfcamQL | 12.7test49 | https://github.com/brugal/wolfcamql | Demo renderer + freecam | ⬜ Download |
| Ghidra | 11.x | https://github.com/NationalSecurityAgency/ghidra | WolfWhisperer.exe RE | ⬜ Download |
| Python | 3.11+ | https://python.org | Runtime | ⬜ Install |

## Directory Layout

```
tools/
  ffmpeg/
    ffmpeg.exe         ← main binary
    ffprobe.exe        ← media inspector
    ffplay.exe         ← player
    VERSION.txt        ← version string
  uberdemotools/
    UDT_GUI.exe        ← GUI application
    UDT_json.exe       ← CLI JSON exporter (main tool we use)
    docs/              ← UDT documentation
  qldemo-python/
    qldemo/            ← Python package
    pyhuffman/         ← C Huffman extension (must compile)
    examples/
  blur/
    blur.exe           ← f0e/blur binary
    config.yaml        ← default blur config
  wolfcamql/
    wolfcamql.exe      ← main binary (latest)
    baseq3/            ← copy QL .pk3 paks here
    wolfcam-ql/        ← configs directory
  ghidra/
    ghidraRun.bat      ← launcher
    docs/              ← Ghidra documentation
  README.md            ← this file
  download_tools.py    ← automated download script
```

## Notes

- FFmpeg: Windows builds at https://www.gyan.dev/ffmpeg/builds/ (get `ffmpeg-release-full.7z`)
- UberDemoTools: get the binary release from GitHub releases page
- WolfcamQL: latest build from https://github.com/brugal/wolfcamql/releases
  - After download, copy Quake Live .pk3 files into `tools/wolfcamql/baseq3/`
  - QL paks location: `Steam\steamapps\common\Quake Live\baseq3\`
- qldemo-python: requires Python and a C compiler for the Huffman extension
  - `cd tools/qldemo-python && pip install -e .`
- f0e/blur: requires VapourSynth — see https://github.com/f0e/blur#installation
- Ghidra: requires Java 17+ JDK
