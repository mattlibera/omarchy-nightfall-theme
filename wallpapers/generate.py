"""
Nightfall wallpaper generator — 5120x1440
Requires: python-numpy python-pillow python-scipy
  sudo pacman -S python-numpy python-pillow python-scipy
"""

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy.ndimage import gaussian_filter
import random
import os

W, H = 5120, 1440
OUT = os.path.dirname(os.path.abspath(__file__))

def hex_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

BG       = hex_rgb("#1c1e26")
BG_ALT   = hex_rgb("#232530")
PURPLE   = hex_rgb("#b877db")
TEAL     = hex_rgb("#64d1a9")
PEACH    = hex_rgb("#fab795")
ORANGE   = hex_rgb("#ff9668")
RED      = hex_rgb("#e95678")
CYAN     = hex_rgb("#34d3fb")
BLUE     = hex_rgb("#70b0ff")
LAVENDER = hex_rgb("#f3c1ff")
GOLD     = hex_rgb("#dbbe7f")
MUTED    = hex_rgb("#5c6e80")
YELLOW   = hex_rgb("#ffd88c")

ACCENTS = [PURPLE, TEAL, CYAN, BLUE, PEACH, RED, LAVENDER, ORANGE, GOLD]


# ── Utility ────────────────────────────────────────────────────────────────────

def blank(color=BG):
    img = Image.new("RGB", (W, H), color)
    return np.array(img, dtype=np.float32)

def save(arr, name):
    arr = np.clip(arr, 0, 255).astype(np.uint8)
    path = os.path.join(OUT, name)
    Image.fromarray(arr).save(path)
    print(f"  saved {path}")

def smooth_noise(h, w, scale, seed=0):
    rng = np.random.default_rng(seed)
    raw = rng.random((h // scale + 2, w // scale + 2)).astype(np.float32)
    img = Image.fromarray((raw * 255).astype(np.uint8), mode="L")
    img = img.resize((w, h), Image.BICUBIC)
    return np.array(img, dtype=np.float32) / 255.0

def blend(base, color, mask, strength=1.0):
    c = np.array(color, dtype=np.float32)
    m = np.clip(mask * strength, 0, 1)[:, :, np.newaxis]
    return base * (1 - m) + c * m


# ── Wallpaper 1: Nebula ────────────────────────────────────────────────────────
# Soft gaussian noise blobs in accent colors over the dark background.

def make_nebula(seed=42):
    print("generating: nightfall-nebula.png")
    rng = np.random.default_rng(seed)
    canvas = blank(BG).astype(np.float32)

    colors = [PURPLE, CYAN, TEAL, BLUE, RED, PEACH, LAVENDER]
    configs = [
        # (scale, sigma, strength, x_bias, y_bias)
        (8,  320, 0.55, 0.15, 0.5),
        (6,  280, 0.45, 0.75, 0.4),
        (10, 400, 0.35, 0.45, 0.6),
        (7,  250, 0.40, 0.30, 0.3),
        (9,  350, 0.30, 0.85, 0.65),
        (5,  200, 0.25, 0.60, 0.5),
        (12, 500, 0.20, 0.10, 0.7),
    ]

    for i, (color, (scale, sigma, strength, xb, yb)) in enumerate(zip(colors, configs)):
        noise = smooth_noise(H, W, scale, seed=seed + i)
        # bias towards a region to spread blobs across the panoramic canvas
        xs = np.linspace(0, 1, W)
        ys = np.linspace(0, 1, H)
        xx, yy = np.meshgrid(xs, ys)
        dist = np.exp(-((xx - xb)**2 * 3 + (yy - yb)**2 * 6))
        mask = gaussian_filter(noise * dist, sigma=sigma)
        mask = (mask - mask.min()) / (mask.max() - mask.min() + 1e-8)
        mask = np.power(mask, 1.8)
        canvas = blend(canvas, color, mask, strength)

    # subtle vignette
    xs = np.linspace(-1, 1, W)
    ys = np.linspace(-1, 1, H)
    xx, yy = np.meshgrid(xs, ys)
    vignette = 1 - np.clip(xx**2 * 0.3 + yy**2 * 0.8, 0, 1) * 0.6
    canvas *= vignette[:, :, np.newaxis]

    save(canvas, "nightfall-nebula.png")


# ── Wallpaper 2: Flow Field ────────────────────────────────────────────────────
# Particles trace paths through a smooth noise-driven angle field.

def make_flow(seed=7):
    print("generating: nightfall-flow.png")
    rng = np.random.default_rng(seed)

    canvas = np.zeros((H, W, 3), dtype=np.float32)
    bg = np.array(BG, dtype=np.float32)
    canvas[:] = bg

    # build angle field from two noise layers
    nx = smooth_noise(H, W, 6, seed=seed)
    ny = smooth_noise(H, W, 6, seed=seed + 1)
    angle_field = (nx - 0.5) * 2 * np.pi * 2 + (ny - 0.5) * np.pi

    line_colors = [PURPLE, CYAN, TEAL, BLUE, PEACH, LAVENDER, MUTED, RED, GOLD]
    n_particles = 12000
    step = 2.5
    steps = 280

    # alpha accumulation layer
    acc = np.zeros((H, W, 3), dtype=np.float32)
    wt  = np.zeros((H, W),    dtype=np.float32)

    for _ in range(n_particles):
        x = rng.uniform(0, W)
        y = rng.uniform(0, H)
        color = np.array(rng.choice(line_colors), dtype=np.float32)
        alpha = rng.uniform(0.03, 0.12)

        for _ in range(steps):
            ix = int(np.clip(x, 0, W - 1))
            iy = int(np.clip(y, 0, H - 1))
            a = angle_field[iy, ix]
            acc[iy, ix] += color * alpha
            wt[iy, ix]  += alpha
            x += np.cos(a) * step
            y += np.sin(a) * step
            if x < 0 or x >= W or y < 0 or y >= H:
                break

    # composite: where weight > 0, blend over background
    mask = np.clip(wt / (wt.max() + 1e-8), 0, 1)
    safe_wt = np.where(wt > 0, wt, 1)[:, :, np.newaxis]
    colors_norm = acc / safe_wt
    m = np.clip(mask * 2.5, 0, 1)[:, :, np.newaxis]
    canvas = bg * (1 - m) + colors_norm * m

    # blur very slightly to anti-alias
    pil = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8))
    pil = pil.filter(ImageFilter.GaussianBlur(radius=0.8))
    canvas = np.array(pil, dtype=np.float32)

    # vignette
    xs = np.linspace(-1, 1, W)
    ys = np.linspace(-1, 1, H)
    xx, yy = np.meshgrid(xs, ys)
    vignette = 1 - np.clip(xx**2 * 0.2 + yy**2 * 0.7, 0, 1) * 0.5
    canvas *= vignette[:, :, np.newaxis]

    save(canvas, "nightfall-flow.png")


