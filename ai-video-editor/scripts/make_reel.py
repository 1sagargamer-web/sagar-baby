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
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent.parent



FPS = 30
W, H = 1080, 1920
FUNNY_PUNCH = ["scratch", "boing", "dundun", "bonk", "airhorn"]
FUNNY_SHOCK = ["bassdrop", "boom", "slip", "sadtrombone", "bonk"]
TTS_PY = HERE / ".venv-tts" / "bin" / "python"
# Fixed voices. Bhagwan: a synthetic reference voice (no real person), spoken naturally by Chatterbox.
# Sagar: cloned from Sagar's own recording (voices/sagar-ref.wav, private, not in git).
VOICES = {
    "krishna": {"ref": HERE / "voices" / "bhagwan-ref.wav", "exaggeration": 0.45, "cfg": 0.4, "seed": 7},
    "sagar": {"ref": HERE / "voices" / "sagar-ref.wav", "exaggeration": 0.4, "cfg": 0.3, "temperature": 0.8, "seed": 11,
              "tempo": 1.15},  # Sagar speaks a bit faster than the raw clone
}
# Trim silence at both ends and level to -16 LUFS
CLEAN = (
    "silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.05,"
    "areverse,silenceremove=start_periods=1:start_threshold=-40dB:start_silence=0.08,areverse,"
    "loudnorm=I=-16:TP=-1.5"
)


def clean(src: Path, out: Path, tempo: float = 1.0) -> None:
    """Trim + level in TWO ffmpeg passes with a timeout each: the one-pass chain
    (rubberband + areverse + loudnorm) can hang ffmpeg forever on some clips (seen 26 Nov 2026)."""
    trim = CLEAN.rsplit(",loudnorm", 1)[0]
    af1 = trim if tempo == 1.0 else f"rubberband=tempo={tempo}:formant=preserved:pitchq=quality," + trim
    mid = out.with_suffix(".mid.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-af", af1, "-ac", "1", "-ar", "48000", str(mid)],
                   check=True, timeout=180)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(mid), "-af", "loudnorm=I=-16:TP=-1.5", "-ac", "1",
                    "-ar", "48000", str(out)], check=True, timeout=180)
    mid.unlink(missing_ok=True)


def drop_stray_tail(wav: Path, gap: float = 0.45, max_blip: float = 0.6) -> None:
    """TTS sometimes adds a short noise after the line ends. Cut short sound islands that come after a pause."""
    data, rate = sf.read(str(wav))
    hop = int(rate * 0.02)
    db = np.array([20 * np.log10(np.sqrt(np.mean(data[i:i + hop] ** 2)) + 1e-9) for i in range(0, len(data), hop)])
    loud = db > -40
    islands, start = [], None
    for i, v in enumerate(loud):
        if v and start is None:
            start = i
        if not v and start is not None:
            islands.append([start, i]); start = None
    if start is not None:
        islands.append([start, len(loud)])
    while len(islands) > 1:
        s, e = islands[-1]
        if (s - islands[-2][1]) * 0.02 >= gap and (e - s) * 0.02 <= max_blip:
            islands.pop()
        else:
            break
    if islands:
        end = min(len(data), (islands[-1][1] * hop) + int(rate * 0.15))
        sf.write(str(wav), data[:end], rate)


