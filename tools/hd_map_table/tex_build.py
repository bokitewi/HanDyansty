"""Build the DDS textures for the Han-Jin lacquer map table.

Run with:  python -P tex_build.py <src_dir> <out_dir> <vanilla_tgp_dir> <sword_dir> <report.json>
"""
import io, json, math, os, random, shutil, struct, sys
from PIL import Image, ImageFilter

src, out, van_tgp, sword_dir, report_path = sys.argv[1:6]
os.makedirs(out, exist_ok=True)
report = {"textures": {}, "black_patches": {}}

DDSD_CAPS, DDSD_HEIGHT, DDSD_WIDTH, DDSD_PIXELFORMAT = 0x1, 0x2, 0x4, 0x1000
DDSD_MIPMAPCOUNT, DDSD_LINEARSIZE = 0x20000, 0x80000
DDSCAPS_COMPLEX, DDSCAPS_TEXTURE, DDSCAPS_MIPMAP = 0x8, 0x1000, 0x400000
DDPF_FOURCC = 0x4


def encode_level(img, fmt):
    buf = io.BytesIO()
    img.convert("RGBA").save(buf, "DDS", pixel_format=fmt)
    data = buf.getvalue()
    return data[128:]


def write_dds(img, path, fmt):
    w, h = img.size
    assert w & (w - 1) == 0 and h & (h - 1) == 0, (w, h)
    block = 8 if fmt == "DXT1" else 16
    levels, sizes = [], []
    cur = img.convert("RGBA")
    while True:
        lw, lh = cur.size
        data = encode_level(cur, fmt)
        expect = max(1, math.ceil(lw / 4)) * max(1, math.ceil(lh / 4)) * block
        assert len(data) == expect, (path, lw, lh, len(data), expect)
        levels.append(data); sizes.append((lw, lh))
        if lw == 1 and lh == 1:
            break
        cur = cur.resize((max(1, lw // 2), max(1, lh // 2)), Image.LANCZOS)
    hdr = bytearray(128)
    hdr[0:4] = b"DDS "
    flags = DDSD_CAPS | DDSD_HEIGHT | DDSD_WIDTH | DDSD_PIXELFORMAT | DDSD_MIPMAPCOUNT | DDSD_LINEARSIZE
    struct.pack_into("<IIIIIII", hdr, 4, 124, flags, h, w, len(levels[0]), 0, len(levels))
    struct.pack_into("<II", hdr, 76, 32, DDPF_FOURCC)
    hdr[84:88] = fmt.encode()
    struct.pack_into("<I", hdr, 108, DDSCAPS_COMPLEX | DDSCAPS_TEXTURE | DDSCAPS_MIPMAP)
    with open(path, "wb") as f:
        f.write(hdr)
        for d in levels:
            f.write(d)
    total = 128 + sum(len(d) for d in levels)
    assert os.path.getsize(path) == total
    report["textures"][os.path.basename(path)] = {"size": [w, h], "fmt": fmt, "mips": len(levels), "bytes": total}


def load(name):
    return Image.open(os.path.join(src, name)).convert("RGB")


def black_patch(img, frac=0.06, probe=64):
    """Darkest window (in Blender UV, v up) that stays dark at a low mip."""
    small = img.resize((probe, max(1, round(probe * img.size[1] / img.size[0]))), Image.BOX).convert("L")
    sw, sh = small.size
    win = max(2, round(frac * sw))
    px = small.load()
    best = None
    for y in range(1, sh - win - 1):
        for x in range(1, sw - win - 1):
            m = max(px[i, j] for i in range(x - 1, x + win + 1) for j in range(y - 1, y + win + 1))
            if best is None or m < best[0]:
                best = (m, x, y)
    m, x, y = best
    u0, u1 = x / sw, (x + win) / sw
    v1, v0 = 1 - y / sh, 1 - (y + win) / sh
    return {"u": [u0, u1], "v": [v0, v1], "max_luma_lowmip": m}


# --- lacquer textures ---------------------------------------------------------
jobs = [
    ("3d66Model-18349387-files-005.png", "hd_han_table_top_diffuse.dds", (4096, 2048)),
    ("3d66Model-18349387-files-002.png", "hd_han_table_side_diffuse.dds", (2048, 512)),
    ("3d66Model-18349387-files-007.png", "hd_han_plate_top_diffuse.dds", (1024, 1024)),
    ("3d66Model-18349387-files-004.png", "hd_han_plate_rim_diffuse.dds", (512, 256)),
    ("3d66Model-18349387-files-009.png", "hd_han_cup_diffuse.dds", (1024, 2048)),
    ("3d66Model-18349387-files-008.png", "hd_han_cup_ears_diffuse.dds", (1024, 1024)),
]
for sname, dname, size in jobs:
    im = load(sname).resize(size, Image.LANCZOS)
    write_dds(im, os.path.join(out, dname), "DXT1")

# black patches used for faces that must render plain black lacquer
top = load("3d66Model-18349387-files-005.png")
centre = top.crop((int(top.size[0] * 0.40), int(top.size[1] * 0.40), int(top.size[0] * 0.60), int(top.size[1] * 0.60)))
report["black_patches"]["table_top_centre_0.4_0.6"] = {
    "u": [0.45, 0.55], "v": [0.45, 0.55],
    "max_luma_full": max(centre.convert("L").getdata()),
    "max_luma_lowmip": max(centre.resize((8, 8), Image.BOX).convert("L").getdata())}
report["black_patches"]["plate_top"] = black_patch(load("3d66Model-18349387-files-007.png"))
report["black_patches"]["cup_ears"] = black_patch(load("3d66Model-18349387-files-008.png"))

# --- bronze for the censer (博山炉) -------------------------------------------
random.seed(18349387)
base = Image.new("RGB", (256, 256))
px = base.load()
for y in range(256):
    for x in range(256):
        n = random.random()
        k = 0.85 + 0.3 * n
        px[x, y] = (int(150 * k), int(112 * k), int(48 * k))
base = base.filter(ImageFilter.GaussianBlur(1.2))
write_dds(base, os.path.join(out, "hd_han_censer_diffuse.dds"), "DXT1")

# --- baked lighting for the floor (light pool + soft table shadow), alpha 255 -----
S = 512
FLOOR = 60000.0
tw, td = 21973.0 / FLOOR, 11140.0 / FLOOR       # table footprint in floor UV
light = Image.new("L", (S, S))
lp = light.load()
for y in range(S):
    for x in range(S):
        dx, dy = (x + 0.5) / S - 0.5, (y + 0.5) / S - 0.5
        r = math.hypot(dx, dy) / 0.5
        lp[x, y] = int(255 * max(0.0, min(1.0, 0.56 * (1 - r ** 1.6))))
shadow = Image.new("L", (S, S), 255)
sp = shadow.load()
for y in range(S):
    for x in range(S):
        u, v = (x + 0.5) / S - 0.5, (y + 0.5) / S - 0.5
        if abs(u) < tw / 2 * 1.04 and abs(v) < td / 2 * 1.08:
            sp[x, y] = 110
shadow = shadow.filter(ImageFilter.GaussianBlur(S * 0.012))
rgb = Image.new("RGBA", (S, S))
rp = rgb.load()
for y in range(S):
    for x in range(S):
        val = lp[x, y] * shadow.getpixel((x, y)) // 255
        rp[x, y] = (val, val, val, 255)
write_dds(rgb, os.path.join(out, "hd_han_floor_lighting.dds"), "DXT5")

# --- copied textures (already CK3 DDS) ------------------------------------------
copies = {
    os.path.join(van_tgp, "tgp_dark_tile_floor_diffuse.dds"): "hd_han_floor_diffuse.dds",
    os.path.join(van_tgp, "tgp_dark_tile_floor_normal.dds"): "hd_han_floor_normal.dds",
    os.path.join(van_tgp, "tgp_dark_tile_floor_properties.dds"): "hd_han_floor_properties.dds",
    os.path.join(sword_dir, "hd_weapon_handao_02_diffuse.dds"): "hd_han_sword_diffuse.dds",
    os.path.join(sword_dir, "hd_weapon_handao_02_normal.dds"): "hd_han_sword_normal.dds",
    os.path.join(sword_dir, "hd_weapon_handao_02_properties.dds"): "hd_han_sword_properties.dds",
}
for s, d in copies.items():
    shutil.copyfile(s, os.path.join(out, d))
    report["textures"][d] = {"copied_from": s, "bytes": os.path.getsize(os.path.join(out, d))}

json.dump(report, open(report_path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print(json.dumps(report["black_patches"], indent=1))
print("TEX_DONE", len(report["textures"]))
