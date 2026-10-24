"""Contact sheet: rows = anim x view, columns = labels (orig/new...).
python sheet.py <render_dir> <out.png> <labels comma> <anims comma> <views comma> [crop x0,y0,x1,y1] [scale]
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

d, out = Path(sys.argv[1]), sys.argv[2]
labels, anims, views = (sys.argv[i].split(",") for i in (3, 4, 5))
crop = tuple(int(v) for v in sys.argv[6].split(",")) if len(sys.argv) > 6 else None
scale = float(sys.argv[7]) if len(sys.argv) > 7 else 1.0
cells = []
for an in anims:
    for vw in views:
        row = []
        for lb in labels:
            p = d / ("%s__%s__%s.png" % (lb, an, vw))
            im = Image.open(p).convert("RGB") if p.exists() else Image.new("RGB", (600, 600), (40, 40, 40))
            if crop:
                im = im.crop(crop)
            if scale != 1.0:
                im = im.resize((int(im.width * scale), int(im.height * scale)))
            ImageDraw.Draw(im).text((6, 4), "%s | %s | %s" % (lb, an.replace("male_body_", "").replace("female_body_", ""), vw), fill=(255, 255, 0))
            row.append(im)
        cells.append(row)
w, h = cells[0][0].size
sheet = Image.new("RGB", (w * len(labels), h * len(cells)), (0, 0, 0))
for r, row in enumerate(cells):
    for c, im in enumerate(row):
        sheet.paste(im, (c * w, r * h))
sheet.save(out)
print("SHEET", out, sheet.size)
