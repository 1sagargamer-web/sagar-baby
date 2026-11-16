// Happy song on Yes, sad song on No. Each can be the owner's mp3 link or,
// if empty, a built-in tune made with the Web Audio API.

// [note, length in eighths]. "R" = rest. 8 bars of 8 eighths each.
const HAPPY = {
  eighth: 0.25, // 120 bpm
  volume: 0.55,
  lead: "bell",
  drums: true,
  bassSteps: [0, 3, 4, 7],
  melody: [
    ["E5", 1], ["G5", 1], ["C6", 2], ["B5", 1], ["A5", 1], ["G5", 2],
    ["D5", 1], ["G5", 1], ["B5", 2], ["A5", 1], ["G5", 1], ["D5", 2],
    ["C5", 1], ["E5", 1], ["A5", 2], ["G5", 1], ["E5", 1], ["C5", 2],
    ["F5", 1], ["A5", 1], ["C6", 1], ["A5", 1], ["G5", 2], ["R", 2],
    ["E5", 1], ["E5", 1], ["G5", 1], ["C6", 1], ["D6", 2], ["C6", 2],
    ["B5", 1], ["A5", 1], ["G5", 1], ["B5", 1], ["D6", 2], ["B5", 2],
    ["C6", 1], ["B5", 1], ["A5", 1], ["E5", 1], ["A5", 2], ["G5", 2],
    ["F5", 1], ["G5", 1], ["A5", 1], ["B5", 1], ["C6", 4],
  ],
  chords: [
    ["C4", "E4", "G4"], ["B3", "D4", "G4"], ["C4", "E4", "A4"], ["C4", "F4", "A4"],
    ["C4", "E4", "G4"], ["B3", "D4", "G4"], ["C4", "E4", "A4"], ["C4", "F4", "A4"],
  ],
  bass: ["C3", "G2", "A2", "F2", "C3", "G2", "A2", "F2"],
};

const SAD = {
  eighth: 0.42, // slow, ~70 bpm
  volume: 0.5,
  lead: "violin",
  drums: false,
  bassSteps: [0, 4],
  melody: [
    ["E5", 2], ["C5", 2], ["A4", 2], ["B4", 2],
    ["C5", 3], ["D5", 1], ["F5", 2], ["E5", 2],
    ["D5", 2], ["B4", 2], ["G4", 2], ["A4", 2],
    ["E5", 4], ["C5", 4],
    ["A4", 2], ["C5", 2], ["F5", 3], ["E5", 1],
    ["D5", 2], ["C5", 2], ["A4", 2], ["F4", 2],
    ["G#4", 2], ["B4", 2], ["E5", 2], ["D5", 2],
    ["C5", 3], ["B4", 1], ["A4", 4],
  ],
  chords: [
    ["A3", "C4", "E4"], ["A3", "D4", "F4"], ["G3", "B3", "D4"], ["G3", "C4", "E4"],
    ["A3", "C4", "F4"], ["A3", "D4", "F4"], ["G#3", "B3", "E4"], ["A3", "C4", "E4"],
  ],
  bass: ["A2", "D2", "G2", "C2", "F2", "D2", "E2", "A2"],
};

