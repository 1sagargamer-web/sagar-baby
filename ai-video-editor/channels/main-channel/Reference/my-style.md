# Main channel: editing style guide (draft v1)

Learned from 3 reference videos Sagar chose (`Reference/refs-list.txt`; the copies in `Reference/refs/` stay out of git).
Studied frame by frame: intro at 2 fps and the first 6 s at 10 fps, the whole video at 1 frame / 30 s, and
the last 30 s at 1 fps, plus cut detection.

- ref-1: "Guess the Song by Emojis" challenge, 2 hosts on camera, game screen with facecam, 18 min, 1440p60.
- ref-2: "Reacting to funny memes" reaction video, 1 host with headset, 15 min, 1080p60.
- ref-3: same creator as ref-2, reaction to memes and short clips, 16.5 min, 2160p60.

**Rule:** copy the *editing* (structure, timing, layouts, kinds of effects). Never copy their logos, channel
cards, music, sound files, fonts, exact text or graphics. Make our own versions that feel the same.

## Sagar's fix list (every fix he asked for; always follow, never undo)
1. Text bigger, bolder and glowing like the references (Poppins Black, 3D extrusion, coloured glow, no black outline).
2. Emoji = big 3D glossy emoji like the references, many at once, behind Sagar.
3. Keep Sagar's ORIGINAL background; no replaced room (looked fake) and no face glow (made a white halo and haze).
4. Text/emoji animations smooth like the references (letter-by-letter springs, motion-blur fly-ins, 3D drift).
5. Sound effects like the references: real recorded-style CC0 sounds, one per text event; no synthesised blips.
6. Cut-out edges clean: no dark blurry ring around hair/hands (`scripts/clean_matte.py`).
7. Hair in front of bright smoke must not look chopped or blink: soft, temporally smoothed edge
   (clean_matte defaults 0.38/0.85, 1.1 px, 3-frame smoothing) and smoke puffs fade in over 0.1 s.
8. Never invent viewer comments; ask Sagar for real comment screenshots when he mentions comments.
9. Text look like ref-2/ref-4 (v7): condensed rounded heavy font **Lilita One** (not wide Poppins Black), glossy
   light top, deep 3D extrusion straight DOWN in a darker shade, strong 3-layer glow in the word's colour, huge
   (260-430 px) but fully inside the frame (only a letter may hide behind the head).
10. Text motion like ref-2 (v7): every word enters in ~0.13 s with **directional motion blur** (SVG blur 60 px along
   the movement: fly-left/right/top, or zoom/pop with round blur), tiny overshoot, then almost still with a slow
   push (scale 1 → 1.05); exits in 0.12 s with blur in the exit direction. No wobble or 3D spinning.
11. Sound like ref-2 (v7): every big word = an airy **swish** just before it (peak on the word) + a deep **bass drop**
   on the word (r-swish + r-drop); big moments add r-suck (reverse impact ending on the word) + r-boom + r-impact;
   fly-ins use r-flyby. Small captions get a quiet r-pop. Final mix around -14 LUFS.

## Format
- YouTube long video, landscape **1920x1080**, 60 fps source looks best (export 30 or 60 fps), 10-18 min.
- Type: talking/reacting host on camera (facecam) + the content being reacted to (memes, short clips,
  game screen).

## INTRO (most important; Sagar asked for extra care here)
The first 3-5 seconds are a fast "greeting title" made of **one big 3D word per spoken word**, synced exactly
to the voice (Whisper word timings).

