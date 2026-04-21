(function (global) {
  'use strict';
  var PRESETS = [
    {
      name: 'Photoreal Surface',
      positive: 'photorealistic PBR material, 8k ultra detailed, physically based rendering, real-world surface texture, subsurface scattering, micro detail, sharp focus, high dynamic range, professional product photography',
      negative: 'stylized, cartoon, anime, flat shading, low poly, blurry, jpeg artifacts, text, watermark, painting, illustration'
    },
    {
      name: 'Neon Cel-Shade',
      positive: 'cel-shaded neon illustration, vibrant electric colors, black outlines, anime-inspired, glowing edges, high contrast, flat color blocks, cyberpunk palette',
      negative: 'photorealistic, blurry, noisy, muddy colors, dull, washed out, realistic texture'
    },
    {
      name: 'Dark Gothic',
      positive: 'dark gothic stone texture, medieval dungeon, weathered carved rock, rust stains, deep shadows, moody atmosphere, horror aesthetic, desaturated',
      negative: 'bright colors, cheerful, clean, modern, plastic, anime, cartoon'
    },
    {
      name: 'Weapon Metal',
      positive: 'photorealistic machined metal weapon, brushed steel, anodized aluminum, precision engineering, industrial finish, scratches and wear marks, high specularity',
      negative: 'cartoon, anime, plastic, painted, low detail, blurry, low resolution'
    },
    {
      name: 'Player Skin',
      positive: 'game character skin texture, Quake tournament player, sci-fi armor suit, detailed surface normal, battle-worn, UV unwrapped flat texture',
      negative: 'blurry, low resolution, cartoon, anime, oversaturated, tiling artifacts'
    },
    {
      name: 'Pickup Icon',
      positive: 'Quake powerup icon, glowing energy item, health pack, ammo box, luminous effect, clean silhouette on dark background, game HUD style',
      negative: 'photo, realistic background, complex scene, low contrast, muted colors'
    }
  ];

  function mount(slot) {
    var wrap = document.createElement('div'); wrap.className = 'list-panel';
    var bar = document.createElement('div'); bar.className = 'list-toolbar';
    var title = document.createElement('span'); title.className = 'panel-iframe-title'; title.textContent = 'PROMPTS';
    bar.appendChild(title);
    var scroll = document.createElement('div'); scroll.className = 'list-scroll';
    PRESETS.forEach(function (p) {
      var row = document.createElement('div'); row.className = 'list-row'; row.style.cssText = 'flex-direction:column;align-items:flex-start;gap:4px;padding:10px 14px';
      var nameEl = document.createElement('div'); nameEl.style.cssText = 'font-size:12px;color:#c9a84c;font-family:Consolas,monospace'; nameEl.textContent = p.name;
      var posEl = document.createElement('div'); posEl.style.cssText = 'font-size:10px;color:#4caf50;font-family:Consolas,monospace;white-space:pre-wrap;word-break:break-word'; posEl.textContent = '+ ' + p.positive;
      var negEl = document.createElement('div'); negEl.style.cssText = 'font-size:10px;color:#c41515;font-family:Consolas,monospace;white-space:pre-wrap;word-break:break-word'; negEl.textContent = '\u2212 ' + p.negative;
      var btnRow = document.createElement('div'); btnRow.style.cssText = 'display:flex;gap:6px;margin-top:4px';
      var btnCopy = document.createElement('button'); btnCopy.className = 'panel-iframe-btn'; btnCopy.textContent = 'COPY+';
      (function (preset, btn) {
        btn.addEventListener('click', function () {
          navigator.clipboard.writeText(preset.positive).then(function () {
            btn.textContent = 'COPIED';
            setTimeout(function () { btn.textContent = 'COPY+'; }, 1200);
          }).catch(function () { btn.textContent = 'ERR'; setTimeout(function () { btn.textContent = 'COPY+'; }, 1200); });
        });
      }(p, btnCopy));
      btnRow.appendChild(btnCopy);
      row.appendChild(nameEl); row.appendChild(posEl); row.appendChild(negEl); row.appendChild(btnRow);
      scroll.appendChild(row);
    });
    wrap.appendChild(bar); wrap.appendChild(scroll);
    slot.replaceChildren(wrap);
  }

  function unmount() {}

  global.CreativePrompts = { mount: mount, unmount: unmount };
}(window));
