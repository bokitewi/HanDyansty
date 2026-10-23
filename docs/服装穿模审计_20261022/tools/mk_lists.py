import glob
import os

SP = os.path.dirname(os.path.abspath(__file__))
root = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanJIn_Clothes\gfx\models\portraits\m_clothes"
fs = [f for f in glob.glob(root + "/**/m_clothes_*.mesh", recursive=True) if "_bs_" not in os.path.basename(f)]
print(len(fs))
with open(os.path.join(SP, "list_mod_clothes.txt"), "w", encoding="utf-8") as o:
    for f in sorted(fs):
        lab = os.path.basename(f)[:-5].replace("m_clothes_", "")
        o.write(lab + "|" + os.path.normpath(f) + "\n")
V = r"D:\SteamLibrary\steamapps\common\Crusader Kings III\game\gfx\models\portraits\m_clothes\tgp_chinese\war_nob_01\m_clothes_sec_tgp_chinese_war_nob_01.mesh"
hd = [l for l in open(os.path.join(SP, "list_mod_clothes.txt"), encoding="utf-8") if "xiongnu_heavy_dark" in l][0]
open(os.path.join(SP, "list_test.txt"), "w", encoding="utf-8").write("V_war_nob_01|" + V + "\n" + hd)
print(open(os.path.join(SP, "list_test.txt"), encoding="utf-8").read())
