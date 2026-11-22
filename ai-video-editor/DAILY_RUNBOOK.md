# Daily runbook (2 Shorts per day for @sagarkekrishna)

Talk to Sagar in simple Hinglish. All the rules in `CLAUDE.md` and `Reference/my-style.md` apply to every video.
This file is the checklist for the two daily scheduled runs (IST). Do not skip steps; do not ask Sagar questions
unless something is blocked.

## Run 1: morning (about 7:30 IST): research + scripts
1. Read `CLAUDE.md`, `Reference/my-style.md`, `daily/log.md` (what was already made, which scenes/sfx were used).
2. Trends: `python3 scripts/yt_trends.py --n 25`, plus `--category 23` (comedy) and `--category 24`. Use WebSearch
   only as a secondary source (it is US-only and often dated). Write what you found in 3 lines.
3. Pick 2 topics. Sagar's feedback (22 Nov 2026): the jokes were NOT funny and NOT relatable. So every script must
   start from a REAL everyday situation that Indian 18-30 year olds have lived (examples: Mummy ka phone/khana, exam
   ke last din, wifi ya data khatam, "5 minute aur" neend, salary/paise, crush ka seen, relatives ke sawal, gym kal se,
   charger 1 percent, delivery late, Maggi/chai, bike petrol, group project). Use today's trend only as a TWIST on
   that situation, never as the whole idea. Write the pain in specific details (numbers, objects, names like Mummy,
   Guddu, aunty) and make Bhagwan's punchline a surprising but kind twist that Sagar's audience would repeat.
   Test each script: "would a friend send this reel with 'bhai ye tu hai'?" If not, rewrite. Do not copy any creator's
   joke. Skip tragedy, politics, real people, and anything that mocks Bhagwan or hurts religious feelings.
4. Write `projects/epNN-<slug>/script.json` for both: 4 to 5 lines, 12 to 18 s, short fast lines (about 8 to 10 words
   each), and END WITH A LAUGH (see below). Make them different from the last
   videos: new `scene`, new expressions (heart/side/wink), and a new funny sfx via `"sfx"` when it fits.
