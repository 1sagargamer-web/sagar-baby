# For You 💖

Ek cute "Do you love me?" web app.

- **Yes** → happy boy naachta hai, "Love you baby ❤️" bolta hai, song bajta hai, hearts udte hain.
- **No** → 💔 + sad music, boy please karta hai / rota hai (rain cloud ke neeche), aur naya sawal aata hai jab tak wo Yes na bole.
- **Owner panel** (`admin.html`): password se khulta hai. Sawal, options, messages, song badlo → Save. Link hamesha chhota aur same rehta hai.

Setup ke steps: [SETUP.md](SETUP.md)

## Files

| File | Kaam |
|---|---|
| `index.html`, `js/app.js` | GF wala app |
| `admin.html`, `js/admin.js` | Owner panel |
| `config.json` | Saare sawal aur text (admin se badalte hain) |
| `js/defaults.js` | Backup default text |
| `js/store.js` | config.json padhna/save karna, owner password |
| `js/boy.js` | Boy character (SVG) |
| `js/music.js` | Built-in happy tune + mp3 player |
| `music/` | Apne mp3 songs yahan |

Local mein chalane ke liye: `python3 -m http.server` aur `http://localhost:8000` kholo.
