// Content lives in config.json in the GitHub repo, so the link stays short.
// The owner saves changes from admin.html, which commits config.json with
// their GitHub token. Password and token stay only on the owner's phone.
import { DEFAULT_CONFIG, DEFAULT_QUESTION } from "./defaults.js";

export { DEFAULT_CONFIG, DEFAULT_QUESTION };

const TOKEN_KEY = "loveAppGhToken";
const PASS_KEY = "loveAppPass";
const ACTIONS = ["happy", "next", "sad"];

// Used when the site isn't on github.io (e.g. testing on localhost).
const FALLBACK_OWNER = "1sagargamer-web";
const FALLBACK_REPO = "my-app";
// Branch GitHub Pages deploys from (used if it can't be detected).
const FALLBACK_BRANCH = "ccr-c22cac67-hmboj9";

const clone = (v) => JSON.parse(JSON.stringify(v));
const str = (v, fallback) => (typeof v === "string" ? v : fallback);

function normOptions(list, fallback) {
  if (!Array.isArray(list) || !list.length) return clone(fallback);
  return list.map((o) => ({
    label: str(o?.label, "Option"),
    action: o?.action === "retry" ? "next" : ACTIONS.includes(o?.action) ? o.action : "happy",
  }));
}

function normQuestion(q) {
  const d = DEFAULT_QUESTION;
  return {
    text: str(q?.text, d.text),
    options: normOptions(q?.options, d.options),
    happyMessage: str(q?.happyMessage, d.happyMessage),
  };
}

// Fills any missing fields with defaults so old/partial data never breaks the app.
export function normalize(raw) {
  const d = clone(DEFAULT_CONFIG);
  if (!raw || typeof raw !== "object") return d;
  const c = { ...d };
  for (const k of ["herName", "happyTitle", "finalMessage", "replayButton", "sadMessage", "sadButton"]) {
    c[k] = str(raw[k], d[k]);
  }
  c.intro = {
    title: str(raw.intro?.title, d.intro.title),
    text: str(raw.intro?.text, d.intro.text),
    button: str(raw.intro?.button, d.intro.button),
  };
  c.song = { url: str(raw.song?.url, "").trim() };
  c.sadSong = { url: str(raw.sadSong?.url, "").trim() };
  c.voice = typeof raw.voice === "boolean" ? raw.voice : d.voice;
  c.questions =
    Array.isArray(raw.questions) && raw.questions.length ? raw.questions.map(normQuestion) : d.questions;
  return c;
}

// ---------- link encoding ----------

function toB64url(bytes) {
  let s = "";
  for (let i = 0; i < bytes.length; i += 0x8000) s += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function fromB64url(s) {
  const bin = atob(s.replace(/-/g, "+").replace(/_/g, "/"));
  return Uint8Array.from(bin, (c) => c.charCodeAt(0));
}

const pipe = async (bytes, stream) => new Uint8Array(await new Response(new Blob([bytes]).stream().pipeThrough(stream)).arrayBuffer());

export async function encodeConfig(cfg) {
  const bytes = new TextEncoder().encode(JSON.stringify(normalize(cfg)));
  if ("CompressionStream" in window) return "z" + toB64url(await pipe(bytes, new CompressionStream("deflate-raw")));
  return "j" + toB64url(bytes);
}

export async function decodeConfig(s) {
  let bytes = fromB64url(s.slice(1));
  if (s[0] === "z") bytes = await pipe(bytes, new DecompressionStream("deflate-raw"));
  return normalize(JSON.parse(new TextDecoder().decode(bytes)));
}

// Link that shows unsaved changes (settings packed after #d=). Used for preview.
export async function makePreviewLink(cfg) {
  const url = new URL("./", location.href);
  url.hash = "d=" + (await encodeConfig(cfg));
  return url.toString();
}

export const shortLink = () => new URL("./", location.href).toString();

// Reads the live content from config.json in the repo.
export async function loadLive() {
  const r = await fetch(new URL(`config.json?v=${Date.now()}`, location.href), { cache: "no-store" });
  if (!r.ok) throw new Error(`config.json ${r.status}`);
  return normalize(await r.json());
}

// For the girlfriend's app: preview link data if present, else config.json.
export async function loadConfig() {
  const m = /[#&]d=([^&]+)/.exec(location.hash);
  if (m) {
    try {
      return await decodeConfig(m[1]);
    } catch (e) {
      console.warn("Bad preview data", e);
    }
  }
  try {
    return await loadLive();
  } catch (e) {
    console.warn("Could not load config.json, using defaults", e);
    return normalize(null);
  }
}

// ---------- saving to GitHub ----------

function repoInfo() {
  const host = location.hostname;
  if (host.endsWith(".github.io")) {
    return { owner: host.split(".")[0], repo: location.pathname.split("/").filter(Boolean)[0] };
  }
  return { owner: FALLBACK_OWNER, repo: FALLBACK_REPO };
}

export const getToken = () => read(TOKEN_KEY) || "";
export const setToken = (t) => write(TOKEN_KEY, t ? t.trim() : null);

async function gh(path, opts = {}) {
  const r = await fetch(`https://api.github.com${path}`, {
    ...opts,
    headers: {
      Accept: "application/vnd.github+json",
      Authorization: `Bearer ${getToken()}`,
      "X-GitHub-Api-Version": "2022-11-28",
      ...(opts.body ? { "Content-Type": "application/json" } : {}),
    },
  });
  if (!r.ok) throw Object.assign(new Error(`GitHub ${r.status}`), { status: r.status });
  return r.json();
}

export async function saveLive(cfg) {
  const { owner, repo } = repoInfo();
  const base = `/repos/${owner}/${repo}`;
  let branch = FALLBACK_BRANCH;
  try {
    branch = (await gh(`${base}/pages`)).source?.branch || branch;
  } catch {}
  let sha;
  try {
    sha = (await gh(`${base}/contents/config.json?ref=${encodeURIComponent(branch)}`)).sha;
  } catch (e) {
    if (e.status !== 404) throw e;
  }
  const json = JSON.stringify(normalize(cfg), null, 2) + "\n";
  const content = btoa(String.fromCharCode(...new TextEncoder().encode(json)));
  await gh(`${base}/contents/config.json`, {
    method: "PUT",
    body: JSON.stringify({ message: "Update love app questions", content, sha, branch }),
  });
}

// ---------- owner password (only on the owner's phone) ----------

const read = (k) => { try { return localStorage.getItem(k); } catch { return null; } };
const write = (k, v) => { try { v == null ? localStorage.removeItem(k) : localStorage.setItem(k, v); } catch {} };


async function hash(text) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("love-app:" + text));
  return toB64url(new Uint8Array(buf));
}
export const hasPassword = () => Boolean(read(PASS_KEY));
export const setPassword = async (p) => write(PASS_KEY, await hash(p));
export const checkPassword = async (p) => (await hash(p)) === read(PASS_KEY);
export function resetAll() {
  write(PASS_KEY, null);
  write(TOKEN_KEY, null);
}
