"""Natural speech in a cloned voice (Chatterbox Multilingual, open source, MIT).

Run with the TTS venv:
    .venv-tts/bin/python scripts/clone_voice.py <reference.wav> "<text>" <out.wav> \
        [--lang hi] [--exaggeration 0.5] [--cfg 0.5] [--temperature 0.8] [--seed 7]

Several lines in one go (loads the model once):
    .venv-tts/bin/python scripts/clone_voice.py <reference.wav> --batch lines.json
    lines.json = [{"text": "...", "out": "a.wav"}, ...]
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
    a = ap.parse_args()

    torch.set_num_threads(max(1, torch.get_num_threads()))
    model = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
    jobs = json.load(open(a.batch)) if a.batch else [{"text": a.text, "out": a.out}]
    for job in jobs:
        random.seed(a.seed)
        np.random.seed(a.seed)
        torch.manual_seed(a.seed)
        wav = model.generate(
            job["text"],
            language_id=a.lang,
            audio_prompt_path=a.ref,
            exaggeration=job.get("exaggeration", a.exaggeration),
            cfg_weight=job.get("cfg", a.cfg),
            temperature=a.temperature,
        )
        ta.save(job["out"], wav, model.sr)
        print("saved", job["out"], flush=True)


if __name__ == "__main__":
    main()
