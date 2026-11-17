"""Voice conversion (Chatterbox VC): keep how a line was spoken, change who it sounds like.

Run with the TTS venv:
    .venv-tts/bin/python scripts/convert_voice.py <target_voice.wav> <in1.wav> <out1.wav> [<in2.wav> <out2.wav> ...]

Used to turn Sagar's recordings of Bhagwan's lines into Bhagwan's fixed voice (voices/bhagwan-ref.wav).
"""
import sys

import torchaudio as ta
from chatterbox.vc import ChatterboxVC


def main() -> None:
    target, pairs = sys.argv[1], sys.argv[2:]
    if not pairs or len(pairs) % 2:
        sys.exit(__doc__)
    vc = ChatterboxVC.from_pretrained(device="cpu")
    vc.set_target_voice(target)
    for src, out in zip(pairs[::2], pairs[1::2]):
        ta.save(out, vc.generate(src), vc.sr)
        print("saved", out, flush=True)


if __name__ == "__main__":
    main()
