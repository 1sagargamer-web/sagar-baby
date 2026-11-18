# THE REAL SAGAR (main channel): video editor rules

Sagar's main YouTube channel **THE REAL SAGAR** (about 2 lakh subscribers). Claude edits Sagar's own recordings.
Talk to Sagar in simple Hinglish. The first channel (Bhagwan + Sagar cartoon reels, `ai-video-editor/CLAUDE.md`)
is separate: never change its files or style from here.

**Before every edit: read `Reference/my-style.md` and follow it.** Copy the references' *editing*, never their
logos, channel cards, music, sound files, fonts, exact text or graphics.

## What the videos are
- **Meme / short-clip reaction videos**: Sagar's face cam reacting to memes and short clips.
- YouTube long, landscape **1920x1080**, **10-12 min** (depends on the raw recording).
- **No watermark.**
- The intro channel card shows "THE REAL SAGAR" (our own card design, Sagar's own profile photo).

## Folders (inside this channel folder)
| Folder | What goes in it |
|---|---|
| `Raw/` | Sagar's raw recordings (never modified or deleted; not in git). |
| `Reference/` | `my-style.md` (style guide) and `refs-list.txt`. Video copies in `Reference/refs/` stay out of git. |
| `projects/<video>/` | One HyperFrames project per video (working files). |
| `Export/` | Finished videos: `<video>-v1.mp4`, `-v2`, ... never overwrite an old version. |
| `characters/` | Channel graphics (channel card, icons) made by us. |

## Getting files
- Reference videos: Sagar's private Hugging Face dataset `sagar5582/main-channel-refs`.
- Raw videos: Sagar's private Hugging Face dataset `sagar5582/main-channel-raw` (the session's Hugging Face
  access is read-only and already connected). Download into `Raw/`, never re-upload anywhere.

## Shared tools (in `ai-video-editor/`, reuse them; change scripts only by adding new options)
- Whisper: `python3 scripts/transcribe.py <file> [out.json] --language hi` (word timings for the intro words,
  captions and silence cuts).
- HyperFrames: skills in `.agents/skills/`; always `check` + `snapshot` and look at frames before `render`.
- Music / SFX: synthesised by us (`scripts/make_music.py`, `scripts/make_sfx.py`, or new channel versions).

## Footage look (every video): original room + glowing Sagar
1. `npx hyperframes remove-background <footage> -o assets/sagar-cutout.webm --quality best` (first time on a new
   container: `npm install onnxruntime-node@1.21.1 --onnxruntime-node-install-cuda=skip --prefix
   ~/.cache/hyperframes/optional/onnxruntime-node@1.21.1`). About 0.7 s per 1080p frame on CPU.
2. `python3 scripts/person_glow.py --footage assets/sagar.mp4 --matte assets/sagar-cutout.webm
   --plate-out assets/plate.mp4 --person-out assets/sagar-glow.webm` (matte cleaned with the empty-room method).
3. Intro: write `intro.json`, then `python3 scripts/make_reaction_intro.py projects/<video>/intro.json`
   (needs `assets/sfx/*.wav` + `assets/sfx/durations.json`, fonts in `assets/fonts/`, emoji in `assets/emoji/`).
   Layers: plate → words/emoji behind → `sagar-glow.webm` → words/cards/emoji in front.

## Every video
1. Download the raw video, transcribe it, and show Sagar the plan (intro words, cuts, clip layout, effects,
   ending) with timestamps. Wait for his OK.
2. Build, check, snapshot, look at the frames, fix, then render.
3. After the render: check duration and loudness (around -14 LUFS, music never covers the voice).
4. Send the video, commit + push the project (never raw videos or recordings).
5. Say clearly what was measured but not heard/seen (e.g. music quality).
