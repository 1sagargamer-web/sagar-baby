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
