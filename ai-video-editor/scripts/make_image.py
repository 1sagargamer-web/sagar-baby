"""Make an illustration with a free open-source image model (SDXL-Turbo), on the CPU, no internet needed once
the model is in models/sdxl-turbo.

Run with the image venv (.venv-img: its own new diffusers/transformers, torch shared from .venv-tts via a .pth file,
so Chatterbox in .venv-tts is untouched; rebuild steps in channels/uth-ja-sagar/CLAUDE.md):
    .venv-img/bin/python scripts/make_image.py "<prompt>" out.png [--size 768] [--steps 4] [--seed 1] [--style "<text>"]

Several images in one go (loads the model once):
    .venv-img/bin/python scripts/make_image.py --batch scenes.json
    scenes.json = [{"prompt": "...", "out": "a.png", "seed": 3, "face": "face.png", "face_scale": 0.55}, ...]

"face" (optional): a photo of a face; the person in the picture is made to look like it (IP-Adapter Plus Face,
models/ip-adapter, 3.4 GB). Jobs without "face" are made exactly as before.
    HF_HUB_DISABLE_XET=1 python3 -c "from huggingface_hub import snapshot_download; snapshot_download('h94/IP-Adapter',
      local_dir='models/ip-adapter', allow_patterns=['models/image_encoder/config.json','models/image_encoder/model.safetensors',
      'sdxl_models/ip-adapter-plus-face_sdxl_vit-h.safetensors'])"

Download the model once (6.5 GB):
    HF_HUB_DISABLE_XET=1 python3 -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/sdxl-turbo',
      local_dir='models/sdxl-turbo', allow_patterns=['model_index.json','*/config.json','scheduler/*','tokenizer*/*',
      '*.fp16.safetensors'], ignore_patterns=['*.onnx*','*openvino*','sd_xl_turbo*'])"
"""
import argparse
import gc
import json
import time
from pathlib import Path

import torch
from diffusers import AutoPipelineForText2Image
from PIL import Image

HERE = Path(__file__).resolve().parent.parent
MODEL = HERE / "models" / "sdxl-turbo"
IPA = HERE / "models" / "ip-adapter"
# Style goes FIRST: CLIP reads only 77 tokens, anything after that is cut (a long scene used to cut the style off).
STYLE = "storybook cartoon illustration, Indian cartoon style, clean outlines, warm cinematic light"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", nargs="?")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--batch")
    ap.add_argument("--size", type=int, default=768)
    ap.add_argument("--steps", type=int, default=4)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--style", default=STYLE)
    a = ap.parse_args()

    torch.set_num_threads(max(1, torch.get_num_threads()))
    # Load the fp16 files as-is (memory-mapped), then convert part by part to bfloat16 (fast on CPU).
    # Loading straight as bfloat16 peaks at ~12 GB and, with the face adapter, ran out of memory (16 GB box).
    pipe = AutoPipelineForText2Image.from_pretrained(str(MODEL), dtype=torch.float16, variant="fp16")
    for part in ("unet", "vae", "text_encoder", "text_encoder_2"):
        getattr(pipe, part).to(torch.bfloat16)
        gc.collect()
    jobs = json.load(open(a.batch)) if a.batch else [{"prompt": a.prompt, "out": a.out}]
    faces = any(j.get("face") for j in jobs)
    if faces:
        from transformers import CLIPVisionModelWithProjection
        enc = CLIPVisionModelWithProjection.from_pretrained(str(IPA / "models" / "image_encoder"), dtype=torch.bfloat16)
        pipe.register_modules(image_encoder=enc)
        pipe.load_ip_adapter(str(IPA), subfolder="sdxl_models", weight_name="ip-adapter-plus-face_sdxl_vit-h.safetensors")
        gc.collect()
    blank = Image.new("RGB", (224, 224), (128, 128, 128))
    for job in jobs:
        t = time.time()
        g = torch.Generator("cpu").manual_seed(job.get("seed", a.seed))
        extra = {}
        if faces:  # the adapter is loaded: give every job an image, scale 0 = no effect for jobs without a face
            pipe.set_ip_adapter_scale(job.get("face_scale", 0.55) if job.get("face") else 0.0)
            extra["ip_adapter_image"] = Image.open(job["face"]).convert("RGB") if job.get("face") else blank
        img = pipe(prompt=f"{a.style}, {job['prompt']}", num_inference_steps=job.get("steps", a.steps),
                   guidance_scale=0.0, width=a.size, height=a.size, generator=g, **extra).images[0]
        img.save(job["out"])
        print(f"saved {job['out']} in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
