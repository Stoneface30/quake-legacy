# Engine moviemaking commands — what wolfcamql 11.3 actually offers

Read from `engine/engines/_canonical/code/cgame/cg_consolecmds.c` (174 cgame
commands, table at :8413) and `code/client/*.c` (61 client commands). Every
line number below is a source location, not a guess. Nothing here is
capture-verified unless it says so.

The short version: the engine does considerably more of PANTHEON's
vocabulary natively than the capability model credited. Three corrections
came out of this review, each of which had a primitive filed behind work it
does not need.

---

## Corrections this review forced

**`cvarinterp <cvar> <from> <to> <seconds> ['real'|'game']`** (:7244)
The engine ramps a cvar itself, on either the real clock or the game clock.
`clearcvarinterp` cancels. The model assumed the only way to vary a control
was a staircase of scheduled `at` sets sampled every 100 ms; a live cvar can
instead be handed a start, an end and a duration in one command. The
source's own examples are `cvarinterp s_volume 0 0.7 2.0` and
`cvarinterp timescale 0.0001 1.0 6.0 real`.

Only useful for live *continuous* cvars. A latched one would be written
every frame and ignored; a discrete one would be driven through values it
does not have.

**`remapshader <original> <new> [time offset] [keep lightmap]`** (:7437)
Live shader replacement, reverted by `clearremappedshader`. MATERIAL_PULSE
was filed as `AVAILABLE_VIA_ASSETS` needing a pk3 rebuild and a reload. It
is a runtime primitive.

**`timescale` via `cvarinterp ... real`**
A speed ramp that happens *before* capture. Particles, motion blur and
animation follow the ramp instead of a finished frame being resampled after
the fact. The post route (`setpts`) stays useful and stays PARTIAL: it
cannot recover sub-frame detail the capture never had.

---

## Camera

| Command | Source | Note |
|---|---|---|
| `chase <entity> [x y z] [range] [angle]` | :1101, bound :8509 | rides any entity, missiles included. No camera file, no sample budget |
| `freecam`, `freecamsetpos`, `freecamlookatplayer` | | the free camera and its aim |
| `loadcamera` / `playcamera` / `stopcamera` / `savecamera` | :2401 / :2183 | the `.cam10` path we use. Ceiling is 509 points, not 512 |
| `addcamerapoint`, `changecamerapoint`, `deletecamerapoint`, `editcamerapoint`, `selectcamerapoint`, `clearcamerapoints` | | interactive path authoring |
| `q3mmecamera`, `addq3mmecamerapoint`, `loadq3mmecamera`, `saveq3mmecamera`, `playq3mmecamera`, `stopq3mmecamera`, `importq3mmecamera` | | **a second camera format the engine reads natively** |
| `loadq3mmedof`, `saveq3mmedof`, `dof` | | depth of field, q3mme-style |
| `recordpath`, `playpath`, `stopplaypath`, `drawrawpath` | :1714 | record a camera path from live movement and replay it |
| `setviewangles`, `setviewpos`, `viewpos`, `viewunlockpitch`, `viewunlockyaw` | | direct view control |
| `setviewpointmark`, `gotoviewpointmark`, `deleteviewpointmark`, `setcamviewpointmarkhere`, `gotocamviewpoint`, `gotonextcamviewpoint`, `setnextcamviewpointhere` | | named camera bookmarks |
| `startOrbit`, `idcamera`, `stopidcamera`, `ecam`, `ucam`, `camtracesave` | | further camera modes, unread |
| `g_fov`, `demo_scale` | | field of view, demo scaling |

`playcamera` seeks the demo to the path's first point — the shot's head is
lost unless the path covers the guard too. That is already handled in
`director_preview._cover_window` and the reason is worth keeping in view.

## Time

| Command | Note |
|---|---|
| `at <t> <command>` | the scheduler everything else rides on. `cg_enableAtCommands` gates it |
| `clearat`, `listat`, `removeat`, `saveat`, `exec_at_time` | manage the schedule |
| `loop [start] [end]` (:1648) | engine-side replay loop between two server times |
| `setloopstart`, `setloopend` | set the bounds from the current position |
| `nextframe`, `prevframe` | single-frame stepping |
| `seekclock`, `servertime`, `seeknextround`, `seekprevround` | seek by clock and by round |
| `seek`, `seeknext`, `seekprev`, `seekend`, `seekservertime`, `fastforward`, `rewind` | client-side seeking |
| `timescale`, `cl_freezeDemo` | speed and hold |
| `fragforward` (:1659) | jump to the next frag |

## Materials, entities and the world

| Command | Note |
|---|---|
| `remapshader` / `clearremappedshader` | live shader replacement — the material-transform primitive |
| `testreplace` | shader replacement probe |
| `entityfreeze <'clear'\|entity>` (:7055) | freeze ONE entity while the world runs on |
| `entityfilter <'clear'\|'all'\|TYPE\|entity>` | show only chosen entities. **Entities, never BSP geometry** — this is not WORLD_REVEAL |
| `eventfilter`, `listeventfilter` | filter events |
| `adddecal`, `addmirrorsurface` | decals and mirror surfaces |
| `clearscene`, `localents` | scene contents |
| `testmodel`, `testgun` | insert a model or weapon into the scene |
| `nextskin`, `prevskin`, `loadmodels`, `listplayermodels` | model and skin control |

## Effects

`runfx`, `runfxat`, `runfxall`, `fxload`, `fxmath`, `listfxscripts`,
`clearfx`. Already in use: a cue is `at <t> runfx <name> [x y z]`, and the
deferred form is the correct one — `runfxat` snapshots the origin at parse
time, which from `cgamepostinit.cfg` is before the demo has seeked.

## Information on screen

`centerprint <string> [char width|'token']`, `centerroll`,
`resetcenterprinttime`, `echopopup`, `echopopupclear`, `echopopupcvar`,
`clearfragmessage`, `printscores`, `dumpstats`, `wcstats`.

Engine-drawn text is lit and compressed with the frame rather than laid over
it. That is a different look from the compositor route, not a better one,
and it gives less control over type.

## Capture and output

`video`, `stopvideo`, `record`, `stoprecord`, `vid_restart`, `sizeup`,
`sizedown`, `condump`, `music`, `stopmusic`, `play`, `s_stop`.

## Diagnostics worth knowing

`printentitystate`, `printnextentitystate`, `printplayerstate`,
`printentitydistance`, `printdirvector`, `printtime`, `printjumps`,
`printlegsinfo`, `dumpents`, `stopdumpents`, `listentities`,
`configstrings`, `cconfigstrings`, `changeconfigstring`.

`dumpents` and `printentitystate` are how an entity number for `chase` gets
confirmed against what the demo actually contains.

---

## What is still not here

No command hides or restores BSP geometry on a schedule. `entityfilter`
hides entities; the world itself stays. WORLD_REVEAL, WALL_XRAY,
GEOMETRY_REBUILD and MAP_CONSTRUCTION remain without a full route, and
`entityfilter` must not be sold as one.

## Unread

`ecam`, `ucam`, `idcamera`, `startOrbit`, `camtracesave`, `dof`,
`fxmath`, `addmirrorsurface`, `demo_scale`, `cvarinterp` on the game clock
versus the real clock. Each is a real command with an unknown envelope.
