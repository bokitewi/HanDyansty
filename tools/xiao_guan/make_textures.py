# Generate diffuse / packed normal / properties for the 孝帽 atlas, then encode with texconv.
# Atlas (Blender UV, v up): shell u0.01-0.61 (7 ribs), band u0.64-0.98 v0.82-0.98,
# plain linen u0.64-0.98 v0.56-0.78, black inner cap u0.64-0.98 v0.04-0.50.
import sys, subprocess, numpy as np
from pathlib import Path
from PIL import Image

out = Path(sys.argv[1]); texconv = sys.argv[2]
NAME = "m_headgear_hd_huaxia_xiao_guan"
S = 1024
rng = np.random.default_rng(1951)
yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
u = (xx + 0.5) / S
v = 1.0 - (yy + 0.5) / S          # image row 0 = top = v 1

def box(r):
    return (u >= r[0] - 0.008) & (u <= r[2] + 0.008) & (v >= r[1] - 0.008) & (v <= r[3] + 0.008)

R_SHELL = (0.01, 0.01, 0.61, 0.99)
R_BAND = (0.64, 0.82, 0.98, 0.98)
R_PLAIN = (0.64, 0.56, 0.98, 0.78)
R_CAP = (0.64, 0.04, 0.98, 0.50)

# fine plain weave: two orthogonal thread ripples + soft noise
noise = rng.normal(0, 1, (S, S)).astype(np.float32)
from PIL import ImageFilter
blur = np.asarray(Image.fromarray(((noise * 20) + 128).clip(0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.2)), np.float32) / 255 - 0.5
weave = 0.5 * np.sin(xx * np.pi / 2.0) * np.sin(yy * np.pi / 2.0)
height = 0.15 * weave + 0.6 * blur        # tiny cloth relief

col = np.zeros((S, S, 3), np.float32)
col[:] = (236, 233, 226)                  # default undyed white linen
rough = np.full((S, S), 52.0, np.float32)

# shell: thin gauze, slightly greyer between the ribs, brighter ribs (梁)
m = box(R_SHELL)
fu = (u - R_SHELL[0]) / (R_SHELL[2] - R_SHELL[0])
rib_d = np.abs(((fu * 6) + 0.5) % 1.0 - 0.5) / 6 * (R_SHELL[2] - R_SHELL[0]) * S   # px distance to nearest rib
rib = np.clip(1 - rib_d / 6.0, 0, 1)
gauze = np.array((212, 210, 205), np.float32)
ribc = np.array((251, 250, 247), np.float32)
shell_col = gauze * (1 - rib[..., None]) + ribc * rib[..., None]
# faint horizontal gauze threads
shell_col *= (1 + 0.025 * np.sin(yy * np.pi / 1.5))[..., None]
col[m] = shell_col[m]
height[m] += (np.cos(np.clip(rib_d / 6.0, 0, 1) * np.pi / 2) ** 2 * 3.0)[m]
rough[m] = (52 - 10 * rib)[m]

# band: plain linen with a stitched seam near both edges
m = box(R_BAND)
fv = (v - R_BAND[1]) / (R_BAND[3] - R_BAND[1])
seam = ((np.abs(fv - 0.12) < 0.025) | (np.abs(fv - 0.88) < 0.025)) & ((xx.astype(int) // 6) % 2 == 0)
c = np.where(seam[..., None], np.array((214, 210, 202), np.float32), np.array((240, 237, 231), np.float32))
col[m] = c[m]
height[m] -= (seam * 1.0)[m]

# black inner cap (内帻): dark gauze
m = box(R_CAP)
col[m] = (np.array((20, 19, 21), np.float32) * (1 + 0.25 * blur[..., None] + 0.12 * weave[..., None]))[m]
rough[m] = 60

col *= (1 + 0.04 * blur)[..., None]
diffuse = np.dstack([col.clip(0, 255), np.full((S, S), 255, np.float32)]).astype(np.uint8)

# packed normal (portrait shader UnpackRRxGNormal: x = G, y = -A), vanilla cloth has R~G, B=0
gy, gx = np.gradient(height)
strength = 0.18
nx = np.clip(-gx * strength, -1, 1)
ny_tex = np.clip(gy * strength, -1, 1)    # image y grows downward = -v
G = (nx * 0.5 + 0.5) * 255
A = (ny_tex * 0.5 + 0.5) * 255            # y = -(A*2-1) -> +v slope sign handled by downward image rows
normal = np.dstack([G, G, np.zeros((S, S)), A]).clip(0, 255).astype(np.uint8)

props = np.dstack([np.zeros((S, S)), np.zeros((S, S)), np.zeros((S, S)), rough]).clip(0, 255).astype(np.uint8)

stage = out / "png"; stage.mkdir(parents=True, exist_ok=True)
for nm, arr in (("diffuse", diffuse), ("normal", normal), ("properties", props)):
    Image.fromarray(arr, "RGBA").save(stage / f"{NAME}_{nm}.png")

def enc(nm, fmt, extra):
    cmd = [texconv, "-nologo", "-y", "-f", fmt, "-m", "0", *extra, "-o", str(out), str(stage / f"{NAME}_{nm}.png")]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(r.stdout + r.stderr)
    d = (out / f"{NAME}_{nm}.dds").read_bytes()
    print(nm, fmt, len(d), d[84:88])

enc("diffuse", "BC1_UNORM", [])
enc("normal", "BC3_UNORM", ["-sepalpha"])
enc("properties", "BC3_UNORM", ["-sepalpha"])
