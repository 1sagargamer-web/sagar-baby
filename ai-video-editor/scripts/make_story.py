"""Build an "Uth Ja Sagar" motivational story reel (HyperFrames project) from a script file.
(The first channel, Bhagwan + Sagar cartoons, uses make_reel.py; this file does not touch it.)

Usage:
    python3 scripts/make_story.py channels/uth-ja-sagar/projects/<name>/script.json
    python3 scripts/make_story.py --finish <rendered.mp4> <Export/name-vN.mp4>   # loudness to -14 LUFS, video copied

script.json:
{
  "title": "haar-mat-maan",
  "heading": {"yellow": "Haar", "white": "Mat Maan", "emoji": "🔥"},
  "watermark": "Made By Sagar Mishra",           # optional (this is the default)
  "allow_clone": false,                          # true only when Sagar says he cannot record
  "gap": 0.35,                                   # seconds between lines (optional)
  "music": {"seed": 4, "volume": 0.6},           # optional, false = no music
  "lines": [
    {"hi": "हिंदी में लाइन ...",                    # what Sagar says; also the caption (word by word)
     "how": "calm, slow, a little sad",          # how to say it (sent to Sagar with the script)
     "prompt": "{SAGAR} sitting alone on a bench at night, rain", "seed": 3,   # the picture for this line
     "motion": "zoom-in",                        # zoom-in | zoom-out | pan-left | pan-right (optional, cycles)
     "audio": "Raw/ep01-line-01.wav",            # Sagar's recording (best take); missing -> clone if allowed
     "sfx": "soft-whoosh",                       # optional extra effect at the start of this line
     "seekh": true,                              # the lesson line: music lifts, riser + soft bell
     "pause_before": 0.3}
  ]
}
Paths in script.json are relative to the channel folder (channels/uth-ja-sagar/).
Writes <project>/index.html + assets/. Then check, snapshot and render with the HyperFrames CLI (see the channel CLAUDE.md).
"""
import difflib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent.parent  # ai-video-editor/
FPS = 30
TTS_PY = HERE / ".venv-tts" / "bin" / "python"
IMG_PY = HERE / ".venv-img" / "bin" / "python"
# Sagar's cloned voice (used only with "allow_clone": true). Tuned for a calm, natural narration.
CLONE = {"exaggeration": 0.5, "cfg": 0.4, "temperature": 0.75, "seed": 11, "tempo": 1.0}
CLEAN = (
    "highpass=f=70,"
    "silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.05,"
    "areverse,silenceremove=start_periods=1:start_threshold=-42dB:start_silence=0.1,areverse,"
    "loudnorm=I=-16:TP=-1.5"
)
MOTIONS = ["zoom-in", "pan-left", "zoom-out", "pan-right"]


def run(cmd, **kw):
    return subprocess.run([str(c) for c in cmd], check=True, **kw)


def clean(src: Path, out: Path, tempo: float = 1.0) -> None:
    af = CLEAN if tempo == 1.0 else f"rubberband=tempo={tempo}:formant=preserved:pitchq=quality," + CLEAN
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ac", "1", "-ar", "48000", out])


def norm(w: str) -> str:
    return "".join(ch for ch in w if ch.isalnum())


