# Phase A1 Canonical Tree — Ready for Deletion Checkpoint

**STATUS 2026-04-19: EXECUTED — tools/quake-source/ removed entirely.**
The rm-rf list below is archival. Per the engine-folder-unification plan
(`docs/research/engine-folder-unification-plan-2026-04-19.md`):
- `tools/quake-source/REPOS.md` → `engine/engines/REPOS.md`
- `tools/quake-source/q3mme/` → `engine/engines/_forks/q3mme/`
- `tools/quake-source/{all others}/` → deleted after extraction of proto-73
  patch series into `engine/engines/wolfcam-knowledge/patches/`
- Per-tree variant dirs now live under `engine/engines/variants/`.

Canonical tree remains at `engine/engines/_canonical/`.
Per-tree thin variant dirs now at `engine/engines/variants/<tree>/`.

## Statistics

- Source trees size: **722,611,232** bytes (722.6 MB)
- New canonical size: **550,777,846** bytes (550.8 MB)
- Variant files size: **30,925,700** bytes (30.9 MB)
- New tree total: **581,703,546** bytes (581.7 MB)
- **Bytes freed by deletion: 140,907,686 (140.9 MB)**

## To complete deletion (user must approve)

```bash
# Verify canonical tree is good first:
ls G:/QUAKE_LEGACY/engine/engines/_canonical/
# Then, after approval:
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/darkplaces'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/demodumper'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/gtkradiant'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/ioquake3'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/openarena-engine'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/openarena-gamecode'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/q3mme'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/q3vm'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/qldemo-python'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/quake1-source'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/quake2-source'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/quake3-source'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/quake3e'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/uberdemotools'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-local-src'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/wolfcamql-src'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/wolfet-source'
rm -rf 'G:/QUAKE_LEGACY/tools/quake-source/yamagi-quake2'
```

## Trees preserved as variants (near-dup cases)

- `darkplaces`
- `demodumper`
- `gtkradiant`
- `ioquake3`
- `openarena-engine`
- `openarena-gamecode`
- `q3mme`
- `q3vm`
- `qldemo-python`
- `quake1-source`
- `quake2-source`
- `quake3-source`
- `quake3e`
- `uberdemotools`
- `wolfet-source`
- `yamagi-quake2`

Near-dup paths: 561
DIFFS docs generated: 513
