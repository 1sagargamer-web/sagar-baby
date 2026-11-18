# THE REAL SAGAR: editing style guide

**Approved baseline: `Export/demo-intro-v7.mp4`** (project `projects/demo-intro/`, spec `intro.json`). Sagar said
"abhi wala video sahi hai, aisa hi banana". Every new video copies v7's look, motion and sound. Only change a rule
when Sagar asks; then add it to the fix list below.

References (copies in `Reference/refs/`, not in git; list in `refs-list.txt`): ref-2 and ref-3 (meme reaction
videos, 1 host with headset) are the main style; ref-4 is Sagar's screen recording of ref-2's intro; ref-1
(2-host challenge video) only for layouts. Copy their *editing*, never their logos, channel cards, music, sound
files, fonts or exact text.

## Sagar's fix list (always follow, never undo)
1. Text bigger, bolder, glowing like the references.
2. Emoji = big 3D glossy emoji, many at once, behind Sagar.
3. Sagar's ORIGINAL background. No replaced room (looked fake/AI), no face glow (white halo + haze).
4. Text/emoji animation smooth like the references.
5. Sound effects like the references: real recorded-style CC0 sounds, no synthesised sounds, no per-letter blips.
6. Clean cut-out: no dark blurry ring around hair or hands.
7. Hair in front of bright smoke must not look chopped or blink.
8. Never invent viewer comments; ask for real comment screenshots when Sagar mentions comments.
9. Font Lilita One with glossy top, deep straight-down 3D and strong glow (not wide Poppins Black).
10. Every word enters fast with directional motion blur, then stays almost still. No wobble / 3D spinning.
11. Every big word = swish before + deep bass drop on the word.

## Format
- YouTube long video, 1920x1080, 30 fps export, 10-12 min (depends on the recording). No watermark.
- Meme / short-clip reaction: Sagar's face cam + the clip he reacts to.

## Footage
- Original room, only a light brightness fix (`eq=gamma=1.12:contrast=1.04:saturation=1.06`, slight unsharp).
- Cut pauses, "umm" and repeated lines; video starts on the first word.
- Cut-out for words behind Sagar: `hyperframes remove-background` → `scripts/clean_matte.py` (defaults: smoothstep
  0.38→0.85, 1.1 px feather, 3-frame temporal smoothing, edge colour from the person). Always check zoomed
  snapshots of hair and hands over bright words/smoke before rendering.

## Intro (most important)
Built with `scripts/make_reaction_intro.py projects/<video>/intro.json` (copy v7's `intro.json` and change words,
times and positions from the Whisper word timings).
- **One big 3D word per key spoken word**, exactly on the voice. Two words may share the screen (BIG + BOSS).
- **Look:** Lilita One, all caps, 225-430 px, glossy light top → bright colour → deeper colour at the bottom,
  3D extrusion straight down (8 layers in a darker shade + 3 darkest), soft drop shadow, 3-layer glow in the word's
  colour. Palettes: gold, pink, red, cyan, lime, neon (white/pink), purple; each word a different colour.
- **Placement:** fully inside the frame. Words behind Sagar (top, beside the head) may lose at most one letter
  behind the head; words at the bottom go in front. Mix behind/front.
- **Motion:** enter in 0.13 s with directional motion blur (fly-left/right: 60 px horizontal blur; fly-top:
  vertical; zoom/pop: round blur), tiny overshoot (1.04 → 1), hold almost still with a slow push (1 → 1.05),
  exit in 0.12 s with blur in the exit direction (left/right/up, or sink). First word and big bottom words may
  come letter by letter (0.03 s apart).
- **Big moment** (e.g. BIG BOSS, TAHALKA): yellow smoke burst behind the words (fades in over 0.1 s, flying
  shards) + fast punch-in zoom with a small shake.
- **Small captions** for the rest of the sentence: Poppins Black Italic, yellow `#ffe02e`, dark-brown edge, lower
  left, 92 px.
- **Channel card:** our own white card (Sagar's photo, "The Real Sagar", "@TheRealSagarr · 200K subscribers"),
  slides up with blur, cursor clicks Subscribe → "SUBSCRIBED ✓", slides down.
- **Emoji:** Microsoft Fluent 3D emoji (MIT, `@lobehub/fluent-emoji-3d`), thin white border. 🔥💯🤩 pops on a
  hype word; at the end a field of ~22 emoji (110-380 px) behind Sagar, fade+scale in, drift up ~1 s.
- **End:** white flash into the main video.
- **What is said** (reaction videos): greeting (0-5 s) → short chat/hook → "chalo dekhte hain" → first clip.

## Sound
- CC0 sounds from `sfx-library/` (SFXMint, see `SOURCE.md`), trimmed into `assets/sfx/r-*.wav`:
  - every big word: `r-swish` 0.26 s before the word + `r-drop` (bass drop) on the word;
  - big moment: `r-suck` (reverse impact ending on the word) + `r-boom` + `r-impact`;
  - word flying in from the side: `r-flyby`; small caption: quiet `r-pop`;
  - channel card `r-card`, Subscribe click `r-sub`, card out `r-exit`; emoji `r-sparkle` + `r-magic`;
    into the white flash `r-riser`.
- Light upbeat music (`scripts/make_music_hype.py`) at volume ~0.14 under the voice.
- Final mix about -14 LUFS (normalise the audio after the render if needed). Sounds are measured, not heard:
  tell Sagar.

## Main part (from the references; to be confirmed on the first real video)
- Reaction split: the vertical clip on the left as a rounded card with a thin white border, Sagar's face cam
  large on the right; Sagar full screen between clips with jump cuts and alternating zoom (100% ↔ 115-130%).
- Funny moments: punch-in zoom + small shake, short meme insert, emoji bursts, black & white for sad/awkward beats.
- Ending: bye → frame shrinks to a small black & white box → "BONUS" clip, and a "Like" tap that bursts into 3D
  like-bubbles (Sagar wants both).
- Thumbnail like the references (discuss with Sagar). Shorts later, only when Sagar asks.
