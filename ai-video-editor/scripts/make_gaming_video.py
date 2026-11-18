"""Build a long gaming-channel video (1920x1080, 30 fps) from a plan file, as a HyperFrames project.

Usage:
    python3 scripts/make_gaming_video.py channels/gaming/projects/<name>/plan.json

Then, inside channels/gaming/projects/<name>/ run the HyperFrames check, snapshot and
`render --quality looks -o ../../Export/<name>-v1.mp4`, and finally
    python3 scripts/make_gaming_video.py channels/gaming/projects/<name>/plan.json --report ../../Export/<name>-v1.mp4
to print duration and loudness.

How it works: FFmpeg prepares every gameplay clip (trim, speed, crop to 16:9, blur boxes, black-and-white) into
assets/video/; the voice (Sagar's recording or clone D), music (new per video), SFX (new pack per video) and game
sound are mixed by FFmpeg into one assets/audio/mix.wav (music ducked under the voice, -14 LUFS); index.html lays
out clips, motion graphics and captions on one GSAP timeline.

plan.json (paths are relative to the channel folder unless absolute):
{
  "title": "ep01-panel-24h",            # also seeds this video's music + SFX pack (or "seed": 123)
  "accent": "#ffd400",                  # optional; otherwise picked per video from the channel palette
  "voice": "clone",                     # "clone" (option D) or "recording" (wait for Sagar's audio files)
  "game_volume": 0.3,                   # game sound under everything (ducked further under the voice)
  "sources": {"m1": "Raw/ep01/match1.mp4"},
  "segments": [
    {"type": "disclaimer", "dur": 4},
    {"type": "hook", "cards": [{"text": "AAJ HUM", "color": "white"},
                               {"text": "PANEL", "color": "red", "clip": {"src": "m1", "in": 12.0}}],
     "vo": [{"hi": "तो गाइस ...", "caption": "To guys, kya aapne *kabhi* socha hai..."}]},
    {"type": "title", "text": "24 HOURS", "sub": "PANEL TEST", "dur": 2.6},
    {"type": "clip", "src": "m1", "in": 30, "out": 58, "speed": 1, "bw": false, "label": "MATCH 1",
     "badge": "HOUR 1", "music": "hype",
     "zooms": [{"at": 3.2, "dur": 1.4, "x": 0.7, "y": 0.3, "scale": 1.4}],
     "blur": [{"x": 0.0, "y": 0.1, "w": 0.3, "h": 0.5, "from": 0, "to": 28}],
     "callouts": [{"at": 6, "dur": 2.2, "x": 0.72, "y": 0.05, "w": 0.26, "h": 0.2, "text": "KILL FEED"}],
     "vo": [{"at": 0.4, "hi": "...", "caption": "Dekho *bhai* ..."}],
     "captions": [{"at": 9.0, "dur": 1.0, "text": "BHAI BHAI BHAI", "color": "yellow"}],
     "sfx": [{"name": "ding", "at": 2.0}], "subscribe": 15, "fx": "glitch", "reveal": true},
    {"type": "endcard", "lines": ["Panel = ID ban", "Cheater dikhe to report karo"], "dur": 8}
  ]
}
Caption marks: *word* = yellow, !word! = red. Times inside a clip are seconds from the clip's start (after speed).
"fx": "glitch" = glitch transition into the clip; "reveal": true = riser before + bass drop (music cuts to suspense
unless "music" says otherwise). Voice lines may carry "audio": "Raw/..." (Sagar's recording, wins over the clone),
"take": "<Hindi text>" to pick the best take from a multi-take recording, "excited": true for more energy.
"""
import hashlib
import html
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / "scripts"))
from make_reel import clean, drop_stray_tail  # noqa: E402  (shared helpers, unchanged)

W, H, FPS = 1920, 1080, 30
SR = 48000
TTS_PY = HERE / ".venv-tts" / "bin" / "python"
PALETTE = ["#ffd400", "#00e5ff", "#ff3d7f", "#7cff4f", "#ff8a00", "#b388ff"]
COLORS = {"white": "#ffffff", "yellow": "#ffd400", "red": "#ff2b2b", "green": "#2bff5a", "blue": "#2bb8ff"}
# Clone option D, chosen by Sagar. Never change between videos.
VOICE_D = {"ref": "voices/sagar-ref-chat.wav", "exaggeration": 0.55, "excited": 0.70, "cfg": 0.3, "temperature": 0.9,
           "seed": 11, "tempo": 1.05}
POLISH = "highpass=f=80,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5"
SFX_VOL = {"whoosh": 0.45, "impact": 0.55, "riser": 0.45, "glitch": 0.5, "pop": 0.5, "ding": 0.4, "bass-drop": 0.6,
           "error": 0.4, "click": 0.4, "swell": 0.45}


def run(cmd):
    subprocess.run([str(c) for c in cmd], check=True)