# ── Wallpaper 3: Geometry ──────────────────────────────────────────────────────
# Low-poly triangulated mesh, each face filled with a palette color + noise gradient.

def make_geometry(seed=13):
    print("generating: nightfall-geometry.png")
    rng = np.random.default_rng(seed)

    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # generate a grid of points with jitter
    cols = 48
    rows = 14
    margin_x = W // cols
    margin_y = H // rows

    pts = []
    for row in range(rows + 1):
        for col in range(cols + 1):
            bx = col * (W / cols)
            by = row * (H / rows)
            jx = rng.uniform(-margin_x * 0.55, margin_x * 0.55)
            jy = rng.uniform(-margin_y * 0.55, margin_y * 0.55)
            pts.append((bx + jx, by + jy))

    def pt(row, col):
        return pts[row * (cols + 1) + col]

    geo_colors = [BG, BG_ALT, MUTED, PURPLE, CYAN, TEAL, BLUE, RED, PEACH,
                  LAVENDER, GOLD, ORANGE]
    # weight heavily towards dark colors so it stays subtle
    weights = [18, 14, 8, 3, 3, 3, 3, 2, 2, 2, 2, 2]
    weights = [w / sum(weights) for w in weights]

    for row in range(rows):
        for col in range(cols):
            tl = pt(row,     col)
            tr = pt(row,     col + 1)
            bl = pt(row + 1, col)
            br = pt(row + 1, col + 1)

            for tri in [(tl, tr, bl), (tr, br, bl)]:
                color = rng.choice(geo_colors, p=weights)
                # slight brightness variation per face
                var = rng.uniform(0.88, 1.08)
                c = tuple(int(min(255, ch * var)) for ch in color)
                coords = [(int(p[0]), int(p[1])) for p in tri]
                draw.polygon(coords, fill=c)

    # draw faint edges
    edge_color = (*BG_ALT, 60)
    img_rgba = img.convert("RGBA")
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    edge_draw = ImageDraw.Draw(overlay)
    for row in range(rows):
        for col in range(cols):
            tl = pt(row,     col)
            tr = pt(row,     col + 1)
            bl = pt(row + 1, col)
            br = pt(row + 1, col + 1)
            for tri in [(tl, tr, bl), (tr, br, bl)]:
                coords = [(int(p[0]), int(p[1])) for p in tri]
                edge_draw.polygon(coords, outline=(*BG_ALT, 40))

    img = Image.alpha_composite(img_rgba, overlay).convert("RGB")

    path = os.path.join(OUT, "nightfall-geometry.png")
    img.save(path)
    print(f"  saved {path}")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_nebula()
    make_flow()
    make_geometry()
    print("done.")
