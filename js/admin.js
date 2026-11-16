import {
  normalize, loadLive, saveLive, makePreviewLink, shortLink,
  getToken, setToken, hasPassword, setPassword, checkPassword, resetAll, DEFAULT_QUESTION,
} from "./store.js";
import { Music } from "./music.js";

const root = document.getElementById("root");
const lockBtn = document.getElementById("lock");
const toastEl = document.getElementById("toast");
const music = new Music();
let cfg;

const ACTIONS = [
  ["happy", "💖 Yes → Happy boy + song"],
  ["next", "➡️ No → Agla sawal (aakhri pe sad boy)"],
  ["sad", "😢 No → Sad boy"],
];

const clone = (v) => JSON.parse(JSON.stringify(v));

function h(tag, props = {}, ...children) {
  const e = document.createElement(tag);
  for (const [k, v] of Object.entries(props)) {
    if (k.startsWith("on")) e.addEventListener(k.slice(2), v);
    else if (k === "class") e.className = v;
    else if (k.includes("-")) e.setAttribute(k, v);
    else if (v === true) e.setAttribute(k, "");
    else if (v !== false && v != null) e[k] = v;
  }
  for (const c of children.flat()) if (c != null) e.append(c);
  return e;
}

function toast(msg, err = false) {
  toastEl.textContent = msg;
  toastEl.className = `toast show${err ? " err" : ""}`;
  clearTimeout(toast.t);
  toast.t = setTimeout(() => (toastEl.className = "toast"), 4000);
}

// Text input bound to obj[key].
function field(label, obj, key, { multi = false, placeholder = "" } = {}) {
  const input = h(multi ? "textarea" : "input", {
    value: obj[key] ?? "",
    placeholder,
    oninput: (e) => (obj[key] = e.target.value),
  });
  return h("label", { class: "field" }, h("span", {}, label), input);
}

function actionSelect(opt) {
  const sel = h("select", { onchange: (e) => (opt.action = e.target.value), "aria-label": "Click karne pe kya ho" });
  for (const [v, t] of ACTIONS) sel.append(h("option", { value: v, selected: opt.action === v }, t));
  return sel;
}

function optionsEditor(list) {
  const box = h("div");
  list.forEach((opt, i) => {
    box.append(
      h("div", { class: "opt-row" },
        h("input", { value: opt.label, placeholder: "Button ka text", oninput: (e) => (opt.label = e.target.value), "aria-label": "Button ka text" }),
        h("div", { class: "row2" },
          actionSelect(opt),
          h("button", {
            class: "icon-btn danger", type: "button", title: "Option hatao", disabled: list.length <= 1,
            onclick: () => { list.splice(i, 1); render(); },
          }, "🗑"),
        ),
      ),
    );
  });
  box.append(h("button", { class: "add", type: "button", onclick: () => { list.push({ label: "Naya option", action: "happy" }); render(); } }, "+ Option add karo"));
  return box;
}

function questionCard(q, i) {
  const qs = cfg.questions;
  const move = (d) => { [qs[i], qs[i + d]] = [qs[i + d], qs[i]]; render(); };
  return h("div", { class: "q-card" },
    h("div", { class: "q-head" },
      h("strong", {}, `Sawal ${i + 1}`),
      h("div", { class: "q-tools" },
        h("button", { class: "icon-btn", type: "button", title: "Upar", disabled: i === 0, onclick: () => move(-1) }, "↑"),
        h("button", { class: "icon-btn", type: "button", title: "Neeche", disabled: i === qs.length - 1, onclick: () => move(1) }, "↓"),
        h("button", {
          class: "icon-btn danger", type: "button", title: "Sawal hatao", disabled: qs.length <= 1,
          onclick: () => { if (confirm(`Sawal ${i + 1} delete karein?`)) { qs.splice(i, 1); render(); } },
        }, "🗑"),
      ),
    ),
    field("Sawal", q, "text", { multi: true }),
    h("h3", {}, "Buttons"),
    optionsEditor(q.options),
    field("Yes pe boy kya bolega 💖", q, "happyMessage"),
  );
}

let testing = null;
function testButton(kind, label) {
  const btn = h("button", {
    class: "chip", type: "button",
    onclick: () => {
      if (testing === kind) { music.stop(); testing = null; btn.textContent = label; return; }
      root.querySelectorAll(".song-test").forEach((b) => (b.textContent = b.dataset.label));
      music.play(kind, (kind === "sad" ? cfg.sadSong : cfg.song).url.trim());
      testing = kind;
      btn.textContent = "⏹ Stop";
    },
  }, label);
  btn.classList.add("song-test");
  btn.dataset.label = label;
  return btn;
}

