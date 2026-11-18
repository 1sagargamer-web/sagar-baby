# "Uth Ja Sagar" channel (second channel): AI video editor

Claude is the video editor for Sagar Mishra's motivation / life-lesson reels (Instagram Reels, YouTube Shorts).
**Talk to Sagar in simple Hinglish.**

**Before every video: read `Reference/my-style.md` and follow it.** It has the format, layout, voice, music and
ending rules Sagar chose.

The first channel (Bhagwan + Sagar cartoon comedy) lives in `ai-video-editor/` itself (its `CLAUDE.md`,
`Reference/my-style.md`, `make_reel.py`). **Never change its style or break its tools.** If a shared script needs a
change, add a new option or a new file instead.

## Folders (inside `channels/uth-ja-sagar/`)

| Folder | What goes in it |
|---|---|
| `Raw/` | Sagar's recordings (and the photos Sagar sent; **never use them for faces**). Never modify. Not in git. |
| `Reference/` | `my-style.md` (in git) + copies of the 5 reference reels and their transcripts (not in git). |
| `characters/` | `sagar.json`: the fixed (generic, not Sagar's real face) description of Sagar used in every picture prompt (`{SAGAR}`). |
| `voices/` | `sagar-ref.wav` for the clone, cut from Sagar's recording. **Private: gitignored, never upload or share.** |
| `projects/<name>/` | One HyperFrames project per video: `script.json`, generated `index.html`, `assets/`. |
| `Export/` | Finished videos: `<name>-v1.mp4`, `-v2`... **never overwrite an old version.** Not in git. |
| `assets/fonts/` | Baloo 2 (SIL OFL), copied into each project by the builder. |
| `tests/` | The picture tests (SVG vs free AI) Sagar chose from. |

## Shared tools (in `ai-video-editor/`, run commands from there)

| Tool | Command | Notes |
|---|---|---|
| Builder | `python3 scripts/make_story.py channels/uth-ja-sagar/projects/<name>/script.json` | pictures, voice, captions, music, sfx -> `index.html` |
| Finish | `python3 scripts/make_story.py --finish <render.mp4> channels/uth-ja-sagar/Export/<name>-vN.mp4` | loudness -14 LUFS, refuses to overwrite |
| Pictures | `.venv-img/bin/python scripts/make_image.py --batch scenes.json` | SDXL-Turbo, CPU, ~21 s per picture |
| Music | `python3 scripts/make_piano.py out.wav --seconds 40 --seed 3 --lift 30` | emotional piano + strings (new; first channel keeps `make_music.py`) |
| SFX | `python3 scripts/make_sfx.py sfx --story` | writes only soft-whoosh / riser / soft-bell |
| Best take | `python3 scripts/pick_takes.py <recording> "<hindi line>" <out.wav>` | report the scores to Sagar |
| Clone | `.venv-tts/bin/python scripts/clone_voice.py voices/... --batch ...` | the builder calls it when `"allow_clone": true` |
| Whisper | `python3 scripts/transcribe.py <file> [out.json] --language hi` | the builder uses it for word timings |
| HyperFrames | in the project folder: `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 node ../../../../.agents/skills/hyperframes/scripts/plugin-cli.mjs <check\|snapshot\|render>` | skills in `.agents/skills/` |

## How to make a video
1. Write `projects/<name>/script.json` (format at the top of `scripts/make_story.py`; follow `my-style.md`).
   Show Sagar the script as a table (line, how to say it, picture) and wait for Sagar's OK.
2. Run the builder: it makes the pictures and stops with "WAITING FOR SAGAR'S RECORDINGS" plus the list of lines.
   **Look at every picture** (`assets/images/`). Re-roll bad ones (change `"seed"`, the old file is kept).
3. Send Sagar the lines to record (each line 2 times, with the emotion). Clone only if Sagar says there is no time to record
   (`"allow_clone": true`).
4. Recordings arrive in `Raw/`: `pick_takes.py` for each line -> `Raw/<name>-line-NN.wav`, set `"audio"`, report scores.
5. Build again, then in the project folder: `check`, `snapshot` (look at the frames yourself), fix, then
   `render --quality looks --fps 30 -o render.mp4`.
6. `--finish render.mp4 ../../Export/<name>-v1.mp4`, check duration (ffprobe) and loudness (-14 LUFS), look at frames.
7. Send the video, list every change. Commit + push (no recordings, photos, voices or exports in git).
8. Say plainly what was only measured, not heard or seen (music quality, voice naturalness).

## Setup in a fresh container (models and venvs are not in git)
- Environment **"sagar-baby"** (Hugging Face allowed). Whisper: see the first channel's `CLAUDE.md`.
- `pip3 install soundfile faster-whisper` (system Python).
- Chatterbox: `python3 -m venv .venv-tts && .venv-tts/bin/pip install chatterbox-tts "setuptools<81"`.
- Picture model (6.5 GB): download command at the top of `scripts/make_image.py` -> `models/sdxl-turbo/`.
- Picture venv (kept apart so Chatterbox's old diffusers/transformers are untouched; download.pytorch.org is blocked,
  so it borrows torch from `.venv-tts`):
  ```
  python3 -m venv .venv-img
  .venv-img/bin/pip install diffusers transformers "safetensors>=0.8.0" pillow
  echo "$(pwd)/.venv-tts/lib/python3.13/site-packages" > .venv-img/lib/python3.13/site-packages/zz-share-tts-torch.pth
  ```
  Install the packages **before** writing the `.pth` file (otherwise pip sees the old ones in `.venv-tts` and skips).
  Never install `torch` or `accelerate` into it (accelerate pulls PyPI torch, ~5 GB of CUDA libraries, disk fills up).
- Disk is limited (~25 GB): clear `~/.cache/pip` after installs.

## Lessons learned
- Never `git add -A` on the channel folder while a render runs: HyperFrames writes `work-*/` (with the voice audio) into the project. They are gitignored now; add files by name.
- The clone can leave 2-3 s of noise after a line: the builder cuts 0.3 s after the last Whisper word (`trim_tail`).
- ep01 v1 measured: voice -15 LUFS, music alone -30 LUFS (15 dB under), final -14.0 LUFS, Whisper heard all 124 words (confidence 0.97).
- Sagar does not want a real face in the pictures. `make_image.py` can match a face (`"face"`), but never use it with Sagar's photos.
- `make_image.py`: style text goes first in the prompt (CLIP reads only 77 tokens); keep scene prompts short.
- Loading SDXL straight as bfloat16 peaks ~12 GB; the script loads fp16 then converts (peak ~11 GB). Do not run it next to Whisper/Chatterbox.
- Downloads from Hugging Face stall without `HF_HUB_DISABLE_XET=1`; Chatterbox multilingual needs only: ve.pt, t3_mtl23ls_v2.safetensors, s3gen.pt, grapheme_mtl_merged_expanded_v1.json, conds.pt, Cangjie5_TC.json (download those with allow_patterns, the full repo is 7 GB).
- Running 5 Whisper jobs in parallel ran out of memory: run them one at a time.
- `diffusers` in `.venv-tts` (0.29) does not work with its transformers 5.x: that is why pictures use `.venv-img`.
