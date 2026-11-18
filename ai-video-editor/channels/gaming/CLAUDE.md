# Gaming channel (second channel): Free Fire awareness videos

Claude is the video editor for Sagar's second channel. Talk to Sagar in simple Hinglish.
**Read `Reference/my-style.md` before every video and follow it**, including the awareness rules.
The first channel (Bhagwan + Sagar cartoon reels, `ai-video-editor/` root) must keep working: never change its
files, and when a shared script needs something new, add an option or flag instead of changing its default.

## Folders (inside `channels/gaming/`)
| Folder | What goes in it |
|---|---|
| `Raw/` | Sagar's gameplay and recordings. Never modify or delete. Not in git. |
| `Reference/` | `my-style.md`, `disclaimer.png` (Sagar's image). Reference video copies are not kept in git. |
| `projects/<name>/` | One project per video: `plan.json`, generated audio/graphics, HyperFrames overlays. |
| `Export/` | Finished videos, `<name>-v1.mp4`, `-v2`, ... never overwrite an old version. Not in git. |
| `voices/` | Sagar's voice reference, clone options and generated lines. **Private, gitignored, never upload.** |
| `characters/` | Any drawn graphics (SVG) the channel uses. |

## Getting Sagar's files (big files cannot come through chat)
Sagar uploads to **private Hugging Face datasets** under his account `sagar5582` (read token is saved on the
"sagar-baby" environment; the proxy adds it, no env variable needed):
- `sagar5582/gaming-ref`: the 4 reference videos.
- `sagar5582/sagar-voice`: his voice recording `sagar.mp3` (also copied to `voices/sagar-gaming-original.mp3`
  at the editor root, gitignored).
- New gameplay: ask him to upload to a private dataset (suggested `sagar5582/gaming-raw`), then download with
  `HF_HUB_DISABLE_XET=1 python3 -c "from huggingface_hub import snapshot_download as d; d('sagar5582/<dataset>', repo_type='dataset', local_dir='channels/gaming/Raw/<name>', token=False)"`.
- List his datasets: `curl -s "https://huggingface.co/api/datasets?author=sagar5582"`; files:
  `curl -s https://huggingface.co/api/datasets/sagar5582/<dataset>/tree/main`.
- Never make these datasets public and never push footage or voice files to GitHub (the repo is public).

## Voice
- Reference: `channels/gaming/voices/sagar-ref.wav` = 0.15-17.95 s (Hindi part) of Sagar's recording, high-pass
  70 Hz, -16 LUFS, 24 kHz mono. Rebuild from `voices/sagar-gaming-original.mp3` if missing.
- Clone with `.venv-tts/bin/python scripts/clone_voice.py <ref> --batch jobs.json --seed 11` (per-job
  `exaggeration` / `cfg`), then speed 1.1x with rubberband (formant preserved), trim silence, -16 LUFS.
- Options sent to Sagar (same line): A exag 0.45 cfg 0.4, B exag 0.7 cfg 0.3, C exag 0.95 cfg 0.25.
  **Chosen: pending.** Once chosen, write it here and in my-style.md and never change it between videos.
- Round 2 (Sagar liked A and C but said "still sounds AI"): Chatterbox only uses the first ~10 s of the reference, and
  the start of his recording is him *reading*. New reference `voices/sagar-ref-chat.wav` (9.2 s) = 0.15-2.45 s
  ("namaste doston main Sagar hoon") + 25.55-32.4 s (casual "agar aapko koi problem...love you yaar").
  Generate **one sentence per job**, temperature 0.9, seed 11, then tempo 1.05 (not 1.1), trim, drop stray tail,
  join with 0.25-0.35 s gaps, light compression (highpass 80, acompressor 3:1), -16 LUFS.
  D = exag 0.55 cfg 0.3 (calm), F = exag 0.85 cfg 0.3 (hype); excited lines get +0.15 exaggeration.
- Next options if still not natural: a new 40-60 s *unscripted* recording from Sagar, or AI4Bharat IndicF5
  (`ai4bharat/IndicF5`, MIT, gated: Sagar must click "Agree" on its Hugging Face page first).
- Check every generated line with Whisper (words right, confidence) before using it; Claude cannot listen.

## Building a video (pipeline, builder to be written: `scripts/make_gaming_video.py`)
Long 1920x1080 gameplay videos are too long to render frame-by-frame in Chrome, so:
1. FFmpeg does the gameplay edit (cuts, punch-in zooms, blur boxes over panel names, B&W/slow-mo) at 1920x1080.
2. HyperFrames renders the motion graphics (hook word cards, title cards, callouts, end card) as short clips.
3. Captions are styled subtitles burned in by FFmpeg (Anton, white + black outline, yellow/red key words).
4. Audio: voice + game sound + music (ducked) + SFX, mixed to -14 LUFS, true peak -1 dB.
Before the final render: check + snapshot the HyperFrames parts and look at frames of the edit; after: ffprobe
duration, loudness, frames. Report what was measured vs. what Claude could not hear/see.

## Every video
1. Plan with timestamps (hook, matches, turning point, ending) + commentary script -> Sagar approves.
2. Voice lines (clone, chosen option), best takes if Sagar records (`scripts/pick_takes.py`).
3. Build, check, snapshot, fix, render `Export/<name>-v1.mp4`.
4. Duration + loudness check, send to Sagar, commit + push (no footage, no voice files).
