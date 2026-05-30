#!/usr/bin/env python3
"""Build the Tova Learn Chinese OG social card (1200x630).

Real-asset rule: uses the actual shipped app icon — never a hand-drawn stand-in.
Brand gradient matches the homepage hero: #46C0EE -> #22A8E0 -> #1090CC.
"""
from PIL import Image, ImageDraw, ImageFont

W, H = 1200, 630
ICON = "tova-learn-icon.png"          # real shipped Tova Learn Chinese icon
OUT = "og-learn.png"

# Brand teal vertical gradient
top, mid, bot = (0x46, 0xC0, 0xEE), (0x22, 0xA8, 0xE0), (0x10, 0x90, 0xCC)
def lerp(a, b, t): return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))
bg = Image.new("RGB", (W, H))
px = bg.load()
for y in range(H):
    t = y / (H - 1)
    c = lerp(top, mid, t * 2) if t < 0.5 else lerp(mid, bot, (t - 0.5) * 2)
    for x in range(W):
        px[x, y] = c
draw = ImageDraw.Draw(bg, "RGBA")

# Soft white halo top-center (mirrors the site's radial highlight)
halo = Image.new("RGBA", (W, H), (0, 0, 0, 0))
hd = ImageDraw.Draw(halo)
hd.ellipse([W//2 - 520, -360, W//2 + 520, 360], fill=(255, 255, 255, 36))
bg = Image.alpha_composite(bg.convert("RGBA"), halo).convert("RGB")
draw = ImageDraw.Draw(bg, "RGBA")

# Rounded app icon, left side
icon = Image.open(ICON).convert("RGBA").resize((300, 300), Image.LANCZOS)
mask = Image.new("L", (300, 300), 0)
ImageDraw.Draw(mask).rounded_rectangle([0, 0, 300, 300], radius=66, fill=255)
# drop shadow
shadow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
sd = ImageDraw.Draw(shadow)
sd.rounded_rectangle([108, 178, 108 + 300, 178 + 300], radius=66, fill=(8, 32, 56, 90))
shadow = shadow.filter(__import__("PIL.ImageFilter", fromlist=["GaussianBlur"]).GaussianBlur(22))
bg = Image.alpha_composite(bg.convert("RGBA"), shadow).convert("RGB")
bg.paste(icon, (100, 165), mask)
draw = ImageDraw.Draw(bg, "RGBA")

def font(sz, bold=True):
    paths = [
        "/System/Library/Fonts/SFNSRounded.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, sz)
        except Exception:
            continue
    return ImageFont.load_default()

tx = 452
draw.text((tx, 168), "Tova Learn Chinese", font=font(72), fill=(255, 255, 255))
draw.text((tx, 270), "Wake. Trace. Speak.", font=font(58), fill=(255, 255, 255, 235))
draw.text((tx, 360), "One Chinese character a day —", font=font(34, False), fill=(255, 255, 255, 210))
draw.text((tx, 404), "stroke order + on-device pronunciation scoring.", font=font(34, False), fill=(255, 255, 255, 210))

# Small "from the makers of Tova Translate" pill
pill = "From the makers of Tova Translate"
f = font(28, False)
pw = draw.textlength(pill, font=f)
draw.rounded_rectangle([tx, 470, tx + pw + 44, 524], radius=27, fill=(255, 255, 255, 38))
draw.text((tx + 22, 481), pill, font=f, fill=(255, 255, 255))

bg.save(OUT)
print("wrote", OUT, bg.size)
