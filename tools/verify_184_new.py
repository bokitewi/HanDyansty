import os, re, sys

base = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"

files = [
    r"history\characters\zz_hd_don_quijote.txt",
    r"common\dynasties\zz_hd_184_new_dynasties.txt",
    r"common\nicknames\zz_hd_184_nicknames.txt",
    r"common\on_action\zz_hd_184_new_setup.txt",
    r"localization\simp_chinese\zz_hd_184_new_l_simp_chinese.yml",
    r"localization\english\zz_hd_184_new_l_english.yml",
    r"common\landed_titles\zz_hd_184_famous_noble_families.txt",
    r"history\titles\zz_hd_184_famous_noble_families.txt",
    r"history\characters\east_asian_bingzhou_180_200.txt",
    r"history\characters\east_asian_han_180_200.txt",
]

def read(p):
    with open(p, "rb") as fh:
        raw = fh.read()
    return raw

print("=== BOM / encoding check ===")
for f in files:
    p = os.path.join(base, f)
    raw = read(p)
    has_bom = raw.startswith(b"\xef\xbb\xbf")
    try:
        raw.decode("utf-8")
        valid = True
    except UnicodeDecodeError:
        valid = False
    print(("OK " if valid else "BAD-ENC ") + ("BOM " if has_bom else "noBOM ") + f)

print()
print("=== Bracket balance check ===")
def balance(p):
    raw = read(p)
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    text = raw.decode("utf-8")
    text = re.sub(r"#[^\n]*", "", text)
    text = re.sub(r'"[^"]*"', '""', text)
    bal = 0
    for ch in text:
        if ch == "{":
            bal += 1
        elif ch == "}":
            bal -= 1
            if bal < 0:
                return "NEGATIVE"
    return bal

for f in files:
    p = os.path.join(base, f)
    b = balance(p)
    flag = "OK" if b == 0 else "FAIL"
    print(flag + " (bal=%s)  %s" % (b, f))

print()
print("=== Reference consistency ===")
checks = [
    ("dynasty_hd_quijano", r"common\dynasties\zz_hd_184_new_dynasties.txt"),
    ("alonso_quijano", r"history\characters\zz_hd_don_quijote.txt"),
    ("character:alonso_quijano", r"common\on_action\zz_hd_184_new_setup.txt"),
    ("character:bokitewi", r"common\on_action\zz_hd_184_new_setup.txt"),
]
for key, f in checks:
    p = os.path.join(base, f)
    txt = open(p, encoding="utf-8-sig").read()
    print(("OK " if key in txt else "MISS ") + key + " in " + f)

print()
print("=== nickname keys cross-file ===")
nicks = ["nick_hd_don_quixote","nick_hd_wolong","nick_hd_zhonghu","nick_hd_daxianliangshi","nick_hd_digong_jiangjun","nick_hd_rengong_jiangjun"]
defn = open(os.path.join(base, r"common\nicknames\zz_hd_184_nicknames.txt"), encoding="utf-8-sig").read()
cn = open(os.path.join(base, r"localization\simp_chinese\zz_hd_184_new_l_simp_chinese.yml"), encoding="utf-8-sig").read()
en = open(os.path.join(base, r"localization\english\zz_hd_184_new_l_english.yml"), encoding="utf-8-sig").read()
oa = open(os.path.join(base, r"common\on_action\zz_hd_184_new_setup.txt"), encoding="utf-8-sig").read()
for n in nicks:
    print(n + ": defn=" + ("Y" if n in defn else "N") + " cn=" + ("Y" if n in cn else "N") + " en=" + ("Y" if n in en else "N") + " on_action=" + ("Y" if n in oa else "N"))

print()
print("=== 世家头衔 cross-file ===")
titles = ["c_hd_nf_famous_h_house_111010042002013", "c_hd_nf_famous_h_uuii_book_house_71074e5c82a2"]
lt = open(os.path.join(base, r"common\landed_titles\zz_hd_184_famous_noble_families.txt"), encoding="utf-8-sig").read()
ht = open(os.path.join(base, r"history\titles\zz_hd_184_famous_noble_families.txt"), encoding="utf-8-sig").read()
for t in titles:
    print(t + ": landed=" + ("Y" if t in lt else "N") + " hist=" + ("Y" if t in ht else "N") + " cn=" + ("Y" if t in cn else "N") + " en=" + ("Y" if t in en else "N"))
