# -*- coding: utf-8 -*-
"""文本重写收尾：全局复核
1) 被删除的本地化键：按隐式命名（trait_X_desc、X_modifier、catalyst 等）推出词干，检查词干是否仍是脚本对象/引用。
2) 所有与备份不同的中文本地化文件：BOM、首行、键行格式、$ref$、格式码配对。
3) 所有与备份不同的脚本：新增行中引用的本地化键是否存在（中文 mod 或原版）。
"""
import difflib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import text_rewrite_check as C  # noqa: E402

MOD, BACKUP, BS = C.MOD, C.BACKUP, chr(92)
cur_all = C.walk_loc(MOD)
bak_all = C.walk_loc(BACKUP)
cur_map, bak_map = {}, {}
for d, m in ((cur_all, cur_map), (bak_all, bak_map)):
    for f in sorted(d, key=lambda x: ('replace/' in x, x)):
        m.update(d[f])
van = C.load_vanilla()
scripts = C.load_scripts()
TOK = re.compile(r'[A-Za-z0-9_.\-]+')
tokset = set()
for t in scripts.values():
    tokset.update(TOK.findall(t))

SUF = re.compile(r'(_desc|_tooltip|_tt|_confirm|_name|_title|_effect_tooltip|_flavor|_adj|_succession_desc|_i)$')


def stems(k):
    s = set()
    k2 = SUF.sub('', k)
    s.add(k2)
    for p in ('trait_', 'building_type_', 'building_', 'modifier_', 'catalyst_', 'situation_', 'game_concept_', 'task_', 'activity_', 'culture_parameter_', 'house_aspiration_'):
        if k2.startswith(p):
            s.add(k2[len(p):])
    return s


print('== 1) 被删除键的隐式引用检查')
deleted = [k for k in bak_map if k not in cur_map and k not in van]
risk = []
for k in deleted:
    if k in tokset:
        risk.append((k, '键名本身仍出现在脚本中'))
        continue
    for s in stems(k):
        if s != k and s in tokset and len(s) > 6:
            risk.append((k, '词干 %s 仍在脚本中' % s))
            break
print('删除键总数', len(deleted), '；可疑', len(risk))
for k, why in risk:
    print('  RISK', k, '|', why)

print('== 2) 改动过的中文本地化文件')
nerr = 0
for f, d in cur_all.items():
    b = bak_all.get(f)
    p = os.path.join(MOD, 'localization', f.replace('/', os.sep))
    raw = open(p, 'rb').read()
    bp = os.path.join(BACKUP, 'localization', f.replace('/', os.sep))
    if os.path.exists(bp) and open(bp, 'rb').read() == raw:
        continue
    txt = raw.decode('utf-8-sig', errors='replace')
    if not raw.startswith(b'\xef\xbb\xbf'):
        print('  ERROR 缺BOM', f); nerr += 1
    first = next((l for l in txt.splitlines() if l.strip() and not l.strip().startswith('#')), '')
    if first.strip() != 'l_simp_chinese:':
        print('  ERROR 首行', f); nerr += 1
    for i, ln in enumerate(txt.splitlines(), 1):
        s = ln.strip()
        if not s or s.startswith('#') or s == 'l_simp_chinese:':
            continue
        if not C.KEYLINE.match(ln):
            print('  ERROR 行格式 %s:%d %s' % (f, i, s[:60])); nerr += 1
    for k, v in d.items():
        old = (b or {}).get(k)
        if old == v:
            continue
        for ref in re.findall(r'\$([A-Za-z0-9_.\-]+)\$', v):
            if ref not in cur_map and ref not in van and not ref.startswith(('EFFECT_LIST', 'BULLET', 'TAB', 'COMMA', 'VALUE')):
                print('  ERROR $ref$ 不存在 %s %s -> %s' % (f, k, ref)); nerr += 1
        if ('$%s$' % k) in v:
            print('  ERROR 自我引用 %s %s' % (f, k)); nerr += 1
        o1, c1 = C.fmt_balance(v)
        if o1 != c1:
            ob = C.fmt_balance(old) if old else (0, 0)
            if ob[0] - ob[1] != o1 - c1:
                print('  ERROR 格式码 %s %s' % (f, k)); nerr += 1
print('本地化错误', nerr)

print('== 3) 改动脚本中新引用的本地化键')
nerr = 0
for rel, t in scripts.items():
    if not rel.endswith('.txt'):
        continue
    bp = os.path.join(BACKUP, rel.replace('/', os.sep))
    if not os.path.exists(bp):
        continue
    bt = open(bp, 'rb').read().decode('utf-8-sig', errors='replace')
    if bt == t:
        continue
    for l in difflib.ndiff(bt.splitlines(), t.splitlines()):
        if not l.startswith('+ '):
            continue
        code = l[2:].split('#')[0]
        for _, key in C.REF_RE.findall(code):
            if key in ('yes', 'no', 'root', 'this', 'prev') or key.startswith(('scope', 'var', 'local_var', 'global_var', 'flag')):
                continue
            if not re.search(r'[._]', key):
                continue
            if key not in cur_map and key not in van:
                print('  ERROR %s: %s' % (rel, key)); nerr += 1
print('脚本引用错误', nerr)
