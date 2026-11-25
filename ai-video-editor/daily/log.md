# Daily log (one entry per day; newest at the bottom)

Already made (do not repeat these topics):
- Ep01 exam ka aashirwad (temple/park) | Ep02 naseeb mein girlfriend | Ep03 pasand ki ladki (story mute) | Ep04 pasand ki ladki 2 (bhaiya kaun)
- Ep05 shaadi season aunty (demo) | Ep06 reel ka nasha (demo)
- YouTube: Ep04 uploaded privately as a test (video id xq8w6m3Hjgw)

## 2026-11-21 (Sat)
- Run 1 done (7:28 IST). Trends seen (YouTube India): GTA 6 gameplay, Tulsi Vivah / Dev Uthani geet (festive), Hindi comedy shorts (My Life Nowadays, School Lunch, Shadi with siblings).
- Video A: Ep07 "GTA 6 cheat code" (trend, scene room, new expressions side + wink)
- Video B: Ep08 "Mahine ka end, Maggi moksh" (evergreen, scene city, heart eyes)
- Waiting for Sagar's recordings until 11:30 IST; otherwise clone + AI Bhagwan.
- Run 2 done (11:33 IST). No recordings arrived, so both videos used clone + AI Bhagwan (marked synthetic).
- Ep07 GTA 6 cheat code: YouTube id mSWWaeqh3BU, scheduled 13:30 IST (08:00Z), scene room, 23.2 s
- Ep08 Maggi moksh: YouTube id usjU3BozST0, scheduled 20:00 IST (14:30Z), scene city, 22.3 s
- Check later: did both become public by themselves at the slot? (un-audited API project; result goes here)
- Yesterday's scheduled videos: none (no daily run yesterday). Ep04 test upload xq8w6m3Hjgw stays private.
- Note: Hindi TTS mispronounces Latin "GTA 6"; write Hindi text as "जीटीए सिक्स" (caption keeps GTA 6).
- Title fix (21 Nov): Sagar said titles were too long. Analysed 60 top Krishna/comedy Shorts (India, last 90 days): top-20 visible title median 32 chars / 6 words; <=35 chars averaged 38M views vs 22M for >45; 85% emoji; ~4 to 5 hashtags. Re-titled Ep07 "GTA 6 vs Asli Zindagi 😭 #shorts #gta6 #comedy #krishna" and Ep08 "Mahine ka End = Maggi Moksh 🍜 #shorts #comedy #krishna". New rule in DAILY_RUNBOOK.md and my-style.md.
- CHECK 21 Nov 13:46 IST: Ep07 (mSWWaeqh3BU) became PUBLIC by itself at its 13:30 IST slot (no audit needed so far). Ep08 (usjU3BozST0) still private, scheduled 20:00 IST. The API did not echo containsSyntheticMedia back (shows None): verify the "altered/synthetic" label in YouTube Studio once.

## 2026-11-22 (Sun)
- Yesterday's result: both Ep07 (463 views) and Ep08 (82 views) went public by themselves at their slots. No manual step needed.
- Run 1 done (7:28 IST). Trends: Tulsi Vivah/Dev Uthani (shaadi season starts), GTA 6 still big, Hindi comedy shorts.
- Video A: Ep09 "Save the date" (trend: shaadi season, scene temple, heart eyes)
- Video B: Ep10 "Sunday raat ka darr" (evergreen, scene night, tears + wink)
- Run 2 done (11:33 IST, 22 Nov). No recordings arrived: clone + AI Bhagwan (marked synthetic). Fixed: "सोमवार" mispronounced by clone, so Hindi text uses "मंडे"; line 1 of Ep10 had stray babble, regenerated with exaggeration 0.5.
- Ep09 Save the Date: YouTube id j_3i8ul9phQ, "Shaadi Season: Save the Date 😭 #shorts #comedy #krishna #shaadi", slot 13:30 IST (08:00Z), scene temple, 22.6 s
- Ep10 Sunday night ka dard: YouTube id uxZJnQ0tJ68, "Sunday Night ka Dard 😭 #shorts #comedy #krishna #monday", slot 20:00 IST (14:30Z), scene night, 21.9 s
- Title research numbers today: shaadi/family comedy top-20 visible title median 36 chars / 7 words, hashtags 5, emoji 2; Sunday/Monday niche has few big videos (0.0M), pattern = short title, 1 emoji, #shorts.
- Titles of yesterday's videos could not be compared yet (views: Ep07 463, Ep08 82 on the morning of 22 Nov).

