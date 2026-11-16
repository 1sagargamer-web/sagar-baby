import { loadConfig } from "./store.js";
import { createBoy } from "./boy.js";
import { Music } from "./music.js";

const stage = document.getElementById("stage");
const fx = document.getElementById("fx");
const muteBtn = document.getElementById("muteBtn");
const music = new Music();
const reduceMotion = matchMedia("(prefers-reduced-motion: reduce)").matches;
let cfg;
let qi = 0;
let noCount = 0; // how many times she said No in this round
let busy = false;
let timers = [];

const fill = (t) => (t || "").replaceAll("{name}", cfg.herName || "");
const pick = (list) => list[Math.floor(Math.random() * list.length)];

function el(tag, cls, text) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (text != null) e.textContent = fill(text);
  return e;
}

function button(text, cls, onClick) {
  const b = el("button", `btn ${cls}`, text);
  b.type = "button";
  b.addEventListener("click", onClick);
  return b;
}

function every(ms, fn) {
  fn();
  timers.push(setInterval(fn, ms));
}

function show(...children) {
  timers.forEach(clearInterval);
  timers = [];
  const screen = el("section", "screen");
  const card = el("div", "card");
  card.append(...children);
  screen.append(card);
  stage.replaceChildren(screen);
  requestAnimationFrame(() => requestAnimationFrame(() => screen.classList.add("in")));
  window.scrollTo({ top: 0 });
}

function boy(state, bubble) {
  const wrap = el("div", `boy-wrap ${state}`);
  if (bubble) wrap.append(el("div", "bubble", bubble));
  wrap.append(createBoy(state));
  return wrap;
}

function setGloom(on) {
  document.body.classList.toggle("gloom", on);
}

// ---------- screens ----------

function intro() {
  music.stop();
  setGloom(false);
  qi = 0;
  noCount = 0;
  show(
    el("div", "badge", "💌"),
    el("h1", "title", cfg.intro.title),
    el("p", "sub", cfg.intro.text),
    button(cfg.intro.button, "primary pulse", () => {
      music.unlock();
      question(0);
    }),
  );
}

const PLEAD_FACES = ["🥺", "🥹", "🙏", "🥺👉👈", "😢", "💔", "😿", "🙏🙏"];

function question(i) {
  qi = i;
  const q = cfg.questions[i];
  const state = noCount === 0 ? "idle" : noCount % 4 === 3 ? "cry" : "plead";
  const face = noCount === 0 ? "🥺" : state === "cry" ? "😭" : PLEAD_FACES[noCount % PLEAD_FACES.length];

  const box = el("div", "options");
  for (const o of q.options) {
    const yes = o.action === "happy";
    const b = button(o.label, yes ? "primary pulse" : "ghost", () => act(o.action, b));
    // Every "No" makes Yes a little bigger and No a little smaller.
    if (yes) b.style.fontSize = `${Math.min(17 + noCount * 0.6, 24)}px`;
    else b.style.fontSize = `${Math.max(17 - noCount * 0.3, 13)}px`;
    box.append(b);
  }
  show(boy(state, face), el("h2", "question", q.text), box);
}

function act(action, btn) {
  if (busy) return;
  if (action === "happy") return happy();
  // No: shake, broken heart, sad music, then the next question.
  busy = true;
  noCount++;
  music.sting();
  music.playSad(cfg.sadSong.url);
  setGloom(true);
  btn?.closest(".card")?.classList.add("shake");
  brokenHeart();
  setTimeout(() => {
    busy = false;
    if (action === "next" && qi < cfg.questions.length - 1) question(qi + 1);
    else sad();
  }, reduceMotion ? 150 : 650);
}

function happy() {
  const q = cfg.questions[qi];
  setGloom(false);
  music.playHappy(cfg.song.url);
  burst();
  heartRain();
  const b = boy("happy", q.happyMessage);
  show(
    el("h1", "title glow", cfg.happyTitle),
    b,
    el("p", "sub final", cfg.finalMessage),
    button(cfg.replayButton, "ghost", intro),
  );
  every(reduceMotion ? 1500 : 380, () => aura(b, ["💖", "💕", "💗", "🎵", "🎶", "✨", "😘"]));
  speak(q.happyMessage);
}

