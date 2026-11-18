# AI Video Editor workspace

Claude is the video editor for short vertical reels (Instagram Reels, YouTube Shorts).
Talk to the owner in simple Hinglish.

## Folder rules

| Folder | What goes in it |
|---|---|
| `Raw/` | Raw, unedited phone footage. Never modify or delete these files. |
| `Reference/` | Notes (and saved copies) of reels whose editing style the owner likes. `my-style.md` lives here. |
| `Export/` | Finished edits. Save every change as a new version: `name-v1.mp4`, `name-v2.mp4`, ... never overwrite an old version. |
| `projects/` | One HyperFrames project per reel (`projects/<reel-name>/`). Working files only. |

**Before every edit: read `Reference/my-style.md`** (once it exists) and follow it.

## Tools installed (cloud container, Linux)

| Tool | How to run | Status |
|---|---|---|
| FFmpeg / FFprobe 6.1 | `ffmpeg`, `ffprobe` | ready |
| Node.js 22 | `node`, `npx` | ready |
| Python 3.13 | `python3` | ready |
| Whisper | `python3 scripts/transcribe.py <video> [out.json] [--language hi\|en]` (faster-whisper, model `large-v3` in `models/`, word timestamps) | ready, tested |
| HyperFrames 0.9.61 | `node .agents/skills/hyperframes/scripts/plugin-cli.mjs <command>` (run inside the project folder) | ready, skills in `.agents/skills/` (linked into `.claude/skills/`) |
| Chrome (for rendering) | `/usr/bin/google-chrome` | ready |

Always set `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1` when running the HyperFrames CLI.

Setup was verified by rendering `Export/test.mp4` (5 s, 1080x1920, 30 fps, title card) from
`projects/test-title/`.

The Whisper model (2.9 GB) is not in git. The cloud environment "sagar-baby" allows the Hugging Face
hosts; download it with:
`HF_HUB_DISABLE_XET=1 python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Systran/faster-whisper-large-v3', local_dir='models/faster-whisper-large-v3')"`

If a tool is missing in a fresh container: `pip3 install faster-whisper`, and the HyperFrames
skills are already committed in `.agents/skills/` (reinstall with `npx skills add heygen-com/hyperframes --all`).

## Edit defaults (unless my-style.md or the owner says otherwise)

- Output: vertical 1080x1920, 30 fps, MP4 (H.264 + AAC).
- Video starts on the first spoken word. Cut silence at start/end, long pauses, repeated or fumbled lines. Keep natural rhythm.
- Word-by-word captions, names and brands spelled correctly, kept out of the bottom 15% of the frame.
- Royalty-free music only, kept low under the voice. Sound effects only where they help.
- No filters, colour grading or face blur unless asked.
- Always show a short plan with timestamps and wait for the owner's OK before building.
- After the render: check duration with ffprobe, look at frames, then list every change made.
- Draw inspiration from reference reels, never copy their exact fonts, graphics, logos, music or text.

## Cartoon reels (Bhagwan + Sagar)

**Read `Reference/my-style.md` before every edit.**

- Characters: `characters/krishna.svg`, `characters/sagar.svg` (same art every video).
- Voices (natural, Chatterbox Multilingual in `.venv-tts/`, not in git): `scripts/clone_voice.py`.
  Bhagwan = `voices/bhagwan-ref.wav` (synthetic reference, committed). Sagar = `voices/sagar-ref.wav`, cut from
  Sagar's own recording `voices/sagar-original.mp3` (private, gitignored; never upload or share it).
  Recreate the venv: `python3 -m venv .venv-tts && .venv-tts/bin/pip install chatterbox-tts "setuptools<81"`.
- Sagar records Sagar's lines AND Bhagwan's lines by default (Bhagwan's are voice-converted automatically into
  `voices/bhagwan-ref.wav`). The builder stops with "WAITING FOR SAGAR'S RECORDINGS" until every line has
  `"audio"`; `"allow_clone": true` / `"allow_ai_bhagwan": true` only when Sagar says he cannot record.
- Build a reel: `python3 scripts/make_reel.py projects/<name>/script.json`, then in that folder run the
  HyperFrames `check`, `snapshot`, and `render --quality looks --fps 30 -o ../../Export/<name>-v1.mp4`.
- Sagar's lines: cloned voice by default; a real recording (`"audio"` in script.json) replaces it.
  `"keep_audio": true` reuses an already generated line instead of re-generating it.
