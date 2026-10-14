# -*- coding: utf-8 -*-
import os, re, sys, csv, json, pickle
from collections import defaultdict

MOD = r'E:/documents/Paradox Interactive/Crusader Kings III/mod/HanDyansty'
GAME = r'D:/SteamLibrary/steamapps/common/Crusader Kings III/game'
OUT = os.path.dirname(os.path.abspath(__file__))

TOKEN = re.compile(r'"[^"]*"|[{}]|[<>!]?=|[^\s{}=<>"#]+|#[^\n]*|\n')


def parse_top(text):
    """返回 [(key, body_items, line, comment)]，body_items 为嵌套列表"""
    toks = []
    line = 1
    for m in TOKEN.finditer(text):
        t = m.group(0)
        if t == '\n':
            line += 1
            continue
        toks.append((t, line))
    pos = 0
    n = len(toks)

    def block():
        nonlocal pos
        items = []
        while pos < n:
            t, ln = toks[pos]
            if t.startswith('#'):
                pos += 1
                continue
            if t == '}':
                pos += 1
                return items
            if t == '{':
                pos += 1
                items.append((None, block(), ln))
                continue
            # find next non-comment
            q = pos + 1
            while q < n and toks[q][0].startswith('#'):
                q += 1
            if q < n and toks[q][0] in ('=', '>=', '<=', '!=', '>', '<'):
                key = t
                pos = q + 1
                while pos < n and toks[pos][0].startswith('#'):
                    pos += 1
                if pos < n and toks[pos][0] == '{':
                    pos += 1
                    items.append((key, block(), ln))
                else:
                    items.append((key, toks[pos][0].strip('"') if pos < n else '', ln))
                    pos += 1
            else:
                items.append((None, t.strip('"'), ln))
                pos += 1
        return items

    # top level with comments captured
    res = []
    while pos < n:
        t, ln = toks[pos]
        if t.startswith('#'):
            pos += 1
            continue
        q = pos + 1
        if q < n and toks[q][0] == '=':
            key = t
            pos = q + 1
            if pos < n and toks[pos][0] == '{':
                cm = ''
                if pos + 1 < n and toks[pos + 1][0].startswith('#') and toks[pos + 1][1] == ln:
                    cm = toks[pos + 1][0]
                pos += 1
                body = block()
                res.append((key, body, ln, cm))
            else:
                pos += 1
        else:
            pos += 1
    return res


def read(p):
    return open(p, encoding='utf-8-sig', errors='replace').read()


def walk(d, ext='.txt'):
    for dp, _, fs in os.walk(d):
        for f in sorted(fs):
            if f.endswith(ext):
                yield os.path.join(dp, f)


# ---------- localization
LOC = {}
LOCRE = re.compile(r'^\s*([\w\.\-]+):\d*\s*"(.*)"')
for base in [os.path.join(GAME, 'localization/simp_chinese'), os.path.join(MOD, 'localization/simp_chinese'),
             os.path.join(MOD, 'localization/replace/simp_chinese')]:
    for p in walk(base, '.yml'):
        for l in read(p).split('\n'):
            m = LOCRE.match(l)
            if m:
                LOC[m.group(1)] = m.group(2)


def loc(k):
    if k is None:
        return ''
    v = LOC.get(k, k)
    # resolve $key$
    for _ in range(3):
        mm = re.search(r'\$([\w\.]+)\$', v)
        if not mm:
            break
        v = v.replace(mm.group(0), LOC.get(mm.group(1), ''))
    return v


# ---------- dynasties / houses
DYN = {}
for p in list(walk(os.path.join(MOD, 'common/dynasties'))) + list(walk(os.path.join(GAME, 'common/dynasties'))):
    for k, body, ln, cm in parse_top(read(p)):
        if k in DYN:
            continue
        d = {kk: vv for kk, vv, _ in body if isinstance(vv, str)}
        DYN[k] = d
HOUSE = {}
for p in list(walk(os.path.join(MOD, 'common/dynasty_houses'))) + list(walk(os.path.join(GAME, 'common/dynasty_houses'))):
    for k, body, ln, cm in parse_top(read(p)):
        if k in HOUSE:
            continue
        HOUSE[k] = {kk: vv for kk, vv, _ in body if isinstance(vv, str)}


def surname(c):
    dyn = c.get('dynasty')
    h = c.get('dynasty_house')
    if h and h in HOUSE:
        dyn = HOUSE[h].get('dynasty', dyn)
    if dyn and dyn in DYN:
        nm = loc(DYN[dyn].get('name'))
        pre = DYN[dyn].get('prefix')
        return nm
    if h and h in HOUSE:
        return loc(HOUSE[h].get('name'))
    return ''


def date(s):
    try:
        y, m, d = (int(x) for x in s.split('.'))
        return (y, m, d)
    except Exception:
        return None


# ---------- characters
CH = []  # list of dicts (all definitions, including duplicate ids)
files = sorted(f for f in os.listdir(os.path.join(MOD, 'history/characters')) if f.endswith('.txt'))
for f in files:
    for cid, body, ln, cm in parse_top(read(os.path.join(MOD, 'history/characters', f))):
        if not isinstance(body, list):
            continue
        c = dict(id=cid, file=f, line=ln, comment=cm.lstrip('#').strip(), birth=None, death=None,
                 father=None, mother=None, female='no', spouses=[])
        for k, v, _ in body:
            if k is None:
                continue
            d = date(k)
            if d and isinstance(v, list):
                for kk, vv, _ in v:
                    if kk == 'birth' and c['birth'] is None:
                        c['birth'] = d
                    elif kk == 'death' and c['death'] is None:
                        c['death'] = d
                    elif kk in ('add_spouse', 'add_matrilineal_spouse') and isinstance(vv, str):
                        c['spouses'].append(vv)
            elif isinstance(v, str) and k not in ('trait',):
                c[k] = v
        c['given'] = loc(c.get('name'))
        c['surname'] = surname(c)
        CH.append(c)

pickle.dump(dict(CH=CH, LOC=LOC, DYN=DYN, HOUSE=HOUSE), open(os.path.join(OUT, 'chars.pkl'), 'wb'))
print('chars', len(CH), 'files', len(files))