function sad() {
  music.playSad(cfg.sadSong.url);
  setGloom(true);
  show(
    boy("cry", cfg.sadMessage),
    button(cfg.sadButton, "primary pulse", () => {
      noCount = 0;
      setGloom(false);
      music.stop();
      question(0);
    }),
  );
}

// ---------- effects ----------

function speak(text) {
  if (!cfg.voice || !("speechSynthesis" in window)) return;
  const clean = fill(text).replace(/[\p{Extended_Pictographic}\u{FE0F}\u{200D}]/gu, "").trim();
  if (!clean) return;
  speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(clean);
  const voices = speechSynthesis.getVoices();
  u.voice = voices.find((v) => v.lang === "en-IN") || voices.find((v) => v.lang.startsWith("en")) || null;
  u.rate = 0.95;
  u.pitch = 1.15;
  u.onstart = () => music.duck(true);
  u.onend = () => music.duck(false);
  setTimeout(() => speechSynthesis.speak(u), 500);
}

const HEARTS = ["💖", "💕", "💗", "💘", "❤️", "🌹", "✨", "💞"];

function spawn(layer, cls, text, style = {}, vars = {}) {
  const s = el("span", cls);
  s.textContent = text;
  Object.assign(s.style, style);
  for (const [k, v] of Object.entries(vars)) s.style.setProperty(k, v);
  s.addEventListener("animationend", () => s.remove());
  layer.append(s);
  return s;
}

function burst() {
  const n = reduceMotion ? 10 : 46;
  for (let i = 0; i < n; i++) {
    const ang = Math.random() * Math.PI * 2;
    const dist = 120 + Math.random() * 260;
    spawn(fx, "burst", HEARTS[i % HEARTS.length], { animationDelay: `${Math.random() * 0.25}s` }, {
      "--dx": `${Math.cos(ang) * dist}px`,
      "--dy": `${Math.sin(ang) * dist - 80}px`,
      "--r": `${Math.random() * 120 - 60}deg`,
      "--s": (0.8 + Math.random() * 1.2).toFixed(2),
    });
  }
}

function heartRain() {
  const n = reduceMotion ? 8 : 40;
  for (let i = 0; i < n; i++) {
    spawn(fx, "fall", pick(HEARTS), {
      left: `${Math.random() * 100}%`,
      fontSize: `${16 + Math.random() * 22}px`,
      animationDuration: `${2.5 + Math.random() * 2.5}s`,
      animationDelay: `${0.3 + Math.random() * 2.5}s`,
    }, { "--r": `${Math.random() * 360 - 180}deg` });
  }
}

function brokenHeart() {
  spawn(fx, "broken", "💔");
}

function aura(wrap, chars) {
  spawn(wrap, "aura", pick(chars), { fontSize: `${16 + Math.random() * 14}px` }, {
    "--x": `${Math.random() * 220 - 110}px`,
    "--r": `${Math.random() * 60 - 30}deg`,
  });
}

function floatingBackground() {
  const bg = document.getElementById("bg");
  const one = () => {
    const sad = document.body.classList.contains("gloom");
    spawn(bg, "float", sad ? pick(["💧", "💔", "💧", "🌧️"]) : HEARTS[Math.floor(Math.random() * 5)], {
      left: `${Math.random() * 100}%`,
      fontSize: `${12 + Math.random() * 22}px`,
      animationDuration: `${8 + Math.random() * 8}s`,
      opacity: (0.25 + Math.random() * 0.45).toFixed(2),
    });
  };
  for (let i = 0; i < 6; i++) setTimeout(one, i * 300);
  setInterval(one, reduceMotion ? 3000 : 900);
}

muteBtn.addEventListener("click", () => {
  music.setMuted(!music.muted);
  muteBtn.textContent = music.muted ? "🔇" : "🔊";
});

// ---------- start ----------

floatingBackground();
loadConfig().then((c) => {
  cfg = c;
  document.title = fill(cfg.intro.title).replace(/[\p{Extended_Pictographic}\u{FE0F}]/gu, "").trim() || "For You";
  intro();
});
