"""Builder for THE REAL SAGAR intros (reference style): word-synced 3D titles, text behind Sagar, smoke bursts,
emoji fields, channel card, punch-in zooms and crispy sound effects. Writes <project>/index.html (HyperFrames).

Usage:
    python3 scripts/make_reaction_intro.py projects/<video>/intro.json

intro.json (all times in seconds on the edited timeline):
{
  "duration": 7.0,
  "plate": "assets/plate.mp4", "person": "assets/sagar-glow.webm", "media_duration": 6.633,
  "voice": "assets/voice.wav", "music": {"src": "assets/music.wav", "volume": 0.14},
  "cams": [{"t": 1.24, "scale": 1.18, "dur": 0.14, "shake": true}, {"t": 3.62, "scale": 1.16, "cut": true}, ...],
  "words": [
    {"id": "ekdam", "text": "EKDAM", "style": "gold", "layer": "front", "x": 560, "y": 860, "size": 240,
     "in": 0.13, "out": 0.48, "enter": "letters" | "fly-left" | "fly-right" | "fly-top" | "pop" | "spin",
     "exit": "sink" | "left" | "right" | "up" | "blur", "rot": -4, "slant": "left" | "right" | "down"}
  ],
  "captions": [{"text": "WALI", "in": 1.09, "out": 1.24}],
  "bursts": [{"t": 1.2, "x": 960, "y": 300, "layer": "behind", "scale": 1.0}],
  "card": {"in": 2.84, "out": 3.55, "click": 3.28, "name": "The Real Sagar", "meta": "@TheRealSagarr · 200K subscribers",
           "photo": "assets/profile-photo.png"},
  "emoji_fields": [{"in": 5.13, "out": 6.15, "count": 22, "layer": "behind", "set": ["1f602", ...], "seed": 3}],
  "emoji_pops": [{"t": 3.96, "out": 4.42, "items": [["1f525", 260, 560, 300], ...]}],
  "flash": 6.25,
  "sfx": [["snap", 0.11, 0.6], ...],     # [name in assets/sfx, start, volume]
  "letter_blips": true                   # add a blip per letter of letter-by-letter words
}
Styles: lime, cyan, pink, gold, red, neon, purple. Layers: "behind" (between the room and Sagar) or "front".
"""
import json
import random
import sys
from html import escape
from pathlib import Path

LETTER_GAP = 0.03  # seconds between letters for "letters" entrances


def word_html(w):
    cls = f"w {w['style']} {w.get('slant', 'down')}" + (" lw" if w.get("enter") == "letters" else "")
    style = f"--size: {w['size']}px"
    if w.get("enter") == "letters":
        letters = "".join(
            f'<span class="l">{"&nbsp;" if ch == " " else escape(ch)}</span>' for ch in w["text"]
        )
        inner = (f'<span class="b" data-layout-allow-occlusion>{letters}</span>'
                 f'<span class="f">{letters}</span>')
    else:
        inner = (f'<span class="b" data-layout-allow-occlusion>{escape(w["text"])}</span>'
                 f'<span class="f">{escape(w["text"])}</span>')
    return (f'        <div id="w-{w["id"]}" class="{cls}" style="{style}; filter: url(#mb-{w["id"]})">{inner}</div>')


def burst_html(i):
    rnd = random.Random(100 + i)
    blobs = []
    for k in range(14):
        s = rnd.randint(140, 300)
        blobs.append(f'<i class="blob" style="width:{s}px;height:{s}px"></i>')
    shards = "".join('<i class="shard"></i>' for _ in range(12))
    return f'        <div id="burst{i}" class="burst">{"".join(blobs)}{shards}</div>'