def word_times(wavs: list[Path], texts: list[str]) -> list[list[float]]:
    """Start time of every script word in each line, from Whisper word timings (one model load for all lines).
    The script's own spelling is shown; Whisper only gives the timing (matched by character position)."""
    from faster_whisper import WhisperModel

    mdir = HERE / "models" / "faster-whisper-large-v3"
    model = WhisperModel(str(mdir) if mdir.exists() else "large-v3", device="cpu", compute_type="int8",
                         cpu_threads=os.cpu_count() or 4)
    out = []
    for wav, text in zip(wavs, texts):
        segs, _ = model.transcribe(str(wav), language="hi", word_timestamps=True, vad_filter=False, beam_size=5)
        ws = [w for s in segs for w in (s.words or []) if norm(w.word)]
        words = [w for w in text.split() if norm(w)]
        dur = sf.info(str(wav)).duration
        if not ws:  # fall back: spread the words over the line by length
            lens = np.cumsum([0] + [len(norm(w)) for w in words])
            out.append([round(float(dur * 0.95 * l / lens[-1]), 3) for l in lens[:-1]])
            continue
        # cumulative character position -> time, from Whisper's words
        pos, times = [0.0], [ws[0].start]
        for w in ws:
            pos.append(pos[-1] + len(norm(w.word)))
            times.append(w.end)
        pos = np.array(pos) / pos[-1]
        starts_w = np.array([w.start for w in ws])
        lens = np.cumsum([0] + [len(norm(w)) for w in words])
        frac = lens[:-1] / lens[-1]
        t = []
        for f in frac:
            k = int(np.searchsorted(pos, f, side="right") - 1)
            k = min(k, len(ws) - 1)
            span = pos[k + 1] - pos[k] if k + 1 < len(pos) else 1
            inside = (f - pos[k]) / span if span > 0 else 0
            t.append(float(starts_w[k] + inside * (ws[k].end - ws[k].start)))
        out.append([round(max(0.0, x), 3) for x in t])
    return out


def pages(words: list[str], max_words: int = 5, max_chars: int = 28) -> list[list[int]]:
    """Group word indexes into caption pages."""
    res, cur, chars = [], [], 0
    for i, w in enumerate(words):
        if cur and (len(cur) >= max_words or chars + len(w) > max_chars):
            res.append(cur); cur, chars = [], 0
        cur.append(i); chars += len(w) + 1
    if cur:
        res.append(cur)
    return res


def duck(music: Path, out: Path, spans: list[tuple[float, float]], under: float = 0.42) -> None:
    """Lower the music while Sagar speaks (smooth 0.25 s ramps)."""
    x, sr = sf.read(str(music))
    n = len(x)
    g = np.ones(n)
    for a, b in spans:
        g[max(0, int((a - 0.1) * sr)):min(n, int((b + 0.1) * sr))] = under
    k = int(0.25 * sr)
    g = np.convolve(g, np.ones(k) / k, mode="same")
    sf.write(str(out), x * (g[:, None] if x.ndim > 1 else g), sr)


def finish(src: Path, dst: Path) -> None:
    """Two-pass loudness normalisation to -14 LUFS (true peak -1.5), video stream copied."""
    if dst.exists():
        sys.exit(f"{dst} already exists. Never overwrite an old version: use the next -vN.")
    r = subprocess.run(["ffmpeg", "-i", str(src), "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null",
                        "-"], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-c:v", "copy", "-af", af, "-ar", "48000", "-c:a", "aac", "-b:a",
         "192k", "-movflags", "+faststart", dst])
    print("finished", dst)


