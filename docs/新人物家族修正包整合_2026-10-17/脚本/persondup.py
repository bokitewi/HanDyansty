"""persondup.py MOD PKG OUT : new package IDs vs mod-only characters in non-package files"""
import sys, os, re, json, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
sys.argv = [sys.argv[0], mod, src]
CH = 'history/characters'
# reuse identity2 helpers
src_code = open(os.path.join(os.path.dirname(__file__), 'identity2.py'), encoding='utf-8').read()
helpers = src_code.split('wt = {}')[0]
exec(helpers)
pkfiles = {f for f in os.listdir(os.path.join(src, CH)) if os.path.getsize(os.path.join(src, CH, f)) > 0}
# final merged state
final = {}
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt'): final.update({k: (f, v) for k, v in L.blocks_of(L.dec(open(os.path.join(mod, CH, f), 'rb').read())).items()})
for f in os.listdir(os.path.join(out, CH)):
    for k in [k for k, (ff, v) in final.items() if ff == f]: del final[k]
    final.update({k: (f, v) for k, v in L.blocks_of(L.dec(open(os.path.join(out, CH, f), 'rb').read())).items()})
rep = open(os.path.join(out, 'report.txt'), encoding='utf-8').read()
newids = re.search(r'## new \d+\n(.*?)\n## ', rep, re.S).group(1).split('\n')
S = {k: sig(v) for k, (f, v) in final.items()}
def surname(x): return x['cn'][0] if x['cn'] else None
others = [k for k, (f, v) in final.items() if f not in pkfiles]
idx = collections.defaultdict(list)
for k in others:
    s = S[k]
    if s['g'] and s['g'] not in ('某', '氏'): idx[s['g']].append(k)
hits = []
for n in newids:
    s = S.get(n)
    if not s or not s['g'] or s['g'] in ('某', '氏'): continue
    c = [o for o in idx.get(s['g'], []) if S[o]['fem'] == s['fem'] and S[o]['birth'] and s['birth'] and abs(S[o]['birth'] - s['birth']) <= 5]
    # surname check: comment surname or house token overlap
    def sur_ok(o):
        a, b = surname(S[o]), surname(s)
        if a and b: return a == b
        ha, hb = (S[o]['house'] or ''), (s['house'] or '')
        return bool(ha and hb and (ha.split('_')[-1] == hb.split('_')[-1] or ha.split('_')[-1] in hb or hb.split('_')[-1] in ha))
    c = [o for o in c if sur_ok(o)]
    if c: hits.append((n, final[n][0], s['g'], s['birth'], s['cn'], s['house'], [(o, final[o][0], S[o]['birth'], S[o]['cn'], S[o]['house']) for o in c]))
print('new ids', len(newids), 'person-dup hits', len(hits))
byfile = collections.Counter(h[6][0][1] for h in hits); print(byfile.most_common())
for h in hits: print(h)
json.dump(hits, open(os.path.join(out, 'persondup.json'), 'w', encoding='utf-8'), ensure_ascii=False)