def dur_of(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
                         capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def loudnorm_2pass(src, out, target=-14.0):
    """Measure, then normalise to `target` LUFS (true peak -1 dB); a limiter first so SFX peaks do not hold it back."""
    pre = "alimiter=limit=0.6:attack=3:release=60:level=false"
    res = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(src), "-af",
                          f"{pre},loudnorm=I={target}:TP=-1:LRA=11:print_format=json", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    m = json.loads(res[res.rindex("{"):res.rindex("}") + 1])
    af = (f"{pre},loudnorm=I={target}:TP=-1:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:"
          f"measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true")
    run(["ffmpeg", "-v", "error", "-y", "-i", src, "-af", af, "-ar", SR, out])


def stable_seed(text):
    return int(hashlib.md5(text.encode()).hexdigest()[:6], 16) % 100000


# ---------------------------------------------------------------- voice ---------------------------------------------
def make_voice(lines, chan, proj, mode):
    """lines: dicts with hi/caption/(audio/take/excited). Writes each line's wav, returns paths (None = waiting)."""
    vdir = proj / "assets" / "audio" / "vo"
    vdir.mkdir(parents=True, exist_ok=True)
    paths, jobs, waiting = [], [], []
    for line in lines:
        key = hashlib.md5(json.dumps([line.get("hi"), line.get("audio"), line.get("take"), line.get("excited"),
                                      VOICE_D], ensure_ascii=False).encode()).hexdigest()[:10]
        out = vdir / f"vo-{key}.wav"
        paths.append(out)
        if out.exists():
            continue
        if line.get("audio"):
            src = Path(line["audio"])
            src = src if src.is_absolute() else chan / src
            if line.get("take"):  # several takes in one file: keep the best (scores printed for Sagar)
                best = out.with_suffix(".take.wav")
                run([sys.executable, HERE / "scripts" / "pick_takes.py", src, line["take"], best])
                src = best
            raw = out.with_suffix(".rec.wav")
            clean(src, raw)
            run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", POLISH, "-ac", "1", "-ar", SR, out])
            raw.unlink()
        elif mode == "recording":
            waiting.append(line)
        else:
            jobs.append({"text": line["hi"], "out": str(out.with_suffix(".raw.wav")),
                         "exaggeration": VOICE_D["excited"] if line.get("excited") else VOICE_D["exaggeration"],
                         "cfg": VOICE_D["cfg"]})
    if waiting:
        print("WAITING FOR SAGAR'S RECORDINGS. Lines to record:")
        for n, line in enumerate(waiting, 1):
            print(f"  {n}. {line.get('caption') or line['hi']}")
        sys.exit(2)
    if jobs:
        ref = chan / VOICE_D["ref"]
        if not ref.exists():
            sys.exit(f"Missing voice reference {ref} (see channels/gaming/CLAUDE.md, Voice).")
        batch = vdir / "_jobs.json"
        batch.write_text(json.dumps(jobs, ensure_ascii=False))
        run([TTS_PY, HERE / "scripts" / "clone_voice.py", ref, "--batch", batch, "--seed", VOICE_D["seed"],
             "--temperature", VOICE_D["temperature"]])
        for j in jobs:
            raw, out = Path(j["out"]), Path(j["out"].replace(".raw.wav", ".wav"))
            tmp = out.with_suffix(".tmp.wav")
            clean(raw, tmp, VOICE_D["tempo"])
            drop_stray_tail(tmp)
            run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af", POLISH, "-ac", "1", "-ar", SR, out])
            raw.unlink()
            tmp.unlink()
        batch.unlink()
    return paths


# ---------------------------------------------------------------- clips ---------------------------------------------
def prep_clip(src, start, end, speed, bw, blurs, out, panel=False):
    """Trim + speed + cover-crop to 16:9 + blur boxes + optional B&W. Writes video (no audio) and a .wav of its sound."""
    if out.exists() and out.with_suffix(".wav").exists():
        return dur_of(out)
    length = (end - start)
    vf = [f"setpts=(PTS-STARTPTS)/{speed}", f"fps={FPS}",
          f"scale={W}:{H}:force_original_aspect_ratio=increase", f"crop={W}:{H}", "setsar=1"]
    chain = ",".join(vf)
    graph = f"[0:v]{chain}[v0]"
    last = "v0"
    for k, b in enumerate(blurs):
        x, y = int(b["x"] * W) // 2 * 2, int(b["y"] * H) // 2 * 2
        w, h = max(16, int(b["w"] * W) // 2 * 2), max(16, int(b["h"] * H) // 2 * 2)
        t0, t1 = b.get("from", 0), b.get("to", 1e6)
        graph += (f";[{last}]split[a{k}][b{k}];[b{k}]crop={w}:{h}:{x}:{y},boxblur=24:3[bb{k}];"
                  f"[a{k}][bb{k}]overlay={x}:{y}:enable='between(t,{t0},{t1})'[v{k + 1}]")
        last = f"v{k + 1}"
    if bw:
        graph += f";[{last}]hue=s=0,eq=contrast=1.15[vbw]"
        last = "vbw"
    if panel:
        graph += f";[{last}]scale=1280:720[vp]"
        last = "vp"
    run(["ffmpeg", "-v", "error", "-y", "-ss", start, "-t", length, "-i", src, "-filter_complex", graph, "-map",
         f"[{last}]", "-an", "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-g", FPS, "-pix_fmt", "yuv420p", out])
    # game sound of the same span (silence if the source has none)
    atempo = []
    s = speed
    while s > 2.0:
        atempo.append("atempo=2.0"); s /= 2.0
    while s < 0.5:
        atempo.append("atempo=0.5"); s /= 0.5
    atempo.append(f"atempo={s}")
    has_audio = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index",
                                "-of", "csv=p=0", str(src)], capture_output=True, text=True).stdout.strip()
    d = length / speed
    if has_audio:
        run(["ffmpeg", "-v", "error", "-y", "-ss", start, "-t", length, "-i", src, "-vn", "-af",
             ",".join(atempo) + f",apad,atrim=0:{d}", "-ac", "2", "-ar", SR, out.with_suffix(".wav")])
    else:
        run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-t", d, "-i", f"anullsrc=r={SR}:cl=stereo",
             out.with_suffix(".wav")])
    return dur_of(out)