function songPanel() {
  return h("div", { class: "panel" },
    h("h2", {}, "🎵 Songs"),
    h("p", { class: "hint" }, "Khaali chhodo to built-in tune bajegi. Apna song: mp3 ka direct link daalo, ya mp3 file GitHub repo ke 'music' folder mein upload karke yahan likho, jaise: music/happy.mp3"),
    field("💖 Yes pe happy song (mp3)", cfg.song, "url", { placeholder: "music/happy.mp3  ya  https://…" }),
    field("💔 No pe sad song (mp3)", cfg.sadSong, "url", { placeholder: "music/sad.mp3  ya  https://…" }),
    h("div", { class: "row" },
      testButton("happy", "▶ Happy test"),
      testButton("sad", "▶ Sad test"),
      h("button", { class: "chip", type: "button", onclick: () => { cfg.song.url = ""; cfg.sadSong.url = ""; render(); toast("Built-in tunes set — Save dabana mat bhoolna"); } }, "Built-in tunes"),
    ),
    h("h3", {}, "Awaaz"),
    h("label", { class: "toggle" },
      h("input", { type: "checkbox", checked: cfg.voice, onchange: (e) => (cfg.voice = e.target.checked) }),
      "Boy apna message bol ke sunaye (phone ki awaaz)",
    ),
  );
}

function linkPanel() {
  const url = shortLink();
  const wa = `https://wa.me/?text=${encodeURIComponent("Tumhare liye kuch special hai 💖 " + url)}`;
  return h("div", { class: "panel link-panel" },
    h("h2", {}, "💌 GF ka link"),
    h("p", { class: "hint" }, "Ye link hamesha same rahega. Aap kuch bhi badlo, isi link pe update ho jayega."),
    h("label", { class: "field" }, h("input", { value: url, readOnly: true, onclick: (e) => e.target.select(), "aria-label": "Link" })),
    h("div", { class: "row" },
      h("button", {
        class: "chip", type: "button",
        onclick: async () => {
          try { await navigator.clipboard.writeText(url); toast("Link copy ho gaya ✅"); } catch { toast(url); }
        },
      }, "📋 Copy"),
      h("a", { class: "chip", href: wa, target: "_blank", rel: "noopener" }, "💬 WhatsApp"),
    ),
  );
}

function tokenPanel() {
  const has = Boolean(getToken());
  const state = { t: "" };
  const newTokenUrl = "https://github.com/settings/personal-access-tokens/new?name=love-app&contents=write";
  return h("details", { class: "panel token", open: !has },
    h("summary", {}, has ? "🔑 GitHub token: set hai ✅" : "🔑 GitHub token (Save ke liye ek baar chahiye)"),
    h("p", { class: "hint" }, "Save karne ke liye app ko aapke GitHub mein likhne ki permission chahiye. Ye token sirf aapke phone pe rehta hai."),
    h("ol", { class: "steps" },
      h("li", {}, h("a", { href: newTokenUrl, target: "_blank", rel: "noopener" }, "Ye link kholo ↗")),
      h("li", {}, "Repository access → Only select repositories → apni repo chuno"),
      h("li", {}, "Permissions → Contents → Read and write"),
      h("li", {}, "Neeche Generate token dabao, token copy karo"),
      h("li", {}, "Yahan paste karke Set dabao"),
    ),
    h("label", { class: "field" }, h("span", {}, "Token"),
      h("input", { type: "password", placeholder: "github_pat_…", autocomplete: "off", oninput: (e) => (state.t = e.target.value) })),
    h("div", { class: "row" },
      h("button", { class: "chip", type: "button", onclick: () => { if (!state.t.trim()) return; setToken(state.t); render(); toast("Token set ho gaya ✅"); } }, "Set"),
      has ? h("button", { class: "chip", type: "button", onclick: () => { setToken(""); render(); } }, "Hatao") : null,
    ),
  );
}

