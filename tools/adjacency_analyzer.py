#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
adjacency_analyzer.py — 只读分析工具（不改动任何模组文件）

用途：给定若干 "地块-地块" 连接对（可通行海峡/河渡候选），从 provinces.png +
definition.csv 中解析出每对之间隔开的海省/河省，生成 CK3 adjacencies.csv 候选行：

    From;To;Type;Through;start_x;start_y;stop_x;stop_y;Comment

方法（稳健边界法）：
  1. 取两省包围盒区域；
  2. 用距离变换求两省"相对最近边界点"（A 上离 B 最近的点、B 上离 A 最近的点）；
  3. 采样两点间像素带，取离开 A 后的第一块水域省作为 Through；
  4. 用"水域省是否同时 8-邻接两省"交叉验证。

约定（与模组现有 adjacencies.csv 及 vanilla 一致）：
  - 水域省名 sea_*  -> Type = sea
  - 水域省名 river_* -> Type = river_large（vanilla 仅 sea / river_large 两种）
  - 坐标列一律 -1（vanilla Tumasik-Johor 等条目同样省略坐标）
  - 三元组行解释为：首省分别连接其余各省（hub 模式）；交叉对仅作信息参考

输出：
  - 控制台报告
  - .workbuddy/adjacency_report.txt
  - .workbuddy/adjacencies_new_rows.csv（待人工确认后并入 adjacencies.csv）