5. Run `python3 scripts/make_reel.py projects/<ep>/script.json` (it stops with the list of lines to record).
6. Post in chat: for each video, the topic + why it is trending, and **the exact lines Sagar should record** (Sagar's
   lines and Bhagwan's lines, with the emotion), and say the cutoff is 11:30 IST; after that the clone / AI voice is used.

## Run 2: late morning (about 11:30 IST): build, upload, hand over
1. Recordings: look in `/root/.claude/uploads/<this session>/` for audio files that arrived after Run 1's message.
   Transcribe each (`scripts/transcribe.py`), match it to the expected line, and pick the best take with
   `scripts/pick_takes.py` (save to `Raw/<ep>-sagar-N.wav` or `-bhagwan-N.wav`). If Sagar changed words, update `hi` and
   `caption` to what Sagar said. Bhagwan recordings get `"vc": true` (converted voice).
2. Lines without a recording: set `"allow_clone": true` and `"allow_ai_bhagwan": true` in script.json (Sagar said: use
   the clone, no questions) and remember that this video is *synthetic* (for the YouTube label).
3. Build (`make_reel.py`), `check`, `snapshot` and LOOK at the frames, render (`--quality looks --fps 30`), measure
   loudness (about -14 LUFS), check duration. Fix problems before going on. If a line is unclear after conversion, try
   other seeds / use the AI voice for that line.
4. Thumbnail: `scripts/make_thumb.py` (two short punchy lines, 2 to 3 words each). LOOK at it. Fix marks.
5. YouTube metadata, from DATA (Sagar's rule: titles must be SHORT and compared with what works):
   run `python3 scripts/yt_title_research.py "<topic keywords>" "krishna comedy shorts hindi"` and compare the
   most-viewed recent Shorts in this niche. Finding on 21 Nov 2026 (60 Shorts): top-20 visible title (text before the
   first #) has a median of 32 chars / 6 words; videos with a visible title <= 35 chars averaged 38M views vs 22M for
   > 45 chars; 85% use emoji (median 2); median 4 to 5 hashtags, 87% have `#shorts`; Hindi (Devanagari) vs Roman
   showed no clear winner (n is small), so use Roman/Hinglish with the topic keyword in the title.
   RULE: visible title <= 35 chars (<= 6 words), the topic keyword first (e.g. "GTA 6", "Maggi"), 1 to 2 emojis,
   then 3 to 4 hashtags starting with `#shorts` (e.g. `#shorts #comedy #krishna`). Never a long sentence.
   Description: 2 to 3 Hinglish lines + "Made By Sagar Mishra" + 5 to 8 hashtags. Tags: 8 to 12, relevant, honest.
   Re-run the research each day, because what works changes. State the numbers you found in the chat message.
6. Upload: `python3 scripts/yt_upload.py --video ... --meta meta.json --thumb thumb.jpg --publish-at <UTC ISO>
   [--synthetic]`. Slots (IST): video A at **13:30**, video B at **20:00** the same day (if a video is late, use the
   next slot at least 30 min ahead, never past 22:00). IST = UTC + 5:30, so 13:30 IST = 08:00Z and 20:00 IST = 14:30Z.
7. Verify: the print-out shows `privacyStatus` and `publishAt`. Later (the next morning run) check with
   `videos.list?part=status&id=...` whether the videos actually became public at the slot. Write the result in
   `daily/log.md`. **Verified on 21 Nov 2026: a video uploaded with --publish-at DID become public by itself at its slot (Ep07), so no
   audit and no manual Public step is needed.** Only if a check ever shows a past slot still private, tell Sagar in one
   line to set it Public in YouTube Studio.
8. Instagram package (Instagram cannot be automated: the Facebook account is closed): send both videos with
   `SendUserFile` and, for each, an Instagram caption (Hinglish, hook first line, 1 to 2 emojis, 8 to 12 hashtags),
   the best time (about 13:00 and 20:30 IST, 12 to 2 PM and 7 to 10 PM windows) and "Instagram app > + > Reel >
   Schedule". Keep it to a short message.
9. Append to `daily/log.md`: date, topics, scene/sfx used, video ids, scheduled times, voice used (real/clone/AI),
   publish status. Commit and push `ai-video-editor/` (never recordings, never `voices/sagar*`, never any token).
10. Final chat message (short, Hinglish): what was made, when it goes live on YouTube, what Sagar must do (only if
    needed). Never paste tokens or secrets.

## Never
- Never put recordings, tokens or the client secret in the public repo `sagar-baby`. Tokens live only in `sagar-private`.
- Never create or use fake accounts; never bypass platform rules.
- Never publish the same video twice; never overwrite an exported version (use v2, v3).
- If anything fails (tools missing, upload error): fix it if you can, otherwise write it in `daily/log.md` and tell
  Sagar in one clear Hinglish line.

## Ending (Sagar's rule, 22 Nov 2026)
After Bhagwan's punchline there must be a funny LAUGH, not a long reaction line: the last line is
`{"who":"sagar","laugh":true,...}` (Sagar laughs, or "sad then laughs") or Krishna laughs `{"who":"krishna","laugh":true}`.
Sagar ends either sad (tears) or happy/mast, never a flat line. If Sagar recorded his own laugh
(`Raw/<ep>-laugh.wav`), use it as `"audio"`.

## Backgrounds (Sagar's rule, 22 Nov 2026)
No buildings, city, room or beach. Use Krishna's world only: `vrindavan` (kadamba trees, flowers), `gokul` (huts, cow,
makhan matke), `yamuna` (river ghat, diyas), `govardhan` (mountain), `temple` (old mandir), `park`. They rotate
automatically (scripts/scenes.py KRISHNA_ORDER); pick the one that fits the story and never repeat yesterday's.