def build(spec_path: Path) -> None:
    proj = spec_path.parent
    S = json.loads(spec_path.read_text())
    T = S["duration"]
    words = S.get("words", [])
    behind = [w for w in words if w.get("layer") == "behind"]
    front = [w for w in words if w.get("layer") != "behind"]
    bursts = S.get("bursts", [])
    fields = S.get("emoji_fields", [])
    pops = S.get("emoji_pops", [])

    # ---- markup ----
    behind_html = [burst_html(i) for i, b in enumerate(bursts) if b.get("layer", "behind") == "behind"]
    front_bursts = [burst_html(i) for i, b in enumerate(bursts) if b.get("layer", "behind") == "front"]
    emo_behind, emo_front = [], []
    field_items = []
    for fi, f in enumerate(fields):
        rnd = random.Random(f.get("seed", fi))
        items = []
        for k in range(f.get("count", 20)):
            code = f["set"][k % len(f["set"])]
            eid = f"ef{fi}-{k}"
            (emo_behind if f.get("layer", "behind") == "behind" else emo_front).append(
                f'        <img id="{eid}" class="emo" src="assets/emoji/{code}.webp" alt="" />')
            items.append({"id": eid, "size": rnd.randint(110, 380), "x": rnd.randint(-40, 1960),
                          "y": rnd.randint(-40, 1100), "rot": rnd.randint(-25, 25),
                          "drift": rnd.randint(90, 220), "delay": round(rnd.uniform(0, 0.22), 3)})
        field_items.append({"in": f["in"], "out": f["out"], "items": items})
    pop_items = []
    for pi, p in enumerate(pops):
        for k, (code, x, y, s) in enumerate(p["items"]):
            eid = f"ep{pi}-{k}"
            emo_front.append(f'        <img id="{eid}" class="emo" src="assets/emoji/{code}.webp" alt="" />')
            pop_items.append({"id": eid, "x": x, "y": y, "size": s, "t": p["t"] + k * 0.04, "out": p["out"] + k * 0.02})
    behind_html += emo_behind + [word_html(w) for w in behind]
    front_html = front_bursts + [word_html(w) for w in front]
    for i, c in enumerate(S.get("captions", [])):
        front_html.append(f'        <div id="cap{i}" class="cap">{escape(c["text"])}</div>')
    card = S.get("card")
    if card:
        front_html.append(f'''        <div id="card">
          <img src="{card.get('photo', 'assets/profile-photo.png')}" alt="" />
          <div>
            <div class="name">{escape(card['name'])} <span class="tick">&#10003;</span></div>
            <div class="meta">{escape(card['meta'])}</div>
            <div class="btn"><span id="sub">SUBSCRIBE</span><span id="subbed">SUBSCRIBED &#10003;</span></div>
          </div>
        </div>
        <svg id="cursor" viewBox="0 0 64 64"><path d="M10 4 L10 52 L22 41 L31 60 L39 56 L30 37 L46 37 Z" fill="#ffffff" stroke="#111" stroke-width="4" stroke-linejoin="round"/></svg>''')
    front_html += emo_front

    # ---- sound ----
    sfx = list(S.get("sfx", []))
    for w in words:  # a crisp blip per letter for letter-by-letter words ("letter_blips": false turns it off)
        if w.get("enter") == "letters" and S.get("letter_blips", True):
            for k, ch in enumerate(w["text"]):
                if ch != " ":
                    sfx.append(["blip", round(w["in"] + k * LETTER_GAP, 3), 0.35])
    audio = []
    md = S.get("media_duration", T)
    audio.append(f'      <audio id="voice" class="clip" src="{S["voice"]}" data-start="0" data-duration="{md}" '
                 f'data-track-index="10" data-volume="1"></audio>')
    if S.get("music"):
        m = S["music"]
        audio.append(f'      <audio id="music" class="clip" src="{m["src"]}" data-start="0" data-duration="{T}" '
                     f'data-track-index="11" data-volume="{m.get("volume", 0.14)}" data-timeline-role="music"></audio>')
    durations = json.loads((proj / "assets" / "sfx" / "durations.json").read_text())
    lanes = []  # reuse a lane once its previous sound ended
    for k, (name, t, vol) in enumerate(sorted(sfx, key=lambda s: s[1])):
        d = durations[name]
        lane = next((i for i, end in enumerate(lanes) if end <= t), None)
        if lane is None:
            lanes.append(0)
            lane = len(lanes) - 1
        lanes[lane] = t + d
        audio.append(f'      <audio id="sfx{k}" class="clip" src="assets/sfx/{name}.wav" data-start="{max(0, t)}" '
                     f'data-duration="{d}" data-track-index="{12 + lane}" data-volume="{vol}"></audio>')

    data = {"T": T, "cams": S.get("cams", []), "words": words, "captions": S.get("captions", []),
            "bursts": bursts, "card": card, "fields": field_items, "pops": pop_items, "flash": S.get("flash"),
            "letterGap": LETTER_GAP}
    filters = "\n".join(
        f'      <filter id="mb-{w["id"]}" x="-60%" y="-60%" width="220%" height="220%">'
        f'<feGaussianBlur stdDeviation="0 0" /></filter>' for w in words)
    html = TEMPLATE.replace("{{FILTERS}}", filters).replace("{{T}}", str(T)).replace("{{MD}}", str(md)) \
        .replace("{{PLATE}}", S["plate"]).replace("{{PERSON}}", S["person"]) \
        .replace("{{BEHIND}}", "\n".join(behind_html)).replace("{{FRONT}}", "\n".join(front_html)) \
        .replace("{{AUDIO}}", "\n".join(audio)).replace("{{DATA}}", json.dumps(data))
    (proj / "index.html").write_text(html)
    print(f"built {proj / 'index.html'}: {len(words)} words, {len(sfx)} sounds, {len(bursts)} bursts")


