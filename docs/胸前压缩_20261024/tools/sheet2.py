"""Garment grid: one row per garment, columns = (orig, new) x (anim, view) pairs.
python sheet2.py <render_dir> <out_prefix> <list.txt> <anim1,anim2> <view1,view2> [rows_per_sheet] [scale]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

d, pre, lst = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
anims, views = sys.argv[4].split(","), sys.argv[5].split(",")
per = int(sys.argv[6]) if len(sys.argv) > 6 else 8
sc = float(sys.argv[7]) if len(sys.argv) > 7 else 0.4
labels = [l.split("|", 1)[0] for l in open(lst, encoding="utf-8") if "|" in l]
gs = [l[:-2] for l in labels if l.endswith("_o")]
crop = (100, 20, 500, 420)
cols = [(an, vw, v) for an in anims for vw in views for v in ("o", "n")]
cw, ch = int(400 * sc), int(400 * sc)
for k in range(0, len(gs), per):
    chunk = gs[k:k + per]
    sheet = Image.new("RGB", (cw * len(cols), ch * len(chunk)), (0, 0, 0))
    for r, g in enumerate(chunk):
        for c, (an, vw, v) in enumerate(cols):
            p = d / ("%s_%s__%s__%s.png" % (g, v, an, vw))
            im = Image.open(p).convert("RGB").crop(crop) if p.exists() else Image.new("RGB", (400, 400), (60, 0, 0))
            im = im.resize((cw, ch))
            dr = ImageDraw.Draw(im)
            dr.text((3, 2), "%s %s" % ("OLD" if v == "o" else "NEW", g[:18]), fill=(255, 255, 0) if v == "n" else (180, 180, 180))
            dr.text((3, ch - 12), "%s %s" % (an.split("_AI_")[-1], vw), fill=(200, 200, 200))
            sheet.paste(im, (c * cw, r * ch))
    out = "%s_%d.png" % (pre, k // per + 1)
    sheet.save(out)
    print("SHEET", out, sheet.size)