"""
import os
import math
import numpy as np
from PIL import Image
from scipy.ndimage import distance_transform_edt

HERE = os.path.dirname(os.path.abspath(__file__))
MAP_DATA = os.path.normpath(os.path.join(HERE, "..", "map_data"))
DEF_CSV = os.path.join(MAP_DATA, "definition.csv")
PROV_PNG = os.path.join(MAP_DATA, "provinces.png")
OUT_DIR = os.path.normpath(os.path.join(HERE, "..", ".workbuddy"))
REPORT_TXT = os.path.join(OUT_DIR, "adjacency_report.txt")
NEW_ROWS_CSV = os.path.join(OUT_DIR, "adjacencies_new_rows.csv")

# ---------------------------------------------------------------- 连接数据
# 每行 = 一个连接组；首元素为 hub，依次连接组内其余省。
CONNECTIONS = [
    [6833, 6373],
    [6157, 6070],
    [6157, 5555, 6409],
    [6833, 5763],
    [166, 5679],
    [166, 5607],
    [6549, 6434],
    [6269, 5996],
    [4986, 5672],
    [6827, 6384],
    [4887, 4884],
    [4806, 6084],
    [6311, 5811],
    [6311, 4835],
    [5647, 1916],
    [1812, 1867],
    [1788, 1767],
    [3096, 3222],
    [3226, 5350],
    [5378, 5352],
    [5360, 5380],
    [5314, 5332],
    [3701, 7006],
    [5399, 3319],
    [3928, 4051],
    [4299, 3104],
    [3256, 3726],
    [3315, 3185],
    [3695, 3689],
    [6626, 4528],
    [6769, 7022],
    [632, 645],
    [591, 572],
    [4542, 2248],
    [1224, 2538],
    [4179, 4126],
    [3923, 2979],
    [1196, 4032],
    [1210, 1208],
    [671, 1152, 1177],
    [4433, 248],
    [706, 368],
    [6907, 6996],
    [22, 4339],
    [5041, 38],
    [34, 84],
    [647, 1091],
    [647, 761],
    [1648, 1613, 746],
    [1676, 1686],
    [4575, 4135],
    [7035, 4354],
    [2332, 4054],
    [3377, 4027],
    [845, 982],
    [932, 851],
    [909, 854],
    [899, 860],
    [891, 877],
    [998, 1350],
    [146, 7026],
    [1217, 499],
    [6972, 2538],
    [1241, 6966],
    [3777, 3467],
    [5015, 6387, 3750],
    [6533, 5985],
    [6296, 5079],
    [6199, 6586],
    [5624, 6291],
]

MARGIN = 80  # 包围盒外扩像素


# ---------------------------------------------------------------- 数据加载
def load_definition():
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


def classify(name):
    if name.startswith("sea_"):
        return "sea"
    if name.startswith("lake_"):
        return "lake"
    if name.startswith("river_"):
        return "river"
    return "land"


WATER_CLS = ("sea", "lake", "river")


def load_id_array(color2id):
    img = Image.open(PROV_PNG).convert("RGB")
    a = np.asarray(img)
    keys = (a[..., 0].astype(np.uint32) << 16) | \
           (a[..., 1].astype(np.uint32) << 8) | \
           a[..., 2].astype(np.uint32)
    del a, img
    # 颜色 -> id（未定义颜色 = -1）
    n = max(color2id) + 1
    lut = np.full(n, -1, dtype=np.int32)
    for k, pid in color2id.items():
        lut[k] = pid
    gid = lut[keys]
    return gid


def compute_stats(gid, max_id):
    """单次分块扫描：各省 质心、包围盒、像素数"""
    H, W = gid.shape
    n = max_id + 1
    cnt = np.zeros(n, dtype=np.int64)
    sum_y = np.zeros(n, dtype=np.float64)
    sum_x = np.zeros(n, dtype=np.float64)
    miny = np.full(n, H, dtype=np.int64)
    maxy = np.full(n, -1, dtype=np.int64)
    minx = np.full(n, W, dtype=np.int64)
    maxx = np.full(n, -1, dtype=np.int64)
    CH = 1024
    for y0 in range(0, H, CH):
        y1 = min(y0 + CH, H)
        ck = gid[y0:y1]
        valid = ck >= 0
        if not valid.any():
            continue
        ys, xs = np.indices(ck.shape)
        ia = ck[valid]
        ly = (ys[valid] + y0).astype(np.int64)
        lx = xs[valid].astype(np.int64)
        cnt += np.bincount(ia, minlength=n)
        sum_y += np.bincount(ia, weights=ly.astype(np.float64), minlength=n)
        sum_x += np.bincount(ia, weights=lx.astype(np.float64), minlength=n)
        # 每块内按 id 聚合 min/max（ufunc.at 就地更新）
        np.minimum.at(miny, ia, ly)
        np.maximum.at(maxy, ia, ly)
        np.minimum.at(minx, ia, lx)
        np.maximum.at(maxx, ia, lx)
    with np.errstate(invalid="ignore", divide="ignore"):
        cx = np.where(cnt > 0, sum_x / cnt, -1.0)
        cy = np.where(cnt > 0, sum_y / cnt, -1.0)
    return cx, cy, cnt, miny, maxy, minx, maxx


def sample_segment(crop, x0, y0, x1, y1, step=1.0):
    """在局部裁剪图上采样线段，返回 id 序列（越界=-2）"""
    H, W = crop.shape
    d = math.hypot(x1 - x0, y1 - y0)
    n = max(2, int(d / step))
    seq = []
    for i in range(n + 1):
        t = i / n
        x = int(round(x0 + (x1 - x0) * t))
        y = int(round(y0 + (y1 - y0) * t))
        if 0 <= x < W and 0 <= y < H:
            seq.append(int(crop[y, x]))
        else:
            seq.append(-2)
    return seq


def adjacent_water_ids(crop, mask, is_water):
    """返回与 mask 8-邻接的水域省 id 集合"""
    pad = np.pad(mask.astype(np.uint8), 1)
    from scipy.ndimage import binary_dilation
    dil = binary_dilation(mask, structure=np.ones((3, 3), dtype=bool))
    contact = dil & is_water
    if not contact.any():
        return {}
    ids, counts = np.unique(crop[contact], return_counts=True)
    return {int(i): int(c) for i, c in zip(ids, counts) if i >= 0}


def analyze_pair(a, b, gid, stats, id2cls, id2name):
    cx, cy, cnt, miny, maxy, minx, maxx = stats
    if a not in id2cls or b not in id2cls:
        return ("MISSING", f"id 不存在于 definition.csv: {a} 或 {b}", None, None, 0)
    if cnt[a] == 0 or cnt[b] == 0:
        return ("NOT_ON_MAP", f"省份 {a}/{b} 在 provinces.png 中无像素", None, None, 0)
    if id2cls[a] != "land":
        return ("NOT_LAND", f"{a} 是 {id2cls[a]} 省，不是地块", None, None, 0)
    if id2cls[b] != "land":
        return ("NOT_LAND", f"{b} 是 {id2cls[b]} 省，不是地块", None, None, 0)

    # ---- 包围盒裁剪
    y0 = max(0, min(miny[a], miny[b]) - MARGIN)
    y1 = min(gid.shape[0], max(maxy[a], maxy[b]) + MARGIN + 1)
    x0 = max(0, min(minx[a], minx[b]) - MARGIN)
    x1 = min(gid.shape[1], max(maxx[a], maxx[b]) + MARGIN + 1)
    crop = gid[y0:y1, x0:x1]
    CH, CW = crop.shape
    maskA = crop == a
    maskB = crop == b

    is_water = np.zeros(crop.shape, dtype=bool)
    for pid, cls in id2cls.items():
        if cls in WATER_CLS:
            is_water |= crop == pid

    # ---- 距离变换求相对最近边界点
    distB = distance_transform_edt(~maskA)      # 到 A 的距离
    distA = distance_transform_edt(~maskB)      # 到 B 的距离
    db = np.where(maskA, distB, np.inf)
    da = np.where(maskB, distA, np.inf)
    # A 上离 B 最近的点、B 上离 A 最近的点
    iy, ix = np.unravel_index(np.argmin(db), db.shape)
    yA, xA = int(iy), int(ix)
    iy, ix = np.unravel_index(np.argmin(da), da.shape)
    yB, xB = int(iy), int(ix)

    # ---- 采样间隙
    seq = sample_segment(crop, xA, yA, xB, yB, step=1.0)
    # 去掉首尾连续 A/B
    i = 0
    while i < len(seq) and seq[i] == a:
        i += 1
    j = len(seq) - 1
    while j >= i and seq[j] == b:
        j -= 1
    gap = seq[i:j + 1]

    gap_land = [p for p in gap if p in id2cls and id2cls[p] == "land" and p not in (a, b)]
    gap_water = [p for p in gap if p in id2cls and id2cls[p] != "land"]
    dist_px = math.hypot(xB - xA, yB - yA)

    # ---- 交叉验证：同时接触两省的水域
    wA = adjacent_water_ids(crop, maskA, is_water)
    wB = adjacent_water_ids(crop, maskB, is_water)
    shared = {k: wA[k] + wB.get(k, 0) for k in wA.keys() & wB.keys()}

    def ptype_of(w):
        return "sea" if id2cls[w] in ("sea", "lake") else "river_large"

    def kind(w):
        return {"sea": "海", "lake": "湖", "river": "河"}.get(id2cls[w], "?")

    if not gap:
        if shared:
            through = max(shared, key=shared.get)
            note = (f"两省边界紧贴但共享水域 {through}({id2name[through]}, {kind(through)})，"
                    f"按海峡处理（最近距 {dist_px:.0f}px）")
            return ("OK", note, through, ptype_of(through), dist_px)
        return ("LAND_TOUCH", f"两省边界紧贴无间隙（最近距 {dist_px:.0f}px）", None, None, dist_px)

    # 首选：同时接触两省的水域（最可靠的海峡标识）
    if shared:
        cands = [w for w in shared if w in gap_water]
        if not cands:
            cands = list(shared)
        through = max(cands, key=lambda w: shared[w] + (100000 if w in gap_water else 0))
        ptype = ptype_of(through)
        note = (f"最近边界距 {dist_px:.0f}px；共享水域 {list(shared)}；"
                f"选中 Through={through}({id2name[through]}, {kind(through)})")
        if gap_land:
            note += f"；⚠ 间隙含其他陆地省 {gap_land[:8]}（可能需拆分两段渡口）"
        note += "；√ 同时接触两省"
        return ("OK", note, through, ptype, dist_px)

    # 无共享水域，仅间隙水域（可信度较低）
    if gap_water:
        mid_prov = gap[len(gap) // 2] if gap else -1
        through = mid_prov if mid_prov in gap_water else gap_water[0]
        ptype = ptype_of(through)
        note = (f"最近边界距 {dist_px:.0f}px；间隙水域 {gap_water[:8]}；"
                f"选中 Through={through}({id2name[through]}, {kind(through)})")
        if gap_land:
            note += f"；⚠ 间隙含其他陆地省 {gap_land[:8]}"
        note += "；⚠ 该水域未同时接触两省，需目测确认"
        return ("OK_FALLBACK", note, through, ptype, dist_px)

    if gap_land:
        return ("LAND_TOUCH", f"两省由陆地连通（间隙含陆省 {gap_land[:10]}）", None, None, dist_px)
    return ("NO_WATER", f"间隙中既无水域也无陆地标识（最近距 {dist_px:.0f}px），需人工确认",
            None, None, dist_px)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    info = load_definition()
    color2id = {}
    id2cls = {}
    id2name = {}
    max_id = 0
    for pid, (rgb, name) in info.items():
        key = (rgb[0] << 16) | (rgb[1] << 8) | rgb[2]
        color2id[key] = pid
        id2cls[pid] = classify(name)
        id2name[pid] = name
        max_id = max(max_id, pid)

    print("加载 provinces.png ...")
    gid = load_id_array(color2id)
    H, W = gid.shape
    print(f"地图尺寸: {W}x{H}")
    stats = compute_stats(gid, max_id)
    print("统计完成")

    lines = []
    rows = []
    pending = []

    pairs = []
    for grp in CONNECTIONS:
        hub = grp[0]
        for other in grp[1:]:
            pairs.append((hub, other, grp))

    seen = set()
    for a, b, grp in pairs:
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        status, note, through, ptype, dpx = analyze_pair(
            a, b, gid, stats, id2cls, id2name)
        if status == "OK":
            rows.append((a, b, ptype, through, f"{a}-{b}"))
            flag = "OK"
        elif status == "OK_FALLBACK":
            rows.append((a, b, ptype, through, f"{a}-{b}"))
            flag = "OK*回退"
        elif status == "LAND_TOUCH":
            pending.append((a, b, status, note))
            flag = "REVIEW-陆地连通"
        elif status == "NO_WATER":
            pending.append((a, b, status, note))
            flag = "REVIEW"
        else:
            pending.append((a, b, status, note))
            flag = f"REVIEW-{status}"
        grp_txt = ",".join(map(str, grp))
        lines.append(f"{a:>6}-{b:<6} [{grp_txt}] {flag:>14} | {note}")

    # 三元组交叉对信息（不产出）
    for grp in CONNECTIONS:
        if len(grp) == 3:
            u, v = grp[1], grp[2]
            status, note, through, ptype, dpx = analyze_pair(
                u, v, gid, stats, id2cls, id2name)
            lines.append(f"  INFO 交叉对 {u}-{v}（未产出）: {status} | {note}")

    rows.sort(key=lambda r: (r[0], r[1]))

    out_lines = []
    for a, b, ptype, through, comment in rows:
        out_lines.append(f"{a};{b};{ptype};{through};-1;-1;-1;-1;{comment}")

    report = []
    report.append("=" * 80)
    report.append("adjacency_analyzer 只读分析报告（稳健边界法）")
    report.append(f"地图: {W}x{H} | 省份数: {len(info)} | 连接组: {len(CONNECTIONS)} | 产出连接: {len(rows)}")
    report.append("=" * 80)
    report.append("\n[逐条分析]")
    report.extend(lines)
    report.append("\n[待人工确认]")
    if pending:
        for a, b, status, note in pending:
            report.append(f"  {a}-{b}: {status} | {note}")
    else:
        report.append("  （无）")
    report.append("\n[候选新增行]")
    report.extend(out_lines)
    report.append("\n[提示]")
    report.append("  - 三元组按 hub 模式解释（首省连接其余各省）；交叉对仅作参考。")
    report.append("  - 坐标列一律 -1（与模组现有条目及 vanilla Tumasik-Johor 一致）。")
    report.append("  - 'OK*共享水域' = 间隙采样未见水，但水域省同时接触两省，仍需目测确认。")

    txt = "\n".join(report)
    print("\n" + txt)

    with open(REPORT_TXT, "w", encoding="utf-8") as f:
        f.write(txt + "\n")
    with open(NEW_ROWS_CSV, "w", encoding="utf-8-sig", newline="") as f:
        f.write("From;To;Type;Through;start_x;start_y;stop_x;stop_y;Comment\n")
        f.write("\n".join(out_lines) + "\n")
    print(f"\n报告: {REPORT_TXT}")
    print(f"候选行: {NEW_ROWS_CSV}")


if __name__ == "__main__":
    main()
