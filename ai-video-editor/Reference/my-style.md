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
- **Sagar's lines: Sagar records them by default.** After each reel's script is ready, send Sagar the
  list of Sagar's lines to record and wait for the recordings (`"audio"` in script.json). Use the cloned voice
  (`voices/sagar-ref.wav`, private, never in git; Chatterbox, sped up 1.15x) **only when Sagar says he cannot
  record** for that reel.
- **Bhagwan's lines: always the same voice, `voices/bhagwan-ref.wav` ("Shaant Gehri", option 1, chosen by
  Sagar; synthetic, no real person's voice). Never change it.**
  - Default: Sagar records Bhagwan's lines too (calm, slow, a smile in the voice, pause at "..."), and they are
    converted into that voice with Chatterbox VC (`"audio": "Raw/...", "vc": true` on the krishna line).
    Ask for these recordings together with Sagar's own lines.
  - If Sagar cannot record Bhagwan's lines, Chatterbox TTS speaks them from the same reference (seed 7).
  - Other options tried and not chosen are kept in `voices/bhagwan-options/` (only if Sagar asks again).
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

## Sound effects (every reel, automatic)
- Made by `scripts/make_sfx.py` into `sfx/` (all synthesised). Bhagwan appears -> whoosh + shimmer;
  thumbs-up -> pop; punchline push-in -> short whoosh; shock + shake -> boom.
- Extra on any line: `"sfx": [{"name": "ding", "at": 0.2}]`. `"sfx": false` at the top turns them off.

## Watermark (every reel)
- "Made By Sagar Mishra", small pill at the top centre (y = 196 px, just under the phone status bar), whole video.
  Change the text with `"watermark": "..."` in script.json.

## Sagar's recordings
- **Sagar may change words while recording (Sagar's own wording). Always transcribe the chosen take and update that
  line's `hi` and `caption` in script.json to what Sagar actually said.** Tell Sagar which lines changed.
- Sagar often says each line 2+ times. Run `python3 scripts/pick_takes.py Raw/<file> "<hi text>" Raw/<reel>-sagar-<n>.wav`:
  it splits the takes, scores them (Whisper confidence, completeness, clipping), saves the best de-clipped, and
  prints the scores to report to Sagar.

## Variety in every video (Sagar's rule: never repeat the same look and sounds)
- **Background**: a different theme each reel: park, temple, night, city, room, beach (`"scene": "..."` in
  script.json, otherwise rotated by title). Pick the one that fits the story (temple for aashirwad, night for
  late-night reels, room for phone/bed jokes, city for shaadi/office, beach for holiday). Do not use the same
  theme as the previous reel. Add new themes in `scripts/scenes.py` when a topic needs one.
- **Funny sound effects**, different per reel (`scripts/make_sfx.py`): scratch, boing, dundun, bonk, airhorn on
  the punchline; bassdrop ("sigma moment" vibe, original), boom, slip, sad trombone on the shock. Picked from the
  title, or choose by hand with `"sfx": [{"name": "bassdrop", "at": 0.1}]`. Never copy a real meme audio.
- **Expressions**: Sagar eyes `heart`, `side` (suspicious), Krishna eyes `wink`, plus the existing ones. Use a
  fresh expression whenever the joke allows. **Keep improving**: every new reel should add or improve something
  (a new expression, effect, background, camera move) instead of repeating the last one.

## How to make a new reel
1. Write `projects/<name>/script.json` (see `projects/demo-result/script.json`).
2. Put Sagar's recordings in `Raw/` and set `"audio"` on each of Sagar's lines.
3. `python3 scripts/make_reel.py projects/<name>/script.json`
4. Check, snapshot, render to `Export/<name>-v1.mp4` (see CLAUDE.md).
