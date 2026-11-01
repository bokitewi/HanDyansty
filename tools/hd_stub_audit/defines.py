import os, re, sys
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD


def load(root):
    d = {}
    for dp, dn, fn in os.walk(os.path.join(root, 'common/defines')):
        for f in sorted(fn):
            if not f.endswith('.txt'):
                continue
            rel = os.path.relpath(os.path.join(dp, f), root).replace('\\', '/')
            toks, lines = pdx.tokenize(pdx.read(os.path.join(dp, f)))
            stack = []
            i = 0
            while i < len(toks):
                t = toks[i]
                if i + 2 < len(toks) and toks[i + 1] == '=' and toks[i + 2] == '{':
                    if not stack:
                        stack.append(t)
                        i += 3
                        continue
                    # array value
                    j = i + 3
                    vals = []
                    while toks[j] != '}':
                        vals.append(toks[j]); j += 1
                    d[(stack[0], t)] = (' '.join(vals), rel, lines[i])
                    i = j + 1
                    continue
                if t == '}':
                    if stack:
                        stack.pop()
                    i += 1
                    continue
                if stack and i + 2 < len(toks) and toks[i + 1] == '=':
                    d[(stack[0], t)] = (toks[i + 2], rel, lines[i])
                    i += 3
                    continue
                i += 1
    return d


v, m = load(VAN), load(MOD)
chg = []
for k, (val, rel, ln) in m.items():
    if k in v and v[k][0] != val:
        chg.append((k, v[k][0], val, rel, ln))
print('changed defines:', len(chg))
for k, vv, mv, rel, ln in sorted(chg):
    print(f'{k[0]}.{k[1]}: {vv[:60]} -> {mv[:60]}   [{rel}:{ln}]')
miss = [k for k in v if k not in m]
print('vanilla-only defines (inherit vanilla unless file shadowed):')
shadow = set()
for k in miss:
    rel = v[k][1]
    if os.path.exists(os.path.join(MOD, rel)):
        shadow.add((k, rel))
print(len(shadow), 'defines lost via shadowed file')
for k, rel in sorted(shadow):
    print('  LOST', k, v[k][0][:50], rel)
