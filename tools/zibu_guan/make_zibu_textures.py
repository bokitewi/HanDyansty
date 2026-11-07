# Textures for the 缁布束发冠: two diffuse variants (black / muted red) + shared packed normal + properties.
# Usage: python make_zibu_textures.py <out_dir> <texconv.exe>
# Atlas (Blender UV, v up) must match build_zibu_guan.py:
#   board gauze u0.01-0.55 (u = 0.5 + x/11, v = arc length / total; ring-covered base is opaque)
#   ring u0.58-0.99 v0.82-0.99 | cord u0.58-0.99 v0.72-0.79 | filigree plaque u0.58-0.86 v0.30-0.69
#   plain metal (boss) u0.88-0.99 v0.30-0.69 | hairpin u0.58-0.99 v0.04-0.27
import sys, math, subprocess, numpy as np
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

out = Path(sys.argv[1]); texconv = sys.argv[2]
NAME = "m_headgear_hd_huaxia_zibu_guan"
S = 1024
import json
_pp = json.load(open(out / "zibu_params.json"))   # written by build_zibu_guan.py
RINGH, LTOT = _pp["RINGH"], _pp["LTOT"]
rng = np.random.default_rng(1951)
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
u = (xx + 0.5) / S
v = 1.0 - (yy + 0.5) / S

R_PANEL = (0.01, 0.01, 0.55, 0.99)
R_RING = (0.58, 0.82, 0.99, 0.99)
R_TRIM = (0.58, 0.72, 0.99, 0.79)
R_ORN = (0.58, 0.30, 0.86, 0.69)
R_METAL = (0.88, 0.30, 0.99, 0.69)
R_PIN = (0.58, 0.04, 0.99, 0.27)
def box(r, pad=0.006):
    return (u >= r[0] - pad) & (u <= r[2] + pad) & (v >= r[1] - pad) & (v <= r[3] + pad)
def blurf(a, rad):
    im = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8))
    return np.asarray(im.filter(ImageFilter.GaussianBlur(rad)), np.float32) / 255

noise = rng.normal(0, 1, (S, S)).astype(np.float32)
soft = blurf(noise * 0.12 + 0.5, 2.0) - 0.5

# material id map: 0 none, 1 gauze, 2 gauze-opaque, 3 ring, 4 cord, 5 filigree, 6 metal
mid = np.zeros((S, S), np.uint8)
alpha = np.ones((S, S), np.float32)
height = np.zeros((S, S), np.float32)
shade = np.ones((S, S), np.float32)          # multiplicative brightness on top of the base colour

# ---- board gauze: square-ish open weave, holes alpha 0
m = box(R_PANEL)
PU, PV = 8.0, 7.0                            # px pitch (≈0.16 unit)
tu = (xx % PU) / PU; tv = (yy % PV) / PV
thread_u = np.clip(1 - np.abs(tu - 0.5) * 2 / 0.42, 0, 1)   # vertical threads (narrow)
thread_v = np.clip(1 - np.abs(tv - 0.5) * 2 / 0.48, 0, 1)
cov = np.clip((1 - (1 - (np.abs(tu - 0.5) < 0.19)) * (1 - (np.abs(tv - 0.5) < 0.22))), 0, 1).astype(np.float32)
# cov = 1 on threads, 0 in holes; soften by 1px
cov = np.clip(blurf(cov, 0.6) * 1.15, 0, 1)
fv_board = (v - R_PANEL[1]) / (R_PANEL[3] - R_PANEL[1])
base_band = fv_board * LTOT < RINGH + 0.15
mid[m] = 1
mid[m & base_band] = 2
alpha[m] = np.where(base_band, 1.0, cov)[m]
height[m] = (0.5 * thread_u + 0.5 * thread_v)[m]
shade[m] = (0.9 + 0.2 * np.maximum(thread_u, thread_v) * cov)[m]
# opaque base band: dense weave + a darker hem line at the band top
hem = base_band & (np.abs(fv_board * LTOT - RINGH) < 0.25)
shade[m & base_band] = (0.85 + 0.12 * thread_u * thread_v)[m & base_band]
shade[m & hem] = 0.7

