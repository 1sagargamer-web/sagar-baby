// Cute cartoon boy drawn in SVG.
// States: "idle" (hopeful), "plead" (puppy eyes, hands joined),
// "cry" (crying under a rain cloud), "happy" (heart eyes, dancing).
let uid = 0;

export function createBoy(state = "idle") {
  const id = `boy${++uid}`;
  const wrap = document.createElement("div");
  wrap.className = "boy-figure";
  wrap.innerHTML = `
<svg class="boy ${state}" viewBox="0 0 220 300" role="img" aria-label="Boy character">
  <defs>
    <linearGradient id="${id}-shirt" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ff5c8a"/>
      <stop offset="1" stop-color="#d6336c"/>
    </linearGradient>
    <radialGradient id="${id}-face" cx="0.45" cy="0.4" r="0.7">
      <stop offset="0" stop-color="#ffe6d2"/>
      <stop offset="1" stop-color="#f9c9a3"/>
    </radialGradient>
    <linearGradient id="${id}-tear" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#bfe6ff"/>
      <stop offset="1" stop-color="#5fb4ff"/>
    </linearGradient>
  </defs>

  <ellipse class="shadow" cx="110" cy="292" rx="58" ry="7" fill="#000" opacity=".25"/>

  <g class="figure">
    <g class="body">
      <g class="leg leg-left">
        <rect x="84" y="236" width="20" height="44" rx="10" fill="#34386b"/>
        <ellipse cx="92" cy="283" rx="16" ry="8" fill="#fff"/>
      </g>
      <g class="leg leg-right">
        <rect x="116" y="236" width="20" height="44" rx="10" fill="#34386b"/>
        <ellipse cx="128" cy="283" rx="16" ry="8" fill="#fff"/>
      </g>

      <g class="arm arm-left">
        <line x1="74" y1="178" x2="54" y2="230" stroke="url(#${id}-shirt)" stroke-width="20" stroke-linecap="round"/>
        <circle cx="52" cy="236" r="11" fill="#f9c9a3"/>
      </g>
      <g class="arm arm-right">
        <line x1="146" y1="178" x2="166" y2="230" stroke="url(#${id}-shirt)" stroke-width="20" stroke-linecap="round"/>
        <circle cx="168" cy="236" r="11" fill="#f9c9a3"/>
      </g>

      <rect x="64" y="160" width="92" height="88" rx="32" fill="url(#${id}-shirt)"/>
      <path class="chest-heart" d="M110 222 C92 208 92 192 102 190 C107 189 110 193 110 196 C110 193 113 189 118 190 C128 192 128 208 110 222 Z" fill="#fff" opacity=".95"/>
      <path class="chest-crack" d="M110 194 L106 202 L113 207 L108 216" stroke="#d6336c" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
      <rect x="100" y="146" width="20" height="18" rx="6" fill="#f2bb93"/>
    </g>

    <g class="head">
      <circle cx="52" cy="106" r="12" fill="#f9c9a3"/>
      <circle cx="168" cy="106" r="12" fill="#f9c9a3"/>
      <circle cx="110" cy="100" r="58" fill="url(#${id}-face)"/>
      <path d="M52 104 C44 44 88 26 114 28 C152 30 178 54 168 104 C162 84 150 72 134 66 C124 80 98 82 80 72 C68 80 58 90 52 104 Z" fill="#3a2418"/>
      <path class="tuft" d="M104 30 C112 14 128 14 134 22 C124 22 116 26 112 34 Z" fill="#3a2418"/>

      <ellipse class="blush" cx="76" cy="126" rx="11" ry="6.5" fill="#ff7fa3"/>
      <ellipse class="blush" cx="144" cy="126" rx="11" ry="6.5" fill="#ff7fa3"/>

      <!-- idle: hopeful round eyes -->
      <g class="st st-idle">
        <g class="blink">
          <circle cx="88" cy="108" r="9" fill="#2b1a12"/><circle cx="91" cy="104" r="3.4" fill="#fff"/>
          <circle cx="132" cy="108" r="9" fill="#2b1a12"/><circle cx="135" cy="104" r="3.4" fill="#fff"/>
        </g>
        <path d="M100 130 Q110 138 120 130" stroke="#7a2a2a" stroke-width="4" fill="none" stroke-linecap="round"/>
      </g>

      <!-- plead: worried brows, big shiny puppy eyes, wobbly mouth -->
      <g class="st st-plead">
        <path d="M76 93 L98 87" stroke="#3a2418" stroke-width="4" stroke-linecap="round"/>
        <path d="M122 87 L144 93" stroke="#3a2418" stroke-width="4" stroke-linecap="round"/>
        <g class="puppy">
          <circle cx="88" cy="109" r="12" fill="#2b1a12"/><circle cx="92" cy="104" r="4.5" fill="#fff"/><circle cx="84" cy="114" r="2.2" fill="#fff"/>
          <circle cx="132" cy="109" r="12" fill="#2b1a12"/><circle cx="136" cy="104" r="4.5" fill="#fff"/><circle cx="128" cy="114" r="2.2" fill="#fff"/>
        </g>
        <path d="M101 136 Q105 131 110 135 Q115 131 119 136" stroke="#7a2a2a" stroke-width="3.5" fill="none" stroke-linecap="round"/>
        <path class="tear drop1" d="M80 122 C76 130 76 134 80 136 C84 134 84 130 80 122 Z" fill="url(#${id}-tear)"/>
      </g>

      <!-- cry: squeezed eyes, tear streams, wailing mouth -->
      <g class="st st-cry">
        <path d="M76 95 L98 90" stroke="#3a2418" stroke-width="4" stroke-linecap="round"/>
        <path d="M122 90 L144 95" stroke="#3a2418" stroke-width="4" stroke-linecap="round"/>
        <path d="M79 102 L95 108 L79 114" stroke="#2b1a12" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <path d="M141 102 L125 108 L141 114" stroke="#2b1a12" stroke-width="4.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
        <rect class="stream" x="82" y="112" width="9" height="40" rx="4.5" fill="url(#${id}-tear)" opacity=".9"/>
        <rect class="stream" x="129" y="112" width="9" height="40" rx="4.5" fill="url(#${id}-tear)" opacity=".9"/>
        <path class="wail" d="M96 142 Q110 120 124 142 Q110 136 96 142 Z" fill="#8a1c3a"/>
        <circle class="splash s1" cx="76" cy="114" r="3.5" fill="#7cc7ff"/>
        <circle class="splash s2" cx="144" cy="114" r="3.5" fill="#7cc7ff"/>
        <circle class="splash s3" cx="74" cy="112" r="2.5" fill="#7cc7ff"/>
        <circle class="splash s4" cx="146" cy="112" r="2.5" fill="#7cc7ff"/>
      </g>

      <!-- happy: heart eyes + big smile -->
      <g class="st st-happy">
        <path class="heart-eye" d="M88 118 C78 111 76 104 80 100 C84 97 88 100 88 104 C88 100 92 97 96 100 C100 104 98 111 88 118 Z" fill="#ff3d6e"/>
        <path class="heart-eye" d="M132 118 C122 111 120 104 124 100 C128 97 132 100 132 104 C132 100 136 97 140 100 C144 104 142 111 132 118 Z" fill="#ff3d6e"/>
        <path d="M92 124 Q110 152 128 124 Z" fill="#8a1c3a"/>
        <ellipse cx="110" cy="137" rx="8" ry="4.5" fill="#ff7c9c"/>
      </g>
    </g>
  </g>

  <!-- rain cloud for crying -->
  <g class="cloud">
    <g class="cloud-body" fill="#8b93b8">
      <circle cx="90" cy="-18" r="16"/><circle cx="112" cy="-28" r="20"/><circle cx="134" cy="-18" r="15"/>
      <rect x="76" y="-20" width="72" height="16" rx="8"/>
    </g>
    <g fill="#7cc7ff">
      <rect class="rain r1" x="88" y="0" width="3" height="10" rx="1.5"/>
      <rect class="rain r2" x="104" y="0" width="3" height="10" rx="1.5"/>
      <rect class="rain r3" x="120" y="0" width="3" height="10" rx="1.5"/>
      <rect class="rain r4" x="136" y="0" width="3" height="10" rx="1.5"/>
    </g>
  </g>
</svg>`;
  return wrap;
}
