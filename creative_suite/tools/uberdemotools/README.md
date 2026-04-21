# tools/uberdemotools/

Slim holding dir for prebuilt `UDT_json.exe` / `UDT.dll` binaries.

**Status 2026-04-19:** empty — upstream source never built locally. The full source
tree was retired from `tools/quake-source/uberdemotools/` in the engine-folder
unification. Thin reference is preserved at:

- `engine/engines/variants/uberdemotools/` (variant dissection notes)

To build binaries:
1. `git clone https://github.com/mightycow/uberdemotools` into a scratch dir
2. Follow UDT_DLL/premake README
3. Copy resulting `UDT_json.exe` (+ x64 variant) and `UDT.dll` here
4. Point tools/download_tools.py at the binaries

Consumers reference this dir via:
- CLAUDE.md §Key Tools: `G:\QUAKE_LEGACY\tools\uberdemotools\UDT_json.exe`
- phase2/dm73parser golden baseline validation
