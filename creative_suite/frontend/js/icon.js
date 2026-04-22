(function () {
  'use strict';

  var SPRITE = '/static/icons/pantheon.svg';

  /**
   * Create an inline SVG <use> element referencing the Pantheon sprite.
   *
   * @param {string} name  Icon id without the i- prefix (e.g. "rg", "play")
   * @param {number} [size=16] Width and height in px
   * @returns {SVGSVGElement}
   */
  function Icon(name, size) {
    size = size || 16;
    var ns = 'http://www.w3.org/2000/svg';
    var svg = document.createElementNS(ns, 'svg');
    svg.setAttribute('width', size);
    svg.setAttribute('height', size);
    svg.setAttribute('aria-hidden', 'true');
    svg.classList.add('p-icon');

    var use = document.createElementNS(ns, 'use');
    use.setAttribute('href', SPRITE + '#i-' + name);
    svg.appendChild(use);
    return svg;
  }

  /**
   * Return the HTML string for an icon (for innerHTML assignment).
   * Use Icon() (DOM) when possible — this exists for template strings.
   */
  Icon.html = function (name, size) {
    size = size || 16;
    return '<svg width="' + size + '" height="' + size + '" aria-hidden="true" class="p-icon">'
      + '<use href="' + SPRITE + '#i-' + name + '"/></svg>';
  };

  window.Icon = Icon;
})();
