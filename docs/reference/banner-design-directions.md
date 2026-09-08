# PANTHEON Banner Design Directions
### In-game ad-board texture replacement — QUAKE TRIBUTE series

*Research doc, 2026-08-31. Feeds programmatic PIL generation of 20 banner textures for the QL
advertisement surfaces (`ad1x1` 256x256, `ad2x1` 512x256, `ad4x1` 1024x256, `ad8x1` 2048x256).
No player names beyond the user's own brand (`pTn.Tr4sH`) may appear — public-repo rule applies.*

---

## 1. Research summary

### 1.1 Quake Live's own ad system (what we are replacing)
- QL launched partially funded by **real in-game ads** (IGA Worldwide contract); after the
  ZeniMax acquisition the boards switched to **in-house Bethesda promos** (RAGE, Brink, id
  titles). So era-correct 2010-2013 footage *already has* branded boards — replacing them
  with series branding is period-authentic, not anachronistic.
- Default ad content files: `ad1x1` (256x256), `ad2x1` (512x256), `ad4x1` (1024x256),
  `ad8x1` — baseline JPEG (progressive JPEG **crashes clients**), shaders in `/scripts`.
  `ad2x1` is the most common board in maps.
- Boards sit on walls in dark industrial/gothic arenas, frequently viewed at **grazing
  angles**, small on screen, under colored dynamic light (rocket orange, quad blue).

### 1.2 Fragmovie / esports precedent
- Classic fragmovie productions (Get Quaked 3 by Robo-K1ll & Fei / Twilight Pictures,
  Annihilation, the defrag texture-remaster tradition typified by phantazm11's high-res
  packs) treat the arena itself as a canvas: retextured surfaces, production idents, and
  tongue-in-cheek fake-sponsor gags are a beloved trope of the genre.
- Modern esports (CS Majors, VCT) brand in-game space with **strict placement discipline**:
  one logo per surface, enforced minimum sizes, central lockups, high-contrast flat marks —
  the Riot model ("premium media product") is the one to copy, not the CS "racing suit"
  logo-soup model.

### 1.3 Billboard readability science (applies directly — ad boards ARE billboards)
- **One focal point per board.** Viewers process a single message; 7 words max, ideally 1-3.
- **Stark contrast is the cornerstone**: light-on-dark or dark-on-light with large luminance
  gap. Gold `#d4af37` on near-black passes; gold on mid-grey does not.
- **Type scale**: 1 in letter height per 30 ft viewing distance → in texture terms, hero text
  should occupy **55-75% of board height** on 2:1/4:1/8:1, and **≥35%** on 1:1.
- Bold sans (Arial-class) wins at distance; generous letterspacing; avoid thin serifs at
  small sizes — reserve serif/Trajan-style for the largest lockups only.
- Mixed case reads faster, but for 1-3 word hero lines ALL-CAPS display type is standard.

