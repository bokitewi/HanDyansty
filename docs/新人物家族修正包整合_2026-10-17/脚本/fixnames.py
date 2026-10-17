import sys, os, re, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.dirname(__file__))
import charmerge_lib as L
mod, out = sys.argv[1], sys.argv[2]
CH = 'history/characters'
v = json.load(open(os.path.join(out, 'validate.json'), encoding='utf-8')); b = json.load(open(sys.argv[3], encoding='utf-8'))
bad = {x.split(': ')[0]: x.split(': ')[1] for x in v['name_key_missing'] if x not in set(b['name_key_missing'])}
wt = {}
for f in os.listdir(os.path.join(mod, CH)):
    if f.endswith('.txt'): wt.update(L.blocks_of(L.dec(open(os.path.join(mod, CH, f), 'rb').read())))
for f in os.listdir(os.path.join(out, CH)):
    p = os.path.join(out, CH, f); t = L.dec(open(p, 'rb').read()); segs = L.parse(t); ch = False; parts = []
    for s in segs:
        if s[0] == 'blk' and s[1] in bad:
            k, key = s[1], bad[s[1]]; blk = s[2]
            m = re.search(r'^\s*name\s*=\s*"?([^"\s}#]+)', wt.get(k, ''), re.M)
            if m and m.group(1) != key and m.group(1) not in bad.values():
                new = m.group(1); how = 'mod原名'
            else:
                hx = re.findall(r'_([0-9A-F]{4,5})(?=_|$)', key)
                if hx:
                    if key.startswith('dynn_'): hx = hx[:1]
                    new = '"' + ''.join(chr(int(h, 16)) for h in hx) + '"'; how = '编码转汉字'
                else: new = None; how = '无法修复'
            if new:
                blk = re.sub(r'(^\s*name\s*=\s*)"?' + re.escape(key) + r'"?', lambda mm: mm.group(1) + new, blk, count=1, flags=re.M); ch = True
            print(k, key, '->', new, how)
            parts.append(blk)
        else: parts.append(s[1] if s[0] == 'text' else s[2])
    if ch: open(p, 'w', encoding='utf-8-sig', newline='\n').write('\n'.join(parts))
