"""Clickbait thumbnail for an "Uth Ja Sagar" story Short, from one of the project's pictures.

Usage: python3 scripts/make_thumb_story.py <picture.png> <out.jpg> "LINE 1" "LINE 2" ["LINE 3"] [--tall]

Default = WIDE 1280x720 (16:9) with everything in the CENTRE: YouTube shows 16:9 in search, suggestions and the channel
page AND makes its own 9:16 "shortsAspectRatio" version (405x720) by cropping the CENTRE of the image, so text on the
left/right would be lost. Layout: blurred background, sharp square picture in the middle, big outlined text stacked in the
centre 400 px (line 1 yellow, middle lines white, last line white on a red bar), red "?" badge. Keep each line short
(<= 9 characters, 3-4 lines). --left = text on the left (loses text in the Shorts crop), --tall = old 1080x1920 version. Roman letters only. ALWAYS look at the result before uploading.
(The first channel uses make_thumb.py; this file does not touch it.)
"""
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
YELLOW, WHITE, RED = (255, 207, 58), (255, 255, 255), (214, 31, 38)


def font_fit(draw, text, max_w, size):
    while size > 36:
        f = ImageFont.truetype(FONT, size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(FONT, 36)


def wide(src, out, lines):
    W, H = 1280, 720
    pic = Image.open(src).convert("RGB")
    bg = pic.resize((W, W), Image.LANCZOS).crop((0, (W - H) // 2, W, (W - H) // 2 + H)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.45)
    side = pic.resize((H, H), Image.LANCZOS)  # sharp square picture on the right
    bg.paste(side, (W - H, 0))
    fade = Image.new("L", (W, H), 0)  # dark fade from the left so the text pops
    fd = ImageDraw.Draw(fade)
    for x in range(0, 760):
        fd.line([(x, 0), (x, H)], fill=int(215 * (1 - x / 760) ** 1.2))
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, fade)
    d = ImageDraw.Draw(im)
    n = len(lines)
    size = 150 if n == 2 else 120
    fonts = [font_fit(d, t, 700, size) for t in lines]
    gap = 14
    total = sum(f.size for f in fonts) + gap * (n - 1)
    y = (H - total) // 2
    for k, (t, f) in enumerate(zip(lines, fonts)):
        t = t.upper()
        w = d.textlength(t, font=f)
        if k == n - 1 and n >= 2:  # last line: white on a red bar
            d.rounded_rectangle((30, y - 6, 50 + w + 30, y + f.size + 14), 18, fill=RED)
            d.text((50, y), t, font=f, fill=WHITE, stroke_width=4, stroke_fill=(0, 0, 0))
        else:
            d.text((40, y), t, font=f, fill=YELLOW if k == 0 else WHITE, stroke_width=9, stroke_fill=(0, 0, 0))
        y += f.size + gap
    bf = ImageFont.truetype(FONT, 90)  # red question badge, top right
    d.ellipse((W - 150, 24, W - 24, 150), fill=RED, outline=WHITE, width=6)
    d.text((W - 87, 88), "?", font=bf, fill=WHITE, anchor="mm", stroke_width=2, stroke_fill=(0, 0, 0))
    im.save(out, quality=92)


def center(src, out, lines):
    W, H = 1280, 720
    pic = Image.open(src).convert("RGB")
    bg = pic.resize((W, W), Image.LANCZOS).crop((0, (W - H) // 2, W, (W - H) // 2 + H)).filter(ImageFilter.GaussianBlur(18))
    bg = Image.blend(bg, Image.new("RGB", (W, H), (0, 0, 0)), 0.4)
    bg.paste(pic.resize((H, H), Image.LANCZOS), ((W - H) // 2, 0))
    shade = Image.new("L", (W, H), 0)  # dark band behind the text, centre only
    ImageDraw.Draw(shade).rectangle((W // 2 - 215, 0, W // 2 + 215, H), fill=120)
    im = Image.composite(Image.new("RGB", (W, H), (0, 0, 0)), bg, shade.filter(ImageFilter.GaussianBlur(40)))
    d = ImageDraw.Draw(im)
    n, gap, maxw = len(lines), 10, 390
    fonts = [font_fit(d, t.upper(), maxw, 140) for t in lines]
    while sum(f.size for f in fonts) + gap * (n - 1) > H - 40:
        fonts = [ImageFont.truetype(FONT, f.size - 6) for f in fonts]
    y = (H - (sum(f.size for f in fonts) + gap * (n - 1))) // 2
    for k, (t, f) in enumerate(zip(lines, fonts)):
        t = t.upper(); w = d.textlength(t, font=f); x = (W - w) / 2
        if k == n - 1 and n >= 2:
            d.rounded_rectangle((x - 16, y - 4, x + w + 16, y + f.size + 12), 14, fill=RED)
            d.text((x, y), t, font=f, fill=WHITE, stroke_width=3, stroke_fill=(0, 0, 0))
        else:
            d.text((x, y), t, font=f, fill=YELLOW if k == 0 else WHITE, stroke_width=8, stroke_fill=(0, 0, 0))
        y += f.size + gap
    d.ellipse((W // 2 + 110, 14, W // 2 + 196, 100), fill=RED, outline=WHITE, width=5)
    d.text((W // 2 + 153, 59), "?", font=ImageFont.truetype(FONT, 62), fill=WHITE, anchor="mm")
    im.save(out, quality=92)


def tall(src, out, lines):
    W, H = 1080, 1920
    im = Image.open(src).convert("RGB")
    s = H / im.height
    im = im.resize((round(im.width * s), H), Image.LANCZOS)
    left = (im.width - W) // 2
    im = im.crop((left, 0, left + W, H))
    d = ImageDraw.Draw(im)
    y = 1330
    for k, t in enumerate(lines[:2]):
        f = font_fit(d, t.upper(), W - 140, 170)
        w = d.textlength(t.upper(), font=f)
        d.text(((W - w) / 2, y), t.upper(), font=f, fill=YELLOW if k == 0 else WHITE, stroke_width=12, stroke_fill=(0, 0, 0))
        y += f.size + 30
    im.save(out, quality=92)


def main() -> None:
    a = [x for x in sys.argv[1:] if x not in ("--tall", "--left")]
    if len(a) < 4:
        sys.exit(__doc__)
    src, out, lines = a[0], a[1], a[2:5]
    (tall if "--tall" in sys.argv else wide if "--left" in sys.argv else center)(src, out, lines)
    print("saved", out)


if __name__ == "__main__":
    main()
