# -*- coding: utf-8 -*-
"""
把三国志11 的六维属性 + 生卒年，写入 mod 对应人物 history 块。

严格约束：
  - 只改 6 个属性字段值（diplomacy/martial/stewardship/intrigue/learning/prowess）
  - 只改 birth / death 日期块的【年份】，月日原样保留
  - 名字、键值、dynasty_house、culture、faith、health、trait、其他日期块一律不动
  - 换行符（CRLF/LF）、BOM 原样保留，非目标行字节级不动

匹配：仅处理「中文名在 mod 中唯一精确对应一个键值」的人物。
重名 / 找不到（含变体）一律跳过，输出未处理名单。

用法：
  python apply_ck3_stats.py           # dry-run，只打印不写文件
  python apply_ck3_stats.py --apply   # 实际写回
"""
import re, json, sys, os

BASE = "E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty/history/characters"
SG_JSON = "C:/Users/15550/Downloads/koei_san_data-main/koei_san11_ck3_characters.json"
MODMAP = "E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty/tools/mod_char_map.json"

APPLY = "--apply" in sys.argv
ATTRS = ["diplomacy", "martial", "stewardship", "intrigue", "learning", "prowess"]

chars = json.load(open(SG_JSON, encoding="utf-8"))
modmap = json.load(open(MODMAP, encoding="utf-8"))


def read_file(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return f.read().splitlines(keepends=True)


def write_file(path, lines):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        f.write("".join(lines))


def content(line):
    return line.rstrip("\r\n")


def newline_of(line):
    return line[len(line.rstrip("\r\n")):]


def get_block_bounds(lines, key):
    start = None
    for i, ln in enumerate(lines):
        if content(ln).strip().startswith(key + "=") and "{" in ln:
            start = i
            break
    if start is None:
        return None
    depth = 0
    for i in range(start, len(lines)):
        depth += content(lines[i]).count("{") - content(lines[i]).count("}")
        if depth <= 0 and i > start:
            return (start, i)
    return None


def apply_to_block(lines, bounds, data):
    start, end = bounds
    changes = []
    # 1) 属性字段
    for attr in ATTRS:
        val = data.get(attr)
        if val is None:
            continue
        for i in range(start, end + 1):
            c = content(lines[i])
            m = re.match(r"^(\s*)(" + attr + r")(\s*=\s*\")[^\"]*(\".*)$", c)
            if m:
                new_c = m.group(1) + m.group(2) + m.group(3) + str(val) + m.group(4)
                if new_c != c:
                    changes.append((attr, c.strip(), new_c.strip()))
                    lines[i] = new_c + newline_of(lines[i])
                break
    # 2) birth / death 年份
    for marker, year_field in [("birth", "birth"), ("death", "death")]:
        year = data.get(year_field)
        if year is None:
            continue
        for i in range(start, end + 1):
            c = content(lines[i])
            if re.search(r"\b" + marker + r"\s*=\s*yes", c):
                for j in range(i, start - 1, -1):
                    cj = content(lines[j])
                    m = re.match(r"^(\s*)(\d+)(\.\d+\.\d+\s*=\s*\{)", cj)
                    if m:
                        if int(m.group(2)) != int(year):
                            new_c = m.group(1) + str(year) + m.group(3)
                            changes.append((marker, cj.strip(), new_c.strip()))
                            lines[j] = new_c + newline_of(lines[j])
                        break
                break
    return changes


file_targets = {}
skipped = []
for c in chars:
    n = c["name"]
    if n not in modmap or len(modmap[n]) != 1:
        skipped.append((n, "重名" if n in modmap else "找不到"))
        continue
    key, fn = modmap[n][0]
    file_targets.setdefault(fn, []).append((key, c))

total_changes = 0
changed_chars = 0
per_file_changes = {}

for fn in sorted(file_targets):
    path = os.path.join(BASE, fn)
    lines = read_file(path)
    orig = "".join(lines)
    file_change_cnt = 0
    for key, data in file_targets[fn]:
        bounds = get_block_bounds(lines, key)
        if bounds is None:
            print("!! 块未找到", key, fn)
            continue
        ch = apply_to_block(lines, bounds, data)
        if ch:
            changed_chars += 1
            total_changes += len(ch)
            file_change_cnt += len(ch)
            if not APPLY:
                print(f"[{fn}] {key}({data['name']}):")
                for kind, old, new in ch:
                    print(f"    {kind}: {old}  ->  {new}")
    per_file_changes[fn] = file_change_cnt
    if APPLY and "".join(lines) != orig:
        write_file(path, lines)

print("\n===== 汇总 =====")
print("唯一匹配可处理:", sum(len(v) for v in file_targets.values()), "人")
print("实际有变化:", changed_chars, "人, 共", total_changes, "处修改")
for fn, cnt in sorted(per_file_changes.items()):
    if cnt:
        print(f"  {fn}: {cnt} 处")
print("跳过(未处理):", len(skipped), "人")
print("重名:", [n for n, r in skipped if r == "重名"])
print("找不到:", [n for n, r in skipped if r == "找不到"])
if not APPLY:
    print("\n[DRY-RUN] 未写文件。确认无误后加 --apply 执行。")
else:
    print("\n[已写入] 修改已保存。")
