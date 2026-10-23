import glob
import os

SP = os.path.dirname(os.path.abspath(__file__))
GM = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits\m_clothes"
mod = [l.strip() for l in open(os.path.join(SP, "list_mod_clothes.txt"), encoding="utf-8")]
van = []
want = ["tgp_chinese\\war_nob_01", "tgp_chinese\\war_02", "tgp_chinese\\nob_01", "tgp_chinese\\com_01", "ccp5\\french_war_nob_01", "fp1\\war_nob_01", "ep3\\war_nob_01", "ccp4\\war_nob_01"]
allv = [f for f in glob.glob(GM + "/**/m_clothes_*.mesh", recursive=True) if "_bs_" not in os.path.basename(f)]
print(len(allv), "vanilla clothes meshes")
for f in sorted(allv):
    low = f.lower()
    if any(w.replace("\\", "/") in low.replace("\\", "/") for w in want) and len(van) < 14:
        van.append("V_" + os.path.basename(f)[:-5].replace("m_clothes_", "")[:50] + "|" + os.path.normpath(f))
for f in sorted(allv):
    b = os.path.basename(f)
    if "_war_" in b and len(van) < 12 and not any(os.path.normpath(f) == v.split("|")[1] for v in van):
        van.append("V_" + b[:-5].replace("m_clothes_", "")[:50] + "|" + os.path.normpath(f))
open(os.path.join(SP, "list_all.txt"), "w", encoding="utf-8").write("\n".join(van + mod) + "\n")
print(len(van), "vanilla +", len(mod), "mod")
print("\n".join(v.split("|")[0] for v in van))
