# Build 孝服 assets from the 东汉平民汉服 (hd_eastern_han/com_01) male + female models.
# Mesh geometry is reused unchanged; colour comes from a new all-white hemp variation + palette.
import shutil, subprocess, sys
from pathlib import Path
import numpy as np
from PIL import Image

MOD = Path(r"E:\documents\Paradox Interactive\Crusader Kings III\mod")
CLO = MOD / "HanJIn_Clothes"
TEXCONV = MOD / "tools/third_party/DirectXTex/may2026/bin/texconv.exe"
VAN_PAL = Path(r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\portraits\accessory_variations\textures\color_palette_tgp_korean_commoner_01.dds")
STAGE = Path(sys.argv[1])
STAGE.mkdir(parents=True, exist_ok=True)

OLD, NEW = "hd_eastern_han_com_01", "hd_xiao_fu_01"
for g, var_old, var_new in (("m", "hd_eastern_han_m_commoner_01", "hd_xiaofu_m_01"),
                            ("f", "hd_eastern_han_f_commoner_01", "hd_xiaofu_f_01")):
    src = CLO / f"gfx/models/portraits/{g}_clothes/hd_eastern_han/com_01"
    dst = CLO / f"gfx/models/portraits/{g}_clothes/hd_eastern_han/xiao_fu_01"
    if dst.exists():
        raise SystemExit(f"refuse to overwrite {dst}")
    dst.mkdir(parents=True)
    for f in src.iterdir():
        if f.suffix in (".mesh", ".dds"):
            shutil.copy2(f, dst / f.name.replace(OLD, NEW))
    asset = (src / f"{g}_clothes_sec_{OLD}.asset").read_text(encoding="utf-8")
    shape = f'"{g}_clothes_sec_{OLD}Shape"'
    assert asset.count(shape) == 1
    asset = asset.replace(shape, "@@SHAPE@@").replace(OLD, NEW).replace("@@SHAPE@@", shape)
    assert asset.count(f'variation = "{var_old}"') == 1
    asset = asset.replace(f'variation = "{var_old}"', f'variation = "{var_new}"')
    (dst / f"{g}_clothes_sec_{NEW}.asset").write_text(asset, encoding="utf-8", newline="\n")
    print("asset", dst / f"{g}_clothes_sec_{NEW}.asset")

# all-white palette (undyed hemp to bleached white), alpha copied from the vanilla palette it replaces
subprocess.run([str(TEXCONV), "-nologo", "-y", "-ft", "png", "-m", "1", "-o", str(STAGE), str(VAN_PAL)], check=True, capture_output=True)
van = np.asarray(Image.open(STAGE / (VAN_PAL.stem + ".png")).convert("RGBA"))
h, w = van.shape[:2]
pal = np.zeros_like(van)
tones = [(250, 249, 246), (244, 242, 236), (238, 235, 227), (247, 246, 241)]
for y in range(h):
    pal[y, :, :3] = tones[y % len(tones)]
pal[..., 3] = van[..., 3]
png = STAGE / "hd_xiaofu_palette.png"
Image.fromarray(pal, "RGBA").save(png)
out_dir = CLO / "gfx/portraits/accessory_variations/hd_xiaofu"
out_dir.mkdir(parents=True, exist_ok=True)
subprocess.run([str(TEXCONV), "-nologo", "-y", "-f", "R8G8B8A8_UNORM", "-m", "5", "-o", str(out_dir), str(png)], check=True, capture_output=True)
print("palette", out_dir / "hd_xiaofu_palette.dds", (out_dir / "hd_xiaofu_palette.dds").stat().st_size, "alpha", np.unique(van[..., 3]))
