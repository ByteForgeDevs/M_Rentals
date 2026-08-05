"""Vectorize the supplied Logo.png into clean SVG paths."""
import numpy as np
import potrace
from PIL import Image

SRC = "static/img/logo-primary.png"
im = Image.open(SRC).convert("RGB")
arr = np.asarray(im).astype(int)
r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

black = (r < 110) & (g < 110) & (b < 110)
green = (abs(r - 27) < 70) & (abs(g - 157) < 70) & (abs(b - 128) < 70) & ~black


def fmt(v):
    return f"{v:.1f}".rstrip("0").rstrip(".")


def trace(mask, alphamax, dx, dy, scale):
    bmp = potrace.Bitmap(((~mask) * 255).astype(np.uint8))
    path = bmp.trace(turdsize=6, alphamax=alphamax, opttolerance=0.15)
    out = []
    for curve in path:
        sp = curve.start_point; sx, sy = sp.x, sp.y
        d = [f"M{fmt((sx - dx) * scale)} {fmt((sy - dy) * scale)}"]
        for seg in curve:
            ep = seg.end_point; ex, ey = ep.x, ep.y
            if seg.is_corner:
                cp = seg.c; cx, cy = cp.x, cp.y
                d.append(f"L{fmt((cx - dx) * scale)} {fmt((cy - dy) * scale)}")
                d.append(f"L{fmt((ex - dx) * scale)} {fmt((ey - dy) * scale)}")
            else:
                p1 = seg.c1; c1x, c1y = p1.x, p1.y
                p2 = seg.c2; c2x, c2y = p2.x, p2.y
                d.append(
                    f"C{fmt((c1x - dx) * scale)} {fmt((c1y - dy) * scale)} "
                    f"{fmt((c2x - dx) * scale)} {fmt((c2y - dy) * scale)} "
                    f"{fmt((ex - dx) * scale)} {fmt((ey - dy) * scale)}"
                )
        d.append("Z")
        out.append("".join(d))
    return out


def bbox(mask):
    ys, xs = np.nonzero(mask)
    return xs.min(), xs.max(), ys.min(), ys.max()


mx0, mx1, my0, my1 = bbox(black)
gx0, gx1, gy0, gy1 = bbox(green)
print("mark bbox", mx0, mx1, my0, my1)
print("word bbox", gx0, gx1, gy0, gy1)

SCALE = 0.25
# Icon-only: origin at the mark's own bounding box.
icon_paths = trace(black, 0.0, mx0, my0, SCALE)
# Lockup: shared origin across mark + wordmark.
lx0, ly0 = min(mx0, gx0), my0
lock_mark = trace(black, 0.0, lx0, ly0, SCALE)
lock_word = trace(green, 1.0, lx0, ly0, SCALE)

import json
json.dump(
    {
        "icon": icon_paths,
        "icon_vb": [0, 0, round((mx1 - mx0) * SCALE, 1), round((my1 - my0) * SCALE, 1)],
        "lock_mark": lock_mark,
        "lock_word": lock_word,
        "lock_vb": [
            0,
            0,
            round((max(mx1, gx1) - lx0) * SCALE, 1),
            round((max(my1, gy1) - ly0) * SCALE, 1),
        ],
    },
    open("/tmp/logo_paths.json", "w"),
)
print("icon paths:", len(icon_paths), "word paths:", len(lock_word))