### 1.4 The PANTHEON motif (greco-roman x Quake gothic)
- **Trajan lineage**: Roman square capitals (capitalis monumentalis, Trajan's Column, 113 AD)
  → Adobe Trajan → the "importance + gravitas" typeface of every epic movie poster. This is
  exactly the register a temple-logo brand wants. Windows-available stand-ins: **Palatino
  Linotype** (all-caps, wide tracking), **Constantia** or **Georgia** caps.
- Compatible motifs that survive low resolution: gold-leaf on black, laurel wreaths,
  column silhouettes, pediment triangles, engraved plaque bevels, weathered bronze,
  war-banner cloth with a single emblem. All are **big-shape** motifs — good at 256px tall.
- Quake's own aesthetic (rusted metal, gothic stone, hazard chevrons) blends naturally with
  "ruined temple" — weathering/grunge overlays unify the two.

---

## 2. Global rules for every banner (bake into the PIL generator)

1. **Contrast floor**: hero element vs background luminance ratio ≥ 7:1.
2. **Safe margin**: 8% of the short edge on all sides — boards clip at edges on some brushes.
3. **One message per board.** Logo OR wordmark OR stat OR gag — never two.
4. **Hero height**: text cap-height ≥ 55% of board height (≥ 35% on 1:1).
5. **Grazing-angle test**: design must survive 4:1 horizontal squash. Prefer wide tracking,
   avoid fine vertical detail.
6. **Palette anchors**: gold `#d4af37`, silver `#c0c0c8`, deep blue `#243e7a`,
   near-black `#0d0d10`, bone `#e8e2d0`, rust accent `#8a3b1e`.
7. **Finish pass**: subtle vignette + 4-6% noise/grunge so flat fills don't shimmer in
   motion; keep JPEG baseline, quality ~92.
8. **Fonts (Windows-available only)**: Arial Black, Impact, Bahnschrift (SemiBold Condensed =
   Bebas-like), Franklin Gothic Medium, Georgia, Palatino Linotype, Constantia.

---

## 3. The eight directions

### D1 — GOLD-LEAF MARBLE (flagship brand)
- **Palette**: black marble `#0d0d10` w/ faint grey veining `#2a2a30`; gold `#d4af37`
  hero + hairline `#f0d98c` highlight edge.
- **Type**: Palatino Linotype ALL CAPS, tracking +12%, fake-engrave (1px dark top inset +
  1px light bottom offset).
- **Layouts** — 1:1: temple logo centered, name below at 12% height · 2:1: logo left third,
  `PANTHEON` right two-thirds · 4:1: `PANTHEON` full-width, laurel sprigs flanking ·
  8:1: `P A N T H E O N` extreme tracking, tiny temple glyph as the A crossbar or centered divider.
- **Content fits**: logo, `PANTHEON`, `QUAKE TRIBUTE`.

### D2 — WEATHERED WAR BANNER (cloth)
- **Palette**: deep blue cloth `#243e7a` shaded to `#16264c`; bone emblem `#e8e2d0`;
  gold fringe `#d4af37`; frayed dark edges.
- **Type**: Bahnschrift SemiBold Condensed caps; emblem dominates, text secondary.
- **Layouts** — 1:1: hanging-banner illusion (darkened top rod, notched bottom), pTn shield
  emblem · 2:1: emblem left, `pTn.Tr4sH` right · 4:1/8:1: horizontal pennant strip, emblem
  center, `pTn` repeated small at ends.
- **Content fits**: `pTn.Tr4sH`, clan shield, `QUAKE TRIBUTE`.

### D3 — ENGRAVED BRONZE PLAQUE (archive/honors)
- **Palette**: bronze `#6e5423` → `#a8803c` vertical gradient, patina spots `#3f5a4a`,
  raised border bevel; lettering punched dark `#241a08`.
- **Type**: Georgia bold caps for hero, Franklin Gothic for small line.
- **Layouts** — 1:1: laurel ring + single stat number · 2:1: stat hero + label line ·
  4:1: `EST. 2010 — CLAN ARENA` single line · 8:1: honors strip `TR4SH · #39 WORLD CA · ELO 2326`.
- **Content fits**: archive stats (`#39 WORLD CA`, `ELO 2326`), `EST. 2010`.

### D4 — NEON ARENA SPONSOR (esports broadcast)
- **Palette**: near-black `#0b0d14`; electric blue glow `#3f6fd8` (deep-blue brand pushed to
  neon); silver `#dfe3ea` text; thin gold keyline.
- **Type**: Bahnschrift Condensed caps, glow = 3 blurred copies underneath.
- **Layouts** — 1:1: glowing temple outline only · 2:1: `PANTHEON` + thin rule +
  `OFFICIAL ARENA PARTNER` micro-line · 4:1: wordmark with left/right glow rules ·
  8:1: broadcast ticker style: `PANTHEON ▸ QUAKE TRIBUTE ▸ PANTHEON ▸`.
- **Content fits**: logo, `QUAKE TRIBUTE`, fake "official partner" lines.

### D5 — MINIMAL MONOGRAM (Riot-style discipline)
- **Palette**: flat silver-grey `#c0c0c8` field OR flat `#0d0d10` field; single gold mark.
- **Type**: none, or 3-letter `pTn` in Arial Black.
- **Layouts** — 1:1: giant centered `P` or temple glyph, nothing else · 2:1: glyph + `pTn` ·
  4:1/8:1: lone glyph centered in vast negative space (confidence read).
- **Content fits**: logo, `pTn`. The "expensive" board — use where boards are tiny/far.

### D6 — FAKE-SPONSOR PARODY (the fragmovie gag trope)
- **Palette**: loud retail — hazard yellow `#e8c020` + black, or red `#b02318` + bone;
  deliberately clashes with D1-D5 so the joke lands.
- **Type**: Impact or Arial Black, crammed retail-ad energy, starburst allowed (only
  direction where clutter is permitted — still one gag per board).
- **Layouts** — 1:1: product-badge parody (`LG™ — 40% ACCURACY GUARANTEED`) · 2:1:
  `EAT ROCKETS` w/ tiny legal-line gibberish · 4:1: `GAUNTLET — WHEN YOU'RE OUT OF AMMO AND DIGNITY` ·
  8:1: highway-billboard one-liner `YOU HAVE TAKEN THE LEAD*  *briefly`.
- **Content fits**: parody sponsor lines only. Cap at ~4 of 20 boards so the joke stays rare.

### D7 — STATS BOARD (arena scoreboard)
- **Palette**: gunmetal `#1a1d22` panel, silver grid hairlines `#3a3f48`, amber-gold LED
  digits `#e6b43c`, blue header bar `#243e7a`.
- **Type**: Bahnschrift (tabular feel) digits huge; Franklin Gothic labels.
- **Layouts** — 1:1: single number hero (`2326`) + micro label (`ELO`) · 2:1: two-cell
  stat (`#39 | WORLD CA`) · 4:1: three-cell strip (`FRAGS 10K+ · MAPS 40 · SEASONS 2010-13`) ·
  8:1: full ticker of era stats.
- **Content fits**: all archive stats; era callouts.

### D8 — MAP-CALLOUT PLATE (wayfinding)
- **Palette**: bone `#e8e2d0` plate, deep blue `#243e7a` text, gold pinstripe border,
  corner rivets — industrial signage meets temple museum label.
- **Type**: Franklin Gothic Medium caps, tight and utilitarian; small `PANTHEON ARCHIVE`
  eyebrow line in gold.
- **Layouts** — 1:1: map-number roman numeral (`XII`) · 2:1: `ASYLUM` plate · 4:1:
  `CAMPGROUNDS — HALLOWED GROUND` · 8:1: `THE PANTHEON ARCHIVE · 6,465 DEMOS · 2010-2013`.
- **Content fits**: map names (use only QL's public map names — safe), archive framing.

---

## 4. The 20 banner specs (programmatic build list)

Format: `id · direction · aspect · content · fg-on-bg`.
Aspect population mirrors in-map frequency (2:1 most common).

| # | ID | Dir | Aspect | Content line(s) | Colors (fg on bg) |
|---|----|-----|--------|-----------------|-------------------|
| 1 | `pan_logo_1x1` | D1 | 1:1 | Temple logo, `PANTHEON` footer | `#d4af37` on `#0d0d10` marble |
| 2 | `pan_word_2x1` | D1 | 2:1 | logo + `PANTHEON` | `#d4af37`/`#f0d98c` on `#0d0d10` |
| 3 | `pan_word_4x1` | D1 | 4:1 | `PANTHEON` + laurel flanks | `#d4af37` on `#0d0d10` |
| 4 | `pan_track_8x1` | D1 | 8:1 | `P A N T H E O N` tracked | `#d4af37` on `#0d0d10` |
| 5 | `tribute_2x1` | D1 | 2:1 | `QUAKE TRIBUTE` two-line, gold rule | `#e8e2d0`+`#d4af37` on `#0d0d10` |
| 6 | `banner_ptn_1x1` | D2 | 1:1 | pTn shield on hanging cloth | `#e8e2d0` on `#243e7a` |
| 7 | `banner_trash_2x1` | D2 | 2:1 | shield + `pTn.Tr4sH` | `#e8e2d0`/`#d4af37` on `#243e7a` |
| 8 | `banner_pennant_4x1` | D2 | 4:1 | pennant strip, center emblem | `#d4af37` on `#243e7a` |
| 9 | `plaque_est_4x1` | D3 | 4:1 | `EST. 2010 — CLAN ARENA` | `#241a08` punched in bronze `#a8803c` |
| 10 | `plaque_honors_8x1` | D3 | 8:1 | `TR4SH · #39 WORLD CA · ELO 2326` | `#241a08` in bronze, patina |
| 11 | `plaque_laurel_1x1` | D3 | 1:1 | laurel ring + `39` | `#241a08` in bronze |
| 12 | `neon_glyph_1x1` | D4 | 1:1 | glowing temple outline | `#3f6fd8` glow on `#0b0d14` |
| 13 | `neon_partner_2x1` | D4 | 2:1 | `PANTHEON` + `OFFICIAL ARENA PARTNER` | `#dfe3ea`/`#3f6fd8` on `#0b0d14` |
| 14 | `neon_ticker_8x1` | D4 | 8:1 | `PANTHEON ▸ QUAKE TRIBUTE ▸ …` | `#dfe3ea` on `#0b0d14`, gold keyline |
| 15 | `mono_glyph_2x1` | D5 | 2:1 | lone gold temple glyph, no text | `#d4af37` on `#c0c0c8` |
| 16 | `mono_ptn_1x1` | D5 | 1:1 | giant `pTn` | `#d4af37` on `#0d0d10` |
| 17 | `parody_rockets_2x1` | D6 | 2:1 | `EAT ROCKETS` + micro legal line | `#0d0d10` on `#e8c020` |
| 18 | `parody_lg_1x1` | D6 | 1:1 | `LG™ 40% ACCURACY GUARANTEED` badge | `#e8e2d0` on `#b02318` |
| 19 | `stats_elo_2x1` | D7 | 2:1 | `ELO 2326` two-cell | `#e6b43c` on `#1a1d22`, blue header |
| 20 | `callout_archive_8x1` | D8 | 8:1 | `THE PANTHEON ARCHIVE · 6,465 DEMOS · 2010-2013` | `#243e7a` on `#e8e2d0` |

Coverage check: D1 x5, D2 x3, D3 x3, D4 x3, D5 x2, D6 x2, D7 x1, D8 x1 — flagship brand
dominates (correct per esports placement discipline), parody stays rare (correct per trope).

Generator notes:
- Render at 2x target (e.g. 1024x512 for `ad2x1`) then downsample LANCZOS — crisper edges.
- Export baseline JPEG q92 (QL crashes on progressive JPEG).
- One shared `draw_finish(img)` pass: vignette 12%, mono noise 5%, 1px inner border darken.
- Engrave effect = text drawn 3x: `#000` at (0,-2), highlight at (0,+2), fill on top.

---

## 5. References consulted

- Quake Live ad system & history (IGA Worldwide → Bethesda in-house boards): [Wikipedia — Quake Live](https://en.wikipedia.org/wiki/Quake_Live)
- Ad texture specs (`ad1x1`..`ad8x1` sizes, baseline-JPEG requirement, shader location): [Steam Guide — Custom banners for your Quake Live server](https://steamcommunity.com/sharedfiles/filedetails/?id=3271868847) (specs via search excerpt; page itself rate-limited during fetch), [Quake3World — QL advertisement lump format](https://www.quake3world.com/forum/viewtopic.php?t=53740) (403 on direct fetch; lump existence confirmed via search)
- Fragmovie lineage: [Get Quaked 3 — IGMDB](https://www.igmdb.org/?m=51), [ESR — Top Quake frag/defrag movies thread](https://www.esreality.com/post/2775835/your-top-3-quake-frag-defrag-movies/), [Internet Archive — Quake 3 Arena Frag Videos](https://archive.org/details/quake3arenafragvideos)
- id's ad-parody heritage (absurdist Quake marketing register for D6): [Kotaku — "Quake Is Good For You"](https://kotaku.com/quake-is-good-for-you-1609654451), [Bloody Disgusting — 90s Quake ads](https://bloody-disgusting.com/news/3304550/90s-quake-ads-hilariously-misleading/)
- Esports in-game branding discipline (Riot centralized vs CS logo-soup): [Esports Charts — Valorant vs CS sponsorship gap](https://escharts.com/news/why-only-30-valorant-teams-carry-primary-sponsor-their-jerseys), [Esports Charts — sponsor media value at CS Majors](https://escharts.com/news/how-brands-captured-media-value-during-starladder-budapest-major-final-day)
- Billboard readability (contrast, 1-in-per-30-ft, one focal point, ≤7 words): [Blip — How to Design a Billboard](https://www.blipbillboards.com/blog/how-to-design-a-billboard/), [Effortless Outdoor Media — Billboard readability science](https://effortlessoutdoormedia.com/billboard-readability-science-behind/), [Trailhead Media — Billboard design principles](https://trailheadmedia.com/billboard-design-principles/), [OBU — Billboard design principles 2024](https://www.obuniversity.com/articles/essential-principles-for-crafting-impactful-billboard-designs-in-2024)
- Trajan / Roman capitals gravitas register: [Wikipedia — Trajan (typeface)](https://en.wikipedia.org/wiki/Trajan_(typeface)), [Kottke — How Trajan took over movie posters](https://kottke.org/18/07/how-trajan-became-the-go-to-typeface-for-movie-posters)
