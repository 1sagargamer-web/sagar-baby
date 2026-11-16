// Fallback content, used only if config.json can't be loaded.
// The live content is in config.json (owner edits it from admin.html).
// {name} is replaced with the girlfriend's name.
//
// Option actions:
//   happy = happy boy + song (the end)
//   next  = go to the next question (on the last question: sad boy)
//   sad   = sad boy, then back to the first question

export const DEFAULT_QUESTION = {
  text: "Naya sawal? 💭",
  options: [
    { label: "Yes 😍", action: "happy" },
    { label: "No 🙄", action: "next" },
  ],
  happyMessage: "Love you baby ❤️",
};

export const DEFAULT_CONFIG = {
  herName: "Baby",
  intro: {
    title: "Hey {name} 💕",
    text: "Sagar ke paas tumhare liye ek bahut zaroori sawal hai...",
    button: "Pucho na 🙈",
  },
  questions: [
    {
      text: "Do you love me? 💖",
      options: [
        { label: "Yes 😍", action: "happy" },
        { label: "No 🙄", action: "next" },
      ],
      happyMessage: "Love you baby ❤️",
    },
  ],
  happyTitle: "Yayyy! 🥰",
  finalMessage: "Tum meri duniya ho, {name} 💞",
  replayButton: "Phir se shuru karo 🔁",
  sadMessage: "Please ek baar aur soch lo 😢",
  sadButton: "Theek hai, phir se poocho 🥺",
  // Empty url = built-in tune (happy on Yes, sad on No).
  song: { url: "" },
  sadSong: { url: "" },
  // Boy says the happy message out loud (phone's voice).
  voice: true,
};
