"""Thumbnail for an "Uth Ja Sagar" story Short, from one of the project's pictures (no caption to erase).

Usage: python3 scripts/make_thumb_story.py <picture.png> <out.jpg> "LINE ONE" "LINE TWO"
Makes a 1080x1920 JPG: the picture fills the frame, a dark fade at the bottom, big outlined text (Roman letters).
ALWAYS look at the result before uploading. (The first channel uses make_thumb.py; this file does not touch it.)
"""
import sys

from PIL import Image, ImageDraw, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
W, H = 1080, 1920


def fit(draw, text, max_w, size):
    while size > 40:
        f = ImageFont.truetype(FONT, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(FONT, 40)


def main() -> None:
    if len(sys.argv) < 5:
        sys.exit(__doc__)
    src, out, l1, l2 = sys.argv[1:5]
    im = Image.open(src).convert("RGB")
    s = H / im.height
    im = im.resize((round(im.width * s), H), Image.LANCZOS)
    left = (im.width - W) // 2
    im = im.crop((left, 0, left + W, H))
    fade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(fade)
    for y in range(H // 2, H):
        d.line([(0, y), (W, y)], fill=int(190 * ((y - H // 2) / (H // 2)) ** 1.4))
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), im, fade)
    d = ImageDraw.Draw(im)
    y = 1330
    for text, fill in ((l1.upper(), (255, 207, 58)), (l2.upper(), (255, 255, 255))):
        f = fit(d, text, W - 140, 170)
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, y), text, font=f, fill=fill, stroke_width=12, stroke_fill=(0, 0, 0))
        y += f.size + 30
    im.save(out, quality=92)
    print("saved", out)


if __name__ == "__main__":
    main()