1. **Word-by-word 3D titles** (0-3 s): e.g. "ALRIGHT" → "SO" → "YO!" → "WHAT'S UP" → "YOUTUBE" →
   "WELCOME" → "BACK" → "REACTION" → "VIDEO".
   - Look: very heavy rounded/bubbly display font, all caps, **thick 3D extrusion**, glossy gradient fill,
     dark outline, drop shadow, soft glow. **Each word a different colour**: yellow-green, cyan, hot pink,
     white-pink, red, yellow-orange.
   - Size: huge, 1/3 to 1/2 of the frame height. Placed left/right of the head, or along the top/bottom.
   - **Text behind the person**: the host's head and body sit *in front of* the big words (person cut-out
     layer above the text). Use this on at least 2-3 words per intro.
   - Motion (each word ~0.3-0.6 s): flies or scales in with motion blur, overshoots (pop), small wobble /
     tilt, then blurs out or is pushed out by the next word. Two words can share the screen (e.g. "SO" left,
     "YO!" right).
   - Extras: a burst/explosion cloud behind the big moment word ("WELCOME BACK"), a flying play-button icon
     next to "YOUTUBE" (draw our own icon, not the real logo).
   - A pop/whoosh sound effect on every word, a bigger impact sound on the burst.
2. **Channel card** (~2.0-2.6 s): a white rounded "profile card" (photo, channel name, Subscribe button)
   pops in at the lower left, slightly tilted, then blurs away. We make our own card with Sagar's channel name.
3. **Small word-by-word captions** for the rest of the greeting sentence: bold italic yellow letters with
   a black outline, lower left ("WE ARE BACK", "WITH ANOTHER").
4. **Topic tease** (3-8 s): punch-in zooms on the host, a full-screen picture of today's topic, previous
   video cards or viewers' comments popping in around the host ("you asked for this"), emoji / heart
   bursts on funny lines.
   **What is said in the intro (ref-1 transcript, ~18 s), the order to follow:**
   greeting + name + a fun rhyming tagline (0-3 s) → "hello, kaise ho" (3-4 s) → "last video par aapne
   comments kiye the ki ye karo" (social proof, 4-9 s) → the question hook "kya aaj ye ho payega?" (10-13 s)
   → "aap bhi saath mein khelna" (13-15 s) → credit line → "let's get started" (17-18 s).
   Reaction videos are quicker: ref-2 = greeting (0-5 s) → "chalo memes dekhte hain, let's go" → first meme at
   ~6 s. ref-3 = greeting (0-4 s) → a short personal chat with viewers (news, "I do it for you guys") →
   "aao reaction video dekhte hain" → first clip at ~35 s.
5. A short subtitle line like "Let's get started" (white italic, bottom centre), then a **white flash** or
   whip transition into the main content. The whole intro is about 15-20 s.

## Main part: layouts
- **Reaction split** (ref-2, ref-3): the vertical (9:16) clip on the left, full height, as a rounded card
  with a thin white border; the host's facecam fills the rest on the right, cropped close on the face.
- **Content big + facecam PiP** (ref-1): the game/content screen fills the frame, the facecam sits as a
  small box in the top-left corner.
- **Host full screen** between clips, while talking; jump cuts with alternating zoom (100% ↔ 115-130%)
  on every cut so it never looks static.

## Pacing
- Intro: a cut / zoom change about every **1.3 s**. Main part: every **2-3 s** in ref-1. In ref-2/3 the
  clip itself plays out (about 7 s between big layout changes), with jump cuts on the host in between.
- Cut every silence, "umm" and repeated line. No dead air.

## Effects used on funny moments
- Fast punch-in zoom (+ small shake) on the host's reaction.
- Meme inserts: a short reaction meme / sticker full screen for 0.5-1 s.
- Emoji rain (laughing, heart eyes) and floating hearts over the host.
- "Confused maths" overlay (equations floating) when someone is thinking.
- **Black & white** freeze/look for a sad or "awkward" beat.
- Whip pan / motion blur transition between sections.
- Short white italic subtitle only for key lines (not full captions all the time).

## Ending
- Host says bye → the frame shrinks into a small black & white box on black → "BONUS" text → a short
  extra funny clip (ref-1).
- Or: a "like" call-to-action where a tap of the finger bursts into many glossy 3D like-bubbles that fill
  the screen (ref-3), then the last line and cut to black.
- No long outro; the video ends within ~3 s of the goodbye.