TEMPLATE = r"""<!doctype html>
<html lang="hi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      @font-face { font-family: "Poppins Black"; src: url("assets/fonts/poppins-black.woff2") format("woff2"); font-weight: 900; }
      @font-face { font-family: "Lilita One"; src: url("assets/fonts/lilita-one.woff2") format("woff2"); }
      @font-face { font-family: "Poppins Black Italic"; src: url("assets/fonts/poppins-black-italic.woff2") format("woff2"); font-weight: 900; font-style: italic; }
      * { margin: 0; padding: 0; box-sizing: border-box; }
      html, body { width: 1920px; height: 1080px; overflow: hidden; background: #000; }
      #root { position: relative; width: 1920px; height: 1080px; overflow: hidden; font-family: "Poppins Black", sans-serif; }
      .cam { position: absolute; inset: 0; transform-origin: 50% 32%; }
      .cam video { position: absolute; inset: 0; width: 1920px; height: 1080px; object-fit: cover; }
      #cam-back { z-index: 1; } #behind { z-index: 2; } #cam-front { z-index: 3; } #front { z-index: 4; } #flash { z-index: 6; }
      .layer { position: absolute; inset: 0; pointer-events: none; perspective: 1100px; }

      /* 3D word (reference look): condensed rounded heavy font, glossy top, deep extrusion straight down in a darker
         shade, strong glow in the word's colour */
      .w { position: absolute; left: 0; top: 0; white-space: nowrap; line-height: 1; opacity: 0; }
      .w .b, .w .f { display: block; font-family: "Lilita One", sans-serif; font-size: var(--size); letter-spacing: 0.01em; }
      .w .b { color: var(--deep); -webkit-text-stroke: calc(var(--size) * 0.03) var(--deep); paint-order: stroke fill;
        text-shadow: 0 2px 0 var(--deep), 0 4px 0 var(--deep), 0 6px 0 var(--deep), 0 8px 0 var(--deep),
          0 10px 0 var(--deep), 0 12px 0 var(--deep), 0 14px 0 var(--deep), 0 16px 0 var(--deep),
          0 18px 0 var(--dark), 0 20px 0 var(--dark), 0 22px 0 var(--dark),
          0 30px 22px rgba(0, 0, 0, 0.4), 0 0 18px var(--glow), 0 0 45px var(--glow), 0 0 110px var(--glow); }
      .w .f { position: absolute; left: 0; top: 0;
        background: linear-gradient(180deg, var(--hi) 0%, var(--hi) 12%, var(--c1) 30%, var(--c1) 58%, var(--c2) 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent; }
      .lime   { --hi: #fbffe0; --c1: #e9ff3a; --c2: #7fe12a; --deep: #2f9a1e; --dark: #1d6612; --glow: rgba(190, 255, 60, 0.75); }
      .cyan   { --hi: #effeff; --c1: #74f2ff; --c2: #2bb8ff; --deep: #1f63d8; --dark: #143f92; --glow: rgba(60, 210, 255, 0.75); }
      .pink   { --hi: #fff0fc; --c1: #ff8bf0; --c2: #f23fd0; --deep: #a51a9e; --dark: #6e0f6a; --glow: rgba(255, 70, 220, 0.8); }
      .gold   { --hi: #fffde6; --c1: #ffec3d; --c2: #ffb300; --deep: #f05a00; --dark: #a82e00; --glow: rgba(255, 150, 0, 0.85); }
      .red    { --hi: #ffe5df; --c1: #ff5d4a; --c2: #ff1e3c; --deep: #a3001f; --dark: #640012; --glow: rgba(255, 40, 60, 0.75); }
      .neon   { --hi: #ffffff; --c1: #ffffff; --c2: #ffd6f2; --deep: #f0479e; --dark: #a51c66; --glow: rgba(255, 60, 150, 0.9); }
      .purple { --hi: #fbf0ff; --c1: #e9a0ff; --c2: #b55bff; --deep: #6a26c4; --dark: #431680; --glow: rgba(200, 110, 255, 0.8); }
      .w .l { display: inline-block; }
      .w.lw .f { background: none; }
      .w.lw .f .l { background: linear-gradient(180deg, var(--hi) 0%, var(--hi) 12%, var(--c1) 30%, var(--c1) 58%, var(--c2) 100%);
        -webkit-background-clip: text; background-clip: text; color: transparent; }
      .w.left  { --dx1: -2px; --dx2: -4px; --dx3: -6px; --dx4: -8px; --dx5: -10px; --dx6: -12px; }
      .w.right { --dx1: 2px; --dx2: 4px; --dx3: 6px; --dx4: 8px; --dx5: 10px; --dx6: 12px; }
      .w.down  { --dx1: 0px; --dx2: 0px; --dx3: 0px; --dx4: 0px; --dx5: 0px; --dx6: 0px; }
      .lime   { --hi: #fdffd0; --c1: #f2ff3c; --c2: #8fe830; --deep: #3f9e1c; --rim: #fbffd8; --glow: rgba(205, 255, 70, 0.6); }
      .cyan   { --hi: #e6feff; --c1: #79f1ff; --c2: #27b8ff; --deep: #1c52d6; --rim: #e8fdff; --glow: rgba(70, 215, 255, 0.65); }
      .pink   { --hi: #ffe2fb; --c1: #ff86ee; --c2: #ff38c4; --deep: #b0158f; --rim: #ffe6fb; --glow: rgba(255, 60, 210, 0.75); }
      .gold   { --hi: #fffbd0; --c1: #fff04a; --c2: #ffbb00; --deep: #ff5e00; --rim: #fff9c8; --glow: rgba(255, 110, 0, 0.8); }
      .red    { --hi: #ffd9cf; --c1: #ff6c47; --c2: #ff2626; --deep: #9c0010; --rim: #ffe0d8; --glow: rgba(255, 50, 30, 0.65); }
      .neon   { --hi: #ffffff; --c1: #ffffff; --c2: #ffd3f1; --deep: #ff3d9a; --rim: #ff6fb6; --glow: rgba(255, 30, 120, 0.95); }
      .purple { --hi: #f6e6ff; --c1: #e08cff; --c2: #a94bff; --deep: #5a1aa8; --rim: #f3e2ff; --glow: rgba(190, 90, 255, 0.7); }

      .cap { position: absolute; left: 110px; top: 890px; opacity: 0; white-space: nowrap; font-family: "Poppins Black Italic";
        font-style: italic; font-size: 92px; color: #ffe02e; letter-spacing: -0.01em;
        -webkit-text-stroke: 7px #2a1600; paint-order: stroke fill; text-shadow: 0 6px 0 #2a1600, 0 12px 22px rgba(0,0,0,.55), 0 0 30px rgba(255,190,0,.5); }

      /* smoke burst: yellow puffs + flying shards */
      .burst { position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; filter: url(#smoke); }
      .burst .blob { position: absolute; left: 0; top: 0; border-radius: 50%; opacity: 0;
        background: radial-gradient(circle at 42% 38%, rgba(255, 253, 230, 0.95) 0%, rgba(255, 238, 120, 0.9) 22%,
          rgba(255, 210, 40, 0.75) 45%, rgba(250, 175, 20, 0.35) 68%, rgba(240, 160, 0, 0) 100%); }
      .burst .shard { position: absolute; left: 0; top: 0; width: 26px; height: 16px; opacity: 0; background: #6b3a12;
        clip-path: polygon(0 0, 100% 30%, 70% 100%, 10% 80%); }

      #card { position: absolute; left: 70px; top: 760px; width: 800px; height: 190px; opacity: 0;
        background: #ffffff; border-radius: 32px; box-shadow: 0 18px 50px rgba(0,0,0,.45), 0 0 0 6px rgba(255,255,255,.35);
        display: flex; align-items: center; gap: 26px; padding: 0 30px; font-family: "Poppins", sans-serif; }
      #card img { width: 132px; height: 132px; border-radius: 50%; object-fit: cover; border: 5px solid #ff2a2a; }
      #card .name { font-weight: 800; font-size: 40px; color: #0f0f0f; display: flex; align-items: center; gap: 10px; }
      #card .tick { width: 30px; height: 30px; border-radius: 50%; background: #606060; color: #fff; font-size: 20px;
        display: inline-flex; align-items: center; justify-content: center; }
      #card .meta { white-space: nowrap; font-weight: 600; font-size: 28px; color: #555; margin-top: 4px; }
      #card .btn { position: relative; margin-top: 12px; width: 230px; height: 56px; border-radius: 28px; }
      #card .btn span { position: absolute; inset: 0; border-radius: 28px; display: flex; align-items: center;
        justify-content: center; font-weight: 700; font-size: 26px; }
      #sub { background: #ff0033; color: #fff; }
      #subbed { background: #e6e6e6; color: #333; opacity: 0; }
      #cursor { position: absolute; left: 0; top: 0; width: 64px; height: 64px; opacity: 0; }

      .emo { position: absolute; left: 0; top: 0; width: 300px; height: 300px; opacity: 0;
        filter: drop-shadow(0 0 3px #ffffff) drop-shadow(0 0 3px #ffffff) drop-shadow(0 12px 16px rgba(0,0,0,.3)); }
      #flash { position: absolute; inset: 0; background: #ffffff; opacity: 0; }
    </style>
  </head>
  <body>
    <svg width="0" height="0" style="position:absolute">
      <filter id="smoke" x="-20%" y="-20%" width="140%" height="140%">
        <feTurbulence type="fractalNoise" baseFrequency="0.018" numOctaves="3" seed="7" result="n" />
        <feDisplacementMap in="SourceGraphic" in2="n" scale="90" xChannelSelector="R" yChannelSelector="G" />
      </filter>
{{FILTERS}}
    </svg>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{{T}}" data-width="1920" data-height="1080">
      <div id="cam-back" class="cam">
        <video id="plate" class="clip" src="{{PLATE}}" data-start="0" data-duration="{{MD}}" data-track-index="0" muted></video>
      </div>
      <div id="behind" class="clip layer" data-start="0" data-duration="{{T}}" data-track-index="1" data-track-kind="graphics" data-layout-allow-overlap data-layout-allow-overflow>
{{BEHIND}}
      </div>
      <div id="cam-front" class="cam">
        <video id="person" class="clip" src="{{PERSON}}" data-start="0" data-media-start="0" data-duration="{{MD}}" data-track-index="2" muted data-layout-allow-occlusion></video>
      </div>
      <div id="front" class="clip layer" data-start="0" data-duration="{{T}}" data-track-index="3" data-track-kind="graphics" data-layout-allow-overlap data-layout-allow-overflow>
{{FRONT}}
      </div>
      <div id="flash" class="clip" data-start="0" data-duration="{{T}}" data-track-index="4"></div>
{{AUDIO}}
    </div>
    <script>
      const D = {{DATA}};
      const tl = gsap.timeline({ paused: true });
      const IR = { immediateRender: false };

      // ---------- camera: punch-ins (fast, slight shake) and jump-cut zoom changes ----------
      const cams = ["#cam-back", "#cam-front"];
      tl.set(cams, { scale: 1, x: 0, y: 0 }, 0);
      for (const c of D.cams) {
        if (c.cut) { tl.set(cams, { scale: c.scale, x: 0, y: 0 }, c.t); }
        else { tl.to(cams, { scale: c.scale, duration: c.dur || 0.14, ease: c.ease || "power3.out" }, c.t); }
        if (c.push) tl.to(cams, { scale: c.push, duration: c.pushDur || 1.2, ease: "none" }, c.t + (c.cut ? 0 : (c.dur || 0.14)));
        if (c.shake) [16, -14, 10, -7, 4, 0].forEach((x, i) =>
          tl.to(cams, { x, y: i % 2 ? 5 : -5, duration: 0.04, ease: "none" }, c.t + i * 0.04));
      }

      // ---------- words (reference: fast entries with directional motion blur, near-still hold, blurred exits) ----------
      const ENTER = {
        "zoom":      { from: { scale: 0.3 }, blur: "14 14" },
        "fly-left":  { from: { x: -520, scaleX: 1.3 }, blur: "60 0" },
        "fly-right": { from: { x: 520, scaleX: 1.3 }, blur: "60 0" },
        "fly-top":   { from: { y: -420, scaleY: 1.3 }, blur: "0 50" },
        "fly-bottom":{ from: { y: 420, scaleY: 1.3 }, blur: "0 50" },
        "pop":       { from: { scale: 0.4 }, blur: "12 12" },
      };
      const EXIT = {
        sink:  { to: { y: 360, rotation: -6 }, blur: "0 40" },
        left:  { to: { x: -800, scaleX: 1.3 }, blur: "70 0" },
        right: { to: { x: 800, scaleX: 1.3 }, blur: "70 0" },
        up:    { to: { y: -600, scaleY: 1.3 }, blur: "0 60" },
        blur:  { to: { scale: 1.25 }, blur: "16 16" },
      };
      for (const w of D.words) {
        const el = "#w-" + w.id, fb = "#mb-" + w.id + " feGaussianBlur", rot = w.rot || 0;
        tl.set(el, { x: w.x, y: w.y, xPercent: -50, yPercent: -50, rotation: rot, scale: 1 }, 0);
        if (w.enter === "letters") {
          tl.set(el, { opacity: 1 }, w.in);
          const ls = document.querySelectorAll(el + " .l");
          const n = ls.length / 2;
          ls.forEach((l, i) => {
            const k = i % n;
            tl.fromTo(l, { opacity: 0, scale: 0.15, y: 60 },
              { opacity: 1, scale: 1.15, y: -6, duration: 0.1, ease: "power3.out", ...IR }, w.in + k * D.letterGap);
            tl.to(l, { scale: 1, y: 0, duration: 0.1, ease: "power2.out" }, w.in + k * D.letterGap + 0.1);
          });
        } else {
          const e = ENTER[w.enter || "zoom"], f = e.from;
          tl.fromTo(el, { opacity: 0, x: w.x + (f.x || 0), y: w.y + (f.y || 0), scale: f.scale || 1, scaleX: f.scaleX || 1, scaleY: f.scaleY || 1 },
            { opacity: 1, x: w.x, y: w.y, scale: 1.04, scaleX: 1, scaleY: 1, duration: 0.13, ease: "power3.out", ...IR }, w.in);
          tl.fromTo(fb, { attr: { stdDeviation: e.blur } }, { attr: { stdDeviation: "0 0" }, duration: 0.13, ease: "power2.out", ...IR }, w.in);
          tl.to(el, { scale: 1, duration: 0.1, ease: "power2.out" }, w.in + 0.13);
        }
        // hold: almost still, slow push toward the camera (reference)
        const hold = Math.max(0.05, w.out - w.in - 0.3);
        tl.to(el, { scale: 1.05, duration: hold, ease: "none" }, w.in + 0.23);
        const x = EXIT[w.exit || "blur"], t = x.to;
        tl.to(el, { x: w.x + (t.x || 0), y: w.y + (t.y || 0), rotation: rot + (t.rotation || 0), scale: t.scale || 1.05,
          scaleX: t.scaleX || 1, scaleY: t.scaleY || 1, opacity: 0, duration: 0.12, ease: "power2.in" }, w.out - 0.06);
        tl.to(fb, { attr: { stdDeviation: x.blur }, duration: 0.12, ease: "power2.in" }, w.out - 0.06);
      }

      // ---------- small yellow captions ----------
      D.captions.forEach((c, i) => {
        const el = "#cap" + i;
        tl.set(el, { transformOrigin: "0% 100%" }, 0);
        tl.fromTo(el, { opacity: 0, scale: 0.5, y: 30 }, { opacity: 1, scale: 1, y: 0, duration: 0.12, ease: "back.out(3)", ...IR }, c.in);
        tl.to(el, { opacity: 0, scale: 0.9, duration: 0.06 }, c.out);
      });

      // ---------- smoke bursts ----------
      D.bursts.forEach((b, i) => {
        const root = "#burst" + i, sc = b.scale || 1;
        let s = 31 + i * 7; const r = () => ((s = (s * 16807) % 2147483647) / 2147483647);
        document.querySelectorAll(root + " .blob").forEach((el, k) => {
          const a = (k / 14) * Math.PI * 2 + r(), d = (60 + r() * 240) * sc;
          tl.set(el, { x: b.x, y: b.y, xPercent: -50, yPercent: -50 }, 0);
          // fade in over ~0.1 s (an instant full-bright puff reads as a light blink)
          tl.fromTo(el, { opacity: 0, scale: 0.15, x: b.x, y: b.y },
            { scale: (1.2 + r() * 0.8) * sc, x: b.x + Math.cos(a) * d * 1.4, y: b.y + Math.sin(a) * d * 0.8,
              duration: 0.5, ease: "power3.out", ...IR }, b.t + k * 0.012);
          tl.to(el, { opacity: 0.88, duration: 0.1, ease: "power1.out" }, b.t + k * 0.012);
          tl.to(el, { opacity: 0, scale: "+=0.35", duration: 0.45, ease: "power1.in" }, b.t + 0.3 + r() * 0.2);
        });
        document.querySelectorAll(root + " .shard").forEach((el, k) => {
          const a = (k / 12) * Math.PI * 2 + r() * 0.5, d = (300 + r() * 450) * sc;
          tl.fromTo(el, { opacity: 1, x: b.x, y: b.y, rotation: r() * 360, scale: 0.6 + r() },
            { x: b.x + Math.cos(a) * d * 1.3, y: b.y + Math.sin(a) * d * 0.7 + 200, rotation: "+=" + (360 + r() * 360),
              duration: 0.7, ease: "power1.out", ...IR }, b.t);
          tl.to(el, { opacity: 0, duration: 0.2 }, b.t + 0.55);
        });
      });

      // ---------- channel card: slides up with blur, subscribe click, slides away ----------
      if (D.card) {
        const c = D.card;
        tl.fromTo("#card", { opacity: 0, y: 260, rotation: -8, filter: "blur(12px)" },
          { opacity: 1, y: 0, rotation: -3, filter: "blur(0px)", duration: 0.2, ease: "power3.out", ...IR }, c.in);
        tl.fromTo("#cursor", { opacity: 0, x: 900, y: 1050 }, { opacity: 1, x: 520, y: 905, duration: 0.28, ease: "power2.out", ...IR }, c.in + 0.1);
        tl.to("#cursor", { scale: 0.8, duration: 0.05 }, c.click - 0.01);
        tl.to("#cursor", { scale: 1, duration: 0.06 }, c.click + 0.04);
        tl.to("#sub", { opacity: 0, duration: 0.05 }, c.click);
        tl.to("#subbed", { opacity: 1, duration: 0.05 }, c.click);
        tl.to("#card .btn", { scale: 0.9, duration: 0.05 }, c.click - 0.01);
        tl.to("#card .btn", { scale: 1, duration: 0.1, ease: "back.out(3)" }, c.click + 0.04);
        tl.to(["#card", "#cursor"], { opacity: 0, y: "+=240", filter: "blur(12px)", duration: 0.16, ease: "power2.in" }, c.out);
      }

      // ---------- emoji fields (behind Sagar, fade + scale in, drift up) and emoji pops ----------
      for (const f of D.fields) for (const e of f.items) {
        const el = "#" + e.id;
        tl.set(el, { width: e.size, height: e.size, xPercent: -50, yPercent: -50 }, 0);
        tl.fromTo(el, { opacity: 0, x: e.x, y: e.y + 40, scale: 0.4, rotation: e.rot - 15 },
          { opacity: 1, y: e.y, scale: 1, rotation: e.rot, duration: 0.22, ease: "back.out(2)", ...IR }, f.in + e.delay);
        tl.to(el, { y: e.y - e.drift, rotation: e.rot + 8, duration: f.out - f.in, ease: "none" }, f.in + e.delay + 0.22);
        tl.to(el, { opacity: 0, scale: 1.15, duration: 0.18, ease: "power1.in" }, f.out + e.delay * 0.5);
      }
      for (const e of D.pops) {
        const el = "#" + e.id;
        tl.set(el, { width: e.size, height: e.size, xPercent: -50, yPercent: -50 }, 0);
        tl.fromTo(el, { opacity: 0, x: e.x, y: e.y, scale: 0.2, rotation: -25 },
          { opacity: 1, scale: 1, rotation: 6, duration: 0.18, ease: "back.out(2.5)", ...IR }, e.t);
        tl.to(el, { y: e.y - 90, scale: 1.15, opacity: 0, filter: "blur(10px)", duration: 0.22, ease: "power1.in" }, e.out);
      }

      if (D.flash != null) tl.fromTo("#flash", { opacity: 0 }, { opacity: 1, duration: 0.4, ease: "power2.in", ...IR }, D.flash);

      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    build(Path(sys.argv[1]).resolve())
