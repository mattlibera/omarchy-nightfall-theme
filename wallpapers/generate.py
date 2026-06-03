"""
Nightfall wallpaper generator — 5120x1440
Requires: python-numpy python-pillow python-scipy
  sudo pacman -S python-numpy python-pillow python-scipy
"""

import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import random
import os

W, H = 5120, 1440
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(SCRIPT_DIR, "..", "backgrounds")

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
    from scipy.ndimage import gaussian_filter
    print("generating: nightfall-nebula.png")
    rng = np.random.default_rng(seed)
    canvas = np.full((H, W, 3), BG, dtype=np.float32)

    xs = np.linspace(0, 1, W)
    ys = np.linspace(0, 1, H)
    xx, yy = np.meshgrid(xs, ys)

    # Each color: list of (cx, cy, sigma) blob centers + overall alpha strength.
    # Blobs are wide enough to overlap so colors mix at boundaries.
    # sigma is in pixels — large enough to feel cosmic, not like a smudge.
    blob_specs = [
        (PURPLE,   [(0.08, 0.50, 210), (0.20, 0.30, 155), (0.14, 0.72, 130)], 0.75),
        (CYAN,     [(0.72, 0.47, 230), (0.60, 0.68, 160), (0.83, 0.28, 125)], 0.70),
        (BLUE,     [(0.44, 0.38, 195), (0.58, 0.58, 155)],                     0.55),
        (TEAL,     [(0.33, 0.62, 175), (0.48, 0.28, 135)],                     0.60),
        (RED,      [(0.24, 0.52, 155), (0.37, 0.72, 115)],                     0.50),
        (PEACH,    [(0.89, 0.44, 175), (0.76, 0.67, 125)],                     0.45),
        (LAVENDER, [(0.52, 0.60, 165), (0.40, 0.45, 110)],                     0.40),
    ]

    for si, (color, blobs, strength) in enumerate(blob_specs):
        layer = np.zeros((H, W), dtype=np.float32)

        # Two noise octaves used to texture every blob for this color.
        coarse_tex = smooth_noise(H, W, 18, seed=seed + si * 5)
        fine_tex   = smooth_noise(H, W,  5, seed=seed + si * 5 + 1)
        texture    = coarse_tex * 0.65 + fine_tex * 0.35

        for bx, by, sigma in blobs:
            point = np.zeros((H, W), dtype=np.float32)
            point[int(by * H), int(bx * W)] = 1.0
            blob = gaussian_filter(point, sigma=sigma)
            blob /= blob.max() + 1e-8
            # fractal texture shreds the smooth circle into wispy organic edges
            blob = blob * (0.45 + texture * 0.55)
            layer = np.maximum(layer, blob)

        layer = (layer - layer.min()) / (layer.max() - layer.min() + 1e-8)
        layer = np.power(layer, 1.5)

        c = np.array(color, dtype=np.float32)
        m = (layer * strength)[:, :, np.newaxis]
        canvas = canvas * (1 - m) + c * m

    canvas = np.clip(canvas, 0, 255)

    vignette = 1 - np.clip(xx ** 2 * 0.20 + yy ** 2 * 0.65, 0, 1) * 0.45
    canvas *= vignette[:, :, np.newaxis]

    save(canvas, "1-nightfall-nebula.png")


# ── Wallpaper 2: Flow Field ────────────────────────────────────────────────────
# Particles trace paths through a smooth noise-driven angle field.