# ---- ring: dense dark gauze, opaque
m = box(R_RING)
mid[m] = 3
tu2 = (xx % 5) / 5; tv2 = (yy % 5) / 5
w2 = np.sin(tu2 * np.pi) * np.sin(tv2 * np.pi)
height[m] = (0.4 * w2)[m]
shade[m] = (0.88 + 0.15 * w2)[m]

# ---- braided cord: diagonal twist stripes
m = box(R_TRIM)
mid[m] = 4
fu = (u - R_TRIM[0]) / (R_TRIM[2] - R_TRIM[0]); fv = (v - R_TRIM[1]) / (R_TRIM[3] - R_TRIM[1])
tw = 0.5 + 0.5 * np.sin(2 * np.pi * (fu * 140 + fv * 1.0))
height[m] = (1.4 * tw)[m]
shade[m] = (0.7 + 0.6 * tw)[m]

# ---- filigree plaque (alpha cut-out), drawn at 4x
ox0, oy0 = int(R_ORN[0] * S), int((1 - R_ORN[3]) * S)
ow, oh = int((R_ORN[2] - R_ORN[0]) * S), int((R_ORN[3] - R_ORN[1]) * S)
K = 4
fil = Image.new("L", (ow * K, oh * K), 0)
dr = ImageDraw.Draw(fil)
def P(x, y):                                  # card coords: x 0..1 left->right, y 0..1 bottom->top
    return (x * ow * K, (1 - y) * oh * K)
def stroke(pts, w):
    dr.line([P(*q) for q in pts], fill=255, width=int(w * ow * K), joint="curve")
    r = w * ow * K / 2
    for q in (pts[0], pts[-1]):
        c = P(*q); dr.ellipse((c[0] - r, c[1] - r, c[0] + r, c[1] + r), fill=255)
def spiral(cx, cy, r0, a0, turns, sgn, w, n=60):
    pts = []
    for k in range(n + 1):
        t = k / n
        r = r0 * (1 - 0.78 * t)
        a = a0 + sgn * turns * 2 * math.pi * t
        pts.append((cx + r * math.cos(a) * 0.85, cy + r * math.sin(a)))
    stroke(pts, w)
def disc(cx, cy, r):
    c = P(cx, cy); rr = r * ow * K
    dr.ellipse((c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr), fill=255)
def ring_(cx, cy, r, w):
    c = P(cx, cy); rr = r * ow * K
    dr.ellipse((c[0] - rr, c[1] - rr, c[0] + rr, c[1] + rr), outline=255, width=int(w * ow * K))
CX, CY = 0.5, 0.42
W = 0.045
# lobed frame (four arcs bulging outward between the diamond tips)
def arc_pts(p0, p1, bulge, n=24):
    mx, my = (p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2
    nx, ny = (mx - CX), (my - CY)
    ln = math.hypot(nx, ny) or 1
    cx_, cy_ = mx + nx / ln * bulge, my + ny / ln * bulge
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * cx_ + t * t * p1[0], (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * cy_ + t * t * p1[1]) for t in (k / n for k in range(n + 1))]
tips = [(CX, 0.76), (0.86, CY), (CX, 0.08), (0.14, CY)]
for i in range(4):
    stroke(arc_pts(tips[i], tips[(i + 1) % 4], 0.07), W)
# rosette: ring + 8 petals + centre (the 3D boss sits on top)
ring_(CX, CY, 0.15, 0.04)
for k in range(8):
    a = k * math.pi / 4
    disc(CX + 0.205 * math.cos(a) * 0.85, CY + 0.205 * math.sin(a), 0.045)
disc(CX, CY, 0.07)
# side scroll arms curling out from the frame tips
for sx in (-1, 1):
    tipx = CX + sx * 0.36
    spiral(tipx + sx * 0.04, CY + 0.13, 0.12, -math.pi / 2 if sx > 0 else -math.pi / 2, 1.1, -sx, 0.04)
    spiral(tipx + sx * 0.04, CY - 0.13, 0.12, math.pi / 2, 1.1, sx, 0.04)
    stroke([(tipx - sx * 0.02, CY), (tipx + sx * 0.1, CY)], 0.05)
    # inner small curls in the frame
    spiral(CX + sx * 0.2, CY + 0.2, 0.06, math.pi, 0.9, sx, 0.028)
    spiral(CX + sx * 0.2, CY - 0.2, 0.06, math.pi, 0.9, -sx, 0.028)
