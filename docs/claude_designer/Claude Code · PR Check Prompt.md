# Claude Code · PR Check Prompt
## QUAKE LEGACY — Branch Audit Protocol

---

## Purpose

Full audit before merging `docs/readme-and-screenshots` → `main`.
Execute phases in order. **STOP at PHASE 4 and wait for user approval.**

---

## PHASE 1 — Code Audit

### 1A. Security scan — innerHTML with untrusted data (Rule UI-1)
- Grep all `*.js` in `creative_suite/frontend/` for `.innerHTML`
- Every hit: verify input is static/escaped or replaced with `textContent` / `createElement`
- Flag any hit that assigns user-supplied or API-sourced content via innerHTML

### 1B. Store contract (Rule UI-2)
- Every panel JS must: store unsub in `_unsub`, call `_unsub()` in `unmount()`
- Check all `*-clips.js`, `*-edit.js`, `lab-*.js`, `creative-*.js` for subscribe/unsubscribe pairs

### 1C. Public-data safety (CLAUDE.md — Public Repo Rules)
- Grep for player names, Steam IDs, real nicknames in all committed `.txt` clip lists
- Verify `part01.txt`–`part12.txt` use only anonymous filenames

### 1D. API contract audit
- `GET /api/studio/parts` — returns `t1_count`, `t2_count`, `t3_count`
- `GET /api/studio/part/{n}/clips` — returns `{part, clips, has_saved_order}`
- `PUT /api/studio/part/{n}/clips` — accepts `ClipOrderBody`, writes `_order.json` + `.txt`
- `GET /api/phase1/music/tracks` — returns list with optional `bpm` field
- `GET /api/phase1/parts/{n}/rebuild` — exists and returns SSE or JSON

### 1E. Pydantic models
- `ClipOrderBody` and `_ClipItem` in `studio.py` — verify `model_dump()` works (Pydantic v2)

### 1F. Python import safety
- `creative_suite/api/__init__.py` must be empty (no `from __future__ import annotations`)
- `creative_suite/config.py` — `quake_video_dir` property exists

---

## PHASE 2 — Bug Fixes

For each issue found in Phase 1:
- Fix inline, commit immediately with `fix(scope): description`
- Re-run the relevant grep/check before moving on

---

## PHASE 3 — Documentation

- Verify `docs/claude_designer/` contains all 6 design files
- Verify `README.md` at repo root is the 2026-styled version with PANTHEON branding
- Update `CLAUDE.md` with any new rules discovered during audit
- Confirm `creative_suite/engine/clip_lists/part01.txt` through `part03.txt` exist

---

## PHASE 4 — Validation Gate (STOP — wait for user approval)

Present a summary report:
```
PHASE 1 findings: N issues (N critical, N minor)
PHASE 2 fixes applied: N commits
PHASE 3 docs: OK / gaps
```

**Do NOT:**
- Create or update any PR
- Push any new commits to origin
- Run `gh pr create` or `gh pr merge`

Wait for user to type "APPROVED — proceed to PR" before Phase 4 actions.

---

## PHASE 4 (after approval) — PR Actions

```bash
git push origin docs/readme-and-screenshots
gh pr create --title "feat(studio): CLIPS + EDIT two-tab redesign, all-tier browser, drag-and-drop, music matching" \
  --body "$(cat <<'EOF'
## Summary
- STUDIO nav reduced to 2 tabs: CLIPS and EDIT
- CLIPS: parts 1-12, all T1/T2/T3 clips, drag-and-drop reorder, BPM music matching
- EDIT: consolidated sub-tab canvas (PREVIEW · TIMELINE · AUDIO · FX GRAPH · INSPECTOR)
- Clip manifests added for parts 1-3
- All-tier scanner in studio.py (T2/T3 dirs from quake_video_dir)
- PUT /api/studio/part/{n}/clips — saves reorder to _order.json + rewrites .txt

## Test Plan
- [ ] Navigate to http://localhost:8765/studio
- [ ] Verify CLIPS tab shows all 12 parts
- [ ] Expand Part 4 — verify T1/T2/T3 clips load
- [ ] Drag a clip row to reorder — verify debounced save fires
- [ ] Click a clip → music panel opens with BPM proposals
- [ ] EDIT tab → PREVIEW sub-tab loads
- [ ] LAB and CREATIVE modes unchanged

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```