## Sound
- A pop / whoosh on every intro word and every pop-up, an impact on bursts and punch-ins.
- Background music: upbeat and light, low under the voice (all music and SFX made by us with
  `scripts/make_music.py` / `scripts/make_sfx.py` style synthesis, never their tracks). Not yet listened
  to the references: music levels are *measured*, not heard.
- Final mix around -14 LUFS.

## Rules from Sagar's feedback on the demo intro (v1 → v2), always follow
- **Big words = reference look:** font **Poppins Black** (`assets/fonts/poppins-black.woff2`), all caps, big
  (160-330 px), **no black outline**. Bright fill with a light top highlight, a 3D extrusion in a darker shade of
  the same colour (6 layers, 3 px apart, slanted left or right), a thin light rim and a glow in the word's colour.
  Palettes: lime, cyan, pink, gold (orange glow), red, neon (white with pink neon rim). See
  `projects/demo-intro/index.html` (`.w` classes) and reuse it.
- Words behind Sagar must stay readable: a word may lose at most one letter behind the head; otherwise move it
  to the side or put it in front at the bottom. Mix behind/front in every intro.
- Small captions: Poppins Black Italic, yellow `#ffe02e`, thin dark-brown edge, lower left, 92 px.
- **Emoji = 3D glossy stickers** (Microsoft Fluent 3D emoji, MIT licence, `@lobehub/fluent-emoji-3d` from npm),
  thin white border, 180-420 px, 10-12 at once popping in all over the screen and drifting up (not tiny flat
  emoji, not falling from the top).
- **Background: keep Sagar's ORIGINAL footage, no glow/face light** (v2: replaced room looked fake; v3: the face glow
  made a white halo and haze around hands and face). Only the light brightness fix of v1.
- **Cut-out edges must be crisp:** always run `scripts/clean_matte.py` on the remove-background output (the raw
  model matte keeps a soft dark fringe of the room around hair and moving hands that shows over bright words,
  smoke and emoji). Check zoomed snapshots of hair and hands over the words before rendering.
- **Animation (frame-by-frame study of the references at 30 fps, v3):** built by `scripts/make_reaction_intro.py`
  from `projects/<video>/intro.json`.
  - Some words come in **letter by letter** (each letter springs up from tiny, 0.03 s apart, overshoot), e.g. the
    first word and the big bottom words ("ALRIGHT", "REACTION" in the references).
  - Others **fly in with motion blur** from the left/right/top (blur 18 px, stretched, 3D turn), or pop with blur.
  - While on screen every word **drifts in 3D** (slow rotateY/rotateX + 5% scale), never dead still.
  - Exit: sink down with a tilt, or fly off left/right/up with blur.
  - Two words share the screen (e.g. BIG left + BOSS right, LEKE + AA GAYA!).
  - Big moment = **smoke burst** (yellow cloudy puffs with turbulent edges + flying brown shards) behind the words,
    plus a fast punch-in zoom with a small shake.
  - Emoji field: ~22 3D emoji **behind Sagar**, fade+scale in within 0.25 s all over the screen, drift up ~1 s.
  - Channel card slides up from the bottom with blur, Subscribe click, slides back down.
- **Sound effects (v4):** real recorded-style CC0 sounds from `sfx-library/` (SFXMint, see SOURCE.md), trimmed to
  `r-*.wav`: r-pop (word appears), r-pop-big (big single word), r-whoosh (word flies in), r-exit (words fly out),
  r-impact + r-boom (big moment / smoke burst), r-reveal (big bottom word), r-card + r-sub (channel card, subscribe),
  r-sparkle + r-magic (emoji), r-riser (into the white flash). **One sound per text event, no per-letter blips**
  (v3's synthesised sounds and blips were rejected). Measured, not heard.
- Comments ("aapne comments mein bola tha"): ask Sagar for real comment screenshots when he says it; never
  invent viewer comments.

## Still to decide with Sagar
Channel name, what Sagar's own video will look like (facecam? game screen? reaction?), length, watermark,
captions language. See CLAUDE.md once filled in.
