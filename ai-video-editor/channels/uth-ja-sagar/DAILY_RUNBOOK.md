# Daily runbook: "Uth Ja Sagar" (2 Shorts per day)

Talk to Sagar in simple Hinglish. Read `CLAUDE.md` and `Reference/my-style.md` of THIS channel first. This channel is
separate from @Sagarkekrishna (`ai-video-editor/DAILY_RUNBOOK.md`): never touch that channel's files, schedule or login.
Run from `ai-video-editor/`. Do not ask Sagar questions unless something is blocked.

**Times (IST), chosen by Sagar (changed 2026-11-25):** Run 1 research + scripts **08:30**; Run 2 build + upload **12:10**
(recording cutoff = 12:10). Videos go public at **18:00** and at **08:00**. 18:00 IST = 12:30Z, 08:00 IST = 02:30Z.
The 08:00 slot is always before Run 2, so Run 2 uploads **video B for today 18:00 (12:30Z)** and **video A for TOMORROW
08:00 (02:30Z of the next day)**. Both are uploaded at 12:10.
First channel runs at 07:30 and 11:30: keep at least 20 minutes between runs (they share one chat/container).

## Run 1: 08:30 research + scripts
1. Read `CLAUDE.md`, `Reference/my-style.md`, `daily/log.md` (topics already made; never repeat).
2. Trends (real data, YouTube India): `python3 scripts/yt_trends.py --channel uth-ja-sagar --n 25`, plus `--category 22`
   (People & Blogs) and `--category 27` (Education). WebSearch only as a second source. Write the findings in 3 lines.
3. Pick 2 topics. Motivation stories must start from a REAL, everyday situation of Indian 18-30 year olds (result ke
   baad ka darr, "log kya kahenge", naukri/paise, rejection, comparison, thakaan, 5 saal baad bhi wahin) and use the
   trend only as a twist. Test every script: "kya koi ise bhejke bolega: bhai ye meri baat hai?" If not, rewrite.
   Skip politics, real people, religion-bashing, medical or money-making promises.
4. Write `projects/epNN-<slug>/script.json` for both, **following the script rules in `Reference/my-style.md`**:
   question hook in the viewer's own thoughts with SUSPENSE (answer only at the end, one teaser in the middle) -> story -> `seekh` line -> emotional comment + follow ending
   (`"cta": true`). 35-45 s, 9-13 lines. Different pictures, music seed and scenes from yesterday.
5. Run `python3 scripts/make_story.py channels/uth-ja-sagar/projects/<ep>/script.json` (makes the pictures, then stops
   with the list of lines to record).
6. LOOK at every picture; re-roll bad ones (new `seed`).
7. Chat: for each video the topic + why, and **the exact lines Sagar should record** (with the emotion, each line 2 times).
   Say the cutoff is 12:10 IST, after that the clone is used.

## Run 2: 12:10 build, upload, hand over
1. Recordings: `/root/.claude/uploads/<this session>/` audio that arrived after Run 1. Transcribe, match to lines, pick
   the best take with `scripts/pick_takes.py` -> `channels/uth-ja-sagar/Raw/<ep>-line-NN.wav`, set `"audio"`, report scores.
   Update `hi` to what Sagar actually said.
2. Lines without a recording: `"allow_clone": true` (clone settings fixed to option A in `make_story.py`). A video with
   any cloned line is *synthetic*: upload with `--synthetic`.
3. Build, then in the project folder `check` and `snapshot` (LOOK at the frames), `render --quality looks --fps 30`,
   `python3 scripts/make_story.py --finish ...` (-14 LUFS), check duration (35-45 s) and loudness.
   Never `git add -A` while rendering (HyperFrames writes `work-*/`).
4. Thumbnail: `python3 scripts/make_thumb_story.py <best picture from projects/<ep>/assets/images> thumb.jpg "WORD" "WORD"` (question/cliffhanger, 2 lines, see "Thumbnail" in `Reference/my-style.md`; the most shocking picture). LOOK at it. Phone verified on 2026-11-25 (thumbnail upload tested OK). If it ever says `forbidden`, skip `--thumb` and tell Sagar in one line.
5. YouTube metadata from DATA: `python3 scripts/yt_title_research.py --channel uth-ja-sagar "<topic> motivation hindi" "motivational shorts hindi"`.
   Rule: visible title <= 35 characters (<= 6 words), topic keyword first, 1-2 emoji, then 3-4 hashtags starting with
   `#shorts` (e.g. `#shorts #motivation #life`). Description: 2-3 Hinglish lines + "Made By Sagar Mishra" + 5-8
   hashtags. Tags 8-12. State the numbers you found.
6. Upload: `python3 scripts/yt_upload.py --channel uth-ja-sagar --video channels/uth-ja-sagar/Export/<ep>-v1.mp4 --meta meta.json --thumb thumb.jpg --publish-at <UTC> [--synthetic]`
   (B: today 12:30Z; A: tomorrow 02:30Z. If Run 2 is late and 18:00 is less than 30 min ahead, move B to 08:00 tomorrow and A to 18:00 tomorrow; never schedule in the past).
7. Verify: privacyStatus + publishAt in the print-out; next morning check `videos.list?part=status` that it became public.
8. Instagram package (not automatic): both videos via `SendUserFile`, each with a Hinglish caption (hook first line,
   1-2 emoji, 8-12 hashtags), best time (about 08:30 and 18:30 IST) and "Instagram app > + > Reel > Schedule".
9. Append to `channels/uth-ja-sagar/daily/log.md`; commit and push (never recordings, photos, voices, tokens).
10. Final chat message (short Hinglish): what was made, when it goes live, what Sagar must do (only if needed).

## Quota (one Google project shared with the first channel: 10,000 units/day)
Upload 1,600 + thumbnail 50 = 1,650 per video. This channel 2 videos = 3,300; first channel 2 videos = 3,300; title
research 2 searches x 100 = 200 per run. About 7,000 of 10,000 per day. **Never more than 6 uploads/day in total.**
Write the day's estimate in the log.

## Never
- Never put recordings, photos, voices or tokens in the public repo `sagar-baby`; tokens only in `sagar-private`
  (`secrets/youtube-uth-ja-sagar.json`). Never touch `secrets/youtube.json` (first channel).
- Never use Sagar's real face in pictures. Never fake accounts or bypass platform rules.
- Never overwrite an exported version (v2, v3). Never publish the same video twice.
- If something fails: fix it if you can, otherwise write it in the log and tell Sagar in one clear Hinglish line.
