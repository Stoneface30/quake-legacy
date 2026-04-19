# quake3e — Client/Server Split

Standard ioquake3 split, modernized:
- Full client + server live
- Separate `quake3e-server` dedicated binary via CMake option
- VMs (cgame, game, ui) run as .qvm by default, native supported

Nothing unusual here. See `_docs/q3mme/CLIENT_SERVER_SPLIT.md` for the general pattern.

## Minor quake3e additions

- Cleaner separation of client-only and server-only source files in CMake
- Server build doesn't pull in renderer (smaller binary, faster build)
- Shared qcommon/ code is the same on both sides
