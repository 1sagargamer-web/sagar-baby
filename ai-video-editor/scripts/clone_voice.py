"""Natural speech in a cloned voice (Chatterbox Multilingual, open source, MIT).

Run with the TTS venv:
    .venv-tts/bin/python scripts/clone_voice.py <reference.wav> "<text>" <out.wav> \
        [--lang hi] [--exaggeration 0.5] [--cfg 0.5] [--temperature 0.8] [--seed 7]

Several lines in one go (loads the model once):
    .venv-tts/bin/python scripts/clone_voice.py <reference.wav> --batch lines.json
    lines.json = [{"text": "...", "out": "a.wav"}, ...]

--takes N (default 1 = old behaviour): make N takes per line (seeds seed, seed+1, ...) and keep the one whose voice is
closest to the reference (Chatterbox voice-encoder cosine similarity). Scores are printed.
"""
import argparse
import json
import random

import numpy as np
import torch
import torchaudio as ta
from chatterbox.mtl_tts import ChatterboxMultilingualTTS


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ref")
    ap.add_argument("text", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--batch")
    ap.add_argument("--lang", default="hi")
    ap.add_argument("--exaggeration", type=float, default=0.5)
    ap.add_argument("--cfg", type=float, default=0.5)
    ap.add_argument("--temperature", type=float, default=0.8)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--takes", type=int, default=1)
    a = ap.parse_args()

    torch.set_num_threads(max(1, torch.get_num_threads()))
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    jobs = json.load(open(a.batch)) if a.batch else [{"text": a.text, "out": a.out}]
    ref_emb = None
    if a.takes > 1:
        import librosa
        ref16, _ = librosa.load(a.ref, sr=16000)
        ref_emb = model.ve.embeds_from_wavs([ref16], sample_rate=16000)[0]
    for job in jobs:
        best, best_score = None, -9.0
        for k in range(a.takes):
            seed = job.get("seed", a.seed) + k
            random.seed(seed)
            np.random.seed(seed)
            torch.manual_seed(seed)
            wav = model.generate(
                job["text"],
                language_id=a.lang,
                audio_prompt_path=a.ref,
                exaggeration=job.get("exaggeration", a.exaggeration),
                cfg_weight=job.get("cfg", a.cfg),
                temperature=job.get("temperature", a.temperature),
            )
            if a.takes == 1:
                best = wav
                break
            import librosa
            w16 = librosa.resample(wav.squeeze(0).numpy(), orig_sr=model.sr, target_sr=16000)
            emb = model.ve.embeds_from_wavs([w16], sample_rate=16000)[0]
            score = float(np.dot(emb, ref_emb) / (np.linalg.norm(emb) * np.linalg.norm(ref_emb)))
            print(f"  take {k + 1} seed {seed}: voice match {score:.3f}", flush=True)
            if score > best_score:
                best, best_score = wav, score
        ta.save(job["out"], best, model.sr)
        print("saved", job["out"] + (f" (voice match {best_score:.3f})" if a.takes > 1 else ""), flush=True)


if __name__ == "__main__":
    main()
