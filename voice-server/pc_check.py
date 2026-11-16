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


REGEX_SHIM = '''"""Sagar Vaani shim: Windows Smart App Control ne asli 'regex' package ki DLL block ki.
transformers isse sirf simple patterns ke liye import karta hai, jo Python ka 're' bhi karta hai."""
import re as _re
from re import *  # noqa: F401,F403
from re import Match, Pattern, compile, error, escape, purge  # noqa: F401

__version__ = "0+sagarvaani-shim"
DEFAULT_VERSION = VERSION0 = V0 = VERSION1 = V1 = 0
'''


def _is_blocked(e: BaseException) -> bool:
    msg = str(e)
    return "4551" in msg or "Application Control" in msg or "blocked" in msg.lower()


def shim_regex_if_blocked() -> None:
    """'regex' ki DLL block ho to uski jagah pure-Python shim lagao."""
    if os.getenv("SIMULATE_BLOCK_REGEX") != "1":
        try:
            import regex  # noqa: F401

            if getattr(regex, "__version__", "").endswith("shim"):
                return
            return  # asli regex chal raha hai
        except Exception as e:  # noqa: BLE001
            if not _is_blocked(e):
                return
    spec = importlib.util.find_spec("regex")
    if not spec or not spec.submodule_search_locations:
        return
    pkg = list(spec.submodule_search_locations)[0]
    backup = pkg + "_blocked"
    try:
        if not os.path.exists(backup):
            os.replace(pkg, backup)
        os.makedirs(pkg, exist_ok=True)
        with open(os.path.join(pkg, "__init__.py"), "w", encoding="utf-8") as f:
            f.write(REGEX_SHIM)
        for m in [m for m in sys.modules if m == "regex" or m.startswith("regex.")]:
            del sys.modules[m]
        importlib.invalidate_caches()
        print("[check] 'regex' block thi - uski jagah Python wala shim laga diya")
    except OSError as e:
        print(f"[check] regex shim nahi laga: {e}")


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
    shim_regex_if_blocked()
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

    # GPU ki files (cuBLAS/cuDNN) pehli baar chalne par load hoti hain - abhi test kar lo
    if not blocked and not failed:
        try:
            import torch

            if torch.cuda.is_available():
                x = torch.randn(1, 8, 64, device="cuda")
                w = torch.randn(8, 8, 3, device="cuda")
                torch.nn.functional.conv1d(x, w)
                (x[0] @ x[0].T).sum().item()
                print("  OK       GPU (" + torch.cuda.get_device_name(0) + ")")
        except Exception as e:  # noqa: BLE001
            print(f"  GPU_BLOCKED  GPU nahi chal raha, CPU use hoga -> {str(e)[:160]}")

    if blocked:
        print("SMART_APP_CONTROL_BLOCKED " + ", ".join(m for m, _ in blocked))
    if blocked or failed:
        return 1
    import torch

    print("ALL_OK GPU=" + str(torch.cuda.is_available()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
