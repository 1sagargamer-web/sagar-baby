# Main channel: editing style guide (draft v1)

Learned from 3 reference videos Sagar chose (`Reference/refs-list.txt`; the copies in `Reference/refs/` stay out of git).
Studied frame by frame: intro at 2 fps and the first 6 s at 10 fps, the whole video at 1 frame / 30 s, and
the last 30 s at 1 fps, plus cut detection.

- ref-1: "Guess the Song by Emojis" challenge, 2 hosts on camera, game screen with facecam, 18 min, 1440p60.
- ref-2: "Reacting to funny memes" reaction video, 1 host with headset, 15 min, 1080p60.
- ref-3: same creator as ref-2, reaction to memes and short clips, 16.5 min, 2160p60.

**Rule:** copy the *editing* (structure, timing, layouts, kinds of effects). Never copy their logos, channel
cards, music, sound files, fonts, exact text or graphics. Make our own versions that feel the same.

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

## Still to decide with Sagar
Channel name, what Sagar's own video will look like (facecam? game screen? reaction?), length, watermark,
captions language. See CLAUDE.md once filled in.
