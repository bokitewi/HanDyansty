"""python deploy.py <stage> <backup_dir> [--apply]  : back up current HanJIn_Clothes files, then copy staged meshes in."""
import json, os, shutil, sys, hashlib
stage, bdir = sys.argv[1], sys.argv[2]
apply = "--apply" in sys.argv
CL = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_headgear"
rep = json.load(open(os.path.join(stage, "report.json"), encoding="utf-8"))
plan = []
for k, v in rep.items():
    if not v["stats"]:
        continue
    folder, sex = k.split("|")
    for fn in (f"{sex}_headgear_{folder}.mesh", f"{sex}_headgear_{folder}_bs_fat.mesh"):
        src = os.path.join(stage, folder, fn)
        dst = os.path.join(CL, folder, fn)
        if not os.path.exists(src):
            continue
        assert os.path.exists(dst), dst
        plan.append((src, dst, os.path.join(bdir, folder, fn)))
print(len(plan), "files")
if apply:
    for src, dst, bk in plan:
        if not os.path.exists(bk):
            os.makedirs(os.path.dirname(bk), exist_ok=True)
            shutil.copy2(dst, bk)
    for src, dst, bk in plan:
        shutil.copyfile(src, dst)
    bad = [d for s, d, b in plan if hashlib.md5(open(s, "rb").read()).digest() != hashlib.md5(open(d, "rb").read()).digest()]
    print("copied", len(plan), "mismatch", len(bad))
