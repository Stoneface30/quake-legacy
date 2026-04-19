// creative_suite/frontend/panel-levels.js

export function renderLevels({ barsEl, canvas, gateEl, levels, syncAudit }) {
  barsEl.replaceChildren();
  gateEl.replaceChildren();
  if (!levels) {
    const p = document.createElement("p");
    p.className = "hint";
    p.textContent = "No levels.json for this part.";
    barsEl.append(p);
  } else {
    const { music_integrated_lufs, game_integrated_lufs, delta_lu, pass } = levels;
    barsEl.append(
      makeBar("Music (LUFS)", music_integrated_lufs, -36, 0),
      makeBar("Game (LUFS)", game_integrated_lufs, -36, 0),
    );
    const led = document.createElement("span");
    led.className = "gate-led";
    led.textContent = pass ? "✓ PASS" : "✗ FAIL";
    led.style.color = pass ? "#10b981" : "#ef4444";
    const pill = document.createElement("span");
    pill.className = "gate-delta";
    pill.textContent = `Δ ${(delta_lu ?? 0).toFixed(1)} LU (target ≥ 12 LU)`;
    gateEl.append(led, pill);
  }
  drawDrift(canvas, syncAudit);
}

function makeBar(label, value, min, max) {
  const row = document.createElement("div");
  row.className = "lufs-row";
  const lbl = document.createElement("span");
  lbl.className = "lufs-label";
  lbl.textContent = label;
  const bar = document.createElement("div");
  bar.className = "lufs-bar";
  const fill = document.createElement("div");
  fill.className = "lufs-fill";
  const pct = value == null ? 0 : Math.max(0, Math.min(1, (value - min) / (max - min)));
  fill.style.width = `${pct * 100}%`;
  bar.append(fill);
  const num = document.createElement("span");
  num.className = "lufs-num";
  num.textContent = value == null ? "—" : value.toFixed(1);
  row.append(lbl, bar, num);
  return row;
}

function drawDrift(canvas, syncAudit) {
  const ctx = canvas.getContext("2d");
  const W = canvas.width, H = canvas.height;
  ctx.fillStyle = "#0b0b0d";
  ctx.fillRect(0, 0, W, H);
  const samples = syncAudit?.samples ?? [];
  if (samples.length === 0) {
    ctx.fillStyle = "#52525b";
    ctx.font = "13px sans-serif";
    ctx.fillText("no sync audit", 12, H / 2);
    return;
  }
  ctx.fillStyle = "#10b98133";
  const bandPx = (40 / 100) * (H / 2);
  ctx.fillRect(0, H/2 - bandPx, W, bandPx * 2);
  ctx.strokeStyle = "#60a5fa";
  ctx.lineWidth = 1.5;
  ctx.beginPath();
  const maxT = samples[samples.length - 1].t || 1;
  for (let i = 0; i < samples.length; i++) {
    const s = samples[i];
    const x = (s.t / maxT) * W;
    const y = H/2 - (s.drift_ms / 100) * (H/2);
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.stroke();
}
