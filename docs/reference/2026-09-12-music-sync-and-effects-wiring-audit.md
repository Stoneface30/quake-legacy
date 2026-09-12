# Music sync, effects, transitions, animation — what the delivered videos actually run

*2026-09-12. Read-only audit of `creative_suite/engine/`, spot-checked by hand
against the cited lines. "Implemented" here means: the code exists, it is
called on the path that produces a delivered video, and a test or an output
proves it. This project has shipped rules whose code never ran before
(effects fired only on hand-written overrides; 8,637 renders never packed).*

## Which path delivers

The root scripts `hl_series.py` / `hl_generate.py` / `hl_all.py` / `hl_batch.py`
run `creative_suite.engine.render_highlight`:
`build()` (`render_highlight.py:1528`) → `render_frag` (`:925`) → `_xfade_chain`
(`:1264`) → `mux_music` (`:1363`). That produced `output/Part4..9_highlight*.mp4`,
**all dated 2026-08-30**.

`render_part_v6.py` is where most of the P1-* sync machinery lives. It is still
reachable from the Cinema Suite REBUILD job (`creative_suite/api/_rebuild_job.py:60`),
but nothing has shipped from it since Parts 4–6 on 2026-08-28.

**Every delivered mp4 predates the current code.** `render_highlight.py` changed
on 08-31 (×2), 09-01 (×2) and 09-08 (see `git log -- creative_suite/engine/render_highlight.py`).

## Verdicts

| Item | Delivered path does | Verdict |
|---|---|---|
| P1-G fixed music level | `MUSIC_VOLUME = 1.24` (`:95`), `amix normalize=0`, 1 s in / 4 s out, peak limiting only; no sidechain | **Wired and proven** |
| P1-S seams, not durations | Lands a slow-mo on a beat by solving its rate (`speed_ramp.accent_rate_for_landing`, called `:1662`, `:1676`); no clip is shortened | Wired, unproven (only accented clips ≤ 7 s) |
| P1-Z recognised game event | Peak = `peak_guard.find_peak_guarded` (`:710`, `:726`, `:1585`), a loudness envelope — the method P1-Z replaced. `recognize_game_events` is called only by `render_part_v6.py` | **Not wired** |
| P1-CC flow-driven cuts | Order by selection/queue; `plan_flow_cuts_v2` only in v6 | **Not wired** |
| P1-AA / P1-R three tracks, phrase cuts, BPM stretch | Two songs, 6 s crossfade, hard cut at body length + 4 s fade | Superseded by the 08-29 "two songs" direction; the rule text is stale |
| P1-BB split graphs, drift gate ≤ 40 ms | PCM intermediates and CFR yes; video+audio in one graph; **no drift audit** in any `hl_*.py` (grep: not found). The only audits are v6's from 08-28 | **Partial — the gate never runs on delivered videos** |
| Song-is-the-score / ChoreographyPlan / temporal solver | Called by proofs and sheets only; not by `render_highlight.py` or `hl_*.py` | **Not wired** |
| +75 ms audible lag / −15 ms hero delta | Constants exist in the solver modules; no offset is applied when landing on a beat | **Not wired** |
| P1-Q-AUTO every frag ramped | Slow-mo on every 3rd clip when it is T1 (`SLOWMO_EVERY_N = 3`, `:170`) plus clips ≤ 7 s; speed-up removed | Partial; contradicts the rule |
| P1-Q ±0.8 s window, ramps, audio A/B/C, confidence ≥ 0.55 | `accent_window` (`:913`) −0.70/+1.10 s, hard rate step, atempo only, no confidence gate | Not wired (simpler variant delivered) |
| P1-H 0.40 s seam xfade | `XFADE_S = 0.35` (`:122`); groups of 6 joined by `concat_copy` (`:1789`) — every 6th seam is a hard cut | Wired, deviates |
| P1-I effect uses structure + beats | Effect choice is cadence + clip length; music only tunes the rate | Partial |
| P1-K FP + one slow FL | FL is a natural-speed picture-in-picture inset (`FL_LEADS_IN = False`, `:158`) | Superseded; rule text stale |
| P1-N / P1-Y / P1-C intro | One generated 8 s opener (`pantheon_intro.render_intro`); `title_card.render_title_card` not called; IntroPart2 only behind an env var | Superseded / partial |
| 4 s countdown lead-in | `review_proxy.py:86` `COUNTDOWN_LEAD_MS = 4000`, review proxies only | Wired for review, **not** for delivered Parts |
| Effect templates / Pandora atlas / transitions DB | Feed the choreography/temporal proofs; `pandora` has no importers | Not wired |
| HUD animation (`engine/pantheon/hud.py`) | Only `doctor.py` touches it | Not wired |
| Presenter / character animation | PANTHEON synthetic-demo path only | Wired there, not in Parts |

## Contradictions between CLAUDE.md and the code

- **Ducking:** P1-AA still says "sidechain-duck ~6 dB"; P1-G v6 bans it. The delivered path doesn't duck; `render_part_v6.py:1004–1009` still does.
- **P1-R/P1-AA** (three tracks, full songs, phrase boundaries) vs two crossfaded songs cut at body length.
- **P1-Q-AUTO** "every frag" vs every 3rd T1 clip plus short clips.
- **P1-Z** recognised events vs loudness-envelope peak.
- **P1-BB** split graphs + drift gate vs a combined graph and no gate.
- **P1-H** 0.40 s vs 0.35 s with hard cuts at group joins.
- **P1-K** FL slow contrast vs natural-speed inset.
- **P1-N/P1-Y** PANTHEON 5 s + 8 s title card vs one generated 8 s opener.

## Human eye-checks

1. `output/Part4_highlight_ep2.mp4` 0:00–0:10 — a generated opener, no IntroPart2/title card; music steady through the first frags, no pumping.
2. Same file, first 1–2 minutes, the 6th/7th segment join — a 0.35 s dissolve, or a hard cut where groups meet?
3. A short (≤ 7 s) T1 clip in `Part5_highlight_ep6.mp4` — does the slow-mo end land on a kick/downbeat? The run log's `[lock] ... lands on <kind> at <t>s` line gives the timestamp.
4. `Part7_highlight_ep5.mp4` about halfway — the song change is a 6 s blend, not beat-matched (expected).
5. **Re-render one episode with the current code** before trusting any of the above: every delivered file predates the 09-01 changes.
