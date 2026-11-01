import os, re, sys, pickle, json
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD, OUT

vf, mf, vi, mi = pickle.load(open(os.path.join(OUT, 'idx.pkl'), 'rb'))
LISTS = {'events', 'random_events', 'first_valid', 'on_actions', 'random_on_actions', 'first_valid_on_action', 'random_on_action'}


def entries(toks):
    """Return list of (listkind, entry) inside an on_action block."""
    out = []
    i, n = 0, len(toks)
    depth = 0
    stack = []
    while i < n:
        t = toks[i]
        if t == '{':
            k = toks[i - 2] if i >= 2 and toks[i - 1] == '=' else '_'
            stack.append(k)
        elif t == '}':
            if stack:
                stack.pop()
        else:
            if len(stack) == 2 and stack[1] in LISTS:
                # skip `key = value` pairs except weight = event
                if i + 1 < n and toks[i + 1] == '=':
                    if re.match(r'^\d+(\.\d+)?$', t) and i + 2 < n and toks[i + 2] not in ('{',):
                        out.append((stack[1], toks[i + 2]))
                    i += 2 if toks[i + 2] != '{' else 1
                    continue
                if not re.match(r'^-?\d+(\.\d+)?$', t):
                    out.append((stack[1], t))
        i += 1
    return out


res = []
van = vi.get('common/on_action', {})
mod = mi.get('common/on_action', {})
# all event ids that exist effectively (vanilla unshadowed + mod)
ev_exist = set()
for key, lst in vi.get('events', {}).items():
    if any(v[0] not in mf for v in lst):
        ev_exist.add(key)
ev_exist |= set(mi.get('events', {}).keys())

for key, vlist in van.items():
    vall = set()
    for vrel, vt, vln, vlines in vlist:
        for e in entries(vt):
            vall.add((vrel, e))
    eff = set()
    for vrel, vt, vln, vlines in vlist:
        if vrel not in mf:
            eff |= {e for e in entries(vt)}
    for mrel, mt, mln, mlines in mod.get(key, []):
        eff |= {e for e in entries(mt)}
    effents = {e[1] for e in eff}
    for vrel, e in sorted(vall):
        if e[1] not in effents:
            res.append(dict(on_action=key, vrel=vrel, list=e[0], entry=e[1],
                            exists=(e[1] in ev_exist) if '.' in e[1] else (e[1] in van or e[1] in mod)))

json.dump(res, open(os.path.join(OUT, 'onaction_missing.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print(len(res))
from collections import Counter
c = Counter((r['on_action'], r['vrel']) for r in res)
for (k, f), n in c.most_common(60):
    ex = [r['entry'] for r in res if r['on_action'] == k and r['vrel'] == f]
    exi = [r['exists'] for r in res if r['on_action'] == k and r['vrel'] == f]
    print(f'{n:3d} {k:45s} {f}  exist={sum(exi)}  {ex[:6]}')
