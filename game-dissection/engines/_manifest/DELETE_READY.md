# Phase A1 Canonical Tree — Ready for Deletion Checkpoint

Canonical tree is built at `game-dissection/engines/_canonical/` plus
per-tree variant dirs at `game-dissection/engines/<tree>/`.

## Statistics

- Source trees size: **722,611,232** bytes (722.6 MB)
- New canonical size: **550,777,846** bytes (550.8 MB)
- Variant files size: **30,925,700** bytes (30.9 MB)
- New tree total: **581,703,546** bytes (581.7 MB)
- **Bytes freed by deletion: 140,907,686 (140.9 MB)**

## To complete deletion (user must approve)

```bash
# Verify canonical tree is good first:
ls G:/QUAKE_LEGACY/game-dissection/engines/_canonical/
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