def synth(who: str, jobs: list[dict]) -> None:
    """jobs: [{"text", "out", "exaggeration"?}] spoken in the character's fixed voice."""
    if not jobs:
        return
    v = VOICES[who]
    if not v["ref"].exists():
        sys.exit(f"Missing voice reference {v['ref']} (see CLAUDE.md).")
    raw = [{**j, "out": str(Path(j["out"]).with_suffix(".raw.wav"))} for j in jobs]
    batch = Path(jobs[0]["out"]).parent / f"_{who}-jobs.json"
    batch.write_text(json.dumps(raw, ensure_ascii=False))
    subprocess.run(
        [str(TTS_PY), str(HERE / "scripts" / "clone_voice.py"), str(v["ref"]), "--batch", str(batch),
         "--exaggeration", str(v["exaggeration"]), "--cfg", str(v["cfg"]), "--seed", str(v["seed"]),
         "--temperature", str(v.get("temperature", 0.8))],
        check=True,
    )
    for j, r in zip(jobs, raw):
        clean(Path(r["out"]), Path(j["out"]), v.get("tempo", 1.0))
        drop_stray_tail(Path(j["out"]))
        Path(r["out"]).unlink()
    batch.unlink()


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

    wavs = [audio_dir / f"line-{i + 1:02d}-{l['who']}.wav" for i, l in enumerate(spec["lines"])]
    jobs = {"krishna": [], "sagar": []}
    for line, wav in zip(spec["lines"], wavs):
        if line.get("audio"):  # a real recording for this line wins
            src = Path(line["audio"])
            src = src if src.is_absolute() else HERE / src
            # Sagar recorded Bhagwan's line: convert it into Bhagwan's voice (default for krishna; "vc": false skips)
            if line.get("vc", line["who"] == "krishna"):
                raw = wav.with_suffix(".vc.wav")
                subprocess.run([str(TTS_PY), str(HERE / "scripts" / "convert_voice.py"), str(VOICES[line["who"]]["ref"]),
                                str(src), str(raw)], check=True)
                clean(raw, wav)
                drop_stray_tail(wav)
                raw.unlink()
            else:
                clean(src, wav)
        elif not (wav.exists() and line.get("keep_audio")):
            job = {"text": line["hi"], "out": str(wav)}
            if "exaggeration" in line:
                job["exaggeration"] = line["exaggeration"]
            jobs[line["who"]].append(job)
    # Rule: Sagar records his own lines AND Bhagwan's lines (Bhagwan's are voice-converted). The clone is used only
    # with "allow_clone": true, AI Bhagwan only with "allow_ai_bhagwan": true (Sagar said he cannot record).
    need = [l for l in spec["lines"] if not l.get("audio") and not l.get("keep_audio")
            and ((l["who"] == "sagar" and not spec.get("allow_clone"))
                 or (l["who"] == "krishna" and not spec.get("allow_ai_bhagwan")))]
    if need:
        print("WAITING FOR SAGAR'S RECORDINGS. Lines to record:")
        for n, line in enumerate(need, 1):
            print(f"  {n}. [{'Sagar' if line['who'] == 'sagar' else 'Bhagwan'}] {line['caption']}")
        return
    for who, js in jobs.items():
        synth(who, js)

    t = 0.3
    lines = []
    for line, wav in zip(spec["lines"], wavs):
        dur = sf.info(str(wav)).duration
        t += line.get("pause_before", 0)
        lines.append({**line, "wav": wav, "start": round(t, 3), "dur": round(dur, 3), "env": mouth_envelope(wav)})
        t += dur + gap
    total = round(t + 1.0, 2)
    # optional meme clip as the final shot (spec "meme": "memes/meme-ref6.mp4", looked up in the private repo)
    meme_start = None
    meme_dur = 0.0
    meme_rel = None
    if spec.get("meme"):
        m = Path(spec["meme"])
        cands = [m, HERE / m, Path("/home/user/sagar-private") / m]
        msrc = next((c for c in cands if c.exists()), None)
        if msrc is None:
            sys.exit(f"meme clip not found: {spec['meme']} (is sagar-private attached?)")
        mdir = proj / "assets" / "meme"
        mdir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(msrc, mdir / "meme.mp4")
        meme_rel = "assets/meme/meme.mp4"
        meme_dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                         str(mdir / "meme.mp4")], capture_output=True, text=True, check=True).stdout)
        meme_start = round(total - 0.6, 2)
    content_end = meme_start if meme_start is not None else total
    if meme_start is not None:
        total = round(meme_start + meme_dur, 2)

    # Krishna appears 0.5 s before his first line
    kr_first = next((l["start"] for l in lines if l["who"] == "krishna"), 0.0)
    kr_enter = max(0.0, round(kr_first - 0.5, 3))
    kr_present = bool(spec.get("krishna_present"))  # Krishna ji is with Sagar from frame 0 (no flash entrance)
    if kr_present:
        kr_enter = 0.0

    # ---- per-frame face states -> keyframes -------------------------------------------------
    defaults = {
        "sagar": {"eyes": "open", "brows": "normal", "mouth": "closed", "pose": "none", "sweat": False, "tears": False},
        "krishna": {"eyes": "open", "brows": "normal", "mouth": "closed", "pose": "none", "sweat": False, "tears": False},
    }
    nframes = int(total * FPS) + 1
    keys = {"sagar": [], "krishna": []}
    for who in keys:
        face = dict(defaults[who])
        last = None
        for f in range(nframes):
            ft = f / FPS
            for l in lines:  # expression changes at the start of each line that sets them
                if abs(l["start"] - ft) < 0.5 / FPS:
                    if l["who"] == who and "face" in l:
                        face = {**defaults[who], **l["face"]}
                    elif f"{who}_face" in l:  # how the listener reacts to this line
                        face = {**defaults[who], **l[f"{who}_face"]}
            eyes, mouth = face["eyes"], face["mouth"]
            talking = next((l for l in lines if l["who"] == who and l["start"] <= ft < l["start"] + l["dur"]), None)
            if talking and mouth != "o":
                k = int(round((ft - talking["start"]) * FPS))
                if k < len(talking["env"]) and talking["env"][k]:
                    mouth = "open"  # between syllables the mouth rests in the expression's shape
            # blink every ~3.2 s (offset per character) while the eyes are open
            period, off = (3.2, 1.1) if who == "sagar" else (3.7, 2.3)
            if eyes == "open" and ((ft - off) % period) < 0.13 and ft > off:
                eyes = "closed"
            state = (eyes, face["brows"], mouth, face["pose"], bool(face["sweat"]), bool(face["tears"]))
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

    # on-screen tick list (green checklist) per line: {"ticks": ["Admit card", ...]} spread across the line
    tick_html, tick_data = [], []
    n_tick = 0
    for l in lines:
        its = l.get("ticks") or []
        for j, txt in enumerate(its):
            n_tick += 1
            at = round(l["start"] + l["dur"] * (0.18 + 0.72 * (j / max(1, len(its)))), 2)
            tick_html.append(f'          <div class="tk" id="tk-{n_tick}"><b>✅</b> {txt}</div>')
            tick_data.append({"sel": f"#tk-{n_tick}", "at": at})
    ticks_block = ""
    if tick_html:
        t0 = min(x["at"] for x in tick_data)
        ticks_block = (f'      <div id="ticks" class="clip" data-start="{round(max(0, t0 - 0.2), 2)}" '
                       f'data-duration="{round(content_end - max(0, t0 - 0.2), 2)}" data-track-index="11" data-layout-allow-overlap>\n'
                       + "\n".join(tick_html) + "\n      </div>")
    # sleeping: {"sleep": true} on a line shows floating Zzz above both characters until the next line
    sleeps = []
    for i2, l in enumerate(lines):
        if l.get("sleep"):
            end = lines[i2 + 1]["start"] if i2 + 1 < len(lines) else content_end
            sleeps.append({"start": l["start"], "end": round(end, 2)})
    zzz_block = ""
    if sleeps:
        z0 = sleeps[0]["start"]
        zzz_block = (f'      <div id="zzz" class="clip" data-start="{z0}" data-duration="{round(content_end - z0, 2)}" '
                     f'data-track-index="12" data-layout-allow-overlap><span id="zz1">Z z z</span><span id="zz2">Z z z</span></div>')
    # blanket: {"blanket": true} on a line pulls a blanket over Sagar's head (hides under the quilt) until the end
    blanket_at = next((l["start"] for l in lines if l.get("blanket")), None)
    blanket_block = ""
    if blanket_at is not None:
        blanket_block = (f'      <div id="blanket" class="clip" data-start="{blanket_at}" data-duration="{round(content_end - blanket_at, 2)}" '
                         f'data-track-index="13" data-layout-allow-overlap></div>')
    topcap = spec.get("top_caption")
    topcap_block = ""
    if topcap:
        topcap_block = (f'      <div id="topcap" class="clip" data-start="0" data-duration="{content_end}" data-track-index="9">'
                        f'<span>{topcap}</span></div>')
    meme_block = ""
    if meme_rel:
        meme_block = (f'      <video id="meme" class="clip" src="{meme_rel}" data-start="{meme_start}" data-duration="{meme_dur}" '
                      f'data-track-index="10" data-has-audio="true" data-volume="0.9" playsinline></video>')

    data = {"total": total, "krEnter": kr_enter, "keys": keys, "nods": nods, "cams": cams,
            "ticks": tick_data, "sleeps": sleeps, "contentEnd": content_end, "krPresent": kr_present}

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
        cap_end = lines[i + 1]["start"] if i + 1 < len(lines) else content_end
        cs = max(0.1, round(l["start"] - 0.05, 3))
        caption_tags.append(
            f'        <div id="cap-{i + 1}" class="clip cap cap-{l["who"]}" data-start="{cs}" '
            f'data-duration="{round(cap_end - cs, 3)}" data-track-index="5"><span>{l["caption"]}</span></div>'
        )

    # background music: an original tune per reel (seed from the script, or from the title), low under the voices
    music = spec.get("music", {})
    if music is not False:
        seed = music.get("seed", sum(map(ord, spec.get("title", proj.name))) % 1000)
        mwav = audio_dir / "music.wav"
        subprocess.run([sys.executable, str(HERE / "scripts" / "make_music.py"), str(mwav),
                        "--seconds", str(content_end), "--seed", str(seed), "--bpm", str(music.get("bpm", 96))], check=True)
        audio_tags.append(
            f'      <audio id="music" class="clip" src="{mwav.relative_to(proj).as_posix()}" data-start="0" '
            f'data-duration="{content_end}" data-track-index="6" data-volume="{music.get("volume", 0.25)}"></audio>'
        )

    # sound effects on the visible actions (files made by scripts/make_sfx.py into sfx/)
    sfx_lib = HERE / "sfx"
    if not (sfx_lib / "bassdrop.wav").exists():
        subprocess.run([sys.executable, str(HERE / "scripts" / "make_sfx.py"), str(sfx_lib)], check=True)
    events = []
    if any(l["who"] == "krishna" for l in lines) and not kr_present:
        events += [("whoosh", kr_enter - 0.2), ("shimmer", kr_enter + 0.03)]
    for l in lines:
        if l.get("face", {}).get("pose") == "thumb":
            events.append(("pop", l["start"] + 0.03))
        # Funny hits vary per video: picked from the pool by the title so consecutive reels sound different.
        seed_n = sum(map(ord, spec.get("title", proj.name)))
        if l.get("punch"):
            events.append(("whoosh-short", l["start"] - 0.05))
            events.append((FUNNY_PUNCH[seed_n % len(FUNNY_PUNCH)], l["start"] + 0.35))
        if l.get("shake"):
            events.append((FUNNY_SHOCK[(seed_n // 3) % len(FUNNY_SHOCK)], l["start"] + 0.03))
        for s in l.get("sfx", []):
            events.append((s["name"], l["start"] + s.get("at", 0)))
    volumes = {"boing": 0.6, "scratch": 0.55, "sadtrombone": 0.6, "airhorn": 0.45, "slip": 0.6, "dundun": 0.7,
               "bassdrop": 0.8, "bonk": 0.65, "boom": 0.75, "shimmer": 0.5, "whoosh": 0.55, "whoosh-short": 0.45, "pop": 0.6, "ding": 0.5}
    if spec.get("sfx", True) is not False:
        for k, (name, at) in enumerate(sorted(events, key=lambda e: e[1])):
            src = sfx_lib / f"{name}.wav"
            dst = audio_dir / f"sfx-{name}.wav"
            shutil.copyfile(src, dst)
            dur = round(sf.info(str(dst)).duration, 3)
            audio_tags.append(
                f'      <audio id="sfx-{k + 1}" class="clip" src="{dst.relative_to(proj).as_posix()}" '
                f'data-start="{max(0.0, round(at, 3))}" data-duration="{dur}" data-track-index="7" '
                f'data-volume="{volumes.get(name, 0.5)}"></audio>'
            )

    sys.path.insert(0, str(HERE / "scripts"))
    import scenes
    theme = scenes.THEMES[scenes.pick(spec.get("scene"), spec.get("title", proj.name))]
    print("scene:", scenes.pick(spec.get("scene"), spec.get("title", proj.name)))
    html = TEMPLATE.format(
        sky_css=theme["sky"], scene_back=theme["back"], scene_mid=theme["mid"], scene_front=theme["front"],
        total=total,
        watermark=spec.get("watermark", "Made By Sagar Mishra"),
        sagar=sagar_svg,
        krishna=krishna_svg,
        audio="\n".join(audio_tags),
        captions="\n".join(caption_tags),
        extra_blocks="\n".join(b for b in [topcap_block, ticks_block, zzz_block, blanket_block, meme_block] if b),
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
      #sky {{ position: absolute; inset: 0; background: {sky_css}; }}
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
      #topcap {{ position: absolute; left: 0; top: 252px; width: 1080px; text-align: center; z-index: 30; }}
      #topcap span {{ display: inline-block; font-weight: 800; font-size: 40px; color: #ffffff; background: rgba(15, 15, 25, 0.62);
        padding: 8px 26px; border-radius: 16px; text-shadow: 0 2px 4px rgba(0,0,0,0.5); }}
      #ticks {{ position: absolute; left: 50px; top: 610px; width: 560px; z-index: 30; }}
      #ticks .tk {{ opacity: 0; font-weight: 800; font-size: 44px; color: #ffffff; line-height: 1.3; margin-bottom: 8px; background: rgba(20,20,20,0.78); border-radius: 14px; padding: 2px 18px; width: fit-content;
        text-shadow: 0 3px 6px rgba(0,0,0,0.7), 0 0 4px rgba(0,0,0,0.6); }}
      #zzz span {{ position: absolute; font-weight: 900; font-size: 64px; color: #ffffff; opacity: 0; letter-spacing: 6px;
        text-shadow: 0 3px 6px rgba(0,0,0,0.6); }}
      #zz1 {{ left: 200px; top: 700px; }} #zz2 {{ left: 780px; top: 700px; }}
      #blanket {{ position: absolute; left: -10px; top: 880px; width: 580px; height: 780px; z-index: 25; opacity: 0;
        border-radius: 280px 280px 30px 30px; border: 6px solid #0f5a58;
        background: repeating-linear-gradient(45deg, #1f9a96 0 46px, #2fb7b1 46px 92px, #f4c542 92px 100px); }}
      #meme {{ position: absolute; left: 0; top: 0; width: 1080px; height: 1920px; object-fit: cover; z-index: 40; }}
      #watermark {{ position: absolute; left: 0; top: 196px; width: 1080px; text-align: center; z-index: 60; }}
      #watermark span {{
        display: inline-block; font-weight: 700; font-size: 32px; letter-spacing: 0.04em; color: #ffffff;
        background: rgba(20, 20, 30, 0.38); padding: 8px 24px; border-radius: 40px;
        text-shadow: 0 2px 4px rgba(0,0,0,0.45);
      }}
    </style>
  </head>
  <body>
    <div id="root" data-composition-id="main" data-start="0" data-duration="{total}" data-width="1080" data-height="1920">
      <div id="scene" class="clip" data-start="0" data-duration="{total}" data-track-index="0" data-layout-allow-overlap>
        <div id="world">
          <div id="sky"></div>
          {scene_back}
          {scene_mid}
          <div id="char-krishna">{krishna}</div>
          <div id="char-sagar">{sagar}</div>
          {scene_front}
          <div id="flash"></div>
        </div>
      </div>
      <div id="captions" class="clip" data-start="0" data-duration="{total}" data-track-index="2" data-layout-allow-overlap>
{captions}
      </div>
      <div id="watermark" class="clip" data-start="0" data-duration="{total}" data-track-index="8"><span>{watermark}</span></div>
{extra_blocks}
{audio}
    </div>
    <script>
      const D = {data};
      const tl = gsap.timeline({{ paused: true }});
      const parts = {{
        sagar: {{ p: "sg", eyes: ["open", "closed", "shock", "heart", "side"], brows: ["normal", "sad", "angry"],
          mouth: ["closed", "open", "o", "sad", "smirk"], arms: ["pray", "thumb"], sweat: true, tears: true }},
        krishna: {{ p: "kr", eyes: ["open", "closed", "half", "wink"], brows: [], mouth: ["closed", "open"], arms: [],
          sweat: false, tears: false }},
      }};
      // face keyframes: show exactly one group of each kind at a time
      for (const who of ["sagar", "krishna"]) {{
        const P = parts[who];
        for (const [t, eyes, brows, mouth, pose, sweat, tears] of D.keys[who]) {{
          for (const e of P.eyes) tl.set(`#${{P.p}}-eyes-${{e}}`, {{ opacity: e === eyes ? 1 : 0 }}, t);
          for (const b of P.brows) tl.set(`#${{P.p}}-brows-${{b}}`, {{ opacity: b === brows ? 1 : 0 }}, t);
          for (const m of P.mouth) tl.set(`#${{P.p}}-mouth-${{m}}`, {{ opacity: m === mouth ? 1 : 0 }}, t);
          for (const a of P.arms) tl.set(`#${{P.p}}-arms-${{a}}`, {{ opacity: a === pose ? 1 : 0 }}, t);
          if (P.sweat) tl.set(`#${{P.p}}-sweat`, {{ opacity: sweat ? 1 : 0 }}, t);
          if (P.tears) tl.set(`#${{P.p}}-tears`, {{ opacity: tears ? 1 : 0 }}, t);
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
      if (!D.krPresent) {{
        tl.fromTo("#char-krishna", {{ opacity: 0, scale: 0.7, y: 60 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.45,
          ease: "back.out(1.8)", transformOrigin: "50% 100%" }}, D.krEnter);
        tl.fromTo("#flash", {{ opacity: 0 }}, {{ opacity: 0.85, duration: 0.08 }}, D.krEnter);
        tl.to("#flash", {{ opacity: 0, duration: 0.4, ease: "power2.out" }}, D.krEnter + 0.08);
        tl.fromTo("#kr-halo", {{ opacity: 0.3 }}, {{ opacity: 1, duration: 0.6, ease: "power2.out" }}, D.krEnter);
      }}
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
      // tick list items pop in one by one
      for (const k of D.ticks) tl.fromTo(k.sel, {{ opacity: 0, x: -30, scale: 0.8 }}, {{ opacity: 1, x: 0, scale: 1, duration: 0.22,
        ease: "back.out(2.4)" }}, k.at);
      // sleeping Zzz floats up above both heads
      for (const sl of D.sleeps) for (const id of ["#zz1", "#zz2"]) {{
        tl.fromTo(id, {{ opacity: 0, y: 40 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "power2.out" }}, sl.start);
        tl.to(id, {{ y: -60, duration: 1.4, ease: "sine.inOut", yoyo: true, repeat: 3 }}, sl.start + 0.5);
      }}
      // blanket slides up over Sagar
      if (document.getElementById("blanket")) {{
        const bs = parseFloat(document.getElementById("blanket").dataset.start);
        tl.fromTo("#blanket", {{ opacity: 1, y: 900 }}, {{ opacity: 1, y: 0, duration: 0.5, ease: "back.out(1.4)" }}, bs);
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