def build(script_path: Path) -> None:
    proj = script_path.parent
    chan = proj.parent.parent  # channels/<name>/
    spec = json.loads(script_path.read_text())
    gap = spec.get("gap", 0.35)
    lines = spec["lines"]
    adir, idir = proj / "assets" / "audio", proj / "assets" / "images"
    adir.mkdir(parents=True, exist_ok=True)
    idir.mkdir(parents=True, exist_ok=True)

    def cpath(p):
        p = Path(p)
        return p if p.is_absolute() else chan / p

    # ---- pictures (SDXL-Turbo), only the missing ones; delete a picture or change its seed to re-roll ----------
    sagar = json.loads((chan / "characters" / "sagar.json").read_text()) if (chan / "characters" / "sagar.json").exists() else {}
    jobs = []
    for i, l in enumerate(lines):
        img = idir / f"scene-{i + 1:02d}-s{l.get('seed', i + 1)}.png"
        l["_img"] = img
        if l.get("image"):
            shutil.copyfile(cpath(l["image"]), img)
        elif not img.exists():
            prompt = l["prompt"].replace("{SAGAR}", sagar.get("prompt", "a young Indian man"))
            jobs.append({"prompt": prompt, "out": str(img), "seed": l.get("seed", i + 1)})
    if jobs:
        batch = idir / "_jobs.json"
        batch.write_text(json.dumps(jobs, ensure_ascii=False))
        run([IMG_PY, HERE / "scripts" / "make_image.py", "--batch", batch])
        batch.unlink()

    # ---- voice: Sagar's recordings; clone only when allowed ----------------------------------------------------
    wavs = [adir / f"line-{i + 1:02d}.wav" for i in range(len(lines))]
    missing = [i for i, l in enumerate(lines) if not l.get("audio")]
    if missing and not spec.get("allow_clone"):
        print("PICTURES READY. WAITING FOR SAGAR'S RECORDINGS. Lines to record (say each one 2 times):")
        for i in missing:
            print(f"  {i + 1}. {lines[i]['hi']}   ({lines[i].get('how', 'natural')})")
        return
    clone_jobs = []
    for i, (l, wav) in enumerate(zip(lines, wavs)):
        if l.get("audio"):
            clean(cpath(l["audio"]), wav)
        elif not (wav.exists() and l.get("keep_audio")):
            clone_jobs.append({"text": l["hi"], "out": str(wav.with_suffix(".raw.wav")), "exaggeration":
                               l.get("exaggeration", CLONE["exaggeration"])})
    if clone_jobs:
        ref = cpath(spec["clone_ref"]) if spec.get("clone_ref") else chan / "voices" / "sagar-ref.wav"  # override = tests only
        if not ref.exists():
            sys.exit(f"Missing {ref} (cut it from Sagar's 30-60 s recording; private, never in git).")
        batch = adir / "_clone-jobs.json"
        batch.write_text(json.dumps(clone_jobs, ensure_ascii=False))
        run([TTS_PY, HERE / "scripts" / "clone_voice.py", ref, "--batch", batch, "--cfg", CLONE["cfg"],
             "--temperature", CLONE["temperature"], "--seed", CLONE["seed"]])
        batch.unlink()
        for j in clone_jobs:
            raw = Path(j["out"])
            clean(raw, raw.with_name(raw.name.replace(".raw", "")), CLONE["tempo"])
            raw.unlink()

    # ---- timeline ----------------------------------------------------------------------------------------------
    t = 0.2
    for l, wav in zip(lines, wavs):
        t += l.get("pause_before", 0)
        l["_start"], l["_dur"] = round(t, 3), round(sf.info(str(wav)).duration, 3)
        t += l["_dur"] + gap
    total = round(lines[-1]["_start"] + lines[-1]["_dur"] + 1.2, 2)
    starts = [round(max(0.0, l["_start"] - 0.15), 3) for l in lines]
    starts[0] = 0.0

    # ---- captions: word timings from Whisper ------------------------------------------------------------------
    texts = [l["hi"] for l in lines]
    wt = word_times(wavs, texts)
    cap_html, cap_keys = [], []
    for i, (l, times) in enumerate(zip(lines, wt)):
        words = [w for w in l["hi"].split() if norm(w)]
        for p, idx in enumerate(pages(words)):
            pid = f"cap-{i + 1}-{p + 1}"
            p_start = l["_start"] + times[idx[0]] - 0.08 if p else starts[i]
            nxt = pages(words)[p + 1][0] if p + 1 < len(pages(words)) else None
            p_end = (l["_start"] + times[nxt] - 0.08) if nxt is not None else (starts[i + 1] if i + 1 < len(lines) else total)
            spans = " ".join(f'<span id="{pid}-w{k}">{words[k]}</span>' for k in idx)
            cap_html.append(f'        <div id="{pid}" class="clip cap" data-start="{round(p_start, 3)}" '
                            f'data-duration="{round(p_end - p_start, 3)}" data-track-index="5">{spans}</div>')
            cap_keys.append({"id": pid, "words": [[f"{pid}-w{k}", round(l["_start"] + times[k], 3)] for k in idx],
                             "start": round(p_start, 3)})

    # ---- pictures on the timeline -----------------------------------------------------------------------------
    pic_html, pics = [], []
    for i, l in enumerate(lines):
        rel = l["_img"].relative_to(proj).as_posix()
        end = starts[i + 1] + 0.3 if i + 1 < len(lines) else total
        pic_html.append(f'          <img id="pic-{i + 1}" class="pic" src="{rel}" alt="">')
        pics.append({"id": f"pic-{i + 1}", "start": starts[i], "end": round(end, 3),
                     "motion": l.get("motion", MOTIONS[i % len(MOTIONS)])})

    # ---- audio: voice, music (ducked), sfx --------------------------------------------------------------------
    audio = []
    for i, (l, wav) in enumerate(zip(lines, wavs)):
        audio.append(f'      <audio id="vo-{i + 1}" class="clip" src="{wav.relative_to(proj).as_posix()}" '
                     f'data-start="{l["_start"]}" data-duration="{l["_dur"]}" data-track-index="3" data-volume="1"></audio>')
    seekh = next((l for l in lines if l.get("seekh")), None)
    music = spec.get("music", {})
    if music is not False:
        seed = music.get("seed", sum(map(ord, spec.get("title", proj.name))) % 1000)
        raw, mwav = adir / "music-raw.wav", adir / "music.wav"
        run([sys.executable, HERE / "scripts" / "make_piano.py", raw, "--seconds", total, "--seed", seed,
             "--lift", seekh["_start"] if seekh else total * 0.72])
        duck(raw, mwav, [(l["_start"], l["_start"] + l["_dur"]) for l in lines])
        raw.unlink()
        audio.append(f'      <audio id="music" class="clip" src="{mwav.relative_to(proj).as_posix()}" data-start="0" '
                     f'data-duration="{total}" data-track-index="6" data-volume="{music.get("volume", 0.6)}"></audio>')
    sfx_lib = HERE / "sfx"
    if not (sfx_lib / "soft-bell.wav").exists():
        run([sys.executable, HERE / "scripts" / "make_sfx.py", sfx_lib, "--story"])
    events = []
    if len(lines) > 1:
        events.append(("soft-whoosh", starts[1] - 0.35))
    for l in lines:
        if l.get("sfx"):
            events.append((l["sfx"], l["_start"] - (0.35 if l["sfx"] == "soft-whoosh" else 0)))
        if l.get("seekh"):
            events += [("riser", l["_start"] - 2.2), ("soft-bell", l["_start"] + 0.05)]
    vols = {"soft-whoosh": 0.5, "riser": 0.45, "soft-bell": 0.45}
    if spec.get("sfx", True) is not False:
        for k, (name, at) in enumerate(sorted(events, key=lambda e: e[1])):
            dst = adir / f"sfx-{name}.wav"
            shutil.copyfile(sfx_lib / f"{name}.wav", dst)
            audio.append(f'      <audio id="sfx-{k + 1}" class="clip" src="{dst.relative_to(proj).as_posix()}" '
                         f'data-start="{max(0.0, round(at, 3))}" data-duration="{round(sf.info(str(dst)).duration, 3)}" '
                         f'data-track-index="7" data-volume="{vols.get(name, 0.5)}"></audio>')

    # ---- fonts + HTML -----------------------------------------------------------------------------------------
    fdir = proj / "assets" / "fonts"
    shutil.copytree(chan / "assets" / "fonts", fdir, dirs_exist_ok=True)
    h = spec.get("heading", {"yellow": spec.get("title", ""), "white": "", "emoji": ""})
    html = TEMPLATE.format(
        total=total, yellow=h.get("yellow", ""), white=h.get("white", ""), emoji=h.get("emoji", ""),
        watermark=spec.get("watermark", "Made By Sagar Mishra"), pics="\n".join(pic_html),
        captions="\n".join(cap_html), audio="\n".join(audio),
        data=json.dumps({"total": total, "pics": pics, "caps": cap_keys}, ensure_ascii=False),
    )
    (proj / "index.html").write_text(html)
    print(f"built {proj / 'index.html'}  duration={total}s  lines={len(lines)}")


