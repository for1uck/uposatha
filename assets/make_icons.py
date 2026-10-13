#!/usr/bin/env python3
"""Generate crisp PNG favicons via 4x supersampling + LANCZOS downscale."""
from PIL import Image, ImageDraw

BG = (184, 71, 45)      # #b8472d
WHITE = (255, 255, 255)
MOON_LIT = (251, 227, 220)  # #fbe3dc
MOON_DARK = (184, 71, 45)

SUPERSAMPLE = 4  # render at 4x then downscale for smooth edges


def draw_at(size: int) -> Image.Image:
    """Draw the icon at `size` (no antialiasing)."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    s = size / 64.0

    radius = int(14 * s)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=radius, fill=BG + (255,))

    lw = max(2, int(2.4 * s))
    pad_x = int(14 * s)
    span = int(36 * s)
    for x in (24, 40):
        xp = int(x * s)
        d.line([xp, pad_x, xp, pad_x + span], fill=WHITE + (255,), width=lw)
    for y in (22, 32, 42):
        yp = int(y * s)
        d.line([pad_x, yp, pad_x + span, yp], fill=WHITE + (255,), width=lw)

    cx, cy, r = int(24 * s), int(32 * s), int(5.5 * s)
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=MOON_LIT + (255,))
    d.pieslice(
        [cx - r, cy - r, cx + r, cy + r],
        start=-90, end=90, fill=MOON_DARK + (255,)
    )
    return img


def render(size: int) -> Image.Image:
    """Draw at SUPERSAMPLE*size, then LANCZOS-downscale to `size`."""
    big = draw_at(size * SUPERSAMPLE)
    return big.resize((size, size), Image.LANCZOS)


def main():
    sizes = {
        "apple-touch-icon.png": 180,
        "apple-touch-icon-256.png": 256,
        "favicon-192.png": 192,
        "favicon-512.png": 512,
        "favicon-32.png": 32,
        "favicon-16.png": 16,
    }
    for name, sz in sizes.items():
        img = render(sz)
        img.save(name, "PNG", optimize=True)
        print(f"wrote {name} ({sz}x{sz})")


if __name__ == "__main__":
    main()
