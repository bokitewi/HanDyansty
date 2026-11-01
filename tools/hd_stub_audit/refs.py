"""For each deleted vanilla key, count references in the effective game (mod files + unshadowed vanilla files, incl. gui)."""
import os, re, sys, pickle, json, collections
sys.path.insert(0, os.path.dirname(__file__))
import pdx
from audit import VAN, MOD, OUT, replaced

vf, mf, vi, mi = pickle.load(open(os.path.join(OUT, 'idx.pkl'), 'rb'))
d = json.load(open(os.path.join(OUT, 'deleted.json'), encoding='utf-8'))
SKIP = ('common/province_terrain', 'common/connection_arrows', 'common/legends/legend_seeds', 'common/flavorization')
keys = {x['key'] for x in d if x['db'] not in SKIP}


def effective_files():
    seen = {}
    for root in (MOD, VAN):
        for top in ('common', 'events', 'gui'):
            for dp, dn, fn in os.walk(os.path.join(root, top)):
                for f in fn:
                    if not f.endswith(('.txt', '.gui')):
                        continue
                    rel = os.path.relpath(os.path.join(dp, f), root).replace('\\', '/')
                    if rel in seen:
                        continue
                    if root == VAN and replaced(rel):
                        continue
                    seen[rel] = (root, os.path.join(dp, f))
    return seen


eff = effective_files()
word = re.compile(r'[A-Za-z0-9_.&\-]+')
hits = collections.defaultdict(list)
for rel, (root, ab) in eff.items():
    text = pdx.read(ab)
    # strip comments
    text = re.sub(r'#[^\n]*', '', text)
    for ln, line in enumerate(text.split('\n'), 1):
        for w in word.findall(line):
            if w in keys:
                hits[w].append(('M' if root == MOD else 'V') + ':' + rel + ':' + str(ln))
out = []
for x in d:
    if x['db'] in SKIP:
        continue
    h = [r for r in hits.get(x['key'], [])]
    # drop the definition line itself (not present since deleted)
    out.append(dict(x, nref=len(h), refs=h[:8]))
json.dump(out, open(os.path.join(OUT, 'deleted_refs.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
for x in out:
    if x['nref']:
        print(x['nref'], x['key'], x['vrel'], '->', x['refs'][:4])
