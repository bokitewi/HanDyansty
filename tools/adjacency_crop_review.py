#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""adjacency_crop_review.py — 为指定连接对生成 provinces.png 局部裁剪叠加图（只读）。
着色：A 省=红，B 省=蓝；海省=浅蓝，湖省=浅青，河省=浅绿。
"""
import os
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_DATA = os.path.normpath(os.path.join(HERE, "..", "map_data"))
DEF_CSV = os.path.join(MAP_DATA, "definition.csv")
PROV_PNG = os.path.join(MAP_DATA, "provinces.png")

MARGIN = 30
COLS = 3
CELL_W = 480
CELL_H = 360

PAIRS = [
    ("LAND", 6907, 6996), ("LAND", 22, 4339), ("LAND", 1648, 1613),
    ("LAND", 706, 368), ("LAND", 4433, 248), ("LAND", 4542, 2248),
    ("LAND", 3923, 2979), ("LAND", 5041, 38), ("LAND", 34, 84),
    ("LAND", 1217, 499), ("LAND", 6972, 2538), ("LAND", 1241, 6966),
    ("LAND", 4179, 4126), ("LAND", 4575, 4135), ("LAND", 998, 1350),
    ("LAND", 146, 7026), ("LAND", 2332, 4054), ("LAND", 3377, 4027),
    ("LAND", 1224, 2538),
    ("FALLBACK", 5399, 3319), ("FALLBACK", 671, 1177), ("FALLBACK", 1648, 746),
    ("OK", 166, 5679), ("OK", 909, 854), ("OK", 5360, 5380),
]


def load_def():
    info = {}
    with open(DEF_CSV, encoding="utf-8-sig", errors="replace") as f:
        for line in f:
            parts = line.rstrip("\r\n").split(";")
            if len(parts) < 5:
                continue
            try:
                pid = int(parts[0])
                rgb = (int(parts[1]), int(parts[2]), int(parts[3]))
            except ValueError:
                continue
            info[pid] = (rgb, parts[4])
    return info


def main(out_path):
    info = load_def()
    img = Image.open(PROV_PNG).convert("RGB")
    arr = np.asarray(img)
    H, W, _ = arr.shape
    color2id = {}
    id2name = {}
    for pid, (rgb, name) in info.items():
        color2id[rgb] = pid
        id2name[pid] = name
    keys = (arr[..., 0].astype(np.uint32) << 16) | \
           (arr[..., 1].astype(np.uint32) << 8) | arr[..., 2].astype(np.uint32)
    lut = np.full(1 << 24, -1, dtype=np.int32)
    for k, v in color2id.items():
        lut[(k[0] << 16) | (k[1] << 8) | k[2]] = v
    gid = lut[keys]
    del lut, keys, arr

    id2cls = {pid: ("sea" if name.startswith("sea_") else
                    "lake" if name.startswith("lake_") else
                    "river" if name.startswith("river_") else "land")
              for pid, (_, name) in info.items()}

    bbox = {}
    for pid in set(p for _, a, b in PAIRS for p in (a, b)):
        ys, xs = np.nonzero(gid == pid)
        if len(ys):
            bbox[pid] = (int(ys.min()), int(ys.max()), int(xs.min()), int(xs.max()))

    rows_n = (len(PAIRS) + COLS - 1) // COLS
    sheet = Image.new("RGB", (COLS * CELL_W, rows_n * CELL_H), (32, 32, 36))

    for i, (tag, a, b) in enumerate(PAIRS):
        ba, bb = bbox.get(a), bbox.get(b)
        if ba is None or bb is None:
            continue
        y0 = max(0, min(ba[0], bb[0]) - MARGIN)
        y1 = min(H, max(ba[1], bb[1]) + MARGIN + 1)
        x0 = max(0, min(ba[2], bb[2]) - MARGIN)
        x1 = min(W, max(ba[3], bb[3]) + MARGIN + 1)
        gcrop = gid[y0:y1, x0:x1].copy()
        gh, gw = gcrop.shape

        gh, gw = gcrop.shape
        sea = np.isin(gcrop, [pid for pid, c in id2cls.items() if c == "sea"])
        lake = np.isin(gcrop, [pid for pid, c in id2cls.items() if c == "lake"])
        river = np.isin(gcrop, [pid for pid, c in id2cls.items() if c == "river"])
        ma = gcrop == a
        mb = gcrop == b

        od = np.full((gh, gw, 3), 24, dtype=np.uint8)
        land = ~(sea | lake | river | ma | mb)
        od[land] = (75, 75, 78)
        od[sea & ~ma & ~mb] = (90, 140, 200)
        od[river & ~ma & ~mb] = (80, 200, 180)
        od[lake & ~ma & ~mb] = (110, 200, 220)
        od[ma] = (235, 40, 40)
        od[mb] = (40, 80, 235)
        overlay = Image.fromarray(od)
        scale = min((CELL_W - 24) / gw, (CELL_H - 40) / gh)
        nw, nh = max(1, int(gw * scale)), max(1, int(gh * scale))
        overlay = overlay.resize((nw, nh), Image.NEAREST)

        r, c = divmod(i, COLS)
        ox = c * CELL_W + (CELL_W - nw) // 2
        oy = r * CELL_H + 30 + (CELL_H - 30 - nh) // 2
        sheet.paste(overlay, (ox, oy))
        # 图例/标签
        from PIL import ImageDraw
        sd = ImageDraw.Draw(sheet)
        sd.text((c * CELL_W + 8, r * CELL_H + 6),
                f"{tag}  {a}-{b}  ({x1-x0}x{y1-y0}px)",
                fill=(245, 245, 245))

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    sheet.save(out_path)
    print(f"已输出: {out_path} ({sheet.width}x{sheet.height})")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else \
        os.path.normpath(os.path.join(HERE, "..", ".workbuddy", "adjacency_review_sheet.png"))
    main(out)
