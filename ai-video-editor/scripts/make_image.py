"""Make an illustration with a free open-source image model (SDXL-Turbo), on the CPU, no internet needed once
the model is in models/sdxl-turbo.

Run with the image venv (.venv-img: new diffusers, shares torch from .venv-tts; see CLAUDE.md):
    .venv-img/bin/python scripts/make_image.py "<prompt>" out.png [--size 768] [--steps 4] [--seed 1] [--style "<text>"]

Several images in one go (loads the model once):
    .venv-img/bin/python scripts/make_image.py --batch scenes.json
    scenes.json = [{"prompt": "...", "out": "a.png", "seed": 3}, ...]

Download the model once (6.5 GB):
    HF_HUB_DISABLE_XET=1 python3 -c "from huggingface_hub import snapshot_download; snapshot_download('stabilityai/sdxl-turbo',
      local_dir='models/sdxl-turbo', allow_patterns=['model_index.json','*/config.json','scheduler/*','tokenizer*/*',
      '*.fp16.safetensors'], ignore_patterns=['*.onnx*','*openvino*','sd_xl_turbo*'])"
"""
import argparse
import json
import time
from pathlib import Path

import torch
from diffusers import AutoPipelineForText2Image

HERE = Path(__file__).resolve().parent.parent
MODEL = HERE / "models" / "sdxl-turbo"
STYLE = ("storybook digital illustration, Indian cartoon style, clean dark outlines, soft warm cinematic light, "
         "detailed background, cosy colours, high quality")


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
    pipe = AutoPipelineForText2Image.from_pretrained(str(MODEL), torch_dtype=torch.bfloat16, variant="fp16")
    pipe.to("cpu")
    jobs = json.load(open(a.batch)) if a.batch else [{"prompt": a.prompt, "out": a.out}]
    for job in jobs:
        t = time.time()
        g = torch.Generator("cpu").manual_seed(job.get("seed", a.seed))
        img = pipe(prompt=f"{job['prompt']}, {a.style}", num_inference_steps=job.get("steps", a.steps),
                   guidance_scale=0.0, width=a.size, height=a.size, generator=g).images[0]
        img.save(job["out"])
        print(f"saved {job['out']} in {time.time() - t:.0f}s", flush=True)


if __name__ == "__main__":
    main()