def make_flow(seed=7):
    print("generating: nightfall-flow.png")
    rng = np.random.default_rng(seed)

    img = Image.new("RGBA", (W, H), (*BG, 255))
    draw = ImageDraw.Draw(img, "RGBA")

    # Very coarse noise (scale=40) so features span hundreds of pixels —
    # particles sweep in long graceful arcs rather than tight spirals.
    nx = smooth_noise(H, W, 40, seed=seed)
    # Dominant direction: roughly left-to-right with gentle vertical drift.
    # Noise perturbs by at most ±60° so lines always feel purposeful.
    base_angle = np.pi * 0.05
    angle_field = base_angle + (nx - 0.5) * np.pi * 1.2

    line_colors = [PURPLE, CYAN, TEAL, BLUE, PEACH, LAVENDER, MUTED, RED, GOLD]
    n_particles = 2200
    step = 2.0
    steps = 900  # long paths so each line sweeps across the canvas

    for _ in range(n_particles):
        # seed particles from the left third so they sweep across the image
        x = rng.uniform(-W * 0.1, W * 0.5)
        y = rng.uniform(0, H)
        color = tuple(rng.choice(line_colors))
        alpha = int(rng.uniform(22, 60))
        rgba = (*color, alpha)

        path = []
        for _ in range(steps):
            ix = int(np.clip(x, 0, W - 1))
            iy = int(np.clip(y, 0, H - 1))
            path.append((float(x), float(y)))
            a = angle_field[iy, ix]
            x += np.cos(a) * step
            y += np.sin(a) * step
            if x < 0 or x >= W or y < 0 or y >= H:
                break

        if len(path) > 1:
            draw.line(path, fill=rgba, width=1)

    canvas = np.array(img.convert("RGB"), dtype=np.float32)

    # vignette
    xs = np.linspace(-1, 1, W)
    ys = np.linspace(-1, 1, H)
    xx, yy = np.meshgrid(xs, ys)
    vignette = 1 - np.clip(xx**2 * 0.2 + yy**2 * 0.7, 0, 1) * 0.5
    canvas *= vignette[:, :, np.newaxis]

    save(canvas, "2-nightfall-flow.png")


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

    path = os.path.join(OUT, "3-nightfall-geometry.png")
    img.save(path)
    print(f"  saved {path}")


# ── Wallpaper 4: Aurora ────────────────────────────────────────────────────────
# Wavy horizontal ribbons of cool light drifting across a dark sky. Bands are
# additively blended so overlaps brighten, the way real aurora does.

def make_aurora(seed=99):
    print("generating: nightfall-aurora.png")
    rng = np.random.default_rng(seed)
    bg_arr = np.array(BG, dtype=np.float32)
    canvas = np.full((H, W, 3), BG, dtype=np.float32)

    # fixed band positions so ribbons don't pile up in the same vertical zone
    band_specs = [
        (TEAL,     0.20),
        (PURPLE,   0.38),
        (CYAN,     0.50),
        (LAVENDER, 0.62),
        (BLUE,     0.78),
    ]
    ys = np.arange(H, dtype=np.float32)[:, np.newaxis]

    for i, (color, y_rel) in enumerate(band_specs):
        # smooth 1D noise gives each band a wobbling centerline along x
        wob = smooth_noise(64, W, scale=80, seed=seed + i * 7)[32]
        base_y = H * y_rel
        amplitude = rng.uniform(35, 70)
        centerline = base_y + (wob - 0.5) * 2 * amplitude

        dist = ys - centerline[np.newaxis, :]

        # halo: wide soft glow gives the ribbon its atmosphere
        halo_sigma = rng.uniform(70, 110)
        halo = np.exp(-(dist ** 2) / (2 * halo_sigma ** 2))
        halo_mod = smooth_noise(H, W, 90, seed=seed + i * 11 + 3)
        halo = halo * (0.85 + halo_mod * 0.20)

        # core: narrow bright ribbon gives the band its definition
        core_sigma = rng.uniform(14, 22)
        core = np.exp(-(dist ** 2) / (2 * core_sigma ** 2))

        # vertical striations — gentle stripes along the ribbon, like aurora rays
        rays_n = smooth_noise(32, W, scale=12, seed=seed + i * 23 + 5)[16]
        rays = 0.75 + (rays_n - 0.5) * 0.50  # ~0.5–1.0 multiplier
        core = core * rays

        band = np.clip(halo * 0.45 + core * 0.90, 0, 1)

        strength = rng.uniform(0.85, 1.0)
        c = np.array(color, dtype=np.float32)
        m = np.clip(band * strength, 0, 1)[:, :, np.newaxis]
        canvas = canvas + (c - bg_arr) * m

    canvas = np.clip(canvas, 0, 255)

    xs_v = np.linspace(-1, 1, W)
    ys_v = np.linspace(-1, 1, H)
    xx, yy = np.meshgrid(xs_v, ys_v)
    vignette = 1 - np.clip(xx ** 2 * 0.15 + yy ** 2 * 0.50, 0, 1) * 0.40
    canvas *= vignette[:, :, np.newaxis]

    save(canvas, "4-nightfall-aurora.png")


