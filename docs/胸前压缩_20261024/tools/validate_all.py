"""Structural validation of staged meshes against the originals (same checks as 10-22 validate_stage.py, any garment).
python validate_all.py <stage_root>      (stage_root/<garment>/*.mesh, originals under HanJIn_Clothes m_clothes/<garment>)
"""
import os
import sys

sys.path.insert(0, r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\服装穿模审计_20261022\tools")
import numpy as np  # noqa: E402

from pdxlib import pdx_data  # noqa: E402

# 输入必须是未压缩的原文件：HanJIn_Clothes 里现在已是压缩后的版本，默认读备份目录，防止二次压缩/拿错基准
BASE = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty\docs\胸前压缩_备份_20261024"


def shapes(root):
    return {s.tag: s for o in root.iter("object") for s in o if s.find("mesh") is not None}


def check(src, dst):
    bad = []
    a, b = pdx_data.read_meshfile(src), pdx_data.read_meshfile(dst)
    sa, sb = shapes(a), shapes(b)
    if list(sa) != list(sb):
        return ["shape list differs"]
    for k in sa:
        ma, mb = sa[k].find("mesh"), sb[k].find("mesh")
        if set(ma.attrib) != set(mb.attrib):
            bad.append("attr set %s" % k[-30:])
        for key in ma.attrib:
            va, vb = ma.attrib[key], mb.attrib[key]
            if len(va) != len(vb):
                bad.append("LEN %s %s" % (k[-30:], key))
            if key in ("p", "n", "ta") and not np.isfinite(np.array(vb, dtype=float)).all():
                bad.append("NAN %s %s" % (k[-30:], key))
            if key in ("u0", "u1", "u2", "tri") and list(va) != list(vb):
                bad.append("CHANGED %s %s" % (k[-30:], key))
        ka, kb = ma.find("skin"), mb.find("skin")
        if (ka is None) != (kb is None):
            bad.append("SKIN presence %s" % k[-30:])
        elif ka is not None and (list(ka.attrib["ix"]) != list(kb.attrib["ix"]) or list(ka.attrib["w"]) != list(kb.attrib["w"])):
            bad.append("SKIN changed %s" % k[-30:])
        if "n" in mb.attrib:
            nb = np.array(mb.attrib["n"], dtype=float).reshape(-1, 3)
            ln = np.linalg.norm(nb, axis=1)
            if len(ln) and (ln.min() < 0.9 or ln.max() > 1.1):
                bad.append("NORMAL len %s %.2f %.2f" % (k[-30:], ln.min(), ln.max()))
        pb = np.array(mb.attrib["p"], dtype=float).reshape(-1, 3)
        ab = mb.find("aabb")
        if len(pb) and not (np.allclose(ab.attrib["min"], pb.min(0), atol=1e-3) and np.allclose(ab.attrib["max"], pb.max(0), atol=1e-3)):
            bad.append("AABB %s" % k[-30:])
        # material / other children untouched
        for ch_a, ch_b in zip(list(ma), list(mb)):
            if ch_a.tag != ch_b.tag:
                bad.append("child order %s" % k[-30:])
            elif ch_a.tag == "material" and dict(ch_a.attrib) != dict(ch_b.attrib):
                bad.append("material %s" % k[-30:])
    return bad


def main():
    root = sys.argv[1]
    nfiles = nbad = 0
    for g in sorted(os.listdir(root)):
        gd = os.path.join(root, g)
        if not os.path.isdir(gd):
            continue
        for f in sorted(os.listdir(gd)):
            if not f.endswith(".mesh"):
                continue
            nfiles += 1
            bad = check(os.path.join(BASE, g, f), os.path.join(gd, f))
            if bad:
                nbad += 1
                print("BAD", g, f, bad[:5])
    print("files", nfiles, "with problems", nbad)


if __name__ == "__main__":
    main()