# ---------------------------------------------------------------- captions ------------------------------------------
def caption_chunks(text, start, dur, max_words=3):
    """Split a Roman caption into 1-3 word pops timed across the spoken line (by character length)."""
    words = text.split()
    chunks, cur = [], []
    for w in words:
        cur.append(w)
        if len(cur) >= max_words or re.search(r"[,.!?…]$", w.strip("*!")):
            chunks.append(cur); cur = []
    if cur:
        chunks.append(cur)
    total = sum(len(" ".join(c)) for c in chunks) or 1
    t, out = start, []
    for c in chunks:
        d = dur * len(" ".join(c)) / total
        out.append((round(t, 3), round(max(0.25, d), 3), c))
        t += d
    return out


def caption_html(words):
    parts = []
    for w in words:
        m = re.match(r"^\*(.+)\*([,.!?]*)$", w) or re.match(r"^!(.+)!([,.!?]*)$", w)
        if m:
            cls = "hl" if w.startswith("*") else "dg"
            parts.append(f'<b class="{cls}">{html.escape(m.group(1))}</b>{html.escape(m.group(2))}')
        else:
            parts.append(html.escape(w))
    return " ".join(parts)


# ---------------------------------------------------------------- build ---------------------------------------------
def build(plan_path: Path):
    proj = plan_path.parent.resolve()
    chan = proj.parent.parent
    plan = json.loads(plan_path.read_text())
    title = plan.get("title", proj.name)
    seed = plan.get("seed", stable_seed(title))
    rng = np.random.default_rng(seed)
    accent = plan.get("accent", PALETTE[seed % len(PALETTE)])
    mode = plan.get("voice", "clone")
    for sub in ("video", "audio", "fonts", "img", "sfx"):
        (proj / "assets" / sub).mkdir(parents=True, exist_ok=True)
    shutil.copyfile(HERE / "fonts" / "Anton-Regular.woff2", proj / "assets" / "fonts" / "Anton-Regular.woff2")
    shutil.copyfile(chan / "Reference" / "disclaimer.png", proj / "assets" / "img" / "disclaimer.png")
    sfx_dir = proj / "assets" / "sfx"
    if not (sfx_dir / "impact.wav").exists():  # this video's own SFX pack
        run([sys.executable, HERE / "scripts" / "make_gaming_sfx.py", sfx_dir, "--seed", seed])
    sources = {k: (Path(v) if Path(v).is_absolute() else chan / v) for k, v in plan.get("sources", {}).items()}

    # 1) voice for every line, in plan order
    all_lines = [ln for seg in plan["segments"] for ln in seg.get("vo", [])]
    vo_paths = make_voice(all_lines, chan, proj, mode)
    vo_iter = iter(vo_paths)

    # 2) timeline
    T = 0.0
    els, tweens, audio_events, sfx_events, captions, music_marks, warnings = [], [], [], [], [], [], []
    game_tracks = []  # (start, wav, volume)
    vid = 0

    def sfx(name, at, gain=1.0):
        sfx_events.append((name, max(0.0, at), SFX_VOL.get(name, 0.5) * gain))

    def card(text, color, start, d, size=200, cls="card"):
        nonlocal vid
        vid += 1
        cid = f"c{vid}"
        col = COLORS.get(color, color)
        els.append(f'<div id="{cid}" class="clip {cls}" data-start="{start:.3f}" data-duration="{d:.3f}" '
                   f'data-track-index="2"><span id="{cid}t" style="color:{col};font-size:{size}px">'
                   f'{html.escape(text)}</span></div>')
        tweens.append(f'tl.fromTo("#{cid}t",{{scale:0.55,opacity:0}},{{scale:1,opacity:1,duration:0.16,'
                      f'ease:"back.out(2.5)"}},{start:.3f});')
        tweens.append(f'tl.to("#{cid}t",{{scale:1.08,duration:{max(0.1, d - 0.2):.3f},ease:"none"}},{start + 0.16:.3f});')
        return cid

    for si, seg in enumerate(plan["segments"]):
        typ = seg["type"]
        if seg.get("music"):
            music_marks.append((T, seg["music"]))
        if typ == "disclaimer":
            d = seg.get("dur", 4)
            els.append(f'<img id="disc" class="clip full" src="assets/img/disclaimer.png" data-start="{T:.3f}" '
                       f'data-duration="{d:.3f}" data-track-index="1">')
            T += d
        elif typ == "hook":
            lines = seg.get("vo", [])
            vstart = T + 0.15
            t = vstart
            for ln in lines:
                p = next(vo_iter)
                d = dur_of(p)
                audio_events.append((t, p))
                captions.append((t, d, ln.get("caption", "")))
                t += d + 0.25
            vo_total = t - vstart
            cards = seg.get("cards", [])
            base = [c.get("dur", 0.8) for c in cards]
            scale = max(1.0, vo_total / max(0.1, sum(base)))  # stretch cards to cover the voice
            ct = T
            for c, bd in zip(cards, base):
                d = bd * scale
                if c.get("clip"):
                    cl = c["clip"]
                    vid += 1
                    out = proj / "assets" / "video" / f"hook-{si}-{vid}.mp4"
                    prep_clip(sources[cl["src"]], cl["in"], cl["in"] + d + 0.2, cl.get("speed", 1), True,
                              cl.get("blur", []), out, panel=True)
                    els.append(f'<div class="panelwrap" id="pw{vid}"><video id="v{vid}" class="clip panel" '
                               f'src="assets/video/{out.name}" data-start="{ct:.3f}" data-duration="{d:.3f}" '
                               f'data-track-index="1" muted></video></div>')
                    tweens.append(f'tl.fromTo("#pw{vid}",{{scale:0.92,rotation:{rng.uniform(-2.5, 2.5):.2f}}},'
                                  f'{{scale:1.0,rotation:0,duration:{d:.3f},ease:"none"}},{ct:.3f});')
                    card(c["text"], c.get("color", "white"), ct, d, 150, "card low")
                else:
                    card(c["text"], c.get("color", "white"), ct, d, c.get("size", 210))
                sfx("whoosh", ct - 0.08, 0.8)
                if c.get("color") in ("red", "yellow") or c.get("impact"):
                    sfx("impact", ct, 0.7)
                ct += d
            T = max(ct, T + vo_total + 0.2)
        elif typ == "title":
            d = seg.get("dur", 2.6)
            vid += 1
            tid = f"t{vid}"
            sub = html.escape(seg.get("sub", ""))
            els.append(f'<div id="{tid}" class="clip title" data-start="{T:.3f}" data-duration="{d:.3f}" '
                       f'data-track-index="2"><div class="stripes" id="{tid}s"></div>'
                       f'<div class="tbig" id="{tid}b">{html.escape(seg["text"])}</div>'
                       f'<div class="tsub" id="{tid}u">{sub}</div><div class="tbar" id="{tid}r"></div></div>')
            tweens += [
                f'tl.fromTo("#{tid}s",{{x:-300}},{{x:0,duration:{d:.3f},ease:"none"}},{T:.3f});',
                f'tl.fromTo("#{tid}b",{{scale:2.2,opacity:0}},{{scale:1,opacity:1,duration:0.22,ease:"power4.out"}},{T + 0.05:.3f});',
                f'tl.fromTo("#{tid}r",{{scaleX:0}},{{scaleX:1,duration:0.35,ease:"power3.out"}},{T + 0.25:.3f});',
                f'tl.fromTo("#{tid}u",{{y:40,opacity:0}},{{y:0,opacity:1,duration:0.3,ease:"power3.out"}},{T + 0.35:.3f});',
                f'tl.to("#{tid}b",{{scale:1.06,duration:{d - 0.3:.3f},ease:"none"}},{T + 0.27:.3f});',
            ]
            sfx("whoosh", T - 0.1)
            sfx("impact", T + 0.05)
            T += d
        elif typ == "clip":
            if seg.get("label"):
                d = seg.get("label_dur", 1.0)
                card(seg["label"], accent, T, d, 190)
                sfx("whoosh", T - 0.08)
                sfx("impact", T + 0.02, 0.6)
                T += d
            speed = seg.get("speed", 1)
            vid += 1
            n = vid
            out = proj / "assets" / "video" / f"clip-{si:03d}.mp4"
            d = prep_clip(sources[seg["src"]], seg["in"], seg["out"], speed, seg.get("bw", False), seg.get("blur", []), out)
            if seg.get("reveal"):
                sfx("riser", T - 2.4)
                sfx("bass-drop", T)
                sfx("impact", T, 0.8)
                if not seg.get("music"):
                    music_marks.append((T, "suspense"))
            els.append(f'<div class="vwrap" id="w{n}"><video id="v{n}" class="clip full" src="assets/video/{out.name}" '
                       f'data-start="{T:.3f}" data-duration="{d:.3f}" data-track-index="0" muted></video></div>')
            game_tracks.append((T, out.with_suffix(".wav"), seg.get("game_volume", plan.get("game_volume", 0.3))))
            for z in seg.get("zooms", []):
                zt, zd, sc = T + z["at"], z.get("dur", 1.2), z.get("scale", 1.35)
                ox, oy = z.get("x", 0.5) * 100, z.get("y", 0.5) * 100
                tweens.append(f'tl.set("#w{n}",{{transformOrigin:"{ox:.1f}% {oy:.1f}%"}},{zt:.3f});')
                tweens.append(f'tl.to("#w{n}",{{scale:{sc},duration:0.16,ease:"power3.out"}},{zt:.3f});')
                tweens.append(f'tl.to("#w{n}",{{scale:1,duration:0.25,ease:"power2.inOut"}},{zt + zd:.3f});')
                sfx("whoosh", zt - 0.05, 0.6)
            if seg.get("fx") == "glitch":
                gid = f"g{n}"
                els.append(f'<div id="{gid}" class="clip glitch" data-start="{T:.3f}" data-duration="0.6" '
                           f'data-track-index="3">' + "".join(
                               f'<i style="top:{rng.uniform(0, 95):.1f}%;height:{rng.uniform(2, 9):.1f}%;'
                               f'background:{rng.choice(["#ff0040", "#00f0ff", "#ffffff", "#000"])}"></i>'
                               for _ in range(9)) + '</div>')
                for k in range(6):
                    tweens.append(f'tl.set("#w{n}",{{x:{rng.uniform(-40, 40):.0f}}},{T + k * 0.07:.3f});')
                    tweens.append(f'tl.set("#{gid}",{{opacity:{0.9 if k % 2 == 0 else 0.3},x:{rng.uniform(-60, 60):.0f}}},'
                                  f'{T + k * 0.07:.3f});')
                tweens.append(f'tl.set("#w{n}",{{x:0}},{T + 0.45:.3f});')
                tweens.append(f'tl.set("#{gid}",{{opacity:0}},{T + 0.45:.3f});')
                sfx("glitch", T)
                sfx("error", T + 0.15, 0.8)
            if seg.get("badge"):
                bid = f"b{n}"
                els.append(f'<div id="{bid}" class="clip badge" data-start="{T:.3f}" data-duration="{d:.3f}" '
                           f'data-track-index="4"><span id="{bid}s">{html.escape(seg["badge"])}</span></div>')
                tweens.append(f'tl.fromTo("#{bid}s",{{x:260}},{{x:0,duration:0.3,ease:"power3.out"}},{T + 0.2:.3f});')
            for k, c in enumerate(seg.get("callouts", [])):
                cid = f"k{n}x{k}"
                x, y, w, h = c["x"] * W, c["y"] * H, c["w"] * W, c["h"] * H
                lab_y = y + h + 14 if y + h + 90 < H else y - 80
                els.append(f'<div id="{cid}" class="clip callout" data-start="{T + c["at"]:.3f}" '
                           f'data-duration="{c.get("dur", 2.0):.3f}" data-track-index="4">'
                           f'<div class="cbox" id="{cid}b" style="left:{x:.0f}px;top:{y:.0f}px;width:{w:.0f}px;height:{h:.0f}px"></div>'
                           f'<div class="clab" id="{cid}l" style="left:{x:.0f}px;top:{lab_y:.0f}px">{html.escape(c["text"])}</div></div>')
                tweens.append(f'tl.fromTo("#{cid}b",{{scale:1.3,opacity:0}},{{scale:1,opacity:1,duration:0.2,ease:"back.out(2)"}},'
                              f'{T + c["at"]:.3f});')
                tweens.append(f'tl.fromTo("#{cid}l",{{y:20,opacity:0}},{{y:0,opacity:1,duration:0.2}},{T + c["at"] + 0.1:.3f});')
                sfx("pop", T + c["at"])
            if seg.get("subscribe") is not None:
                st = T + seg["subscribe"]
                sid = f"s{n}"
                els.append(f'<div id="{sid}" class="clip sub" data-start="{st:.3f}" data-duration="3.2" data-track-index="5">'
                           f'<span id="{sid}s"><b>&#9654;</b> SUBSCRIBE</span></div>')
                tweens.append(f'tl.fromTo("#{sid}s",{{x:-500}},{{x:0,duration:0.35,ease:"back.out(1.6)"}},{st:.3f});')
                tweens.append(f'tl.to("#{sid}s",{{scale:0.92,duration:0.12,yoyo:true,repeat:1}},{st + 1.2:.3f});')
                tweens.append(f'tl.to("#{sid}s",{{x:-500,duration:0.3,ease:"power2.in"}},{st + 2.85:.3f});')
                sfx("pop", st)
                sfx("click", st + 1.2)
            for ln in seg.get("vo", []):
                p = next(vo_iter)
                vd = dur_of(p)
                at = T + ln.get("at", 0)
                if ln.get("at", 0) + vd > d + 0.5:
                    warnings.append(f"segment {si}: voice line runs {ln.get('at', 0) + vd - d:.1f}s past the clip end")
                audio_events.append((at, p))
                captions.append((at, vd, ln.get("caption", "")))
            for c in seg.get("captions", []):
                vid += 1
                kid = f"q{vid}"
                col = COLORS.get(c.get("color", "white"), c.get("color", "#fff"))
                els.append(f'<div id="{kid}" class="clip bigcap" data-start="{T + c["at"]:.3f}" '
                           f'data-duration="{c.get("dur", 1.0):.3f}" data-track-index="6"><span id="{kid}s" '
                           f'style="color:{col}">{html.escape(c["text"])}</span></div>')
                tweens.append(f'tl.fromTo("#{kid}s",{{scale:0.5,opacity:0}},{{scale:1,opacity:1,duration:0.15,'
                              f'ease:"back.out(3)"}},{T + c["at"]:.3f});')
                sfx("impact", T + c["at"], 0.35)
            for s in seg.get("sfx", []):
                sfx(s["name"], T + s.get("at", 0), s.get("gain", 1.0))
            T += d
        elif typ == "endcard":
            d = seg.get("dur", 8)
            vid += 1
            eid = f"e{vid}"
            items = "".join(f'<li id="{eid}i{k}">{html.escape(t)}</li>' for k, t in enumerate(seg.get("lines", [])))
            els.append(f'<div id="{eid}" class="clip endcard" data-start="{T:.3f}" data-duration="{d:.3f}" '
                       f'data-track-index="2"><div class="ehead" id="{eid}h">{html.escape(seg.get("head", "SABAK"))}</div>'
                       f'<ul>{items}</ul><div class="ebtn" id="{eid}b"><b>&#9654;</b> SUBSCRIBE</div></div>')
            tweens.append(f'tl.fromTo("#{eid}h",{{y:-60,opacity:0}},{{y:0,opacity:1,duration:0.35,ease:"power3.out"}},{T + 0.1:.3f});')
            for k in range(len(seg.get("lines", []))):
                tweens.append(f'tl.fromTo("#{eid}i{k}",{{x:-80,opacity:0}},{{x:0,opacity:1,duration:0.3,ease:"power3.out"}},'
                              f'{T + 0.5 + k * 0.45:.3f});')
                sfx("pop", T + 0.5 + k * 0.45, 0.8)
            bt = T + 0.6 + len(seg.get("lines", [])) * 0.45
            tweens.append(f'tl.fromTo("#{eid}b",{{scale:0,opacity:0}},{{scale:1,opacity:1,duration:0.35,ease:"back.out(2.2)"}},{bt:.3f});')
            tweens.append(f'tl.to("#{eid}b",{{scale:1.08,duration:0.5,yoyo:true,repeat:{max(1, int((d - (bt - T)) / 0.5) - 2)},'
                          f'ease:"sine.inOut"}},{bt + 0.4:.3f});')
            sfx("impact", bt, 0.6)
            for ln in seg.get("vo", []):
                p = next(vo_iter)
                audio_events.append((T + ln.get("at", 0.3), p))
                captions.append((T + ln.get("at", 0.3), dur_of(p), ln.get("caption", "")))
            if not seg.get("music"):
                music_marks.append((T, "ending"))
            T += d
        else:
            sys.exit(f"unknown segment type {typ}")
    total = round(T + 0.5, 3)

    # 3) captions for every voice line (1-3 word pops)
    cap_tags = []
    for k, (start, d, text) in enumerate(captions):
        for j, (cs, cd, words) in enumerate(caption_chunks(text, start, d)):
            cid = f"cap{k}x{j}"
            cap_tags.append(f'<div id="{cid}" class="clip cap" data-start="{cs:.3f}" data-duration="{cd:.3f}" '
                            f'data-track-index="7"><span id="{cid}s">{caption_html(words)}</span></div>')
            tweens.append(f'tl.fromTo("#{cid}s",{{scale:0.8,opacity:0}},{{scale:1,opacity:1,duration:0.1,ease:"back.out(2)"}},{cs:.3f});')

    # 4) audio mix: game sound + voice + music (ducked) + sfx -> mix.wav at -14 LUFS
    adir = proj / "assets" / "audio"
    n = int(total * SR)
    game, voice, fx = np.zeros((n, 2)), np.zeros((n, 2)), np.zeros((n, 2))

    def add(buf, path, at, gain):
        x, sr = sf.read(str(path), always_2d=True)
        if sr != SR:
            tmp = adir / "_rs.wav"
            run(["ffmpeg", "-v", "error", "-y", "-i", path, "-ar", SR, tmp])
            x, _ = sf.read(str(tmp), always_2d=True)
        if x.shape[1] == 1:
            x = np.repeat(x, 2, 1)
        s = int(at * SR)
        if s < 0:
            x, s = x[-s:], 0
        e = min(n, s + len(x))
        if e > s:
            buf[s:e] += x[: e - s] * gain

    for at, p, vol in [(a, b, c) for a, b, c in game_tracks]:
        add(game, p, at, vol)
    for at, p in audio_events:
        add(voice, p, at, 1.0)
    for name, at, gain in sfx_events:
        add(fx, sfx_dir / f"{name}.wav", at, gain)
    # music: one new track per mood span (seeded by this video), crossfaded at mood changes
    music = np.zeros((n, 2))
    marks = sorted(music_marks) or [(0.0, "hype")]
    if marks[0][0] > 0.01:
        marks = [(0.0, "hype")] + marks
    if plan.get("music", True) is not False:
        for k, (mt, mood) in enumerate(marks):
            end = marks[k + 1][0] if k + 1 < len(marks) else total
            if mood == "none" or end - mt < 0.5:
                continue
            mw = adir / f"music-{k}-{mood}.wav"
            run([sys.executable, HERE / "scripts" / "make_gaming_music.py", mw, "--seconds", round(end - mt + 1.5, 2),
                 "--mood", mood, "--seed", seed + k * 17])
            add(music, mw, mt, 1.0)
    # duck music + game under the voice (smooth envelope)
    env = np.abs(voice[:, 0])
    win = int(0.05 * SR)
    env = np.convolve(env, np.ones(win) / win, mode="same")
    talking = (env > 0.01).astype(float)
    sm = int(0.25 * SR)
    talking = np.convolve(talking, np.ones(sm) / sm, mode="same")
    duck = 1.0 - 0.55 * np.clip(talking, 0, 1)
    mix = voice + fx + (music * plan.get("music_volume", 0.22) + game) * duck[:, None]
    raw = adir / "mix-raw.wav"
    sf.write(str(raw), np.clip(mix, -4, 4).astype(np.float32), SR, subtype="FLOAT")
    loudnorm_2pass(raw, adir / "mix.wav")
    raw.unlink()

    # 5) HTML
    page = TEMPLATE.format(total=total, accent=accent, elements="\n      ".join(els), captions="\n      ".join(cap_tags),
                           tweens="\n      ".join(tweens))
    (proj / "index.html").write_text(page)
    m, s = divmod(total, 60)
    print(f"built {proj / 'index.html'}  duration={int(m)}:{s:04.1f}  voice lines={len(audio_events)}  "
          f"sfx={len(sfx_events)}  seed={seed}  accent={accent}")
    for w in warnings:
        print("WARNING:", w)


