"""postfix.py MOD PKG OUT : (a) dedupe single-valued depth-1 keys (keep package value) (b) re-add mod trait lines dropped by merges"""
import sys, os, re, collections
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
CH = 'history/characters'
SINGLE = ('name', 'father', 'mother', 'dynasty', 'dynasty_house', 'culture', 'rite', 'female', 'sexuality', 'health', 'fertility',
          'diplomacy', 'martial', 'stewardship', 'intrigue', 'learning', 'prowess')
wt = {}
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt'): wt.update(L.blocks_of(L.dec(open(os.path.join(mod, CH, f), 'rb').read())))
pk = {}
for f in os.listdir(os.path.join(src, CH)):
    pk.update(L.blocks_of(L.dec(open(os.path.join(src, CH, f), 'rb').read())))
merged_ids = set()
sec = None
for line in open(os.path.join(out, 'report.txt'), encoding='utf-8'):
    if line.startswith('## '): sec = line.split()[1]; continue
    if sec in ('merged_conflict_pkgwins', 'merged_clean'): merged_ids.add(line.split()[0])
def depth1(block):
    """yield (lineindex, key, value) for depth-1 assignments"""
    depth = 0
    for i, line in enumerate(block.split('\n')):
        code = line.split('#', 1)[0]
        if depth == 1:
            for m in re.finditer(r'(?:^|\s)([A-Za-z_]+)\s*=\s*("[^"]*"|[^\s{}]+)', code):
                yield i, m.group(1), m.group(2).strip('"')
        depth += code.count('{') - code.count('}')
log = collections.defaultdict(list)
def fix(k, b):
    lines = b.split('\n')
    # (a) duplicates
    seen = collections.defaultdict(list)
    for i, key, val in depth1(b):
        if key in SINGLE: seen[key].append((i, val))
    pvals = {key: val for _, key, val in depth1(pk.get(k, ''))}
    drop = set()
    for key, occ in seen.items():
        if len(occ) > 1:
            keep = next((i for i, v in occ if v == pvals.get(key)), occ[-1][0])
            for i, v in occ:
                if i != keep: drop.add(i)
            log['dup_key'].append(f'{k}: {key} {[v for _, v in occ]} -> {pvals.get(key, occ[-1][1])}')
    # (b) dropped mod traits
    add = []
    if k in merged_ids and k in wt:
        have = {v for _, key, v in depth1(b) if key == 'trait'}
        pkt = {v for _, key, v in depth1(pk.get(k, '')) if key == 'trait'}
        for _, key, v in depth1(wt[k]):
            if key == 'trait' and v not in have and v not in add:
                add.append(v); log['trait_readded'].append(f'{k}: {v}')
    if not drop and not add: return b
    lines = [l for i, l in enumerate(lines) if i not in drop]
    if add:
        # insert after the first depth-1 line
        lines.insert(1, '\n'.join(f'\ttrait = {t}' for t in add))
    return '\n'.join(lines)
for f in os.listdir(os.path.join(out, CH)):
    p = os.path.join(out, CH, f); t = L.dec(open(p, 'rb').read())
    parts = [s[1] if s[0] == 'text' else fix(s[1], s[2]) for s in L.parse(t)]
    nt = '\n'.join(parts)
    if nt != t: open(p, 'w', encoding='utf-8-sig', newline='\n').write(nt)
with open(os.path.join(out, 'postfix.txt'), 'w', encoding='utf-8') as fh:
    for k, v in log.items(): fh.write(f'## {k} {len(v)}\n' + '\n'.join(v) + '\n')
for k, v in log.items(): print(k, len(v), v[:8])
