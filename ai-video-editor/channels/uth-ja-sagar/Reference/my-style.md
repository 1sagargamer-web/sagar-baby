# "Uth Ja Sagar" style guide (second channel)

Motivation / life lessons. Learned from 5 reference reels (`Reference/ref-1.mp4` ... `ref-5.mp4`, private copies, not
in git). We take the *principles* only. Never reuse their pictures, characters, channel names, logos, music, voices or
exact lines.

## What the references do (measured 2026-11-18)
- Vertical 720x1280, 10-90 s, one narrator voice, soft emotional music, loudness about **-14 LUFS** (all five).
- Black frame. Big title at the top (one word yellow, rest white, plus an emoji). A **square illustration** in the
  middle, full width. Warm, golden / sunset palette, detailed storybook look.
- Picture changes every ~1-6 s (short reels change faster), slight slow zoom on each picture.
- Hindi word-by-word captions **under** the picture: spoken words white, the current word yellow, coming words faint.
- Channel name faint at the bottom of the picture.
- Hook in the first line (a bold claim or a question), short story, ends on a lesson or a question to the viewer.

## Our format (Sagar's answers, 2026-11-18)
- **Vertical 1080x1920, 30 fps, 30-45 seconds.**
- Layout (pixels on 1080x1920):
  - black background
  - title: centre, top 250 px, Baloo 2 ExtraBold 84 px, first word yellow `#ffcf3a`, rest white, one emoji at the end
    (title is per video, short, Hinglish in Roman letters, e.g. "**Haar** Mat Maan 🔥")
  - picture: 1080x1080 at top 420 px, slow Ken Burns move (zoom in / zoom out / pan), short crossfade between pictures
  - watermark: **"Made By Sagar Mishra"**, centre, inside the bottom of the picture (top 1436 px), white 30 px on a
    light dark pill (a plain faint text failed the contrast check on bright pictures)
  - captions: centre, top 1560 px, Baloo 2 ExtraBold 62 px, **Hindi (Devanagari)**, word by word; spoken words white,
    current word yellow, coming words faint white. Up to 6 words (~32 characters) per caption page, so each page stays on screen long enough to read.
- Fonts: `assets/fonts/` (Baloo 2, SIL Open Font License). Emoji: Noto Color Emoji (installed).

## Pictures
- Made by the free open-source model **SDXL-Turbo** on the CPU (`scripts/make_image.py`, ~21 s per picture at 768 px,
  shown at 1080). Sagar chose this over hand-drawn SVG and over making them in ChatGPT personally.
- 8-12 pictures per video, one per narration line. Same style text on every picture (built into `make_image.py`):
  storybook digital illustration, Indian cartoon style, clean outlines, warm cinematic light.
- Because the AI changes faces a little between pictures, write scenes where that matters less (from behind, from far,
  hands, objects, silhouettes) and always use the same character description.
- Look at every picture before building. Re-roll (new seed) any picture with broken hands/faces, extra people, text
  or a wrong mood.

## Characters
- **Sagar** is the one fixed character in every video, as a **generic cartoon man, NOT Sagar's real face**. Sagar said
  "mera face mat lagao" (2026-11-18): never use Sagar's photos for face matching or to copy the face. Only the outfit stays
  the same every video: white t-shirt + open navy leather jacket + blue jeans. Description in `characters/sagar.json`
  (`{SAGAR}` in a scene prompt is replaced by it).
- Everyone else (boy, girl, maa, papa, dost, teacher...) changes with each story.

## Script
- **Claude writes the script**, Sagar approves or rejects it before anything is built.
- 8-12 short lines in simple Hindi (everyday words), one line per picture, ~85-110 words in total for 30-45 s.
- Line 1 = hook (bold claim or question). Middle = a small real-life story. Second to last = the lesson (`"seekh": true`).
  **Last line = a question to the viewer** so people comment (e.g. "Aap hote to kya karte?").
- Never copy a reference's exact story or lines.

## Voice (narrator = Sagar, always Sagar's voice)
- With every script, send Sagar the list of lines to record, with how to say each one (calm, emotional, pause at "...").
  Ask Sagar to say each line 2 times. Pick the best take with `scripts/pick_takes.py` and report the scores.
- **If Sagar says there is no time to record**, use the clone of Sagar's voice (`voices/sagar-ref.wav`, cut from Sagar's 30-60 s recording;
  private, never in git) via Chatterbox (`scripts/clone_voice.py`), tuned to sound natural, like Sagar. Set
  `"allow_clone": true` in script.json only when Sagar says so.

## Sound
- **Music: emotional piano** + soft strings, made by `scripts/make_piano.py` (synthesised, no licence issues). New tune
  per video (seed from the title). Swells on the lesson line. Ducked under the voice so it never covers it.
- **Sound effects: light, only sometimes**: a soft whoosh on 1-2 picture changes, a riser into the lesson line and a
  soft bell when the lesson lands. Made by `scripts/make_sfx.py --story`.
- Final mix about **-14 LUFS**, voice clearly on top.

## Ending
- Lesson line, then the question line, hold the last picture ~1 s, end. No separate end card.
