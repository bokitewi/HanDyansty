# -*- coding: utf-8 -*-
"""2026-10-18 同人合并的防复发：修正包合并输出里再出现已删 ID 时，删掉其人物块、把引用改指并入方。

用法：python -I tools/apply_del18.py "<mod 目录>" <输出目录>   （pipeline.sh 末尾调用）
名单：<mod>/docs/人物审查/合并记录_2026-10-18.csv（删除ID -> 并入ID）
"""
import csv, os, re, sys

mod, out = sys.argv[1:3]
M = {r['删除ID']: r['并入ID'] for r in
     csv.DictReader(open(os.path.join(mod, 'docs/人物审查/合并记录_2026-10-18.csv'), encoding='utf-8-sig'))}
# 2026-10-19 吴郡孙氏合并：OE 孙氏宗室副本同样删块改指
M.update({r['删除ID']: r['并入ID'] for r in
          csv.DictReader(open(os.path.join(mod, 'docs/人物审查/合并记录_2026-10-19.csv'), encoding='utf-8-sig'))})
# 2026-10-25 貂蝉、二乔、清河公主、太原郭氏、潘岳、裴楷去重：同样删块改指
M.update({r['删除ID']: r['并入ID'] for r in
          csv.DictReader(open(os.path.join(mod, 'docs/人物审查/合并记录_2026-10-25.csv'), encoding='utf-8-sig'))})
# 2026-10-25「某氏」甄别：UUII 无关联的某氏 1,000 人纯删除，没有并入方，只删块、不改引用
DROP = {r['角色ID'] for r in
        csv.DictReader(open(os.path.join(mod, 'docs/人物审查/某氏甄别记录_2026-10-25.csv'), encoding='utf-8-sig'))
        if r['处理'] == '删除'}
# 2026-10-19：人物文件里的富春孙氏改回吴郡孙氏（只改 characters 目录，不碰家族定义文件）
HOUSE_REMAP = {'house_fuchun_sun': 'wujun_sun'}
TOK = re.compile(r'(?<![A-Za-z0-9_.:$])([A-Za-z0-9_]+)(?![A-Za-z0-9_])')
KEY = re.compile(r'([A-Za-z0-9_\-\.]+)\s*=\s*\{')


def spans(text):
    res = []; i = 0; n = len(text); depth = 0
    while i < n:
        ch = text[i]
        if ch == '#':
            j = text.find('\n', i); i = n if j < 0 else j; continue
        if ch == '"':
            i = text.find('"', i + 1) + 1; continue
        if depth == 0:
            m = KEY.match(text, i)
            if m:
                key, start, depth, i = m.group(1), text.rfind('\n', 0, i) + 1, 1, m.end(); continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                j = text.find('\n', i); end = n if j < 0 else j + 1
                res.append((key, start, end)); i = end; continue
        i += 1
    return res


def code_sub(line):
    code, cm = (line.split('#', 1) + [''])[:2] if '#' in line else (line, None)
    parts = re.split(r'("[^"]*")', code)
    parts = [('"' + M.get(p[1:-1], p[1:-1]) + '"') if p.startswith('"') else TOK.sub(lambda m: M.get(m.group(1), m.group(1)), p) for p in parts]
    return ''.join(parts) + ('' if cm is None else '#' + cm)


dropped = rewired = 0
for root, _, fs in os.walk(out):
    for f in fs:
        if not f.endswith('.txt'):
            continue
        p = os.path.join(root, f)
        raw = open(p, 'rb').read()
        is_char = os.path.basename(os.path.dirname(p)) == 'characters'
        if not any(k.encode() in raw for k in M) and not (is_char and any(k.encode() in raw for k in HOUSE_REMAP)) \
                and not (is_char and any(k.encode() in raw for k in DROP)):
            continue
        bom = raw.startswith(b'\xef\xbb\xbf')
        t = raw.decode('utf-8-sig')
        if is_char:
            for k, s, e in sorted(spans(t), key=lambda x: -x[1]):
                if k in M or k in DROP:
                    t = t[:s] + t[e:]; dropped += 1
            for a, b in HOUSE_REMAP.items():
                t = re.sub(r'(dynasty_house\s*=\s*"?)' + a + r'\b', r'\g<1>' + b, t)
        nt = '\n'.join(code_sub(l) for l in t.split('\n'))
        rewired += nt != t
        open(p, 'w', encoding='utf-8-sig' if bom else 'utf-8', newline='').write(nt)
print('del18: dropped blocks', dropped, 'files rewired', rewired)
