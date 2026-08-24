# -*- coding: utf-8 -*-
"""
阶段B：根据 placement_final.csv，在对应 history/provinces 文件的省份块内插入
    special_building = <TK键>
写在开括号行之后（与现有 1172/1961 同风格，tab 缩进）。
- 写入前备份原文件为 .bak
- 若目标省份块已含 special_building 则跳过（防重）
"""
import csv, re, os, shutil

MOD = r"E:\documents\Paradox Interactive\Crusader Kings III\mod\HanDyansty"
PROVDIR = os.path.join(MOD, "history", "provinces")
FIN = os.path.join(MOD, ".workbuddy", "placement_final.csv")

rows = list(csv.DictReader(open(FIN, encoding="utf-8-sig")))
by_file = {}
for r in rows:
    by_file.setdefault(r["文件"], {})[r["province_id"]] = r["TK键"]
print("待处理文件:", {f: len(d) for f, d in by_file.items()})

OPEN_RE = re.compile(r"^(\d+)\s*=\s*\{")
INSERT_LINE = "\tspecial_building = %s\n"

total_inserted = 0
total_skipped = 0

for fn, pid2key in by_file.items():
    fp = os.path.join(PROVDIR, fn)
    bak = fp + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(fp, bak)
        print("  备份:", bak)
    lines = open(fp, encoding="utf-8", errors="ignore").read().split("\n")
    out = []
    done = set()
    inserted = skipped = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        out.append(line)
        m = OPEN_RE.match(line)
        if m and m.group(1) in pid2key and m.group(1) not in done:
            pid = m.group(1)
            # 从本行起向下扫描当前块，判断是否已含 special_building
            depth = line.count("{") - line.count("}")
            has_sb = "special_building" in line
            j = i + 1
            while j < len(lines) and depth > 0:
                nl = lines[j]
                if "special_building" in nl:
                    has_sb = True
                depth += nl.count("{") - nl.count("}")
                j += 1
            if has_sb:
                skipped += 1
            else:
                out.append(INSERT_LINE % pid2key[pid])
                inserted += 1
            done.add(pid)
        i += 1
    open(fp, "w", encoding="utf-8").write("\n".join(out))
    total_inserted += inserted
    total_skipped += skipped
    print(f"  {fn}: 插入 {inserted}, 跳过(已存在) {skipped}")

print("\n=== 阶段B 完成 ===")
print("总插入:", total_inserted, " 总跳过:", total_skipped)
