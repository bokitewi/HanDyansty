"""repair.py MOD GAME OUT : fix newly-introduced invalid values in OUT/history/characters (in place). log -> OUT/repair.txt"""
import sys, os, re, collections, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, game, out = sys.argv[1], sys.argv[2], sys.argv[3]
CH = 'history/characters'
def topkeys(*dirs):
    ks = set()
    for d in dirs:
        if os.path.isdir(d):
            for root, _, fs in os.walk(d):
                for f in fs:
                    if f.endswith('.txt'): ks |= set(L.blocks_of(L.dec(open(os.path.join(root, f), 'rb').read())))
    return ks
dyn = topkeys(f'{mod}/common/dynasties', f'{game}/common/dynasties', f'{out}/common/dynasties')
house = topkeys(f'{mod}/common/dynasty_houses', f'{game}/common/dynasty_houses', f'{out}/common/dynasty_houses')
culture = topkeys(f'{mod}/common/culture/cultures', f'{game}/common/culture/cultures')
death = topkeys(f'{mod}/common/deathreasons', f'{game}/common/deathreasons')
wt = {}
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt'): wt.update(L.blocks_of(L.dec(open(os.path.join(mod, CH, f), 'rb').read())))
files = {f: os.path.join(out, CH, f) for f in os.listdir(os.path.join(out, CH))}
allids = set(wt)
for f, p in files.items(): allids |= set(L.blocks_of(L.dec(open(p, 'rb').read())))
# ids removed by merge (renamed/moved-dropped) are not valid targets any more
removed = set()
for line in open(os.path.join(out, 'report.txt'), encoding='utf-8'):
    m = re.match(r'(\S+) -> \S+ \(', line)
    if m: removed.add(m.group(1))
final_ids = set()
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt') and f not in files: final_ids |= set(L.blocks_of(L.dec(open(os.path.join(mod, CH, f), 'rb').read())))
for f, p in files.items(): final_ids |= set(L.blocks_of(L.dec(open(p, 'rb').read())))
CULT = {'di': 'diren', 'jie': 'jieren'}
DEATH = {'death_bttle': 'death_battle', 'death_exection': 'death_execution', 'death_execution_beheading': 'death_execution',
         'death_suicide_poison': 'death_suicide', 'death_suicide_hanging': 'death_suicide'}
log = collections.defaultdict(list)
def cval(C, key):
    if not C: return None
    m = re.search(r'^\s*' + key + r'\s*=\s*"?([^\s"}#]+)', C, re.M)
    return m.group(1) if m else None
def fix_block(k, b):
    C = wt.get(k)
    Cn = set(L.norm_set(C)) if C else set()
    lines = b.split('\n'); outl = []
    for line in lines:
        code, sep, com = line.partition('#')
        orig = code
        normline = L.norm_set(code)
        unchanged_from_mod = bool(normline) and normline[0] in Cn
        # religion/faith -> rite
        code = re.sub(r'^(\s*)(religion|faith)(\s*=)', r'\1rite\3', code)
        code = re.sub(r'SEXUALITY_(heterosexual|homosexual|bisexual|asexual)', r'\1', code)
        if not unchanged_from_mod:
            m = re.match(r'^(\s*culture\s*=\s*"?)([^\s"}]+)', code)
            if m and m.group(2) not in culture:
                cv = cval(C, 'culture'); nv = cv if cv in culture else CULT.get(m.group(2))
                if nv: code = code.replace(m.group(0), m.group(1) + nv); log['culture'].append(f'{k}: {m.group(2)} -> {nv}')
                else: log['culture_unfixed'].append(f'{k}: {m.group(2)}')
            m = re.match(r'^(\s*)(dynasty|dynasty_house)(\s*=\s*"?)([^\s"}]+)"?', code)
            if m and m.group(4) not in (dyn if m.group(2) == 'dynasty' else house):
                v = m.group(4); rep = None
                cd, ch = cval(C, 'dynasty'), cval(C, 'dynasty_house')
                if ch and ch in house: rep = f'dynasty_house = {ch}'
                elif cd and cd in dyn: rep = f'dynasty = {cd}'
                else:
                    base = v[:-4] if v.endswith('_dyn') else v
                    for cand, kind in ((base, 'dynasty_house'), ('hd_s2_' + base, 'dynasty_house'), ('house_' + base, 'dynasty_house'), (base, 'dynasty')):
                        if cand in (house if kind == 'dynasty_house' else dyn): rep = f'{kind} = {cand}'; break
                if rep: code = m.group(1) + rep; log['dynasty'].append(f'{k}: {m.group(2)}={v} -> {rep}')
                else: log['dynasty_unfixed'].append(f'{k}: {m.group(2)}={v}'); code = ''; com = (com + ' ') if com else ''; com = '整合时移除无效 ' + m.group(2) + '=' + v
            m = re.match(r'^(\s*)(father|mother)(\s*=\s*"?)([^\s"}]+)"?', code)
            if m and m.group(4) not in final_ids:
                cv = cval(C, m.group(2))
                if cv and cv in final_ids: code = m.group(1) + f'{m.group(2)} = {cv}'; log['parent_reverted'].append(f'{k}: {m.group(2)} {m.group(4)} -> {cv}')
                else: log['parent_removed'].append(f'{k}: {m.group(2)}={m.group(4)}'); code = ''; com = f'整合时移除无效 {m.group(2)}={m.group(4)}'
            for m in list(re.finditer(r'\b(add_spouse|add_matrilineal_spouse|add_concubine|killer|employer)\s*=\s*"?([^\s"}#]+)"?', code)):
                if m.group(2) in final_ids: continue
                # same statement present in mod with valid target?
                log['ref_removed_' + m.group(1)].append(f'{k}: {m.group(2)}')
                code = code.replace(m.group(0), '')
                if m.group(1) in ('add_spouse', 'add_matrilineal_spouse', 'add_concubine', 'employer') and re.fullmatch(r'\s*[0-9.]+\s*=\s*\{\s*\}\s*', code):
                    code = ''
            for m in list(re.finditer(r'\bdeath_reason\s*=\s*"?([^\s"}#]+)"?', code)):
                if m.group(1) in death: continue
                cv = cval(C, 'death_reason'); nv = cv if cv in death else DEATH.get(m.group(1))
                if nv: code = code.replace(m.group(0), f'death_reason = {nv}'); log['death_reason'].append(f'{k}: {m.group(1)} -> {nv}')
                else: log['death_reason_unfixed'].append(f'{k}: {m.group(1)}')
        if code != orig: log['_lines_changed'].append(k)
        if code.strip() == '' and orig.strip() != '':
            outl.append(re.match(r'\s*', orig).group(0) + ('# ' + com.strip() if com.strip() else '')); continue
        outl.append(code + (sep + com if sep or com else ''))
    return '\n'.join(outl)
for f, p in files.items():
    t = L.dec(open(p, 'rb').read())
    parts = [s[1] if s[0] == 'text' else fix_block(s[1], s[2]) for s in L.parse(t)]
    open(p, 'w', encoding='utf-8-sig', newline='\n').write('\n'.join(parts))
with open(os.path.join(out, 'repair.txt'), 'w', encoding='utf-8') as fh:
    for k, v in log.items(): fh.write(f'## {k} {len(v)}\n' + '\n'.join(v) + '\n')
for k, v in log.items(): print(k, len(v), v[:4])
