# Sagar ki reel style guide

Learned from 5 reference reels (`Reference/ref-1.mp4` ... `ref-5.mp4`, 10-22 s each). We take the
*principles* only. Never reuse their characters, drawings, watermarks, voices or exact jokes.

## Format
- 2D flat cartoon comedy, vertical 1080x1920, 30 fps, **10-20 seconds**.
- Exactly **2 characters**: **Bhagwan** (Krishna ji) and **Sagar** (the owner).
  Character art lives in `characters/krishna.svg` and `characters/sagar.svg`; reuse them every time.
- One simple outdoor scene (sky, clouds, hills, bushes in front). Both characters face camera, side by side,
  Sagar left, Bhagwan right.

## Story shape (from the references)
1. **Hook in the first line** (0-3 s): Sagar asks Bhagwan for something everyday (job, result, breakup, money).
2. **Bhagwan appears** with a soft divine flash and replies calmly.
3. **Back and forth**, 3-6 short lines total, Hindi/Hinglish, everyday words.
4. **Twist / punchline from Bhagwan** (camera push-in on him, smug half-closed eyes).
5. **Sagar's reaction** (shocked eyes, "O" mouth, sweat drop, small camera shake), hold ~1 s, end.

## Voices
- **Sagar's lines: cloned from Sagar's own recording** (`voices/sagar-ref.wav`, private, never in git) with
  Chatterbox Multilingual. A real recording of a line (`"audio"` in script.json) always wins.
- **Bhagwan's lines: always the same natural voice**: Chatterbox speaking from the fixed synthetic reference
  `voices/bhagwan-ref.wav` (no real person's voice), seed 7. Settings in `VOICES` in `scripts/make_reel.py`.
  Never change them between videos.
- Listener reactions: `"sagar_face"` / `"krishna_face"` on a line set how the other character reacts.

## Captions
- One caption per line in **Hinglish (Roman letters)**, white rounded box with black outline, bold Poppins,
  near the top (y = 330 px), pops in with each line. Bhagwan's box is light gold.

## Motion
- Lip-flap from the voice, blinks every ~3-4 s, gentle breathing, head nods while talking.
- Camera: push-in on the punchline, shake on the shock. No fast cuts; it is one continuous shot.

## Sound
- **Every reel gets background music**: an original tune made by `scripts/make_music.py` (bansuri + tanpura +
  soft keherwa tabla, all synthesised, no licence issues). A new tune per reel (seed from the title), volume 0.25
  under the voices. `"music": {"seed": 5, "bpm": 100, "volume": 0.3}` in script.json changes it,
  `"music": false` turns it off (e.g. to add trending audio in Instagram).
- Sagar's cloned voice is sped up 1.15x (rubberband, formant preserved). Mix around -14 LUFS.

## How to make a new reel
1. Write `projects/<name>/script.json` (see `projects/demo-result/script.json`).
2. Put Sagar's recordings in `Raw/` and set `"audio"` on each of Sagar's lines.
3. `python3 scripts/make_reel.py projects/<name>/script.json`
4. Check, snapshot, render to `Export/<name>-v1.mp4` (see CLAUDE.md).
