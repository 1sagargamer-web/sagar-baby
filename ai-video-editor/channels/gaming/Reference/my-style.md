# Gaming channel style guide (Free Fire awareness videos)

Learned from 4 reference videos (Sagar's private Hugging Face dataset `sagar5582/gaming-ref`, never in git):
ref1 "I Used J@DU For 24 Hours" (9:12), ref2 "Free Fire Panel for 24 Hours... Is It Really Safe?" (17:21),
ref3 "Playing Tournaments by Using Antiban Panel" (10:20), ref4 "Most Dangerous P@nel for 24 Hours" (10:01).
We take the *editing principles* only. Never reuse their footage, thumbnails, logos, music, voice or exact lines.

## What the channel is
- YouTube **long videos, 8-15 minutes, landscape 1920x1080** (gameplay decides the source size; output is always
  1920x1080). No watermark.
- Topic: **awareness** about Free Fire cheat panels/hacks, so new players do not fall for them.
- Sagar sends the gameplay. Claude does everything else: cuts, zooms, motion graphics, captions, voice, music, SFX.

## Awareness rules (every video, no exceptions)
1. **Disclaimer first**, 4 s, Sagar's own text (`Reference/disclaimer.png`, crisp 1920x1080 remake of his image
   `Reference/disclaimer-original.jpg`; same words, do not change them).
2. **Never show a panel's name, logo, login screen, website, Telegram/YouTube/Discord link, price or seller.**
   Blur them whenever they are on screen. Never say or show where to get a panel.
3. Cheat features (aimbot, ESP lines) may be shown, framed as "this is how cheaters ruin matches", never as
   "look how OP this is, you should try it".
4. **Every video ends with the truth**: ban screen, scam / money lost, account or ID stolen, how to spot a
   cheater and report them. The ending is not optional.
5. Titles and hooks may be curiosity clickbait ("Maine panel test kiya... aur ye hua 😱"), never promotion
   ("pro ban jao", "100% antiban", "SHOCKING RESULTS ✅").
6. Advice given to Sagar (his call): record in training ground / custom rooms / with friends, not ranked or
   tournaments with real players; test only on an old phone with a fresh guest account.

## Structure (from the references)
1. **0-3 s:** disclaimer card.
2. **3-25 s, hook:** big words on black, one or two at a time, punchy (white / yellow / red / green), with short
   black-and-white gameplay clips in between ("AAJ HUM... 24 GHANTE... BUT.."). Ends on a question:
   "kya ID ban hogi?"
3. **Setup (~30-60 s):** lobby, account level, what we are testing, "24 HOURS" title card.
4. **Main gameplay (most of the video):** match after match, a short title card per match/round
   ("MATCH 1", "CLASH SQUAD", "ROUND 6"), commentary over it.
5. **Turning point:** the consequence (ban notice, scam, account gone): slow zoom, music drops out, boom.
6. **Ending (~30-60 s):** lesson + "cheater ko kaise pehchano / report karo", subscribe ask, end card.

## Pacing and motion
- Something changes every **1-3 s** in the hook and every **3-6 s** in gameplay: cut, zoom, caption, pop-up.
- Cut dead time: loading screens, menus, running with nothing happening, death cams (keep 1 s max).
- **Punch-in zoom** (110-140 %, 0.15 s in) on kills, important UI text, chat messages, the ban notice.
- **Pop-up callouts**: a zoomed copy of a UI detail (kill feed, chat, level-up) in a rounded box with an arrow.
- **Meme / reaction cutaways** (0.5-1.5 s): only our own drawn graphics or text cards, never copied
  memes, stock faces or other creators' clips. Red flash + "HAHA" style text punch is fine (our own design).
- Black-and-white + slow motion for "flashback" or dramatic moments.
- Transitions: hard cuts mostly; a quick whip/zoom blur between matches. No slow dissolves.

## Captions and on-screen text
- **Key-word captions** (not every word): big bold condensed CAPS (font: Anton, open licence), white with a thick
  black outline, bottom centre (above the bottom 12 %), 1-3 words at a time, pop in (scale 80 -> 100 %).
  Important word in **yellow**, danger words (BAN, SCAM, HACK) in **red**.
- Title cards (black background): same font, one word or short phrase, centred, 0.5-1 s each.
- Hindi words in Roman letters (Hinglish).

## Commentary script (from the reference transcripts)
- **Opening line is a question** (first 5-8 s): "Kya aapne kabhi socha hai ki agar 24 ghante panel use karein to ID
  ka kya hoga?" / "Kya is baar Garena detect kar payegi?"
- Then **stakes + tease the ending**: "End mein jo hua na bhai, wo bilkul miss mat karna, abhi spoiler nahi
  dunga." Optional one-line recap of the last video ("pichhli video mein...").
- Then "chalo fatafat start karte hain" and straight into gameplay within ~30 s.
- During gameplay: short live reactions ("bhai bhai bhai", "dekho", "ye peeche se aa raha hai"), explain what is
  happening on screen, keep talking; silence longer than ~3 s gets music/SFX or a cut.
- Speaking speed in the references: about 120-200 words per minute, i.e. fast and energetic.
- Our own addition (awareness): the voice says *why it is wrong / risky* at least once per match and fully at the
  end. Never "panel kahan milega wo bhi bataunga" (ref2 does this; we never do).

## Voice
- Sagar's own voice, **cloned** from his recording (private, never in git). **Claude writes the whole commentary**;
  Sagar only sends gameplay.
- Sagar's feedback (2026-11-18): options A (calm) and C (hype) both good, but still sounds AI -> make it more natural.
  Chosen setup: see `CLAUDE.md` (Voice).
- Commentary style in the references: casual live Hinglish, talking to viewers ("guys", "dekho", "bhai"),
  reacting to kills, chatting with teammates, ending on the ban reveal.
- If Sagar's gameplay already has his live mic commentary, keep it (clean it up, cut fumbles) and use the
  clone only for extra lines he asks for.

## Sound
- Loudness: final mix **-14 LUFS**, true peak -1 dB. Voice always on top; music ducks under voice.
- Game sound kept but low under the voice (references measured: non-speech parts around -30 dB).
- Music (approved by Sagar): original synthesised tracks (`scripts/make_gaming_music.py`): hype trap/phonk style beat for
  gameplay, dark suspense pad for the turning point, silence for 0.5 s before a big reveal.
- SFX (`scripts/make_gaming_sfx.py` -> `sfx/gaming/`, all synthesised): whoosh on title cards, impact/boom on
  big words and reveals, riser before the reveal, glitch on the ban notice, pop on callouts, ding on kills.

## Never
- No watermark. No copied memes, music, logos or creator footage. Never show panel names/links/prices.
- Never overwrite an export: `Export/<name>-v1.mp4`, `-v2`, ...
