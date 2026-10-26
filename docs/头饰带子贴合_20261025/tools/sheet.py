import sys
from PIL import Image, ImageDraw
out = sys.argv[1]; cols = int(sys.argv[2]); files = sys.argv[3:]
ims = [Image.open(f).convert("RGB") for f in files]
w, h = ims[0].size
rows = (len(ims) + cols - 1) // cols
S = Image.new("RGB", (w * cols, (h + 18) * rows), "white")
d = ImageDraw.Draw(S)
import os
for i, (im, f) in enumerate(zip(ims, files)):
    x, y = (i % cols) * w, (i // cols) * (h + 18)
    S.paste(im, (x, y + 18)); d.text((x + 4, y + 2), os.path.basename(f)[:-4], fill="black")
S.save(out)
