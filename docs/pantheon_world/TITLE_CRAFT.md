# In-engine titles — what the craft actually does, with sources

Researched from primary sources: id Software's released Q3A code and shader
manual, q3mme's and WolfcamQL's own repositories and shipped shaders, ESReality's
28-part moviemaking interview series, and myT's shader-tricks article.

## The honest baseline

**Post-production titling is what the classics did.** Across the ESR
moviemaking interview corpus, Sony Vegas is named by 18 of 28 makers and After
Effects by 15 of 28; only 8 of 28 name any 3-D package at all. F51 (EDGE):
*"After Effects. That's the place where movie starts looking like a movie."*

Building titles **in engine** is the minority path — the one Kabcorp took
(*"Quake III Movie Maker Edition for ALL editing. Yes, all effects are made
in-game"*, plus a purpose-built custom HUD) and the one stupid fresh argues
for (*"I tend to make content look like its a part of the game"*). That is the
path PANTHEON is on, deliberately. It is not the common one, and saying so
keeps the choice honest.

## The canonical in-engine 3-D logo — id's own, and we already have it

Quake III's main menu draws its own banner as an **MD3 rendered into a
sub-rectangle of the screen with `RDF_NOWORLDMODEL`** — no map loaded at all —
with a slow sine yaw. From `code/q3_ui/ui_menu.c::Main_MenuDraw()`:

```c
refdef.rdflags = RDF_NOWORLDMODEL;
adjust = 5.0 * sin( (float)uis.realtime / 5000 );
VectorSet( angles, 0, 180 + adjust, 0 );
ent.hModel = s_main.bannerModel;          // models/mapobjects/banner/banner5.md3
ent.renderfx = RF_LIGHTING_ORIGIN | RF_NOSHADOW;
trap_R_AddRefEntityToScene( &ent );
trap_R_RenderScene( &refdef );
```

**Our host already has this**: `--no-world` is the same `RDF_NOWORLDMODEL`
path, and `prop` already adds an MD3 to the scene. A PANTHEON title plate on a
clean background, with no map, is a flag away. The ±5° sine sway is the
motion id itself used, and it is one line.

## Shader recipes worth stealing, verbatim from shipped files

**Chrome / rim, two lines** — q3mme's `mme.shader`, `mme_df_unavailableItem`:

```
{ map textures/effects/quadmap2.tga
  blendfunc GL_ONE GL_ONE
  tcGen environment }
```

**Text with a real drop shadow** — also `mme.shader`. The shadow is a
*multiply-darken* pass, not a black copy, and `clampmap` + `alphafunc GT0` are
what keep glyph edges hard:

```
mme/menu/scrollFontShadow
{	cull none
	{ clampmap menu/art/font1_prop.tga
	  depthwrite
	  alphafunc GT0
	  blendfunc gl_zero gl_src_color
	  alphagen vertex
	  rgbgen const ( 0.5 0.5 0.5 ) } }
```

**Gloss over diffuse** — a posted ..::LvL shader; `alphaGen lightingSpecular`
is the specular term, the env stage is the highlight:

```
{ map <diffuse>.tga   rgbGen identity   alphaGen lightingSpecular }
{ map <gloss>.tga     blendfunc add     rgbGen identity   tcGen environment }
```

**Additive glow that the FX system can drive** — `rgbGen vertex` /
`alphaGen vertex` let per-vertex colour animate the pass; `cull none` for a
flat card.

**myT's prime-number desync** — give each animated layer a period that is
awkwardly non-round so the layers only realign after `d1 x d2` seconds and the
loop stops being visible:
`rgbGen wave sin 0.75 0.25 0 0.14` beside
`tcMod turb 0 0.1 0 0.183076923...`.

**Interpolated animMap** — cross-fade frame N and N+1 with complementary
sawtooths for smooth sprite animation:
`rgbGen wave inverseSawtooth 0 1 0 16` on one stage,
`rgbGen wave sawtooth 0 1 0 16` on the next.

## Keywords, from id's shader manual

`tcGen environment` "make this object environment mapped" ·
`rgbGen wave <func> <base> <amp> <phase> <freq>` ·
`rgbGen entity` "colors are grabbed from the entity's modulate field" — this
is how code fades a logo per frame ·
`rgbGen lightingDiffuse` "used for dynamic models" — **model shaders only** ·
`blendFunc add` = `GL_ONE GL_ONE` · `blend` = `GL_SRC_ALPHA
GL_ONE_MINUS_SRC_ALPHA` · `filter` always darkens ·
`tcMod scroll <s> <t>` in "textures per second" · `tcMod rotate <deg/sec>`,
positive is clockwise · `tcMod stretch` · `tcMod turb` "back and forth
churning" · `animMap <freq> <1..8 textures>` · `depthWrite` matters when
layering additive passes over 3-D type.

## Two capabilities we are not using yet

* **WolfcamQL is the real in-engine TEXT engine** — `/centerprint`, TrueType
  via libfreetype2 (`font "myfonts/arial.ttf" 12`), `/loadmenu` with
  `menuDef`/`itemDef`, per-item `run` scripts evaluated every screen draw,
  `realtime`/`gametime` in expressions, `textExt` string interpolation, and
  full `cg_drawCenterPrint*` typography. The README's own example is an
  animated fading title. This is a **WolfcamQL** capability, not a q3mme one.
* **Chroma key and depth are supported in both** — `mme_skyKey`,
  `mme_worldShader`, `r_singleShader` + `r_fastSkyColor`, `mme_saveDepth` — so
  in-engine elements can be keyed into post-production typography rather than
  choosing one path or the other.

## Flagged by the research as unverified

No published fragmovie was found that used `mov_hudOverlay` for a title card
(the capability is documented; the practice is not). Multispec repurposed for
titles: not found. rEnk's *Edge of the Earth* is confirmed to use custom q3mme
fx-scripts and to have an intro, but **not** that its title graphics were
in-engine. And several movie names in circulation did not survive verification
at all.

Sources: id's `ui_menu.c` and Q3A Shader Manual (icculus/Stanford mirrors) ·
q3mme `trunk/files/scripts/mme.shader`, `cvars.txt`, `fxScript.txt` ·
WolfcamQL `README-wolfcam.txt` · ESReality moviemaking interview series
(28 parts) · myT, "Q3 shader tricks", 2024.