## 2026-11-23 (Mon)
- Performance on 23 Nov morning (views/likes): Ep08 Maggi moksh 1133/10, Ep10 Sunday night 661/15, Ep07 GTA 6 572/2, Ep09 Save the Date 423/1. Relatable everyday situations beat trend topics (small numbers, but matches Sagar's feedback). All four became public by themselves at their slots.
- Run 1 done (7:28 IST), first run with the new rules (relatable story, laugh ending, Krishna-world scenes, 12 to 18 s).
- Video A: Ep11 "Mummy ki chappal" (relatable, scene gokul, Maiya/okhli twist, Sagar's laugh at the end)
- Video B: Ep12 "Paper ke baad roll number yaad" (relatable, scene govardhan, Geeta twist, Bhagwan laughs at the end)
- Run 2 done (11:33 IST, 23 Nov). No recordings arrived: clone + AI Bhagwan (synthetic label), fixed laughs used (Sagar's in Ep11, Bhagwan's in Ep12). Fixed: Ep12 line 3 clone dropped "रोल नंबर" -> regenerated (exaggeration 0.5). Fixed: Govardhan mountain floated above the hills -> widened and joined to the ground in scripts/scenes.py.
- Ep11 Mummy ki chappal: YouTube id voWzeEx8dd4, "Mummy ki Chappal 😱😭 #shorts #funny #maa #krishna", slot 13:30 IST (08:00Z), scene gokul, 13.8 s
- Ep12 Paper ke baad roll number: YouTube id f9Y3rIFsmv8, "Paper ke Baad Roll Number 😭 #shorts #funny #exam #krishna", slot 20:00 IST (14:30Z), scene govardhan, 15.2 s
- Title research numbers today: mummy/chappal top-20 visible title median 38 chars / 8 words, hashtags 2, emoji 1 (e.g. "Are meri chappal 😱😭"); exam/paper top-20 median 34 chars / 6 words, hashtags 5, emoji 2 (e.g. "Students in Exam Hall 📝").

## 2026-11-24 (Tue)
- Performance morning of 24 Nov (views/likes): Ep10 Sunday night 1383/28, Ep08 Maggi 1142/10, Ep07 GTA 588/2, Ep09 Save the Date 567/2, Ep11 Mummy chappal 336/1 (posted 13:30 IST yesterday), Ep12 Roll number 138/2 (posted 20:00 IST yesterday, only ~11 h old). All six public by themselves.
- Run 1 done (7:28 IST). Trends: Avengers Doomsday trailer, Panchayat S5 trailer, GTA 6, Tulsi Vivah; winter starting.
- Video A: Ep13 "Sardi mein razai" (relatable, scene yamuna, Sagar-manthan pun on Sagar's name, Bhagwan laughs)
- Video B: Ep14 "Fridge baar baar" (relatable, scene vrindavan, makhan-chori twist, Sagar laughs)
- Run 2 done (11:33 IST, 24 Nov). No recordings arrived: clone + AI Bhagwan (synthetic label); fixed laughs used (Bhagwan's in Ep13, Sagar's in Ep14). Voice clarity 94 to 99 %.
- Ep13 Sardi mein razai: YouTube id YcPAIUED2iQ, "Sardi mein Razai se Nikalna 🥶😭 #shorts #funny #krishna", slot 13:30 IST (08:00Z), scene yamuna, 18.5 s. Thumbnail frame chosen at 80 % (earlier frames showed a tree trunk block behind the text).
- Ep14 Fridge baar baar: YouTube id 3ZshxLTi_rg, "Fridge Baar Baar Kholna 😭 #shorts #funny #relatable", slot 20:00 IST (14:30Z), scene vrindavan, 17.6 s.
- Title research numbers: winter/razai niche top-20 visible title median 53 chars (weak data, mostly tiny videos); fridge niche median 58 chars but nearly all under 1M views. Kept our titles at about 40 chars, 1 to 2 emoji, 3 hashtags (shorter titles did better in the 21 Nov analysis).
- Note for the next run: thumbnails with a tree at the top-left can show a brown block behind the text; check the frame at 0.5/0.8 and look at it before uploading.

## 2026-11-25 (Wed)
- Performance morning of 25 Nov (views/likes): Ep10 Sunday night 1514/28, Ep08 Maggi 1145/10, Ep12 Roll number 1117/12, Ep11 Mummy chappal 974/7, Ep09 Save the Date 581/3, Ep07 GTA 587/2, Ep14 Fridge 369/6 (12 h old), Ep13 Razai 340/1. All eight public by themselves. Exam/Mummy (shared school-home situations) beat seasonal/trend ones.
- Run 1 done (7:28 IST). Trends: Avengers Doomsday trailer, Panchayat S5 trailer, GTA 6, Tulsi Vivah, chess world championship.
- Video A: Ep15 "Bijli ka bill" (relatable, scene gokul, Sagar laughs)
- Video B: Ep16 "Group mein sabne seen kiya" (relatable, scene vrindavan, Sudama twist, Bhagwan laughs)
- Run 2 done (11:33 IST, 25 Nov). No recordings arrived: clone + AI Bhagwan (synthetic label), fixed laughs (Sagar's in Ep15, Bhagwan's in Ep16). Fixed stray words in Ep15 line 1 ("काय थी") and Ep16 line 3 ("चाहिए", 6 s) by regenerating at exaggeration 0.5; both videos shrank to about 16 s.
- Ep15 Bijli ka bill: YouTube id ie-6Cw2J_zs, "Bijli ka Bill 😱 #shorts #funny #comedy #krishna", slot 13:30 IST (08:00Z), scene gokul, 16.2 s
- Ep16 Group mein seen no reply: YouTube id KTMfnD1q-Qw, "Group mein Seen, No Reply 😭 #shorts #funny #relatable", slot 20:00 IST (14:30Z), scene vrindavan, 16.1 s
- Title research numbers: bijli-bill niche top titles are very short (e.g. "Ac ka bill" 10 chars 0.5M, "Tension nhi leni" 19 chars 0.3M), top-20 median 46 chars; group-chat niche has little data (8 videos). Kept ours at 30 to 40 chars.
- Thumbnail lessons added to DAILY_RUNBOOK.md (no emoji in thumbnail text, choose frame with both characters and no brown block).