# top finial: tapered spike with a pair of leaves
for k in range(14):
    t = k / 13
    y0 = 0.76 + 0.22 * t
    disc(CX, y0, 0.05 * (1 - 0.8 * t))
for sx in (-1, 1):
    stroke([(CX, 0.8), (CX + sx * 0.07, 0.85), (CX + sx * 0.1, 0.9)], 0.035)
# bottom drop
disc(CX, 0.035, 0.04)
stroke([(CX, 0.08), (CX, 0.04)], 0.03)
fil = fil.resize((ow, oh), Image.LANCZOS)
fa = np.asarray(fil, np.float32) / 255
m = box(R_ORN, 0.0)
mid[m] = 5
sub = (slice(oy0, oy0 + oh), slice(ox0, ox0 + ow))
alpha[m] = 0.0
alpha[sub] = np.clip(fa * 1.4, 0, 1)
fh = blurf(fa, 1.6)
height[sub] = fh * 3.0
shade[sub] = 0.55 + 0.6 * np.clip(fh * 1.3, 0, 1)
mid[sub] = np.where(fa > 0.02, 5, mid[sub])

# ---- plain metal (boss) and hairpin: lightly brushed
for r, k in ((R_METAL, 6), (R_PIN, 6)):
    m = box(r)
    mid[m] = k
    brushed = blurf(np.clip(noise * 0.2 + 0.5, 0, 1), 0.8)
    height[m] = (0.3 * brushed)[m]
    shade[m] = (0.85 + 0.3 * brushed)[m]

# ---------------------------------------------------------------- variants
VAR = {
    "black": {1: (30, 29, 33), 2: (24, 23, 27), 3: (21, 20, 23), 4: (20, 19, 22), 5: (138, 148, 160), 6: (132, 142, 154)},
    "red":   {1: (118, 60, 54), 2: (104, 52, 47), 3: (96, 48, 44), 4: (84, 42, 38), 5: (176, 112, 74), 6: (166, 104, 70)},
}
stage = out / "png"; stage.mkdir(parents=True, exist_ok=True)
for vn, pal in VAR.items():
    col = np.zeros((S, S, 3), np.float32); col[:] = (128, 128, 128)
    for k, c in pal.items():
        mk = mid == k
        col[mk] = np.array(c, np.float32)
    col *= (shade * (1 + 0.5 * soft))[..., None]
    a = np.where(mid == 0, 1.0, alpha)
    diffuse = np.dstack([col.clip(0, 255), (a * 255).clip(0, 255)]).astype(np.uint8)
    Image.fromarray(diffuse, "RGBA").save(stage / f"{NAME}_{vn}_diffuse.png")

gy, gx = np.gradient(height)
strength = 0.22
nx = np.clip(-gx * strength, -1, 1); ny_tex = np.clip(gy * strength, -1, 1)
G = (nx * 0.5 + 0.5) * 255; A = (ny_tex * 0.5 + 0.5) * 255
normal = np.dstack([G, G, np.zeros((S, S)), A]).clip(0, 255).astype(np.uint8)
metal = np.isin(mid, (5, 6))
B = np.where(metal, 225.0, 0.0)
Arough = np.where(metal, 80.0, np.where(mid == 4, 150.0, 185.0))
props = np.dstack([np.zeros((S, S)), np.zeros((S, S)), B, Arough]).clip(0, 255).astype(np.uint8)
Image.fromarray(normal, "RGBA").save(stage / f"{NAME}_normal.png")
Image.fromarray(props, "RGBA").save(stage / f"{NAME}_properties.png")

def enc(nm, fmt, extra):
    cmd = [texconv, "-nologo", "-y", "-f", fmt, "-m", "0", *extra, "-o", str(out), str(stage / f"{NAME}_{nm}.png")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout + r.stderr)
    d = (out / f"{NAME}_{nm}.dds").read_bytes()
    print(nm, fmt, len(d), d[84:88])
enc("black_diffuse", "BC3_UNORM", ["-sepalpha"])
enc("red_diffuse", "BC3_UNORM", ["-sepalpha"])
enc("normal", "BC3_UNORM", ["-sepalpha"])
enc("properties", "BC3_UNORM", ["-sepalpha"])
