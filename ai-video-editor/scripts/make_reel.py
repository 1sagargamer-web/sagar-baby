"""Build a Bhagwan + Sagar cartoon reel (HyperFrames project) from a script file.

Usage:
    python3 scripts/make_reel.py projects/<reel>/script.json

script.json:
{
  "title": "result",
  "gap": 0.25,                       # seconds between lines (optional)
  "lines": [
    {"who": "sagar",   "hi": "हे भगवान ...", "caption": "Hey Bhagwan ...",
     "audio": "Raw/my-line-1.m4a",   # Sagar's own recording (optional; placeholder voice if missing)
     "face": {"eyes": "closed", "pose": "pray"}},
    {"who": "krishna", "hi": "वत्स ...",     "caption": "Vatsa ...", "face": {"eyes": "half"},
     "punch": true},                 # camera pushes in on the speaker
    {"who": "sagar", "hi": "क्या?!", "caption": "Kya?!", "face": {"eyes": "shock", "mouth": "o", "sweat": true},
     "shake": true}                  # camera shake at the start of the line
  ]
}

eyes: open | closed | half (krishna) | shock (sagar); mouth: closed | o (sagar); pose: none | pray (sagar)
Writes projects/<reel>/index.html + assets/audio/*.wav. Then check and render with the HyperFrames CLI.
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "scripts"))
import god_voice  # noqa: E402

FPS = 30
W, H = 1080, 1920
# Placeholder for Sagar's lines until his own recording is given. Never used for Bhagwan.
SAGAR_PLACEHOLDER = {"voice": "hm_psi", "speed": 1.05, "pitch": 1.04, "echo": "anull"}


def sagar_audio(line: dict, out: Path) -> None:
    src = line.get("audio")
    if src:
        src_path = (HERE / src) if not Path(src).is_absolute() else Path(src)
        # trim silence at both ends, level to -16 LUFS
        af = (
            "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
            "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.08,areverse,"
            "loudnorm=I=-16:TP=-1.5"
        )
        subprocess.run(
            ["ffmpeg", "-v", "error", "-y", "-i", str(src_path), "-af", af, "-ac", "1", "-ar", "48000", str(out)],
            check=True,
        )
    else:
        god_voice.make(line["hi"], out, SAGAR_PLACEHOLDER)


def mouth_envelope(wav: Path) -> list[bool]:
    """True per video frame where the mouth should be open."""
    data, rate = sf.read(str(wav))
    if data.ndim > 1:
        data = data.mean(axis=1)
    hop = rate // FPS
    n = len(data) // hop
    rms = np.array([np.sqrt(np.mean(data[i * hop : (i + 1) * hop] ** 2)) for i in range(n)])
    if not len(rms) or rms.max() == 0:
        return []
    rms = np.convolve(rms, np.ones(2) / 2, mode="same")
    opened = rms > 0.22 * rms.max()
    # flap: never hold the mouth open more than 4 frames, so long vowels still move
    out, run = [], 0
    for o in opened:
        run = run + 1 if o else 0
        out.append(bool(o) and not (run > 4 and run % 5 == 0))
    return out


def build(script_path: Path) -> None:
    proj = script_path.parent
    spec = json.loads(script_path.read_text())
    gap = spec.get("gap", 0.25)
    audio_dir = proj / "assets" / "audio"
    audio_dir.mkdir(parents=True, exist_ok=True)

    t = 0.3
    lines = []
    for i, line in enumerate(spec["lines"]):
        wav = audio_dir / f"line-{i + 1:02d}-{line['who']}.wav"
        if line["who"] == "krishna":
            god_voice.make(line["hi"], wav)
        else:
            sagar_audio(line, wav)
        dur = sf.info(str(wav)).duration
        t += line.get("pause_before", 0)
        lines.append({**line, "wav": wav, "start": round(t, 3), "dur": round(dur, 3), "env": mouth_envelope(wav)})
        t += dur + gap
    total = round(t + 1.0, 2)

    # Krishna appears 0.5 s before his first line
    kr_first = next((l["start"] for l in lines if l["who"] == "krishna"), 0.0)
    kr_enter = max(0.0, round(kr_first - 0.5, 3))

    # ---- per-frame face states -> keyframes -------------------------------------------------
    defaults = {
        "sagar": {"eyes": "open", "mouth": "closed", "pose": "none", "sweat": False},
        "krishna": {"eyes": "open", "mouth": "closed"},
    }
    nframes = int(total * FPS) + 1
    keys = {"sagar": [], "krishna": []}
    for who in keys:
        face = dict(defaults[who])
        last = None
        for f in range(nframes):
            ft = f / FPS
            for l in lines:  # expression changes at the start of each line that sets them
                if l["who"] == who and abs(l["start"] - ft) < 0.5 / FPS and "face" in l:
                    face = {**defaults[who], **l["face"]}
            eyes, mouth = face["eyes"], face["mouth"]
            talking = next((l for l in lines if l["who"] == who and l["start"] <= ft < l["start"] + l["dur"]), None)
            if talking and mouth != "o":
                k = int(round((ft - talking["start"]) * FPS))
                mouth = "open" if k < len(talking["env"]) and talking["env"][k] else "closed"
            # blink every ~3.2 s (offset per character) while the eyes are open
            period, off = (3.2, 1.1) if who == "sagar" else (3.7, 2.3)
            if eyes == "open" and ((ft - off) % period) < 0.13 and ft > off:
                eyes = "closed"
            state = (eyes, mouth, face.get("pose", "none"), bool(face.get("sweat", False)))
            if state != last:
                keys[who].append([round(ft, 3), *state])
                last = state

    # head nods while talking
    nods = {"sagar": [], "krishna": []}
    for l in lines:
        nods[l["who"]].append([l["start"], l["dur"]])

    cams = []
    for l in lines:
        if l.get("punch"):
            cams.append({"type": "punch", "who": l["who"], "start": l["start"], "dur": l["dur"]})
        if l.get("shake"):
            cams.append({"type": "shake", "start": l["start"]})

    data = {"total": total, "krEnter": kr_enter, "keys": keys, "nods": nods, "cams": cams}

    # ---- HTML -----------------------------------------------------------------------------
    sagar_svg = (HERE / "characters" / "sagar.svg").read_text()
    krishna_svg = (HERE / "characters" / "krishna.svg").read_text()
    audio_tags, caption_tags = [], []
    for i, l in enumerate(lines):
        rel = l["wav"].relative_to(proj).as_posix()
        audio_tags.append(
            f'      <audio id="vo-{i + 1}" class="clip" src="{rel}" data-start="{l["start"]}" '
            f'data-duration="{l["dur"]}" data-track-index="{3 if l["who"] == "sagar" else 4}" data-volume="1"></audio>'
        )
        cap_end = lines[i + 1]["start"] if i + 1 < len(lines) else total
        cs = max(0.1, round(l["start"] - 0.05, 3))
        caption_tags.append(
            f'        <div id="cap-{i + 1}" class="clip cap cap-{l["who"]}" data-start="{cs}" '
            f'data-duration="{round(cap_end - cs, 3)}" data-track-index="5"><span>{l["caption"]}</span></div>'
        )

    html = TEMPLATE.format(
        total=total,
        sagar=sagar_svg,
        krishna=krishna_svg,
        audio="\n".join(audio_tags),
        captions="\n".join(caption_tags),
        data=json.dumps(data, ensure_ascii=False),
    )
    (proj / "index.html").write_text(html)
    print(f"built {proj / 'index.html'}  duration={total}s  lines={len(lines)}")


TEMPLATE = """<!doctype html>
<html lang="hi" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #8fd6ff; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "Poppins", sans-serif; }}
      #world {{ position: absolute; inset: 0; transform-origin: 50% 55%; }}
      #sky {{ position: absolute; inset: 0; background: linear-gradient(#58bff2 0%, #a9e3ff 58%, #d8f3ff 70%); }}
      .bg-svg {{ position: absolute; left: 0; width: 1080px; }}
      #char-sagar, #char-krishna {{ position: absolute; top: 690px; width: 560px; height: 933px; }}
      #char-sagar {{ left: -20px; }}
      #char-krishna {{ left: 540px; }}
      #char-sagar svg, #char-krishna svg {{ width: 100%; height: 100%; overflow: visible; }}
      .cap {{ position: absolute; left: 0; top: 330px; width: 1080px; padding: 0 120px; text-align: center; }}
      .cap span {{
        display: inline-block; background: #ffffff; color: #141414; font-weight: 700; font-size: 54px;
        line-height: 1.25; padding: 22px 34px; border-radius: 26px; border: 5px solid #141414;
        box-shadow: 0 8px 0 rgba(0,0,0,0.18);
      }}
      .cap-krishna span {{ background: #fff4c7; border-color: #a3601a; }}
      #flash {{ position: absolute; inset: 0; background: #fff6cf; opacity: 0; }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <div id="scene" class="clip" data-start="0" data-duration="{total}" data-track-index="0" data-layout-allow-overlap>
        <div id="world">
          <div id="sky"></div>
          <svg class="bg-svg" id="clouds" style="top:120px;height:420px" viewBox="0 0 1080 420">
            <g fill="#ffffff" opacity="0.95">
              <ellipse cx="190" cy="120" rx="120" ry="48"/><ellipse cx="260" cy="95" rx="80" ry="55"/><ellipse cx="140" cy="100" rx="60" ry="40"/>
              <ellipse cx="830" cy="230" rx="140" ry="52"/><ellipse cx="900" cy="200" rx="85" ry="58"/><ellipse cx="770" cy="210" rx="65" ry="42"/>
            </g>
          </svg>
          <svg class="bg-svg" style="top:1080px;height:840px" viewBox="0 0 1080 840">
            <path d="M0 220 C180 120 340 140 520 210 C700 120 900 110 1080 200 L1080 840 L0 840 Z" fill="#7fd36b"/>
            <path d="M0 330 C240 270 520 290 1080 320 L1080 840 L0 840 Z" fill="#5cbf55"/>
          </svg>
          <div id="char-krishna">{krishna}</div>
          <div id="char-sagar">{sagar}</div>
          <svg class="bg-svg" style="top:1560px;height:360px" viewBox="0 0 1080 360">
            <g fill="#3fa34a" stroke="#2a7a35" stroke-width="6">
              <circle cx="40" cy="150" r="110"/><circle cx="210" cy="190" r="120"/><circle cx="400" cy="170" r="105"/>
              <circle cx="600" cy="200" r="125"/><circle cx="800" cy="165" r="110"/><circle cx="1000" cy="185" r="125"/>
            </g>
            <rect x="0" y="230" width="1080" height="130" fill="#3fa34a"/>
          </svg>
          <div id="flash"></div>
        </div>
      </div>
      <div id="captions" class="clip" data-start="0" data-duration="{total}" data-track-index="2" data-layout-allow-overlap>
{captions}
      </div>
{audio}
    </div>
    <script>
      const D = {data};
      const tl = gsap.timeline({{ paused: true }});
      const parts = {{
        sagar: {{ eyes: ["open", "closed", "shock"], mouth: ["closed", "open", "o"], p: "sg" }},
        krishna: {{ eyes: ["open", "closed", "half"], mouth: ["closed", "open"], p: "kr" }},
      }};
      // face keyframes: show exactly one eye group and one mouth group at a time
      for (const who of ["sagar", "krishna"]) {{
        const P = parts[who];
        for (const [t, eyes, mouth, pose, sweat] of D.keys[who]) {{
          for (const e of P.eyes) tl.set(`#${{P.p}}-eyes-${{e}}`, {{ opacity: e === eyes ? 1 : 0 }}, t);
          for (const m of P.mouth) tl.set(`#${{P.p}}-mouth-${{m}}`, {{ opacity: m === mouth ? 1 : 0 }}, t);
          if (who === "sagar") {{
            tl.set("#sg-arms-pray", {{ opacity: pose === "pray" ? 1 : 0 }}, t);
            tl.set("#sg-sweat", {{ opacity: sweat ? 1 : 0 }}, t);
          }}
        }}
      }}
      // idle breathing (head leads, body follows, different rates per character)
      const breath = (sel, amt, per, delay) => {{
        const n = Math.max(1, Math.floor((D.total - delay) / per));
        tl.fromTo(sel, {{ scaleY: 1 }}, {{ scaleY: amt, duration: per / 2, ease: "sine.inOut", yoyo: true, repeat: n * 2 - 1,
          transformOrigin: "50% 100%" }}, delay);
      }};
      breath("#sg-body", 1.012, 2.6, 0); breath("#kr-body", 1.01, 3.1, 0.4);
      // head nods while speaking
      for (const who of ["sagar", "krishna"]) {{
        const head = who === "sagar" ? "#sg-head" : "#kr-head";
        for (const [s, d] of D.nods[who]) {{
          let t = s, dir = who === "sagar" ? 1 : -1, i = 0;
          while (t + 0.34 < s + d) {{
            tl.to(head, {{ rotation: dir * (i % 2 ? 1.2 : 2.6), y: i % 2 ? 0 : -4, duration: 0.34, ease: "sine.inOut",
              svgOrigin: "300 560" }}, t);
            t += 0.34; dir *= -1; i++;
          }}
          tl.to(head, {{ rotation: 0, y: 0, duration: 0.25, ease: "sine.out", svgOrigin: "300 560" }}, s + d);
        }}
      }}
      // Krishna appears with a divine flash
      tl.fromTo("#char-krishna", {{ opacity: 0, scale: 0.7, y: 60 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.45,
        ease: "back.out(1.8)", transformOrigin: "50% 100%" }}, D.krEnter);
      tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.08 }}, D.krEnter);
      tl.to("#flash", {{ opacity: 0, duration: 0.4, ease: "power2.out" }}, D.krEnter + 0.08);
      tl.fromTo("#kr-halo", {{ opacity: 0.3 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, D.krEnter);
      tl.to("#kr-halo", {{ opacity: 0.7, duration: 1.8, ease: "sine.inOut", yoyo: true,
        repeat: Math.max(1, Math.floor((D.total - D.krEnter) / 1.8)) }}, D.krEnter + 0.6);
      // clouds drift
      tl.fromTo("#clouds", {{ x: 0 }}, {{ x: 60, duration: D.total, ease: "none" }}, 0);
      // camera
      for (const c of D.cams) {{
        if (c.type === "punch") {{
          const ox = c.who === "sagar" ? "26%" : "74%";
          tl.to("#world", {{ scale: 1.16, transformOrigin: `${{ox}} 57%`, duration: 0.35, ease: "power3.out" }}, c.start);
          tl.to("#world", {{ scale: 1, duration: 0.3, ease: "power2.inOut" }}, c.start + c.dur + 0.1);
        }} else {{
          const xs = [18, -16, 12, -9, 6, -3, 0];
          xs.forEach((x, i) => tl.to("#world", {{ x, y: i % 2 ? 6 : -6, duration: 0.045, ease: "none" }}, c.start + i * 0.045));
          tl.to("#world", {{ y: 0, duration: 0.05 }}, c.start + xs.length * 0.045);
        }}
      }}
      // captions pop in
      document.querySelectorAll(".cap").forEach((el) => {{
        const s = parseFloat(el.dataset.start);
        tl.fromTo(el.querySelector("span"), {{ scale: 0.7, opacity: 0 }}, {{ scale: 1, opacity: 1, duration: 0.22,
          ease: "back.out(2.2)" }}, s);
      }});
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
