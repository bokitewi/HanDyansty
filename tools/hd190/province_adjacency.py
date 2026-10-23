# -*- coding: utf-8 -*-
"""由 map_data/provinces.png 与 definition.csv 计算省份相邻关系，缓存到 tools/hd190/_adj_cache.json。
用法：python tools/hd190/province_adjacency.py <mod 根目录>
输出：{ "prov": {id: [邻省id...]}, "county": {c_xxx: [邻县...]} }（县邻接 = 任一省份像素相接，不分江河）。"""
import sys, os, re, json, glob
import numpy as np
from PIL import Image

Image.MAX_IMAGE_PIXELS = None
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import pdx


def main(root):
    im = np.asarray(Image.open(root + '/map_data/provinces.png').convert('RGB'))
    h, w, _ = im.shape
    key = (im[:, :, 0].astype(np.uint32) << 16) | (im[:, :, 1].astype(np.uint32) << 8) | im[:, :, 2].astype(np.uint32)
    pairs = set()
    for a, b in ((key[:, :-1], key[:, 1:]), (key[:-1, :], key[1:, :])):
        m = a != b
        pa = a[m]
        pb = b[m]
        lo = np.minimum(pa, pb).astype(np.uint64)
        hi = np.maximum(pa, pb).astype(np.uint64)
        code = np.unique((lo << np.uint64(32)) | hi)
        pairs.update(code.tolist())
    color2id = {}
    with open(root + '/map_data/definition.csv', encoding='utf-8-sig', errors='ignore') as f:
        for line in f:
            p = line.strip().split(';')
            if len(p) >= 4 and p[0].isdigit():
                try:
                    color2id[(int(p[1]) << 16) | (int(p[2]) << 8) | int(p[3])] = int(p[0])
                except ValueError:
                    pass
    adj = {}
    for code in pairs:
        a = color2id.get(code >> 32)
        b = color2id.get(code & 0xFFFFFFFF)
        if a is None or b is None:
            continue
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    # 县 -> 省份
    county_provs = {}
    prov2county = {}

    def walk(items, cur_c):
        for k, o, v in items:
            if not isinstance(v, list):
                continue
            if k and k.startswith('c_'):
                for bk, bo, bv in v:
                    if bk and bk.startswith('b_') and isinstance(bv, list):
                        for pk, po, pv in bv:
                            if pk == 'province' and not isinstance(pv, list) and pv.isdigit():
                                county_provs.setdefault(k, []).append(int(pv))
                                prov2county[int(pv)] = k
            else:
                walk(v, cur_c)
            if k and k.startswith('c_'):
                continue

    for f in sorted(glob.glob(root + '/common/landed_titles/*.txt')):
        walk(pdx.load(f), None)
    # 陆路相连：河流省份、湖泊当作可通过（河湖不算「隔着别人的地」），县经由连续的河/湖省份也算相邻
    water = set()
    for line in open(root + '/map_data/default.map', encoding='utf-8-sig', errors='ignore'):
        m = re.match(r'^\s*(river_provinces|lakes)\s*=\s*(RANGE|LIST)\s*\{([^}]*)\}', line)
        if not m:
            continue
        nums = [int(x) for x in m.group(3).split() if x.isdigit()]
        if m.group(2) == 'RANGE' and len(nums) == 2:
            water.update(range(nums[0], nums[1] + 1))
        else:
            water.update(nums)
    land_adj = {}
    for c, ps in county_provs.items():
        reach = set()
        for p in ps:
            for q in adj.get(p, ()):
                cq = prov2county.get(q)
                if cq and cq != c:
                    reach.add(cq)
                elif q in water:
                    # 只跨一个河/湖省份（整条江的连锁不算，否则沿江几百个县全成了相邻）
                    for r in adj.get(q, ()):
                        cr = prov2county.get(r)
                        if cr and cr != c:
                            reach.add(cr)
        land_adj[c] = sorted(reach)
    cadj = {}
    for c, ps in county_provs.items():
        s = set()
        for p in ps:
            for q in adj.get(p, ()):
                cq = prov2county.get(q)
                if cq and cq != c:
                    s.add(cq)
        cadj[c] = sorted(s)
    json.dump({'county': cadj, 'county_land': land_adj}, open(HERE + '/_adj_cache.json', 'w', encoding='utf-8'), ensure_ascii=False)
    print(len(pairs), 'province pairs;', len(cadj), 'counties')


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty')
