import sys, os, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
from charmerge_lib import blocks_of, dec
mod, src = sys.argv[1], sys.argv[2]
CH = 'history/characters'
loc = {}
for root, _, files in os.walk(os.path.join(mod, 'localization')):
    if 'english' in root: continue
    for f in files:
        if f.endswith('.yml'):
            for line in dec(open(os.path.join(root, f), 'rb').read()).split('\n'):
                m = re.match(r'\s*([A-Za-z0-9_\-\.]+):\d*\s*"(.*)"', line)
                if m: loc[m.group(1)] = m.group(2)
CJK = re.compile(r'[㐀-鿿\U00020000-\U0002ffff]')
def given(name):
    if not name: return None
    if CJK.search(name): return ''.join(CJK.findall(name))
    hx = re.findall(r'_([0-9A-F]{4,5})(?=_|$)', name)
    if hx:
        try: return ''.join(chr(int(h, 16)) for h in hx)
        except Exception: pass
    v = loc.get(name)
    if v and CJK.search(v): return ''.join(CJK.findall(v))
    return None
def sig(b):
    head = b.split('\n', 1)[0]
    com = head.split('#', 1)[1].strip() if '#' in head else ''
    n = re.search(r'^\s*name\s*=\s*"?([^"\s#]+)', b, re.M)
    y = re.search(r'(\d+)\.\d+\.\d+\s*=\s*\{\s*birth', b)
    h = re.search(r'^\s*dynasty(?:_house)?\s*=\s*"?([A-Za-z0-9_]+)', b, re.M)
    cn = ''.join(CJK.findall(re.split(r'[，,\s字（(/|]', com)[0])) if com else ''
    return dict(g=given(n.group(1) if n else None), birth=int(y.group(1)) if y else None,
                house=h.group(1) if h else None, cn=cn, fem=bool(re.search(r'^\s*female\s*=\s*yes', b, re.M)))
def same(a, b, tol=15):
    if a['birth'] and b['birth'] and abs(a['birth'] - b['birth']) > tol: return False
    sfx = lambda x, y: x == y or x.endswith(y) or y.endswith(x)
    if a['cn'] and b['cn'] and sfx(a['cn'], b['cn']): return True
    if a['g'] and b['g'] and sfx(a['g'], b['g']): return True
    if a['birth'] and a['birth'] == b['birth'] and tol >= 15: return True
    if not (a['g'] and b['g']) and not (a['cn'] and b['cn']): return a['birth'] == b['birth']
    return False
wt = {}
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt'):
        for k, v in blocks_of(dec(open(os.path.join(mod, CH, f), 'rb').read())).items(): wt[k] = (f, v)
pk = {}
for f in os.listdir(os.path.join(src, CH)):
    for k, v in blocks_of(dec(open(os.path.join(src, CH, f), 'rb').read())).items(): pk[k] = (f, v)
pkfiles = {f for f in os.listdir(os.path.join(src, CH)) if os.path.getsize(os.path.join(src, CH, f)) > 0}
WS = {k: sig(v) for k, (f, v) in wt.items()}; PS = {k: sig(v) for k, (f, v) in pk.items()}
repurposed = [k for k in pk if k in wt and not same(WS[k], PS[k], tol=10**6)]
print('REPURPOSED', len(repurposed))
for k in repurposed: print('  ', k, wt[k][0], '->', pk[k][0], '| mod', WS[k]['g'], WS[k]['birth'], WS[k]['cn'], '| pkg', PS[k]['g'], PS[k]['birth'], PS[k]['cn'])
# candidates: package ids that are new or repurposed
cand = [k for k in pk if k not in wt] + repurposed
byg = collections.defaultdict(list)
for k in cand: byg[PS[k]['g'] or PS[k]['cn']].append(k)
leaving = [k for k, (f, v) in wt.items() if f in pkfiles and k not in pk] + repurposed
ren = {}; unmatched = []
used = set()
for k in leaving:
    s = WS[k]; key = s['g'] or s['cn']
    c = [x for x in byg.get(key, []) if x != k and same(s, PS[x], tol=5) and x not in used]
    if key in ('某', '氏', None, '') or (s['cn'] and s['cn'][-1] in '某氏'):
        c = [x for x in c if s['cn'] and PS[x]['cn'] == s['cn'] and abs((PS[x]['birth'] or 0) - (s['birth'] or 0)) <= 2]
    if len(c) > 1 and s['house']:
        c2 = [x for x in c if PS[x]['house'] and (PS[x]['house'].split('_')[-1] == s['house'].split('_')[-1])]
        c = c2 or c
    if len(c) > 1:
        c.sort(key=lambda x: abs((PS[x]['birth'] or 0) - (s['birth'] or 0)))
    if c: ren[k] = c[0]; used.add(c[0])
    else: unmatched.append(k)
# pass 2: unmatched -> same surname + given name ignoring birth, or same surname + birth+-2 + same given length
def surname(x):
    return x['cn'][0] if x['cn'] else None
still = []
for k in unmatched:
    s = WS[k]
    c = [x for x in cand if x not in used and x != k and surname(PS[x]) and surname(PS[x]) == surname(s)
         and ((s['g'] and PS[x]['g'] and s['g'] == PS[x]['g'] and s['g'] not in ('某', '氏'))
              or (s['cn'] and PS[x]['cn'] == s['cn'] and s['cn'][-1] not in '某氏'))]
    if len(c) != 1 and s['birth']:
        c = [x for x in cand if x not in used and x != k and surname(PS[x]) == surname(s) and surname(s)
             and PS[x]['birth'] and abs(PS[x]['birth'] - s['birth']) <= 2 and PS[x]['g'] and s['g']
             and len(PS[x]['g']) == len(s['g']) and PS[x]['fem'] == s['fem']]
    if len(c) == 1: ren[k] = c[0]; used.add(c[0])
    else: still.append((k, c[:5]))
unmatched = [k for k, _ in still]
print('PASS2 ambiguous/unmatched detail')
for k, c in still: print('    ', k, WS[k]['g'], WS[k]['birth'], WS[k]['cn'], 'cands', c)
print('RENAMED', len(ren))
for k, v in ren.items(): print('  ', k, WS[k]['g'], WS[k]['birth'], '->', v, PS[v]['g'], PS[v]['birth'], pk[v][0])
print('UNMATCHED (author removed, no replacement)', len(unmatched))
for k in unmatched: print('  ', k, wt[k][0], WS[k]['g'], WS[k]['birth'], WS[k]['cn'], 'REPURPOSED' if k in repurposed else '')
json.dump({'repurposed': repurposed, 'ren': ren, 'unmatched': unmatched}, open(os.path.join(os.path.dirname(__file__), 'identity2.json'), 'w', encoding='utf-8'), ensure_ascii=False)