# ── Wallpaper 5: Starfield ─────────────────────────────────────────────────────
# Deep-space scene: sparse star field, a few nebula cores, a faint milky way.

def make_starfield(seed=21):
    print("generating: nightfall-starfield.png")
    rng = np.random.default_rng(seed)

    # darker than BG for actual deep-space vibe
    deep = np.array([10, 11, 16], dtype=np.float32)
    canvas = np.zeros((H, W, 3), dtype=np.float32) + deep

    xs = np.arange(W, dtype=np.float32)[np.newaxis, :]
    ys = np.arange(H, dtype=np.float32)[:, np.newaxis]

    # nebula cores via analytical 2D gaussian (no scipy dependency)
    cores = [
        (PURPLE,   0.18, 0.42, 320, 0.60),
        (CYAN,     0.55, 0.55, 280, 0.50),
        (TEAL,     0.78, 0.32, 230, 0.45),
        (RED,      0.42, 0.70, 180, 0.30),
    ]
    for color, cx_r, cy_r, sigma, strength in cores:
        cx, cy = cx_r * W, cy_r * H
        dist_sq = (xs - cx) ** 2 + (ys - cy) ** 2
        blob = np.exp(-dist_sq / (2 * sigma ** 2))
        tex = smooth_noise(H, W, 18, seed=seed + int(cx_r * 1000))
        blob = blob * (0.50 + tex * 0.65)
        c = np.array(color, dtype=np.float32)
        m = (blob * strength)[:, :, np.newaxis]
        canvas = canvas + (c - deep) * m

    # faint milky way streak — a soft diagonal brightening
    xx_n = np.linspace(0, 1, W)
    yy_n = np.linspace(0, 1, H)
    XX, YY = np.meshgrid(xx_n, yy_n)
    diag = YY - 0.5 - (XX - 0.5) * 0.20
    streak = np.exp(-(diag ** 2) / (2 * 0.09 ** 2))
    streak_tex = smooth_noise(H, W, 25, seed=seed + 77)
    streak = streak * (0.35 + streak_tex * 0.85) * 0.22
    streak_color = np.array(LAVENDER, dtype=np.float32)
    canvas = canvas + (streak_color - deep) * streak[:, :, np.newaxis]

    canvas = np.clip(canvas, 0, 255)

    img = Image.fromarray(canvas.astype(np.uint8))
    draw = ImageDraw.Draw(img)

    star_palette = [
        (255, 255, 255), (240, 240, 255), (220, 230, 255),
        LAVENDER, GOLD, YELLOW, CYAN,
    ]

    # dense field of small stars — power-law size distribution (mostly tiny)
    for _ in range(5000):
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, H))
        r = rng.random() ** 6 * 3.0 + 0.4
        brightness = rng.uniform(0.5, 1.0)
        color = star_palette[int(rng.integers(0, len(star_palette)))]
        c = tuple(int(ch * brightness) for ch in color)
        if r < 1.0:
            draw.point((x, y), fill=c)
        else:
            draw.ellipse([x - r, y - r, x + r, y + r], fill=c)

    # a sprinkling of bigger highlight stars
    for _ in range(120):
        x = int(rng.integers(0, W))
        y = int(rng.integers(0, H))
        r = rng.uniform(2.0, 4.5)
        color = star_palette[int(rng.integers(0, len(star_palette)))]
        draw.ellipse([x - r, y - r, x + r, y + r], fill=color)

    canvas = np.array(img, dtype=np.float32)
    save(canvas, "5-nightfall-starfield.png")


