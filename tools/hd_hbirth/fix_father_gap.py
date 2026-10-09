# -*- coding: utf-8 -*-
"""修正 history 中父亲与儿子年龄差不足 18 岁的情况：把父亲生年提前，使父亲至少比每个儿子大 18 岁。

- 只看儿子（female != yes），用户 2026-10-09 裁决；女儿不参与计算。
- 同人异 ID（docs/人物审查/同一人物多ID.csv）被误连成父子的跳过。
- 父亲提前后可能与祖父冲突，循环处理直到全部满足。
- 只改出生日期块的日期键，保留月日（2 月 29 日改 28 日）；修改前文件备份到
  docs/人物审查/修改前备份/<时间>_父子年龄差前/，改动清单写入 docs/人物审查/父子年龄差修正.csv。

用法（mod 根目录）：python -I tools/hd_hbirth/fix_father_gap.py [--dry]
"""
import csv
import os
import re
import shutil
import sys
import time

MOD = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HC = os.path.join(MOD, 'history/characters')
GAP = 18
MIN_YEAR = -9999  # history 本已使用公元前日期（如 00_liangzhou 的 -110.1.1），允许父亲提前到公元前
DRY = '--dry' in sys.argv

ID_RE = re.compile(r'(?m)^([A-Za-z0-9_\.]+)\s*=\s*\{')
BIRTH_RE = re.compile(r'(-?\d+)\.(\d+)\.(\d+)(\s*=\s*\{\s*birth\s*=\s*yes)')


def strip_comments(s):
    return re.sub(r'#[^\n]*', lambda m: ' ' * len(m.group(0)), s)


def block_end(s, start):
    """start 指向 '{' 之后；返回匹配 '}' 的位置（s 已去注释、去字符串）。"""
    d = 1
    for i in range(start, len(s)):
        ch = s[i]
        if ch == '{':
            d += 1
        elif ch == '}':
            d -= 1
            if d == 0:
                return i
    return len(s)


files = {}
chars = {}  # id -> dict(file, span, birth, birth_span, father, female)
for f in sorted(os.listdir(HC)):
    if not f.endswith('.txt'):
        continue
    raw = open(os.path.join(HC, f), 'rb').read()
    text = raw.decode('utf-8-sig')
    files[f] = dict(bom=raw.startswith(b'\xef\xbb\xbf'), text=text)
    clean = re.sub(r'"[^"\n]*"', lambda m: '"' + ' ' * (len(m.group(0)) - 2) + '"', strip_comments(text))
    pos = 0
    while True:
        m = ID_RE.search(clean, pos)
        if not m:
            break
        end = block_end(clean, m.end())
        body = clean[m.end():end]
        cid = m.group(1)
        c = dict(file=f, birth=None, bspan=None, father=None, female=False)
        b = BIRTH_RE.search(body)
        if b:
            c['birth'] = tuple(int(x) for x in b.groups()[:3])
            c['bspan'] = (m.end() + b.start(), m.end() + b.start(3) + len(b.group(3)))
        fm = re.search(r'(?m)^\s*father\s*=\s*"?([A-Za-z0-9_\.]+)', text[m.end():end])
        if fm:
            c['father'] = fm.group(1)
        c['female'] = bool(re.search(r'(?m)^\s*female\s*=\s*yes', body))
        chars[cid] = c  # 同 ID 多次定义时后加载者生效
        pos = end + 1

alias = set()
for r in csv.DictReader(open(os.path.join(MOD, 'docs/人物审查/同一人物多ID.csv'), encoding='utf-8-sig')):
    alias.add((r['ID_A'], r['ID_B']))
    alias.add((r['ID_B'], r['ID_A']))


def latest_allowed(son_birth):
    y, m, d = son_birth
    return (y - GAP, m, d)


orig = {cid: c['birth'] for cid, c in chars.items()}
changed = {}
unreachable = set()
for _ in range(50):
    need = {}
    for cid, c in chars.items():
        f = c['father']
        if c['female'] or not f or f not in chars or (cid, f) in alias:
            continue
        fb, sb = chars[f]['birth'], c['birth']
        if not fb or not sb:
            continue
        lim = latest_allowed(sb)
        if lim[0] < MIN_YEAR:
            lim = (MIN_YEAR, 1, 1)
            if fb <= lim:
                continue
            unreachable.add((f, cid))
        if fb > lim:
            need[f] = min(need.get(f, lim), lim)
    if not need:
        break
    for f, lim in need.items():
        y, m, d = chars[f]['birth']
        new = (lim[0], m, min(d, 28) if m == 2 else d)
        if new > lim:
            new = (lim[0] - 1, new[1], new[2]) if lim[0] > MIN_YEAR else lim
        chars[f]['birth'] = new
        changed[f] = new
else:
    sys.exit('未收敛')

print('fathers changed', len(changed)); print('unreachable', sorted(unreachable))
if DRY:
    sys.exit(0)

stamp = time.strftime('%Y%m%d_%H%M%S')
bak = os.path.join(MOD, 'docs/人物审查/修改前备份', f'{stamp}_父子年龄差前')
os.makedirs(bak, exist_ok=True)
by_file = {}
for f, new in changed.items():
    by_file.setdefault(chars[f]['file'], []).append(f)
for fn, ids in by_file.items():
    shutil.copy2(os.path.join(HC, fn), os.path.join(bak, fn))
    text = files[fn]['text']
    for cid in sorted(ids, key=lambda i: chars[i]['bspan'][0], reverse=True):
        a, b = chars[cid]['bspan']
        y, m, d = chars[cid]['birth']
        text = text[:a] + f'{y}.{m}.{d}' + text[b:]
    with open(os.path.join(HC, fn), 'wb') as out:
        out.write((b'\xef\xbb\xbf' if files[fn]['bom'] else b'') + text.encode('utf-8'))

with open(os.path.join(MOD, 'docs/人物审查/父子年龄差修正.csv'), 'w', encoding='utf-8-sig', newline='') as out:
    w = csv.writer(out)
    w.writerow(['父亲ID', '原生年', '新生年', '提前年数', '原184开局在世', '新184开局在世', '文件'])
    for f in sorted(changed):
        o, n = orig[f], changed[f]
        w.writerow([f, '.'.join(map(str, o)), '.'.join(map(str, n)), o[0] - n[0],
                    '是' if o <= (184, 1, 1) else '', '是' if n <= (184, 1, 1) else '', chars[f]['file']])
print('files', len(by_file), 'backup', bak)
print('unreachable (father,son) at year 1:', sorted(unreachable))
