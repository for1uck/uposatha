#!/usr/bin/env python3
"""Generate PNG favicons (calendar + moon phase) at multiple sizes."""
from PIL import Image, ImageDraw

BG = (184, 71, 45)      # #b8472d
WHITE = (255, 255, 255)
MOON_LIT = (251, 227, 220)  # #fbe3dc
MOON_DARK = (184, 71, 45)    # same as bg, for crescent


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 64.0  # scale factor (design is 64x64)

    # rounded square background
    radius = int(14 * s)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG + (255,))

    lw = max(2, int(2.4 * s))
    # calendar grid lines
    # vertical: x = 24, 40 (in 64-grid); horizontal: y = 22, 32, 42
    pad_x = int(14 * s)
    span = int(36 * s)
    for x in (24, 40):
        xp = int(x * s)
        d.line([xp, pad_x, xp, pad_x + span], fill=WHITE + (255,), width=lw)
    for y in (22, 32, 42):
        yp = int(y * s)
        d.line([pad_x, yp, pad_x + span, yp], fill=WHITE + (255,), width=lw)

    # moon at (24, 32) radius 5.5 — crescent (lit on left, dark on right)
    cx, cy, r = int(24 * s), int(32 * s), int(5.5 * s)
    # full light disc
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOON_LIT + (255,))
    # dark half on the right (covers right semicircle) to make a left crescent
    d.pieslice(
        [cx - r, cy - r, cx + r, cy + r],
        start=-90, end=90, fill=MOON_DARK + (255,)
    )
    return img


def main():
    sizes = {
        "apple-touch-icon.png": 180,
        "favicon-192.png": 192,
        "favicon-512.png": 512,
        "favicon-32.png": 32,
    }
    for name, sz in sizes.items():
        img = draw_icon(sz)
        img.save(name, "PNG")
        print(f"wrote {name} ({sz}x{sz})")
    # also a 16x16 for legacy
    draw_icon(16).save("favicon-16.png", "PNG")
    print("wrote favicon-16.png (16x16)")


if __name__ == "__main__":
    main()