# ── Wallpaper 6: Topographic ───────────────────────────────────────────────────
# Contour lines from a multi-octave noise heightmap, colored by elevation.

def make_topographic(seed=31):
    print("generating: nightfall-topographic.png")

    n1 = smooth_noise(H, W, 200, seed=seed)
    n2 = smooth_noise(H, W, 80,  seed=seed + 1)
    heightmap = n1 * 0.72 + n2 * 0.28
    heightmap = (heightmap - heightmap.min()) / (heightmap.max() - heightmap.min() + 1e-8)

    # subtle background gradient BG → BG_ALT driven by elevation
    bg_arr  = np.array(BG,     dtype=np.float32)
    alt_arr = np.array(BG_ALT, dtype=np.float32)
    h3 = heightmap[:, :, np.newaxis]
    canvas = bg_arr * (1 - h3 * 0.8) + alt_arr * (h3 * 0.8)

    # quantize into bands, then mark pixels where neighbors are on a different band
    n_levels = 16
    quantized = np.floor(heightmap * n_levels).astype(np.int32)
    edge_x = np.zeros_like(quantized, dtype=bool)
    edge_y = np.zeros_like(quantized, dtype=bool)
    edge_x[:, :-1] = quantized[:, :-1] != quantized[:, 1:]
    edge_y[:-1, :] = quantized[:-1, :] != quantized[1:, :]
    edges = edge_x | edge_y

    accents = [PURPLE, BLUE, CYAN, TEAL, LAVENDER, PEACH, GOLD]
    for lvl in range(n_levels):
        mask = edges & (quantized == lvl)
        if not mask.any():
            continue
        color = np.array(accents[lvl % len(accents)], dtype=np.float32)
        # taper so high elevations sit a bit brighter than low ones
        brightness = 0.75 + 0.25 * (lvl / max(n_levels - 1, 1))
        canvas[mask] = color * brightness

    save(canvas, "6-nightfall-topographic.png")


# ── Wallpaper 7: Mesh ──────────────────────────────────────────────────────────
# Minimal mesh gradient — a handful of huge soft gaussians, no texture, no noise.

def make_mesh(seed=53):
    print("generating: nightfall-mesh.png")

    canvas = np.full((H, W, 3), BG, dtype=np.float32)
    xs = np.arange(W, dtype=np.float32)[np.newaxis, :]
    ys = np.arange(H, dtype=np.float32)[:, np.newaxis]

    blobs = [
        (PURPLE,   0.15, 0.30, 620, 0.85),
        (BLUE,     0.40, 0.70, 580, 0.75),
        (TEAL,     0.65, 0.35, 560, 0.70),
        (PEACH,    0.88, 0.65, 520, 0.60),
        (LAVENDER, 0.50, 0.15, 460, 0.55),
    ]

    for color, cx_r, cy_r, sigma, strength in blobs:
        cx, cy = cx_r * W, cy_r * H
        dist_sq = (xs - cx) ** 2 + (ys - cy) ** 2
        blob = np.exp(-dist_sq / (2 * sigma ** 2))
        c = np.array(color, dtype=np.float32)
        m = (blob * strength)[:, :, np.newaxis]
        canvas = canvas * (1 - m) + c * m

    save(canvas, "7-nightfall-mesh.png")


# ── Main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    make_nebula()
    make_flow()
    make_geometry()
    make_aurora()
    make_starfield()
    make_topographic()
    make_mesh()
    print("done.")