def report(plan_path: Path, video: Path):
    video = video if video.is_absolute() else (plan_path.parent / video).resolve()
    d = dur_of(video)
    out = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af", "ebur128=peak=true", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    lufs = re.findall(r"I:\s+(-?[\d.]+) LUFS", out)
    peak = re.findall(r"Peak:\s+(-?[\d.]+) dBFS", out)
    m, s = divmod(d, 60)
    print(f"{video.name}: duration {int(m)}:{s:04.1f}, loudness {lufs[-1] if lufs else '?'} LUFS, "
          f"true peak {peak[-1] if peak else '?'} dBFS")


TEMPLATE = """<!doctype html>
<html lang="hi" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <script src="https://cdn.jsdelivr.net/npm/gsap@3.15.0/dist/gsap.min.js"></script>
    <style>
      @font-face {{ font-family: "Anton"; src: url("assets/fonts/Anton-Regular.woff2") format("woff2"); }}
      * {{ margin: 0; padding: 0; box-sizing: border-box; }}
      html, body {{ width: 1920px; height: 1080px; overflow: hidden; background: #000; }}
      #root {{ position: relative; width: 1920px; height: 1080px; background: #000; overflow: hidden; font-family: "Inter", sans-serif; }}
      .full {{ position: absolute; left: 0; top: 0; width: 1920px; height: 1080px; object-fit: cover; }}
      .vwrap {{ position: absolute; inset: 0; }}
      .panelwrap {{ position: absolute; left: 320px; top: 120px; width: 1280px; height: 720px; }}
      .panel {{ width: 1280px; height: 720px; border: 6px solid #fff; border-radius: 18px; box-shadow: 0 30px 80px rgba(0,0,0,.8); }}
      .card {{ position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; }}
      .card:not(.low) {{ background: radial-gradient(circle at 50% 50%, #1a1a1a 0%, #000 70%); }}
      .card.low {{ align-items: flex-end; padding-bottom: 300px; }}
      .card span {{ font-family: "Anton"; letter-spacing: 3px; text-transform: uppercase; display: inline-block;
        text-shadow: 0 10px 0 rgba(0,0,0,.55), 0 0 40px rgba(0,0,0,.6); -webkit-text-stroke: 4px #000; paint-order: stroke fill; }}
      .title {{ position: absolute; inset: 0; background: #0b0b0b; overflow: hidden; }}
      .stripes {{ position: absolute; inset: -200px -400px; opacity: .16;
        background: repeating-linear-gradient(-55deg, {accent} 0 40px, transparent 40px 120px); }}
      .tbig {{ position: absolute; left: 0; width: 1920px; top: 300px; text-align: center; font-family: "Anton"; font-size: 300px;
        line-height: 1; color: #fff; letter-spacing: 6px; text-shadow: 0 14px 0 {accent}; }}
      .tbar {{ position: absolute; left: 610px; width: 700px; top: 660px; height: 14px; background: {accent}; transform-origin: 0 50%; }}
      .tsub {{ position: absolute; left: 0; width: 1920px; top: 700px; text-align: center; font-weight: 800; font-size: 64px;
        color: #fff; letter-spacing: 14px; }}
      .glitch {{ position: absolute; inset: 0; mix-blend-mode: screen; }}
      .glitch i {{ position: absolute; left: 0; width: 1920px; display: block; }}
      .badge {{ position: absolute; right: 40px; top: 36px; }}
      .badge span {{ display: inline-block; font-family: "Anton"; font-size: 46px; letter-spacing: 2px; color: #000;
        background: {accent}; padding: 6px 26px; border-radius: 12px; box-shadow: 0 6px 0 rgba(0,0,0,.5); }}
      .callout {{ position: absolute; inset: 0; }}
      .cbox {{ position: absolute; border: 7px solid {accent}; border-radius: 16px; box-shadow: 0 0 0 4px #000, 0 0 30px {accent}; }}
      .clab {{ position: absolute; font-family: "Anton"; font-size: 44px; color: #000; background: {accent};
        padding: 4px 18px; border-radius: 10px; border: 4px solid #000; }}
      .sub {{ position: absolute; left: 40px; bottom: 150px; }}
      .sub span {{ display: inline-block; font-weight: 900; font-size: 46px; color: #fff; background: #e00000;
        padding: 12px 30px; border-radius: 14px; box-shadow: 0 8px 0 rgba(0,0,0,.45); }}
      .bigcap {{ position: absolute; left: 0; width: 1920px; top: 380px; text-align: center; }}
      .bigcap span {{ display: inline-block; font-family: "Anton"; font-size: 150px; letter-spacing: 3px;
        -webkit-text-stroke: 10px #000; paint-order: stroke fill; text-shadow: 0 10px 0 rgba(0,0,0,.6); }}
      .cap {{ position: absolute; left: 0; width: 1920px; top: 850px; text-align: center; }}
      .cap span {{ display: inline-block; font-family: "Anton"; font-size: 78px; letter-spacing: 1.5px; color: #fff;
        text-transform: uppercase; -webkit-text-stroke: 9px #000; paint-order: stroke fill; text-shadow: 0 6px 0 rgba(0,0,0,.6); }}
      .cap .hl {{ color: #ffd400; }}
      .cap .dg {{ color: #ff2b2b; }}
      .endcard {{ position: absolute; inset: 0; background: radial-gradient(circle at 50% 40%, #1d1d1d, #000 75%); }}
      .ehead {{ position: absolute; top: 120px; left: 0; width: 1920px; text-align: center; font-family: "Anton"; font-size: 150px;
        color: {accent}; letter-spacing: 6px; }}
      .endcard ul {{ position: absolute; top: 340px; left: 360px; width: 1200px; list-style: none; }}
      .endcard li {{ font-weight: 800; font-size: 62px; color: #fff; margin-bottom: 26px; padding-left: 70px; position: relative; }}
      .endcard li::before {{ content: ""; position: absolute; left: 0; top: 22px; width: 36px; height: 36px; border-radius: 8px; background: {accent}; }}
      .ebtn {{ position: absolute; left: 710px; top: 850px; width: 500px; text-align: center; font-weight: 900; font-size: 60px; color: #fff;
        background: #e00000; padding: 18px 0; border-radius: 18px; box-shadow: 0 10px 0 rgba(0,0,0,.5); }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1920" data-height="1080">
      {elements}
      {captions}
      <audio id="mix" class="clip" src="assets/audio/mix.wav" data-start="0" data-duration="{total}" data-track-index="9" data-volume="1"></audio>
    </div>
    <script>
      const tl = gsap.timeline({{ paused: true }});
      {tweens}
      window.__timelines = window.__timelines || {{}};
      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.exit(__doc__)
    if "--report" in args:
        i = args.index("--report")
        report(Path(args[0]), Path(args[i + 1]))
    else:
        build(Path(args[0]))
