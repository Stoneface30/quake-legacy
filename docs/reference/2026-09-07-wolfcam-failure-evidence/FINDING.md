# First failing stage (evidence, not inference)

The client exits rc=1 ~3 s in, on the hidden desktop AND in a normal window,
with staging rebuilt from canonical, for EVERY profile including two that were
never modified (TR4SH_REVIEW_V2, TR4SH_GAMEPLAY_MASTER_V2).

## Where it actually stops

qconsole.log ends while resolving MME post-process shaders:

    scripts/posteffect.vs ->
    scripts/colorcorrect.fs ->
    scripts/blurhoriz.fs ->
    scripts/blurvertical.fs ->
    scripts/brightpass.fs ->
    scripts/combine.fs ->
    scripts/downsample1.fs ->

Each name is followed by "->" and nothing. No `scripts/*.fs` or `*.vs` exists
anywhere in staging (0 loose files); `wc-glsl.pk3` contains 5 files, all under
`glsl/` (cameraline.vs/fs, ql-compat.vs, ql-compat-multi.vs). The
post-process shader set is absent from this install.

Earlier in the same log, before AA was set to 0:

    anti-alias samples: 2
    InitFrameBufferAndRenderBuffer  multisample framebuffer error: 0x8cdd
    unsupported

0x8cdd is GL_FRAMEBUFFER_UNSUPPORTED. That error stopped once AA was 0; the
rc=1 exit did not.

## What is NOT established

- That `Stop-Process -Force` caused this. It is the most conspicuous global
  action taken before the failure, and that is not evidence.
- That the GPU driver is unhealthy. The doctor's hidden-desktop probe passes,
  GL_RENDERER reports the RTX 5060 Ti, and extensions enumerate normally.
- That the missing shaders are the cause rather than a symptom: captures
  succeeded earlier from the same install, so either these shaders were not
  requested then, or their absence is tolerated and the exit is later still.

## Next step for track A

After a controlled reboot, one capture with the known-good REVIEW profile,
clean staging, no AA/resolution overrides. If it still fails, instrument the
renderer init path rather than changing cvars.
