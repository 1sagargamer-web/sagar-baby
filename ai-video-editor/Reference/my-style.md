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
- **Sagar's lines: Sagar's own recorded voice** (one clip per line, or one recording split by Whisper).
- **Bhagwan's lines: always the same AI voice**, set in `scripts/god_voice.py` (`VOICE`): Kokoro Hindi male,
  slightly slow, 10% deeper, soft echo. Never change it between videos.

## Captions
- One caption per line in **Hinglish (Roman letters)**, white rounded box with black outline, bold Poppins,
  near the top (y = 330 px), pops in with each line. Bhagwan's box is light gold.

## Motion
- Lip-flap from the voice, blinks every ~3-4 s, gentle breathing, head nods while talking.
- Camera: push-in on the punchline, shake on the shock. No fast cuts; it is one continuous shot.

## Sound
- Voices are the main sound. Music only if Sagar gives a royalty-free track, or he adds trending audio in
  Instagram himself. Mix around -14 LUFS.

## How to make a new reel
1. Write `projects/<name>/script.json` (see `projects/demo-result/script.json`).
2. Put Sagar's recordings in `Raw/` and set `"audio"` on each of his lines.
3. `python3 scripts/make_reel.py projects/<name>/script.json`
4. Check, snapshot, render to `Export/<name>-v1.mp4` (see CLAUDE.md).