TEMPLATE = """<!doctype html>
<html lang="hi" data-resolution="portrait">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <link rel="stylesheet" href="assets/fonts/fonts.css" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1080px; height: 1920px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 100%; height: 100%; font-family: "Baloo2", "Noto Color Emoji", sans-serif; }}
      #title {{ position: absolute; top: 250px; left: 0; width: 1080px; text-align: center; color: #fff; font-weight: 800;
        font-size: 84px; line-height: 1.05; }}
      #title b {{ color: #ffcf3a; }}
      #frame {{ position: absolute; top: 420px; left: 0; width: 1080px; height: 1080px; overflow: hidden; background: #111; }}
      .pic {{ position: absolute; inset: 0; width: 100%; height: 100%; object-fit: cover; opacity: 0; }}
      #watermark {{ position: absolute; top: 1440px; left: 0; width: 1080px; text-align: center; font-weight: 600;
        font-size: 30px; color: rgba(255,255,255,0.6); text-shadow: 0 2px 6px rgba(0,0,0,0.7); }}
      .cap {{ position: absolute; top: 1560px; left: 0; width: 1080px; padding: 0 70px; text-align: center;
        font-weight: 800; font-size: 62px; line-height: 1.3; }}
      .cap span {{ color: rgba(255,255,255,0.28); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <div id="title" class="clip" data-start="0" data-duration="{total}" data-track-index="1"><b>{yellow}</b> {white} {emoji}</div>
      <div id="frame" class="clip" data-start="0" data-duration="{total}" data-track-index="0" data-layout-allow-overlap>
{pics}
      </div>
      <div id="watermark" class="clip" data-start="0" data-duration="{total}" data-track-index="8">{watermark}</div>
      <div id="captions" class="clip" data-start="0" data-duration="{total}" data-track-index="2" data-layout-allow-overlap>
{captions}
      </div>
{audio}
    </div>
    <script>
      const D = {data};
      const tl = gsap.timeline({{ paused: true }});
      // pictures: crossfade in, slow Ken Burns move for the whole time on screen
      D.pics.forEach((p, i) => {{
        const el = "#" + p.id, d = p.end - p.start;
        tl.set(el, {{ zIndex: i + 1 }}, 0);
        tl.fromTo(el, {{ opacity: 0 }}, {{ opacity: 1, duration: i ? 0.3 : 0.01, ease: "none" }}, p.start);
        const m = {{
          "zoom-in": [{{ scale: 1.0, x: 0 }}, {{ scale: 1.1, x: 0 }}],
          "zoom-out": [{{ scale: 1.1, x: 0 }}, {{ scale: 1.0, x: 0 }}],
          "pan-left": [{{ scale: 1.1, x: 35 }}, {{ scale: 1.1, x: -35 }}],
          "pan-right": [{{ scale: 1.1, x: -35 }}, {{ scale: 1.1, x: 35 }}],
        }}[p.motion] || [{{ scale: 1, x: 0 }}, {{ scale: 1.08, x: 0 }}];
        tl.fromTo(el, m[0], {{ ...m[1], duration: d, ease: "none" }}, p.start);
        if (i < D.pics.length - 1) tl.set(el, {{ opacity: 0 }}, p.end);
      }});
      // captions: words go white when spoken, the current word is yellow
      D.caps.forEach((c) => {{
        tl.fromTo("#" + c.id, {{ opacity: 0, y: 12 }}, {{ opacity: 1, y: 0, duration: 0.15, ease: "power2.out" }}, c.start);
        c.words.forEach(([id, t], k) => {{
          tl.set("#" + id, {{ color: "#ffcf3a" }}, t);
          const next = c.words[k + 1];
          if (next) tl.set("#" + id, {{ color: "#ffffff" }}, next[1]);
        }});
      }});
      window.__timelines["main"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    if len(sys.argv) >= 4 and sys.argv[1] == "--finish":
        finish(Path(sys.argv[2]), Path(sys.argv[3]))
    elif len(sys.argv) >= 2:
        build(Path(sys.argv[1]).resolve())
    else:
        sys.exit(__doc__)
