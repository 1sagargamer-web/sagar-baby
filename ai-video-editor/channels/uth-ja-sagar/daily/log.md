# Daily log: Uth Ja Sagar (newest at the bottom)

Already made (do not repeat these topics):
- Ep01 "Sabr Rakho": bamboo ki kahani, v1 (not uploaded; first test video)

## 2026-11-24
- Setup day. Decisions by Sagar: 2 videos/day, public at 19:00 and 21:30 IST, research 08:30, build 12:10 (cutoff),
  Instagram package every day. YouTube channel not created yet; login + schedule pending.

## 2026-11-25
- Channel created: Uth Ja Sagar, handle @uthjasagar, channel id UCiqYieQjg26EG7NbJTw7XlQ, Google account utajasagar@gmail.com.
- Login done (device-code); token saved ONLY in sagar-private/secrets/youtube-uth-ja-sagar.json. channels?mine=true shows the right channel.
- Test upload (private, synthetic): Ep01 "Sabr Rakho" video id ffV5lAgZKME. Stays private (test).
- Custom thumbnail: 403 forbidden (channel not phone-verified yet). Sagar must verify at youtube.com/verify. scripts/make_thumb_story.py ready.
- API did not echo containsSyntheticMedia (same as the first channel): check the label once in YouTube Studio.
- Scheduled tasks created: Run 1 daily 08:30 IST (trig_01UUPAtWhoKXKv9oHu51ZtC5), Run 2 daily 12:10 IST (trig_01VDwNc8tpmaTnbVD1ddD7Kq). First channel runs at 07:27 and 11:33 (gap >= 37 min).
- Phone verified by Sagar; custom thumbnail upload tested OK on ffV5lAgZKME (50 units).

## 2026-11-25 (later)
- Sagar changed the public times to 08:00 and 18:00 IST. Run 2 (12:10) uploads B for today 18:00 and A for tomorrow 08:00. First 08:00 video: 2026-11-27 (first Run 2 is 2026-11-26).

- Channel settings set via API (2026-11-25): description, keywords, country IN, language hi, banner (assets/brand/banner.jpg). Profile picture cannot be set by API: Sagar sets assets/brand/avatar.jpg by hand. Rules added: suspense hook + question thumbnail (my-style.md).

## 2026-11-26
- Run 1 done (08:30 IST). Trends (YouTube India): shaadi season vlogs, purana ghar, Panchayat S5, GTA 6, Avengers. Category 27 (education) has no trending chart in India (404).
- Video B (today 18:00): Ep03 "Last Bench Wala" (evergreen, late bloomer). Video A (tomorrow 08:00): Ep02 "Aunty Ka Sawal" (shaadi season). Pictures generated; waiting for recordings until 12:10 IST.
- Run 2 done (12:10 IST). No recordings arrived, so both videos used the clone (option A) and are marked synthetic (`--synthetic`).
- Ep03 "Last Bench Wala" (video B): YouTube id T_etu-tH-3w, scheduled today 18:00 IST (12:30Z), 46.0 s, -14.0 LUFS. Title "Last Bench Wala 🥹 Emotional Story" (33 chars).
- Ep02 "Aunty Ka Sawal" (video A): YouTube id AQ7IxqJPdBw, scheduled tomorrow 27 Nov 08:00 IST (02:30Z), 45.1 s, -14.1 LUFS.
- Thumbnails (question style) uploaded OK on both. Title research (49 Shorts, niche motivation/story): top-20 visible title median 58 chars/12 words, 3 hashtags, 2 emoji; we kept titles at 33 chars (Sagar's short-title rule).
- Quota estimate today: this channel 2 x 1,650 = 3,300 + title research 200; first channel 3,300 => about 6,800 / 10,000. Uploads today: 2 here + 2 first channel = 4 (limit 6).
- Check tomorrow morning: did Ep03 become public at 18:00 and Ep02 at 08:00 by themselves? Also check the synthetic label in Studio (API does not echo it).

## 2026-11-27
- Yesterday check: Ep03 (T_etu-tH-3w) and Ep02 (AQ7IxqJPdBw) both became public by themselves at their slots. Views so far 1 and 0 (new channel).
- Run 1 done (08:30 IST). Trends: shaadi season vlogs, ghar ko alvida, Panchayat S5, GTA 6, Avengers, comedy shorts.
- Video B (today 18:00): Ep04 "Maa Ki Parchi" (ghar chhodna, trend). Video A (tomorrow 08:00): Ep05 "Tulna Ka Rule" (comparison). Pictures being generated; waiting for recordings until 12:10 IST.
- Run 2 done (12:10 IST). No recordings arrived, so both videos used the clone (option A), marked synthetic.
- Ep04 "Maa Ki Parchi" (video B): YouTube id sVh7yCpM-Ts, scheduled today 18:00 IST (12:30Z), 43.2 s, -14.0 LUFS.
- Ep05 "Tulna Ka Rule" (video A): YouTube id zLrrCH9ZgrA, scheduled tomorrow 28 Nov 08:00 IST (02:30Z), 45.4 s, -14.1 LUFS.
- Question thumbnails uploaded OK on both. Title research (50 Shorts): top-20 median 55 chars/10 words, 2 hashtags, 2 emoji; our titles stay at ~33 chars.
- Quota estimate today: 2 x 1,650 = 3,300 + research 200 here; first channel 3,300 => about 6,800 / 10,000. Uploads today: 4 (limit 6).
- Check tomorrow: did Ep04 become public at 18:00 and Ep05 at 08:00? Look at views/likes/comments of all Uth Ja Sagar videos.