function render() {
  root.replaceChildren(
    linkPanel(),
    h("div", { class: "panel" },
      h("h2", {}, "💕 Basic"),
      field("Girlfriend ka naam", cfg, "herName"),
      h("p", { class: "hint" }, "Kisi bhi text mein {name} likhoge to wahan uska naam aa jayega."),
      h("h3", {}, "Pehli screen"),
      field("Title", cfg.intro, "title"),
      field("Message", cfg.intro, "text", { multi: true }),
      field("Button", cfg.intro, "button"),
    ),
    h("div", { class: "panel" },
      h("h2", {}, "❓ Sawal", h("span", { class: "hint", style: "margin:0" }, `${cfg.questions.length} total`)),
      h("p", { class: "hint" }, "Har 'No' pe agla sawal aata hai, jab tak wo Yes na bole. Aakhri sawal pe bhi No kiya to sad boy aayega aur phir pehle sawal se shuru hoga."),
      ...cfg.questions.map(questionCard),
      h("button", { class: "add", type: "button", onclick: () => { cfg.questions.push(clone(DEFAULT_QUESTION)); render(); } }, "+ Naya sawal add karo"),
    ),
    h("div", { class: "panel" },
      h("h2", {}, "🎉 Yes ke baad"),
      field("Title", cfg, "happyTitle"),
      field("Aakhri message", cfg, "finalMessage"),
      field("Phir se shuru button", cfg, "replayButton"),
      h("h2", { style: "margin-top:18px" }, "😢 Sad screen"),
      field("Boy kya bolega", cfg, "sadMessage"),
      field("Button (wapas pehle sawal pe)", cfg, "sadButton"),
    ),
    songPanel(),
    tokenPanel(),
    h("div", { class: "panel" },
      h("h2", {}, "⚙️ Reset"),
      h("button", { class: "chip", type: "button", onclick: () => { if (confirm("Sab kuch default pe reset karein?")) { cfg = normalize(null); render(); toast("Reset ho gaya — Save dabao to pakka ho jayega"); } } }, "Sab default pe reset karo"),
    ),
    h("div", { class: "savebar" },
      h("div", { class: "savebar-row" },
        h("button", { class: "btn ghost", type: "button", onclick: preview }, "👀 Preview"),
        saveBtn(),
      ),
    ),
  );
}

async function preview() {
  window.open(await makePreviewLink(cfg), "_blank", "noopener");
}

function saveBtn() {
  const b = h("button", { class: "btn primary", type: "button" }, "💾 Save karo");
  b.addEventListener("click", async () => {
    if (!getToken()) {
      const t = root.querySelector(".token");
      t.open = true;
      t.scrollIntoView({ behavior: "smooth", block: "center" });
      return toast("Pehle GitHub token set karo (steps yahan hain)", true);
    }
    b.disabled = true;
    b.textContent = "Saving…";
    try {
      await saveLive(cfg);
      toast("Save ho gaya ✅ 1-2 minute mein GF ke link pe update ho jayega");
    } catch (e) {
      console.error(e);
      const msg = e.status === 401 ? "Token galat ya expire ho gaya ❌ naya token daalo"
        : e.status === 403 || e.status === 404 ? "Token ko permission nahi hai ❌ Contents: Read and write do"
        : "Save nahi hua ❌ Internet check karo";
      toast(msg, true);
    } finally {
      b.disabled = false;
      b.textContent = "💾 Save karo";
    }
  });
  return b;
}

function passwordForm() {
  const isNew = !hasPassword();
  const state = { p1: "", p2: "" };
  const form = h("form", {
    class: "panel login",
    onsubmit: async (e) => {
      e.preventDefault();
      if (isNew) {
        if (state.p1.length < 4) return toast("Password kam se kam 4 letter ka rakho", true);
        if (state.p1 !== state.p2) return toast("Dono password same nahi hain ❌", true);
        await setPassword(state.p1);
        toast("Password set ho gaya 🔐");
        return openEditor();
      }
      if (await checkPassword(state.p1)) return openEditor();
      toast("Galat password ❌", true);
    },
  },
    h("h2", {}, isNew ? "Apna password banao 🔐" : "Sirf owner ke liye 🔒"),
    h("p", { class: "hint" }, isNew
      ? "Ye password sirf aapke phone pe save hoga. Agli baar admin khologe to yahi maangega."
      : "Apna password daalo."),
    h("label", { class: "field" }, h("span", {}, "Password"),
      h("input", { type: "password", autocomplete: isNew ? "new-password" : "current-password", required: true, oninput: (e) => (state.p1 = e.target.value) })),
    isNew ? h("label", { class: "field" }, h("span", {}, "Password dobara"),
      h("input", { type: "password", autocomplete: "new-password", required: true, oninput: (e) => (state.p2 = e.target.value) })) : null,
    h("button", { class: "btn primary", type: "submit" }, isNew ? "Password set karo" : "Kholo 🔓"),
    isNew ? null : h("button", {
      class: "chip forgot", type: "button",
      onclick: () => {
        if (confirm("Password bhool gaye? Reset karne se password aur token hat jayenge. Sawal safe rahenge.")) {
          resetAll();
          passwordForm();
        }
      },
    }, "Password bhool gaye?"),
  );
  root.replaceChildren(form);
}

async function openEditor() {
  lockBtn.hidden = false;
  root.replaceChildren(h("p", {}, "Loading…"));
  try {
    cfg = await loadLive();
  } catch (e) {
    console.error(e);
    cfg = normalize(null);
    toast("Saved sawal load nahi hue, default dikha raha hoon", true);
  }
  render();
}

lockBtn.addEventListener("click", () => {
  lockBtn.hidden = true;
  passwordForm();
});

passwordForm();
