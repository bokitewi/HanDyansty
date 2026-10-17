"""datecheck.py MOD OUT : title holders / bookmark chars alive at their dates, baseline vs merged"""
import sys, os, re, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, out = sys.argv[1], sys.argv[2]
CH = 'history/characters'
def life(b):
    bd = dd = None
    for m in re.finditer(r'(\d+)\.(\d+)\.(\d+)\s*=\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}', b):
        d = tuple(int(x) for x in m.groups()[:3]); body = m.group(4)
        if re.search(r'\bbirth\s*=', body) and bd is None: bd = d
        if re.search(r'\bdeath\s*=', body) and dd is None: dd = d
    return bd, dd
def load(over):
    ch = {}
    for f in os.listdir(os.path.join(mod, CH)):
        if f.endswith('.txt') and not (over and os.path.exists(os.path.join(over, CH, f))):
            for k, v in L.blocks_of(L.dec(open(os.path.join(mod, CH, f), 'rb').read())).items(): ch[k] = life(v)
    if over:
        for f in os.listdir(os.path.join(over, CH)):
            for k, v in L.blocks_of(L.dec(open(os.path.join(over, CH, f), 'rb').read())).items(): ch[k] = life(v)
    return ch
base = load(None); new = load(out)
def tfile(rel):
    p = os.path.join(out, 'other', rel)
    return p if os.path.exists(p) else os.path.join(mod, rel)
refs = []  # (id, date, where)
td = os.path.join(mod, 'history/titles')
for f in os.listdir(td):
    t = L.dec(open(tfile('history/titles/' + f), 'rb').read())
    for m in re.finditer(r'(\d+)\.(\d+)\.(\d+)\s*=\s*\{([^{}]*)\}', t):
        d = tuple(int(x) for x in m.groups()[:3])
        for h in re.finditer(r'\bholder\s*=\s*"?([A-Za-z0-9_]+)', m.group(4)):
            if h.group(1) != '0': refs.append((h.group(1), d, 'titles/' + f))
bm = L.dec(open(os.path.join(mod, 'common/bookmarks/bookmarks/00_bookmarks.txt'), 'rb').read())
for name, blk in L.blocks_of(bm).items():
    sd = re.search(r'start_date\s*=\s*(\d+)\.(\d+)\.(\d+)', blk)
    if not sd: continue
    d = tuple(int(x) for x in sd.groups())
    for c in re.finditer(r'\bhistory_id\s*=\s*"?([A-Za-z0-9_]+)', blk): refs.append((c.group(1), d, 'bookmark ' + name))
def ok(lf, d):
    if lf is None: return 'missing'
    b, e = lf
    if b and b > d: return f'unborn(b{b[0]})'
    if e and e <= d: return f'dead(d{e[0]})'
    return None
bad = []
for i, d, w in refs:
    nb, ob = ok(new.get(i), d), ok(base.get(i), d)
    if nb and not ob: bad.append((i, d[0], w, nb, base.get(i), new.get(i)))
print('refs', len(refs), 'newly invalid', len(bad))
for x in bad: print(x)
