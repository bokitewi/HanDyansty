"""validate.py MOD GAME OVERLAY  -> checks character history after overlay (OVERLAY/history/characters replaces same-named mod files)
writes OVERLAY/validate.txt"""
import sys, os, re, collections, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, game, ov = sys.argv[1], sys.argv[2], sys.argv[3]
CH = 'history/characters'
def topkeys_dir(*dirs):
    ks = set()
    for d in dirs:
        if not os.path.isdir(d): continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.endswith('.txt'):
                    t = L.dec(open(os.path.join(root, f), 'rb').read())
                    ks |= set(L.blocks_of(t))
    return ks
def nested_keys(d, depth_target=1):
    """keys at depth 1 inside top-level blocks (e.g. faiths inside religions, cultures)"""
    ks = set()
    for root, _, files in os.walk(d):
        for f in files:
            if not f.endswith('.txt'): continue
            depth = 0
            for line in L.dec(open(os.path.join(root, f), 'rb').read()).split('\n'):
                s = line.split('#', 1)[0]
                m = re.match(r'\s*([A-Za-z0-9_\-\.]+)\s*=\s*\{', s)
                if m and depth == depth_target: ks.add(m.group(1))
                depth += s.count('{') - s.count('}')
    return ks
dyn = topkeys_dir(os.path.join(mod, 'common/dynasties'), os.path.join(game, 'common/dynasties'), os.path.join(ov, 'common/dynasties'))
house = topkeys_dir(os.path.join(mod, 'common/dynasty_houses'), os.path.join(game, 'common/dynasty_houses'), os.path.join(ov, 'common/dynasty_houses'))
culture = topkeys_dir(os.path.join(mod, 'common/culture/cultures'), os.path.join(game, 'common/culture/cultures'))
trait = topkeys_dir(os.path.join(mod, 'common/traits'), os.path.join(game, 'common/traits'))
death = topkeys_dir(os.path.join(mod, 'common/deathreasons'), os.path.join(game, 'common/deathreasons'))
rites = set()
for base in (mod, game):
    p = os.path.join(base, 'common/religion/religions')
    if os.path.isdir(p): rites |= nested_keys(p, 2)  # religion = { faiths = { X = {
rites |= topkeys_dir(os.path.join(mod, 'common/religion/rites'))
for base in (mod, game):
    p = os.path.join(base, 'common/religion/religions')
    if os.path.isdir(p): rites |= nested_keys(p, 1)
loc = set()
for root, _, files in list(os.walk(os.path.join(mod, 'localization'))) + list(os.walk(os.path.join(ov, 'localization'))) + list(os.walk(os.path.join(game, 'localization', 'english'))) + list(os.walk(os.path.join(game, 'localization', 'simp_chinese'))):
    if 'english' in root and not root.startswith(game): continue
    for f in files:
        if f.endswith('.yml'):
            for line in L.dec(open(os.path.join(root, f), 'rb').read()).split('\n'):
                m = re.match(r'\s*([A-Za-z0-9_\-\.]+):\d*\s*"', line)
                if m: loc.add(m.group(1))
# overlay chars
files = {}
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt'): files[f] = os.path.join(mod, CH, f)
for f in os.listdir(os.path.join(ov, CH)):
    files[f] = os.path.join(ov, CH, f)
blocks = {}; where = collections.defaultdict(list)
for f, p in sorted(files.items()):
    for k, v in L.blocks_of(L.dec(open(p, 'rb').read())).items():
        blocks[k] = v; where[k].append(f)
# count duplicates within files too
dups = {}
for f, p in sorted(files.items()):
    seen = collections.Counter(s[1] for s in L.parse(L.dec(open(p, 'rb').read())) if s[0] == 'blk')
    for k, n in seen.items():
        if n > 1: dups[k] = f'{f} x{n}'
for k, v in where.items():
    if len(v) > 1: dups[k] = v
ids = set(blocks)
issues = collections.defaultdict(list)
CJK = re.compile(r'[㐀-鿿\U00020000-\U0002ffff]')
REF = re.compile(r'\b(father|mother|killer|add_spouse|add_matrilineal_spouse|add_concubine|employer|remove_spouse|real_father)\s*=\s*"?([^\s"}#]+)')
for k, v in blocks.items():
    code = '\n'.join(l.split('#', 1)[0] for l in v.split('\n'))
    for m in REF.finditer(code):
        if m.group(2) not in ids: issues['bad_ref_' + m.group(1)].append(f'{k}: {m.group(2)}')
    for m in re.finditer(r'\bdynasty\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) not in dyn: issues['bad_dynasty'].append(f'{k}: {m.group(1)}')
    for m in re.finditer(r'\bdynasty_house\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) not in house: issues['bad_house'].append(f'{k}: {m.group(1)}')
    for m in re.finditer(r'\bculture\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) not in culture: issues['bad_culture'].append(f'{k}: {m.group(1)}')
    for m in re.finditer(r'\b(rite|religion|faith)\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) != 'rite': issues['nonrite_key_' + m.group(1)].append(f'{k}: {m.group(2)}')
        if m.group(2) not in rites: issues['bad_rite'].append(f'{k}: {m.group(2)}')
    for m in re.finditer(r'\btrait\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) not in trait: issues['bad_trait'].append(f'{k}: {m.group(1)}')
    for m in re.finditer(r'\bdeath_reason\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) not in death: issues['bad_death_reason'].append(f'{k}: {m.group(1)}')
    for m in re.finditer(r'\bsexuality\s*=\s*"?([^\s"}]+)', code):
        if m.group(1) not in ('heterosexual', 'homosexual', 'bisexual', 'asexual'): issues['bad_sexuality'].append(f'{k}: {m.group(1)}')
    for m in re.finditer(r'\bname\s*=\s*"?([^"\s}]+)', code):
        n = m.group(1)
        if not CJK.search(n) and n not in loc: issues['name_key_missing'].append(f'{k}: {n}')
    if code.count('{') != code.count('}'): issues['unbalanced'].append(k)
with open(os.path.join(ov, 'validate.txt'), 'w', encoding='utf-8') as fh:
    fh.write(f'## duplicates {len(dups)}\n' + '\n'.join(f'{k} {v}' for k, v in dups.items()) + '\n')
    for k, v in issues.items(): fh.write(f'## {k} {len(v)}\n' + '\n'.join(v) + '\n')
print('chars', len(ids), 'dups', len(dups))
for k, v in sorted(issues.items()): print(k, len(v), v[:6])
json.dump({k: v for k, v in issues.items()}, open(os.path.join(ov, 'validate.json'), 'w', encoding='utf-8'), ensure_ascii=False)
