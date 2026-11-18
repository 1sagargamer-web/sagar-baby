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

## Script (Sagar's rules after episode 1, 2026-11-18: apply to EVERY video)
- **Claude writes the script**, Sagar approves or rejects it before anything is built.
- 9-13 short lines in simple, spoken Hindi (how people really talk, not bookish), one line per picture, ~100-120 words
  for 35-45 s.
- **Shape (always this order):**
  1. **Hook = a question, in the viewer's own thoughts** (0-3 s). Say what people secretly think or feel, so they stop
     scrolling: "Kya tumhe bhi lagta hai... itni mehnat ke baad bhi kuch nahi badal raha?" / "Kabhi socha hai log
     tumpe hanste kyun hain?" Never start with the story itself.
  2. **The story / the whole point**, told simply, with feeling (small real-life moments, "main", "tum").
  3. **The lesson** (`"seekh": true`), one strong line.
  4. **Emotional ending that makes people comment AND follow**, then the video ends (no extra hold):
     ask them to comment something specific ("Comment mein likho 'main rukunga nahi'"), and give an emotional reason to
     follow ("Follow kar lo... kyunki jis din tum haar maanne wale hoge, us din meri agli video tumhe rok legi.").
     Use `"cta": true` on these last 1-2 lines.
- Never copy a reference's exact story or lines.

## Voice (narrator = Sagar, always Sagar's voice)
- With every script, send Sagar the list of lines to record, with how to say each one (calm, emotional, pause at "...").
  Ask Sagar to say each line 2 times. Pick the best take with `scripts/pick_takes.py` and report the scores.
- **If Sagar says there is no time to record**, use the clone of Sagar's voice (`voices/sagar-ref.wav`, cut from Sagar's 30-60 s recording;
  private, never in git) via Chatterbox (`scripts/clone_voice.py`). **Settings fixed: option "A"** (chosen by Sagar
  from 4 samples, 2026-11-18): exaggeration 0.5, cfg 0.4, temperature 0.75, seed 11, normal speed, reference
  `voices/sagar-ref.wav` (3.0-22.5 s of `Raw/sagar-rec-01.mp3`). Do not change them without asking. The clone still
  sounds a bit AI to Sagar, so always offer recording first; Sagar's real recording is the most natural. Set
  `"allow_clone": true` in script.json only when Sagar says so.

## Sound
- **Music: emotional piano** + soft strings, made by `scripts/make_piano.py` (synthesised, no licence issues). New tune
  per video (seed from the title). Swells on the lesson line. Ducked under the voice so it never covers it.
- **Sound effects: light, only sometimes**: a soft whoosh on 1-2 picture changes, a riser into the lesson line and a
  soft bell when the lesson lands. Made by `scripts/make_sfx.py --story`.
- Final mix about **-14 LUFS**, voice clearly on top.

## Ending
- Lesson line, then the emotional comment + follow line(s) (see Script), end on the last word with only a short
  breath (~0.6 s). No separate end card.