const SEMI = { C: 0, D: 2, E: 4, F: 5, G: 7, A: 9, B: 11 };
function freq(note) {
  const m = /^([A-G])(#?)(\d)$/.exec(note);
  const midi = 12 * (Number(m[3]) + 1) + SEMI[m[1]] + (m[2] ? 1 : 0);
  return 440 * 2 ** ((midi - 69) / 12);
}

export class Music {
  constructor() {
    this.ctx = null;
    this.audio = null;
    this.master = null;
    this.kind = null; // "happy" | "sad" | null
    this.muted = false;
    this.timer = null;
  }

  // Must be called from a tap/click so phones allow sound.
  unlock() {
    if (!this.ctx) {
      const AC = window.AudioContext || window.webkitAudioContext;
      if (AC) this.ctx = new AC();
    }
    if (this.ctx && this.ctx.state === "suspended") this.ctx.resume();
  }

  playHappy(url) { this.play("happy", url); }
  playSad(url) { this.play("sad", url); }

  // Keeps playing if the same kind is already on.
  play(kind, url) {
    if (this.kind === kind) return;
    this.stop();
    this.kind = kind;
    this.unlock();
    const song = kind === "sad" ? SAD : HAPPY;
    if (url) {
      const audio = new Audio(url);
      audio.loop = true;
      audio.muted = this.muted;
      this.audio = audio;
      const fallback = () => {
        if (this.kind === kind && this.audio === audio) {
          this.audio = null;
          this.tune(song);
        }
      };
      audio.addEventListener("error", fallback);
      audio.play().catch(fallback);
      return;
    }
    this.tune(song);
  }

  tune(song) {
    if (!this.ctx) return;
    this.song = song;
    this.master = this.ctx.createGain();
    this.master.gain.value = this.muted ? 0 : song.volume;
    this.master.connect(this.ctx.destination);
    this.noise = this.noise || this.makeNoise();
    this.schedule(song, this.ctx.currentTime + 0.05);
  }

  schedule(song, t0) {
    const out = this.master;
    const E = song.eighth;
    const loop = song.melody.reduce((s, [, l]) => s + l, 0) * E;
    let t = t0;
    for (const [n, len] of song.melody) {
      if (n !== "R") (song.lead === "violin" ? this.violin : this.bell).call(this, out, freq(n), t, len * E);
      t += len * E;
    }
    for (let bar = 0; bar < 8; bar++) {
      const bt = t0 + bar * 8 * E;
      for (const n of song.chords[bar]) this.pad(out, freq(n), bt, 8 * E, song.drums ? 0.035 : 0.05);
      for (const step of song.bassSteps) {
        this.bass(out, freq(song.bass[bar]) * (step === 7 ? 2 : 1), bt + step * E, song.drums ? E * 0.9 : E * 3.5);
      }
      if (song.drums) {
        for (const beat of [0, 2, 4, 6]) this.kick(out, bt + beat * E);
        for (const beat of [2, 6]) this.clap(out, bt + beat * E);
      }
    }
    const wait = (t0 + loop - this.ctx.currentTime - 0.6) * 1000;
    this.timer = setTimeout(() => this.master === out && this.schedule(song, t0 + loop), wait);
  }

  env(out, start, attack, peak, end) {
    const g = this.ctx.createGain();
    g.gain.setValueAtTime(0.0001, start);
    g.gain.exponentialRampToValueAtTime(peak, start + attack);
    g.gain.exponentialRampToValueAtTime(0.0001, end);
    g.connect(out);
    return g;
  }

  osc(type, f, dest, start, stop) {
    const o = this.ctx.createOscillator();
    o.type = type;
    o.frequency.setValueAtTime(f, start);
    o.connect(dest);
    o.start(start);
    o.stop(stop + 0.05);
    return o;
  }

  bell(out, f, t, len) {
    const end = t + Math.max(len, 0.3) + 0.25;
    this.osc("triangle", f, this.env(out, t, 0.01, 0.28, end), t, end);
    this.osc("sine", f * 2, this.env(out, t, 0.005, 0.06, t + 0.4), t, t + 0.4);
  }

  // Soft, slow, slightly wobbly lead for the sad tune.
  violin(out, f, t, len) {
    const end = t + len + 0.35;
    const lp = this.ctx.createBiquadFilter();
    lp.type = "lowpass";
    lp.frequency.value = 1400;
    lp.connect(this.env(out, t, Math.min(0.18, len / 2), 0.16, end));
    const o = this.osc("sawtooth", f, lp, t, end);
    const s = this.osc("sine", f, lp, t, end);
    const lfo = this.ctx.createOscillator();
    const depth = this.ctx.createGain();
    lfo.frequency.value = 5;
    depth.gain.value = f * 0.007;
    lfo.connect(depth);
    depth.connect(o.frequency);
    depth.connect(s.frequency);
    lfo.start(t);
    lfo.stop(end + 0.05);
  }

  pad(out, f, t, len, vol) {
    this.osc("sine", f, this.env(out, t, 0.2, vol, t + len), t, t + len);
  }

  bass(out, f, t, len) {
    this.osc("triangle", f, this.env(out, t, 0.01, 0.22, t + len), t, t + len);
  }

  kick(out, t) {
    const o = this.osc("sine", 140, this.env(out, t, 0.005, 0.5, t + 0.18), t, t + 0.2);
    o.frequency.exponentialRampToValueAtTime(45, t + 0.15);
  }

  clap(out, t) {
    const src = this.ctx.createBufferSource();
    src.buffer = this.noise;
    const bp = this.ctx.createBiquadFilter();
    bp.type = "bandpass";
    bp.frequency.value = 1500;
    src.connect(bp).connect(this.env(out, t, 0.003, 0.18, t + 0.15));
    src.start(t);
    src.stop(t + 0.2);
  }

  makeNoise() {
    const b = this.ctx.createBuffer(1, this.ctx.sampleRate * 0.3, this.ctx.sampleRate);
    const d = b.getChannelData(0);
    for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1;
    return b;
  }

  // Short "wah wah" sound when she taps No.
  sting() {
    if (!this.ctx || this.muted) return;
    const t = this.ctx.currentTime + 0.02;
    ["D4", "C#4", "C4", "B3"].forEach((n, i) => {
      const st = t + i * 0.22;
      const len = i === 3 ? 0.6 : 0.2;
      const lp = this.ctx.createBiquadFilter();
      lp.type = "lowpass";
      lp.frequency.value = 900;
      lp.connect(this.env(this.ctx.destination, st, 0.02, 0.12, st + len));
      const o = this.osc("sawtooth", freq(n), lp, st, st + len);
      if (i === 3) o.frequency.linearRampToValueAtTime(freq(n) * 0.94, st + len);
    });
  }

  // Lower the volume a bit while the boy is speaking.
  duck(on) {
    if (this.audio) this.audio.volume = on ? 0.35 : 1;
    if (this.master && !this.muted) {
      const t = this.ctx.currentTime;
      this.master.gain.cancelScheduledValues(t);
      this.master.gain.setTargetAtTime(on ? 0.2 : this.song.volume, t, 0.1);
    }
  }

  setMuted(m) {
    this.muted = m;
    if (this.audio) this.audio.muted = m;
    if (this.master) this.master.gain.value = m ? 0 : this.song.volume;
  }

  stop() {
    this.kind = null;
    clearTimeout(this.timer);
    if (this.audio) {
      this.audio.pause();
      this.audio = null;
    }
    if (this.master) {
      const m = this.master;
      this.master = null;
      const t = this.ctx.currentTime;
      m.gain.cancelScheduledValues(t);
      m.gain.setTargetAtTime(0, t, 0.08);
      setTimeout(() => m.disconnect(), 600);
    }
  }
}
