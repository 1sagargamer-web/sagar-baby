"""
Windows PC check: Smart App Control jo native files rokta hai unhe sambhalo,
phir har zaroori package ko alag-alag import karke batao kya chal raha hai.

- torchaudio ka native hissa (lib/*.pyd) hamare kaam ka nahi hai (sirf audio file
  IO / sox ke liye hai). Use hata dete hain, taaki torchaudio pure-Python mode mein
  chale (Resample, Spectrogram, kaldi.fbank sab chalte hain).

Exit code 0 = sab theek, 1 = kuch block hai (list print hoti hai).
"""

import importlib
import importlib.util
import os
import sys
import traceback


def disable_torchaudio_native() -> None:
    spec = importlib.util.find_spec("torchaudio")
    if not spec or not spec.submodule_search_locations:
        return
    lib = os.path.join(list(spec.submodule_search_locations)[0], "lib")
    if not os.path.isdir(lib):
        return
    for name in os.listdir(lib):
        if name.lower().endswith((".pyd", ".dll", ".so")):
            src = os.path.join(lib, name)
            try:
                os.replace(src, src + ".off")
                print(f"[check] torchaudio native file hata di: {name}")
            except OSError as e:
                print(f"[check] {name} hata nahi paya: {e}")


MODULES = [
    "numpy",
    "scipy",
    "torch",
    "torchaudio",
    "torchaudio.compliance.kaldi",
    "soundfile",
    "librosa",
    "lameenc",
    "pydantic_core",
    "safetensors",
    "tokenizers",
    "transformers",
    "diffusers",
    "s3tokenizer",
    "perth",
    "fastapi",
    "uvicorn",
    "httpx",
    "firebase_admin",
    "imageio_ffmpeg",
    "chatterbox.mtl_tts",
]


def main() -> int:
    disable_torchaudio_native()
    blocked, failed = [], []
    for m in MODULES:
        try:
            importlib.import_module(m)
            print(f"  OK       {m}")
        except Exception as e:  # noqa: BLE001
            msg = f"{type(e).__name__}: {e}"
            if "4551" in msg or "Application Control" in msg or "blocked" in msg.lower():
                blocked.append((m, msg))
                print(f"  BLOCKED  {m}  ->  {msg[:160]}")
            else:
                failed.append((m, msg))
                print(f"  ERROR    {m}  ->  {msg[:160]}")
                if os.getenv("CHECK_VERBOSE"):
                    traceback.print_exc()

    # torchaudio ke jo hisse hum use karte hain, wo sach mein chal rahe hain?
    if not blocked and not failed:
        try:
            import torch
            import torchaudio
            from torchaudio.compliance import kaldi

            x = torch.zeros(1, 16000)
            torchaudio.transforms.Resample(16000, 24000)(x)
            torchaudio.transforms.Spectrogram()(x)
            kaldi.fbank(x, num_mel_bins=80)
            print("  OK       torchaudio transforms")
        except Exception as e:  # noqa: BLE001
            failed.append(("torchaudio transforms", str(e)))
            print(f"  ERROR    torchaudio transforms -> {e}")

    if blocked:
        print("SMART_APP_CONTROL_BLOCKED " + ", ".join(m for m, _ in blocked))
    if blocked or failed:
        return 1
    import torch

    print("ALL_OK GPU=" + str(torch.cuda.is_available()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
